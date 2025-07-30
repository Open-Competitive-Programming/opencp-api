"""
Documentation
"""

import uuid
import schema
import datetime

from apiflask import APIBlueprint
from flask import g, request


users = APIBlueprint(
    "users",
    __name__,
    tag={
        "name": "User Management",
        "description": "Operations related to management of users (CRUD, Auth)",
    },
)


@users.before_request
def assign_request_id():
    """
    This function executes before any request.
    It creates a request uuid and assigns it in the global namespace variable 'g'.
    """
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))


@users.after_request
def add_request_id_to_response(response):
    """
    This function executes after any request.
    It puts the uuid created in the 'g' global variable to the response dictionary.
    """
    response.headers["X-Request-ID"] = g.request_id
    return response


@users.route("/", methods=["GET"])
@users.output(schema.GenericResponse, status_code=200)
def api_get_users():
    """
    Gets all users.
    """


@users.route("/", methods=["POST"])
@users.output(schema.GenericResponse, status_code=200)
def api_post_user():
    """
    Create a new user.
    """


@users.route("/token", methods=["POST"])
@users.input(schema.Authentication, location="json")
@users.output(schema.GenericResponse, status_code=200)
def api_post_users_token(json: dict):
    """
    Generate an OAuth2.0 token for an existing user.

    Returns:
        - A JSON response with the OAuth2.0 token.
    """

    username = json.get("username")
    password = json.get("password")

    token = ""

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


@users.route("/<user_id>", methods=["GET"])
@users.output(schema.GenericResponse, status_code=200)
def api_get_user():
    """
    Get an existing user.
    """


@users.route("/<user_id>", methods=["PATCH"])
@users.output(schema.GenericResponse, status_code=200)
def api_patch_user():
    """
    Update an existing user.
    """


@users.route("/<user_id>", methods=["DELETE"])
@users.output(schema.GenericResponse, status_code=200)
def api_delete_user():
    """
    Delete an existing user.
    """
