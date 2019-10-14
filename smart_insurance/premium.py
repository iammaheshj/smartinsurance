import logging
import boto3
import botocore
import requests
from flask import Response, json, request
from smart_insurance import app

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.route('/premium', methods=['POST'])
def get_premium():
    try:
        data = request.form

        vehicle_type = data.get("vehicle_type", "Unknown")
        basic_value = data.get("basic_value", 0)
        miles_run = data.get("miles_run", 0)
        garage_condition = data.get("garage_condition", "Bad")
        has_anti_theft = data.get("has_anti_theft", "false")
        has_multi_policy = data.get("has_multi_policy", "false")
        has_multi_car = data.get("has_multi_car", "false")
        has_driver_training = data.get("has_driver_training", "false")
        accident_violation = data.get("accident_violation", 0)
        vehicle_number = data.get("vehicle_number", "Unknown")
        vin_number = data.get("vin_number", "Unknown")
        vehicle_owner = data.get("vehicle_owner", "Unknown")
        vehicle_image_path = data.get("vehicle_image_path", "Unknown")

        premium = None
        discount = None

        base_premium = 0.01 * basic_value

        if miles_run < 5000:
            discount += 5

        if garage_condition.Good:
            discount += 5
        elif garage_condition.Bad:
            discount = discount - 5

        if has_anti_theft:
            discount += 2

        if has_multi_policy:
            discount += 2

        if has_multi_car:
            discount += 2

        if has_driver_training:
            discount += 2

        if 2 <= accident_violation <= 5:
            discount = discount - 5

        premium = base_premium - base_premium * discount / 100

        resp_dict = {"result":
                         {"vehicle_type": vehicle_type,
                          "basic_value": basic_value,
                          "miles_run": miles_run,
                          "garage_condition": garage_condition,
                          "has_anti_theft": has_anti_theft,
                          "has_multi_policy": has_multi_policy,
                          "has_multi_car": has_multi_car,
                          "has_driver_training": has_driver_training,
                          "accident_violation": accident_violation,
                          "vehicle_number": vehicle_number,
                          "vin_number": vin_number,
                          "vehicle_owner": vehicle_owner,
                          "vehicle_image_path": vehicle_image_path,
                          "premium": premium},
                     "response": "200"}

        # inserting data in dynamo db
        __insert_vehicle_info_into_dynamo(resp_dict)

        response = Response(json.dumps(resp_dict), 200)

    except Exception as e:
        logger.exception("Error while calculating premium: (%s)", e)
        resp_dict = {"result": str(e), "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    logger.info(json.dumps(resp_dict, indent=4, sort_keys=True))

    response = Response(json.dumps(resp_dict), 200)
    return response


def __insert_vehicle_info_into_dynamo(vehicle_info):
    try:
        dynamodb = boto3.client('dynamodb')
        item = {
            'vehicle_type': {'S': vehicle_info['vehicle_type']},
            'basic_value': {'S': str({'basic_value': vehicle_info['basic_value']})},
            'miles_run': {'S': str({'miles_run': vehicle_info['miles_run']})},
            'garage_condition': {'S': vehicle_info['garage_condition']},
            'has_anti_theft': {'B': vehicle_info['has_anti_theft']},
            'has_multi_policy': {'B': vehicle_info['has_multi_policy']},
            'has_multi_car': {'B': vehicle_info['has_multi_car']},
            'has_driver_training': {'B': vehicle_info['has_driver_training']},
            'accident_violation': {'S': str({'accident_violation': vehicle_info['accident_violation']})},
            'vehicle_number': {'S': vehicle_info['vehicle_number']},
            'vin_number': {'S': vehicle_info['vin_number']},
            'vehicle_owner': {'S': vehicle_info['vehicle_owner']},
            'vehicle_image_path': {'S': vehicle_info['vehicle_image_path']},
            'premium': {'S': str({'basic_value': vehicle_info['premium']})},
        }
        dynamodb.put_item(TableName='vehicle-premium-info', Item=item)
    except Exception as e:
        logger.info("Exception while inserting item '{}' in dynamo db : {}".format(item, str(e)))
        raise Exception(str(e))
