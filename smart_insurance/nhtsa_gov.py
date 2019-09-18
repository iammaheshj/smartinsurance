import logging
import requests
from flask import Response, json, request
from smart_insurance import app

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
        logger.error("Error while calling root", e)
        resp_dict = {"result": str(e), "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    logger.info(json.dumps(resp_dict, indent=4, sort_keys=True))
    return response


if __name__ == '__main__':
    app.run(debug=True)
