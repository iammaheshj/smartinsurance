import logging
import boto3
from flask import Response, json, request
from smart_insurance import app

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def __get_text_from_image(photo_path):
    text_detections = None
    try:
        client = boto3.client('rekognition')
        logger.info("Photo: ", photo_path)
        response = client.detect_text(Image={'S3Object': {'Bucket': 'smart-insurance', 'Name': photo_path}})
        text_detections = response['TextDetections']
    except Exception as e:
        logger.info("Exception while detection text from image '{}' : {}".format(photo_path, str(e)))
        raise Exception(str(e))
    return text_detections


def __insert_vehicle_info_into_dynamo(vehicle_info):
    try:
        dynamodb = boto3.client('dynamodb')
        item = {
            'path': {'S': vehicle_info['path']},
            'info': {'S': str({'vehicle_number': vehicle_info['vehicle_number']})}
        }
        dynamodb.put_item(TableName='vehicle-info', Item=item)
    except Exception as e:
        logger.info("Exception while inserting item '{}' in dyanomodb : {}".format(item, str(e)))
        raise Exception(str(e))


def __get_vehicle_number_from_txt_detections(text_detections):
    word_dict = {}
    vehicle_num = None
    for text in text_detections:
        if text['Type'] == "WORD" and text['Confidence'] > 80:
            parent_id = text['ParentId']
            if not word_dict.get(parent_id):
                word_dict[parent_id] = ''
            word_dict[parent_id] = word_dict[parent_id] + text['DetectedText']
    for line in word_dict:
        word = word_dict[line]
        if any(char.isdigit() for char in word) and any(char.isalpha() for char in word):
            vehicle_num = word

    return vehicle_num


@app.route('/cognitive/detect_number', methods=['GET'])
def detect_text():
    logger.info("[API] /cognitive/detect_number")
    vehicle_num = ''
    try:
        photo_path = request.args.get('photo_path')

        text_detections = __get_text_from_image(photo_path)
        vehicle_num = __get_vehicle_number_from_txt_detections(text_detections)

        resp_dict = {"result":
                         {"vehicle_number": vehicle_num,
                          "path": photo_path},
                     "response": "200"}

        # inserting data in dynamodb
        __insert_vehicle_info_into_dynamo(resp_dict)

        response = Response(json.dumps(resp_dict), 200)
    except Exception as e:
        logger.error("Error while calling root", e)
        resp_dict = {"result": str(e), "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    logger.info(json.dumps(resp_dict, indent=4, sort_keys=True))

    return response


if __name__ == '__main__':
    app.run(debug=True)
