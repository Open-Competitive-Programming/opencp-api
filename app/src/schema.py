import json
import logging
from apiflask import Schema, abort
from apiflask.fields import Boolean, Integer, String, DateTime, Dict, List, URL
from apiflask.validators import Length, OneOf, Regexp, Range
from marshmallow import (
    pre_load,
    fields,
    INCLUDE,
    validates,
    post_dump,
    ValidationError,
    validate,
    validates_schema,
)

__version__ = "v1"


class GenericResponse(Schema):
    url = fields.URL(required=True)
    success = fields.Boolean(required=True)
    version = fields.String(required=True)
    timestamp = fields.DateTime(required=True)
    id = fields.String(required=True)

    data = fields.Dict(required=False)
    error = fields.Dict(required=False)

    class Meta:
        unknown = INCLUDE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, data):
        """
        Custom validation to ensure either 'result' or 'error' is present
        based on the 'success' value.
        """
        if data.get("success"):
            if not data.get("data"):
                raise ValueError("'data' field is required when success is True.")
        else:
            if not data.get("error"):
                raise ValueError("'error' field is required when success is False.")
        return data


class Authentication(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)
