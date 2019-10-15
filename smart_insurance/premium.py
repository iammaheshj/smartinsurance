import logging
import boto3
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
        has_anti_theft = data.get("has_anti_theft", False)
        has_multi_policy = data.get("has_multi_policy", False)
        has_multi_car = data.get("has_multi_car", False)
        has_driver_training = data.get("has_driver_training", False)
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

        vehicle_info = {"detail": {
            "vehicle_type": vehicle_type,
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
            "vehicle_image_path": vehicle_image_path
        },
            "calculated": {
                "discount": discount,
                "premium": premium
            }
        }

        resp_dict = {"result":
                         {"vehicle_info": vehicle_info},
                     "response": "200"}

        # inserting data in dynamo db
        __insert_vehicle_info_into_dynamo(vehicle_info)

        response = Response(json.dumps(resp_dict), 200)

    except Exception as e:
        logger.exception("Error while calculating premium: (%s)", e)
        resp_dict = {"result": str(e), "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    logger.info(json.dumps(resp_dict, indent=4, sort_keys=True))

    return response


def __insert_vehicle_info_into_dynamo(vehicle_info):
    try:
        dynamodb = boto3.client('dynamodb')
        vehicle_details = vehicle_info['detail']
        vehicle_calculated = vehicle_info['calculated']
        item = {
            'vehicle_type': {'S': vehicle_details['vehicle_type']},
            'basic_value': {'S': str({'basic_value': vehicle_details['basic_value']})},
            'miles_run': {'S': str({'miles_run': vehicle_details['miles_run']})},
            'garage_condition': {'S': vehicle_details['garage_condition']},
            'has_anti_theft': {'B': vehicle_details['has_anti_theft']},
            'has_multi_policy': {'B': vehicle_details['has_multi_policy']},
            'has_multi_car': {'B': vehicle_details['has_multi_car']},
            'has_driver_training': {'B': vehicle_details['has_driver_training']},
            'accident_violation': {'S': str({'accident_violation': vehicle_details['accident_violation']})},
            'vehicle_number': {'S': vehicle_details['vehicle_number']},
            'vin_number': {'S': vehicle_details['vin_number']},
            'vehicle_owner': {'S': vehicle_details['vehicle_owner']},
            'vehicle_image_path': {'S': vehicle_details['vehicle_image_path']},
            'discount': {'S': str({'discount': vehicle_calculated['discount']})},
            'premium': {'S': str({'premium': vehicle_calculated['premium']})}
        }
        dynamodb.put_item(TableName='vehicle-premium-info', Item=item)
    except Exception as e:
        logger.info("Exception while inserting item '{}' in dynamo db : {}".format(item, str(e)))
        raise Exception(str(e))
