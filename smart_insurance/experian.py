import logging
import requests
from flask import Response, json, request
from smart_insurance import app

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.route('/experian/vehicle/vin/<vin>', methods=['GET'])
def get_expvehicle_details_by_vin(vin):
    logger.info('[API] /vehicle/vin/<vin>')
    resp_dict = {}

    try:
        endpoint = 'https://sandbox-us-api.experian.com/automotive/accuselect/v1/vinspecifications?vinlist={}'
        endpoint = endpoint.format(vin)
        logger.debug('Experian endpoint: {}'.format(endpoint))
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer eyJraWQiOiJESmpTMXJQQjdJODBHWjgybmNsSlZPQkF3V3B3ZTVYblNKZUdSZHdpcEY0IiwidHlwIjoiSldUIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiJzaGlscGFhbWRla2FyQGdtYWlsLmNvbSIsIkVtYWlsIjoic2hpbHBhYW1kZWthckBnbWFpbC5jb20iLCJGaXJzdE5hbWUiOiJTaGlscGEiLCJpc3MiOiJFWFBFUklBTiIsIkxhc3ROYW1lIjoiQW1kZWthciIsImV4cCI6MTU2ODgzNzM3MiwiaWF0IjoxNTY4ODM1NTcyLCJqdGkiOiIzOWQxN2RjYi01Y2U3LTQ0M2QtYmJkMS1hZWQ5NTc4YWU2MTAifQ.gHpMvOUnwfu1XlXH_FHnUeMdzARfbtfc62ygXSTTQX1_KzDFMKFGV4JOThKrzN1KiYZWcjgjKXiTPvM_RZ4MSM9wm1IvKZfmxE3X3V6m0H3Wu2TM1wnMe-okmwohvCQV-6ED7swdMjwkl4UWBHXDJbifQIaNN_ruY9rgunJAX6qRl4UXT4dPwvFyAeleVBu7DtaFihmQZiOvjTr3HhMbZ4D--a0QF6MAxW2Ks3h-f-QvPzyUl0mV_6SWGxFG_6INORwHJiwdrcCNQlA_VE65eG4sWMBKBz_BA0DsDrbTM-igAvKSvEthJPeS7NthSV7BUudIVA0iq9LXJneax9htNA"
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
