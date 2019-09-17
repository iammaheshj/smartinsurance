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
            resp_dict = {"result": "error", "response": "408"}
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
        resp_dict = {"result": "error", "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    return response


if __name__ == '__main__':
    app.run(debug=True)
