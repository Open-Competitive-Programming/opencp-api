"""
Documentation
"""

import datetime

from apiflask import APIBlueprint
from flask import request

import schema
import kutils


auth = APIBlueprint(
    "auth",
    __name__,
    tag={
        "name": "Authentication and Authorization",
        "description": "Operations related to authentication of users",
    },
)


@auth.route("/token", methods=["POST"])
@auth.input(schema.Authentication, location="json")
@auth.output(schema.GenericResponse, status_code=200)
def api_post_users_token(json_data: dict):
    """
    Generate an OAuth2.0 token for an existing user.

    Returns:
        - A JSON response with the OAuth2.0 token.
    """

    username = json_data.get("username")
    password = json_data.get("password")

    token = kutils.get_token(username, password)

    if token:
        json, code = {
            "url": request.url,
            "success": True,
            "version": "v1",
            "timestamp": datetime.datetime.now(),
            "data": {"token": token},
        }, 200
    else:
        json, code = {
            "url": request.url,
            "success": False,
            "version": "v1",
            "timestamp": datetime.datetime.now(),
            "error": {"name": "Unauthorized", "msg": "Invalid username or password."},
        }, 401

    return json, code
