"""
Schema
"""

from apiflask import Schema
from marshmallow import fields


class GenericResponse(Schema):
    """
    Generic response
    """

    url = fields.URL(required=True)
    success = fields.Boolean(required=True)
    version = fields.String(required=True)
    timestamp = fields.DateTime(required=True)
    id = fields.String(required=True)


class SuccessfullResponse(GenericResponse):
    """
    OK response
    """

    data = fields.Dict(required=True)


class ErrorResponse(GenericResponse):
    """
    Error response
    """

    error = fields.Dict(required=True)


class Authentication(Schema):
    """
    Input parameters for authentication
    """

    username = fields.String(required=True)
    password = fields.String(required=True)
