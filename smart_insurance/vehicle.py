import logging
import requests
import os
import boto3
from flask import Response, json, request
from smart_insurance import app

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.route('/vehicle/premium', methods=['POST'])
def get_vehicle_premium():
    """
    Calculates the premium of the vehicle

    :return:
    """
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

        premium = 0
        discount = 0

        base_premium = 0.01 * basic_value

        if miles_run < 5000:
            discount += 5

        if garage_condition == 'Good':
            discount += 5
        elif garage_condition == 'Bad':
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
        __insert_vehicle_info(vehicle_info)

        response = Response(json.dumps(resp_dict), 200)

    except Exception as e:
        logger.exception("Error while calculating premium: (%s)", e)
        resp_dict = {"result": str(e), "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    logger.info(json.dumps(resp_dict, indent=4, sort_keys=True))

    return response


def __insert_vehicle_info(vehicle_info):
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


@app.route('/vehicle/vin/<vin>', methods=['GET'])
def get_vehicle_details_by_vin(vin):
    logger.info('[API] /vehicle/vin/<vin>')
    resp_dict = {}

    try:
        endpoint = 'https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{}?format=json'
        endpoint = endpoint.format(vin)
        logger.debug('NHTSA GOV endpoint: {}'.format(endpoint))
        headers = {
            "Accept": "application/json"
        }

        vin_details = requests.get(endpoint, headers=headers).json()
        resp_dict = {"result": vin_details, "response": "200"}
        response = Response(json.dumps(resp_dict), 200)

    except Exception as e:
        logger.exception("Error while calling root", e)
        resp_dict = {"result": str(e), "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    logger.info(json.dumps(resp_dict, indent=4, sort_keys=True))
    return response


@app.route('/vehicle/detectplate/<vehicle_plate_no>/state/<state_code>', methods=['GET'])
def detect_plate(vehicle_plate_no, state_code):
    """
    Rapid API: vin-decoder API
    [https://rapidapi.com/vinfreecheck/api/vin-decoder-1?endpoint=apiendpoint_fa17ddfd-93bb-40cd-b10c-9ebdccafa76d]
    This is a VIN (Vehicle Identification Number) decoder that designed to work within North America, Asia and Europe.
    The Salvage VIN Checker only works within North America as of now
    Example API: https://5xs1vpigp8.execute-api.us-east-1.amazonaws.com/dev/vehicle/detectplate/6NTE470/state/CA
    :param vehicle_plate_no: string
    :param state_code: string
    :return:
    """
    logger.info('[API] /vehicle/detectplate/{}/state/{}'.format(vehicle_plate_no, state_code))
    resp_dict = {}
    x_rapidapi_key = os.environ.get('x_rapidapi_key')

    try:
        response = json.loads(requests.post(
            'https://vindecoder.p.rapidapi.com/api/v4/decode_plate',
            data={
                'state': state_code,
                'plate': vehicle_plate_no
            },
            headers={
                'X-RapidAPI-Key': x_rapidapi_key,
                'X-RapidAPI-Host': 'vindecoder.p.rapidapi.com'
            },
        ).text)

        if 'success' in response and response['success']:
            resp_dict = {"result": response, "response": "200"}
            response = Response(json.dumps(resp_dict), 200)
        else:
            resp_dict = {"result": response, "response": "400"}
            response = Response(json.dumps(resp_dict), 400)
    except Exception as e:
        logger.exception("Error while calling detect plate number api: (%s)", e)
        resp_dict = {"result": str(e), "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    logger.info(json.dumps(resp_dict, indent=4, sort_keys=True))

    return response


@app.route('/vehicle/report/vin/<vin>', methods=['GET'])
def get_vehicle_report(vin):
    """
    Rapid API: vin-decoder API
    [https://rapidapi.com/vinfreecheck/api/vin-decoder-1?endpoint=apiendpoint_86dfa8b9-d963-4c83-8b33-1ccb38c97c6d]
    Use This API to fetch full vehicle history report. It has 27 title brand checks, odometer records,
    and accident records.

    Example API: https://5xs1vpigp8.execute-api.us-east-1.amazonaws.com/dev/vehicle/report/vin/19XFA4F57BE000055

    :param vin: string
    :return: vehicle full history
    """
    logger.info('[API] /vehicle/report/vin/{}'.format(vin))
    resp_dict = {}
    x_rapidapi_key = os.environ.get('x_rapidapi_key')

    try:
        response = json.loads(requests.post(
            'https://vindecoder.p.rapidapi.com/api/v4/get_full_report',
            data={
                'vin': vin
            },
            headers={
                'X-RapidAPI-Key': x_rapidapi_key,
                'X-RapidAPI-Host': 'vindecoder.p.rapidapi.com'
            },
        ).text)
        logger.info('RapidAPI get full report response: {}'.format(response))

        if 'success' in response and response['success']:
            resp_dict = {"result": response, "response": "200"}
            response = Response(json.dumps(resp_dict), 200)
        else:
            resp_dict = {"result": response, "response": "400"}
            response = Response(json.dumps(resp_dict), 400)
    except Exception as e:
        logger.exception("Error while calling get full report api: (%s)", e)
        resp_dict = {"result": str(e), "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    logger.info(json.dumps(resp_dict, indent=4, sort_keys=True))

    return response


@app.route('/vehicle/salvage_check/vin/<vin>', methods=['GET'])
def get_salvage_check(vin):
    """
    Rapid API: vin-decoder API
    [https://rapidapi.com/vinfreecheck/api/vin-decoder-1?endpoint=53f5efc1e4b0e49ee00a6e10]
    Retrieve Salvage Information based on VIN Number

    Example API: https://5xs1vpigp8.execute-api.us-east-1.amazonaws.com/dev/vehicle/salvage_check/vin/19XFA4F57BE000055

    :param vin: string
    :return: vehicle full history
    """
    logger.info('[API] /vehicle/salvage_check/vin/{}'.format(vin))
    resp_dict = {}
    x_rapidapi_key = os.environ.get('x_rapidapi_key')

    try:
        response = json.loads(requests.get(
            'https://vindecoder.p.rapidapi.com/salvage_check?vin={}'.format(vin),
            headers={
                'X-RapidAPI-Key': x_rapidapi_key,
                'X-RapidAPI-Host': 'vindecoder.p.rapidapi.com'
            },
        ).text)
        logger.info('RapidAPI salvage check response: {}'.format(response))

        if 'success' in response and response['success']:
            resp_dict = {"result": response, "response": "200"}
            response = Response(json.dumps(resp_dict), 200)
        else:
            resp_dict = {"result": response, "response": "400"}
            response = Response(json.dumps(resp_dict), 400)
    except Exception as e:
        logger.exception("Error while calling salvage check api: (%s)", e)
        resp_dict = {"result": str(e), "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    logger.info(json.dumps(resp_dict, indent=4, sort_keys=True))

    return response


if __name__ == '__main__':
    app.run(debug=True)
