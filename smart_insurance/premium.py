import logging
import boto3
import botocore
import requests
from flask import Response, json, request
from smart_insurance import app

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def __get_premium(car_type,
                  basic_value,
                  miles_run,
                  garage_condition,
                  has_anti_theft,
                  has_multi_policy,
                  has_multi_car,
                  has_driver_training,
                  accident_violation):
    premium = None
    discount = None

    try:
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

        premium = base_premium - base_premium * discount/100

    except Exception as e:
        logger.exception("Error while calculating premium: (%s)", e)
        resp_dict = {"result": str(e), "response": "408"}
        response = Response(json.dumps(resp_dict), 408)

    logger.info(json.dumps(resp_dict, indent=4, sort_keys=True))

    return premium
