"""
Documentation
"""

import uuid
import datetime
import schema
import kutils

from apiflask import APIBlueprint
from flask import g, request


auth = APIBlueprint(
    "auth",
    __name__,
    tag={
        "name": "Authentication and Authorization",
        "description": "Operations related to authentication of users",
    },
)


@auth.before_request
def assign_request_id():
    """
    This function executes before any request.
    It creates a request uuid and assigns it in the global namespace variable 'g'.
    """
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))


@auth.after_request
def add_request_id_to_response(response):
    """
    This function executes after any request.
    It puts the uuid created in the 'g' global variable to the response dictionary.
    """
    response.headers["X-Request-ID"] = g.request_id
    return response


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
        return {
            "url": request.url,
            "success": True,
            "id": g.request_id,
            "version": "v1",
            "timestamp": datetime.datetime.now(),
            "data": {"token": token},
        }, 200
    else:
        return {
            "url": request.url,
            "success": False,
            "id": g.request_id,
            "version": "v1",
            "timestamp": datetime.datetime.now(),
            "error": {"name": "Unauthorized", "msg": "Invalid username or password."},
        }, 401
