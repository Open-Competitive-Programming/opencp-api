"""
Documentation
"""

import uuid

from apiflask import APIBlueprint
from flask import g, request

import schema


users = APIBlueprint(
    "users",
    __name__,
    tag={
        "name": "User Management",
        "description": "Operations related to management of users (CRUD)",
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
