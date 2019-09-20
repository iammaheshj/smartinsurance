import logging
from flask import Response, json, request
from smart_insurance import app

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.route('/', methods=['GET'])
def root(event=None, context=None):
    logger.info('root function invoked')
    resp_dict = {}

    if request.method == "GET" or request.method == "POST":
        try:
            resp_dict = {"result": "success", "response": "200"}
            response = Response(json.dumps(resp_dict), 200)

        except Exception as e:
            logger.exception("Error while calling root", e)
            resp_dict = {"result": str(e), "response": "408"}
            response = Response(json.dumps(resp_dict), 408)

    logger.info(json.dumps(resp_dict, indent=4, sort_keys=True))
    return response


if __name__ == '__main__':
    app.run(debug=True)
