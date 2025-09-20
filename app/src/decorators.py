"""
This module contains all the decorator functions
"""

import datetime
from flask import session, request
from functools import wraps

import kutils


def active_session(f):
    """
    This function checks if the current token or session is active and valid
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if request.headers.get("Authorization"):
                access_token = request.headers.get("Authorization").split(" ")[1]
            else:
                access_token = session.get("access_token")
                if access_token is None:

                    json, code = {
                        "url": request.url,
                        "success": False,
                        "version": "v1",
                        "timestamp": datetime.datetime.now(),
                        "error": {
                            "name": "Authentication Error",
                            "msg": "Bearer token is not valid",
                        },
                    }, 401

                    return json, code

            # Check if the token is valid
            if not kutils.introspect_token(access_token):
                json, code = {
                    "url": request.url,
                    "success": False,
                    "version": "v1",
                    "timestamp": datetime.datetime.now(),
                    "error": {
                        "name": "Authentication Error",
                        "msg": "Bearer token is expired",
                    },
                }, 401

                return json, code

        except (IndexError, ValueError):
            json, code = {
                "url": request.url,
                "success": False,
                "version": "v1",
                "timestamp": datetime.datetime.now(),
                "error": {
                    "name": "Authentication Error",
                    "msg": "Bearer token is missing or malformed",
                },
            }, 400

            return json, code

        except Exception as e:

            json, code = {
                "url": request.url,
                "success": False,
                "version": "v1",
                "timestamp": datetime.datetime.now(),
                "error": {
                    "name": "Internal Server Error",
                    "msg": f"{str(e)}",
                },
            }, 500

            return json, code

        return f(*args, **kwargs)

    return decorated_function
