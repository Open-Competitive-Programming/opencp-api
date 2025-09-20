"""
Documentation
"""

import datetime
from apiflask import APIBlueprint
from flask import request

import schema


problemset = APIBlueprint(
    "problemset",
    __name__,
    tag={
        "name": "Problem Set Management",
        "description": "Operations related to management of problems (CRUD)",
    },
)


@problemset.route("/", methods=["GET"])
@problemset.output(schema.SuccessfulResponse, status_code=200)
@problemset.output(schema.ErrorResponse, status_code=501)
def api_get_problems():
    """
    Gets all problems.
    """
    payload = {
        "url": request.url,
        "success": False,
        "version": "v1",
        "timestamp": datetime.datetime.now(),
        "error": {
            "name": "Not Implemented",
            "msg": "Endpoint not implemented yet",
        },
    }
    return payload, 501
