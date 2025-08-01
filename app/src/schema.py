"""
Schema
"""

from apiflask import Schema
from marshmallow import fields


class GenericResponse(Schema):
    url = fields.URL(required=True)
    success = fields.Boolean(required=True)
    version = fields.String(required=True)
    timestamp = fields.DateTime(required=True)
    id = fields.String(required=True)


class OKResponse(GenericResponse):
    data = fields.Dict(required=True)


class ErrorResponse(GenericResponse):
    error = fields.Dict(required=True)


class Authentication(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)
