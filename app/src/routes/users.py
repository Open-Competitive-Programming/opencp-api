"""
Documentation
"""

import datetime

from apiflask import APIBlueprint
from flask import request

from decorators import active_session
import schema
import kutils


users = APIBlueprint(
    "users",
    __name__,
    tag={
        "name": "User Management",
        "description": "Operations related to management of users (CRUD)",
    },
)


@users.route("/", methods=["GET"])
@users.output(schema.GenericResponse, status_code=200)
@users.input(schema.PaginationParameters, location="query")
@active_session
def api_get_users(query_data: dict):
    """
    Gets all users.
    """

    offset = query_data.get("offset", 0)
    limit = query_data.get("limit", 0)

    json, code = {
        "url": request.url,
        "success": False,
        "version": "v1",
        "timestamp": datetime.datetime.now(),
        "error": {
            "name": "Internal Server Error",
            "msg": "Endpoint not implemented yet",
        },
    }, 501

    return json, code
