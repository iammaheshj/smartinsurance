import logging
import boto3
from flask import Flask, Response, json, request
import requests 
from urllib3.util import timeout

app = Flask(__name__)
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.route('/', methods=['GET', 'POST'])
def root(event=None, context=None):
    logger.info('root function invoked')
    resp_dict = {}

    if request.method == "GET" or request.method == "POST":
        data = request.form
        domain = data.get("domain", "")

        try:
            result = requests.get(domain, timeout=timeout).elapsed.total_seconds()
            resp_dict = {"result": result, "response": "200"}
            response = Response(json.dumps(resp_dict), 200)

        except Exception as e:
            resp_dict = {"result": str(e), "response": "408"}
            response = Response(json.dumps(resp_dict), 408)

    return response


@app.route('/vehicles', methods=['GET'])
def get_vehicle_details(event=None, context=None):
    logger.info('Lambda function invoked')
    resp_dict = {}
    try:
        client = boto3.client('s3')
        logger.info('Getting file from S3')
        s3_obj = client.get_object(Bucket='smart-insurance', Key='images/cars/10037308.jpg')
        resp_dict = {"result": "", "response": "200"}
        response = Response(json.dumps(resp_dict), 200)

    except Exception as e:
        resp_dict = {"result": str(e), "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    return response


def __get_text_from_image(photo_path):
    text_detections = None
    try:
        client=boto3.client('rekognition')
        print("Photo: ", photo_path)
        response=client.detect_text(Image={'S3Object':{'Bucket':'smart-insurance','Name': photo_path}})
        text_detections=response['TextDetections']
    except Exception as e:
        print("Exception occured while detection text from image '{}' : {}".format(photo_path, str(e)))
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
            print("Exception occured while inserting item '{}' in dyanomodb : {}".format(item, str(e)))
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


@app.route('/detect_number', methods=['GET'])
def detect_text():
    vehicle_num = ''
    try:
        photo_path = request.args.get('photo_path')
        
        text_detections = __get_text_from_image(photo_path)
        vehicle_num = __get_vehicle_number_from_txt_detections(text_detections)

        resp_dict = {"vehicle_number": vehicle_num, "response": "200", "path": photo_path}
        
        # inserting data in dynamodb
        __insert_vehicle_info_into_dynamo(resp_dict)
        
        response = Response(json.dumps(resp_dict), 200)
    except Exception as e:
        resp_dict = {"result": str(e), "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    return response


if __name__ == '__main__':
    app.run(debug=True)
