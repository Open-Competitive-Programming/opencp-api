"""
Documentation
"""

import uuid

from apiflask import APIBlueprint
from flask import g, request

import schema


problemset = APIBlueprint(
    "problemset",
    __name__,
    tag={
        "name": "Problem Set Management",
        "description": "Operations related to management of problems (CRUD)",
    },
)


@problemset.before_request
def assign_request_id():
    """
    This function executes before any request.
    It creates a request uuid and assigns it in the global namespace variable 'g'.
    """
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))


@problemset.after_request
def add_request_id_to_response(response):
    """
    This function executes after any request.
    It puts the uuid created in the 'g' global variable to the response dictionary.
    """
    response.headers["X-Request-ID"] = g.request_id
    return response


@problemset.route("/", methods=["GET"])
@problemset.output(schema.GenericResponse, status_code=200)
def api_get_problems():
    """
    Gets all problems.
    """


@problemset.route("/", methods=["POST"])
@problemset.output(schema.GenericResponse, status_code=200)
def api_post_problem():
    """
    Create a new problem.
    """


@problemset.route("/<problem_id>", methods=["GET"])
@problemset.output(schema.GenericResponse, status_code=200)
def api_get_problem():
    """
    Get a specific problem.
    """


@problemset.route("/<problem_id>", methods=["PATCH"])
@problemset.output(schema.GenericResponse, status_code=200)
def api_patch_problem():
    """
    Update a specific problem.
    """


@problemset.route("/<problem_id>", methods=["DELETE"])
@problemset.output(schema.GenericResponse, status_code=200)
def api_delete_problem():
    """
    Delete a specific problem.
    """


@problemset.route("/<problem_id>/submissions", methods=["GET"])
@problemset.output(schema.GenericResponse, status_code=200)
def api_get_problem_submissions():
    """
    Get the submissions on a specific problem
    """


@problemset.route("/<problem_id>/submissions/<submission_id>", methods=["GET"])
@problemset.output(schema.GenericResponse, status_code=200)
def api_get_problem_submission():
    """
    Get a specific submission on a specific problem
    """


@problemset.route("/submit/<problem_id>", methods=["POST"])
@problemset.output(schema.GenericResponse, status_code=200)
def api_post_problem():
    """
    Submit code for a specific problem.
    """
