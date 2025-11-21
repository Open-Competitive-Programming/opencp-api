import datetime
import json
import logging
from functools import wraps
from typing import Optional, Dict
from keycloak import (
    KeycloakAuthenticationError,
    KeycloakConnectionError,
    KeycloakDeleteError,
    KeycloakGetError,
    KeycloakInvalidTokenError,
    KeycloakPostError,
    KeycloakPutError,
)

from backend.keycloak import KEYCLOAK_ADMIN_CLIENT, KEYCLOAK_OPENID_CLIENT
from exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    InternalError as InternalException,
    InvalidError,
    NotFoundError,
)
from utils import is_valid_uuid
from fastapi import Request

logger = logging.getLogger(__name__)


def raise_keycloak_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (
            KeycloakAuthenticationError,
            KeycloakGetError,
            KeycloakPostError,
            KeycloakPutError,
            KeycloakDeleteError,
            KeycloakConnectionError,
            KeycloakInvalidTokenError,
        ) as e:
            logger.error(
                "Keycloak error in %s: %s", func.__name__, str(e), exc_info=True
            )
            response_code = getattr(e, "response_code", None)
            detail_message = ""
            if hasattr(e, "response_body") and e.response_body:
                try:
                    # Attempt to decode and extract the detailed message from the response body.
                    error_detail = json.loads(e.response_body.decode("utf-8"))
                    detail_message = error_detail.get("message", str(e))
                except Exception:
                    detail_message = str(e.response_body)
            else:
                detail_message = str(e)

            if response_code == 409:
                raise ConflictError(
                    detail=detail_message,
                ) from e
            elif response_code == 400:
                raise InvalidError(
                    detail=detail_message,
                ) from e
            elif response_code == 404:
                raise NotFoundError(
                    detail="Resource not found",
                ) from e
            elif response_code == 401:
                raise AuthenticationError(
                    detail="Invalid user credentials",
                ) from e
            else:
                raise InternalException(detail=detail_message) from e

    return wrapper


def email_username_unique(username, email):
    username_unique(username=username)
    email_unique(email=email)


def convert_iat_to_date(timestamp):
    date = None
    if timestamp:
        date = datetime.datetime.fromtimestamp(timestamp / 1000.0).isoformat()
        return date
    else:
        return None


@raise_keycloak_error
def username_unique(username):
    # Check for existing users with the same username
    existing_users = KEYCLOAK_ADMIN_CLIENT().get_users({"username": username})

    if existing_users:
        raise ConflictError(f"A user with the username '{username}' already exists.")


@raise_keycloak_error
def email_unique(email):
    # Check for existing users with the same email
    existing_emails = KEYCLOAK_ADMIN_CLIENT().get_users({"email": email})
    if existing_emails:
        raise ConflictError(f"A user with the email '{email}' already exists.")


@raise_keycloak_error
def introspect_token(access_token):
    """
    Introspects the given access token to check if it's valid and active.
    Returns True if the token is valid, False if the token is invalid or expired.
    """

    introspect_response = KEYCLOAK_OPENID_CLIENT().introspect(access_token)
    # Check if the token is active
    if introspect_response.get("active", False):
        return introspect_response
    else:
        raise AuthenticationError(detail="Token is invalid or expired")


def introspect_admin_token(access_token):
    """
    Introspects the given access token to check if it's valid, active,
    and if the user has the admin role.
    Returns True if the token is valid and admin.
    Raises TokenExpiredError if the token is inactive/expired.
    Raises AuthorizationError if the token is active but not for an admin user.
    """
    introspect_response = introspect_token(access_token)

    # Optionally check for realm_access if needed
    if not introspect_response.get("realm_access", False):
        raise AuthenticationError(
            detail="Token is missing realm access information",
        )

    # Check if the token has admin role
    roles = introspect_response["realm_access"].get("roles", [])
    if "admin" not in roles:
        raise AuthorizationError(detail="User is not an admin")

    return True

def current_token(request: Request) -> Optional[str]:
    """
    Extracts the current access token from the Authorization header.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        str | None: The access token if available, otherwise None.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return None


def current_user(request: Request) -> Optional[Dict]:
    """
    Resolves the current user from the access token in the request headers.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        dict | None: A dictionary containing user information if available, otherwise None.
    """
    token = current_token(request)
    if token:
        return get_user_by_token(token)
    return None

def is_admin(request: Request) -> bool:
    """
    Checks if the current user is an admin based on the access token in the request headers.

    Args:
        request (Request): The incoming HTTP request.
    Returns:
        bool: True if the user is an admin, otherwise False.
    """
    token = current_token(request)
    if token:
        try:
            introspect_admin_token(token)
            return True
        except (AuthenticationError, AuthorizationError):
            return False
    return False

def get_token(username, password):
    """
    Returns a token for a user in Keycloak by using username and password.

    Args:
        username: The username of the user in Keycloak.
        password: The secret password of the user in Keycloak.

    Returns:
        dict: The token dictionary containing the access_token and additional details.

    Raises:
        AuthenticationError: If the token could not be retrieved.
    """
    return KEYCLOAK_OPENID_CLIENT().token(username, password)

def get_user_by_token(access_token):
    """
    Introspects the given access token to return the user information if the token is active
    Returns the user json if the token is valid, False if the token is invalid or expired.
    """
    return introspect_token(access_token)


def is_token_active(access_token):
    """
    Introspects the given access token to check if it's valid and active.
    Returns True if the token is valid, False if the token is invalid or expired.
    """

    introspect_response = KEYCLOAK_OPENID_CLIENT().introspect(access_token)
    # Check if the token is active
    if introspect_response.get("active", False):
        return introspect_response
    else:
        return False


@raise_keycloak_error
def refresh_access_token(refresh_token):
    """
    Refreshes the access token using the refresh token given as args.

    This function initializes the Keycloak OpenID client and uses the stored refresh token
    to obtain a new access token. If successful, it updates the session with the new
    access token and refresh token. In case of failure, it returns an appropriate error detail.

    Args:
        - refresh_token: The refresh token to use.

    Returns:
        tuple: A tuple containing:
            - str or None: The refreshed access token if successful, otherwise None.
            - str or None: An error detail if the refresh fails, otherwise None.
    """

    if not refresh_token:
        raise InvalidError(detail="Missing refresh token.")

    token = KEYCLOAK_OPENID_CLIENT().refresh_token(
        refresh_token, grant_type="refresh_token"
    )
    return token


@raise_keycloak_error
def get_token(username, password):
    """
    Returns a token for a user in Keycloak by using username and password.

    Args:
        username: The username of the user in Keycloak.
        password: The secret password of the user in Keycloak.

    Returns:
        dict: The token dictionary containing the access_token and additional details.

    Raises:
        AuthenticationError: If the token could not be retrieved.
    """
    return KEYCLOAK_OPENID_CLIENT().token(username, password)


@raise_keycloak_error
def get_user_roles(user_id):
    """
    Fetches the roles assigned to a user with the given user_id using KeycloakAdmin object.

    :param user_id: The ID of the user whose roles are to be fetched.
    :return: A list of roles assigned to the user.
    """
    realm_roles = KEYCLOAK_ADMIN_CLIENT().get_realm_roles_of_user(user_id)

    if not realm_roles:
        return []

    # Filter out default roles and extract role names
    filtered_roles = [
        role["name"]
        for role in realm_roles
        if role.get("name") and role["name"] != "default-roles-master"
    ]

    return filtered_roles


@raise_keycloak_error
def get_role(role_id):
    """
    Fetches the role by ID from the Realm

    :param user_id: The ID or the name of the role to be fetched.
    :return: The role representation
    """

    if is_valid_uuid(role_id):
        role_rep = KEYCLOAK_ADMIN_CLIENT().get_realm_role_by_id(role_id)
    else:
        role_rep = KEYCLOAK_ADMIN_CLIENT().get_realm_role(role_id)

    return role_rep


@raise_keycloak_error
def get_realm_roles():
    """
    Returns the realm roles exluding the Keycloak default roles.
    """
    roles = KEYCLOAK_ADMIN_CLIENT().get_realm_roles(brief_representation=True)

    # Define a set of roles to exclude
    roles_to_exclude = {
        "offline_access",
        "uma_authorization",
        "create-realm",
        "default-roles-master",
    }

    # Filter the roles, excluding those in the roles_to_exclude set
    filtered_roles = [role for role in roles if role["name"] not in roles_to_exclude]

    return filtered_roles


@raise_keycloak_error
def get_user(user_id):
    """
    Retrieve a user from Keycloak by user ID.
    It also returns the roles

    :param user_id: The ID of the user to retrieve (str). If None, returns None.
    :return: A dictionary representation of the user if found, otherwise None.
    """
    # Support both searching by UUID and by Username
    if is_valid_uuid(user_id):
        user_representation = KEYCLOAK_ADMIN_CLIENT().get_user(user_id)
    else:
        id = KEYCLOAK_ADMIN_CLIENT().get_user_id(user_id)
        user_representation = KEYCLOAK_ADMIN_CLIENT().get_user(id)

    if user_representation:
        creation_date = convert_iat_to_date(user_representation["createdTimestamp"])

        filtered_roles = get_user_roles(user_representation["id"])

        active_status = user_representation.get("enabled", False)
        email_verified = user_representation.get("emailVerified", False)

        user_info = {
            "username": user_representation.get("username"),
            "email": user_representation.get("email"),
            "fullname": f"{user_representation.get('firstName', '')} {user_representation.get('lastName', '')}".strip(),
            "first_name": user_representation.get("firstName"),
            "last_name": user_representation.get("lastName"),
            "joined_date": creation_date,
            "id": user_representation.get("id"),
            "roles": filtered_roles,
            "active": active_status,
            "email_verified": email_verified,
            "is_admin": (
                True
                if user_representation.get("attributes")
                and "is_admin" in user_representation["attributes"]
                else False
            ),
        }

        return user_info
    return None


@raise_keycloak_error
def get_users_from_keycloak(offset, limit, public=False):
    """
    Retrieves a list of users from Keycloak with pagination and additional user details.

    Args:
        offset (int): The starting index for the users to retrieve.
        limit (int): The maximum number of users to retrieve. Use 0 to retrieve all users starting from offset.

    Returns:
        A list of user dictionaries containing user details.

    Raises:
        InvalidError: If invalid values for offset or limit are provided.
    """
    if offset < 0 or limit < 0:
        raise InvalidError("Limit and offset must be greater than 0.")

    query = {"first": offset} if limit == 0 else {"first": offset, "max": limit}

    users = KEYCLOAK_ADMIN_CLIENT().get_users(query=query)

    if public:
        # If public is True, return only usernames and IDs
        result = [
            {
                "username": user.get("username"),
                "id": user.get("id"),
                "fullname": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
            }
            for user in users
            if user.get("enabled", False)
        ]

    else:
        result = []
        for user in users:
            creation_date = convert_iat_to_date(user["createdTimestamp"])
            filtered_roles = get_user_roles(user["id"])
            active_status = user.get("enabled", False)

            user_info = {
                "username": user.get("username"),
                "email": user.get("email"),
                "fullname": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
                "first_name": user.get("firstName"),
                "last_name": user.get("lastName"),
                "joined_date": creation_date,
                "id": user.get("id"),
                "roles": filtered_roles,
                "active": active_status,
            }
            result.append(user_info)

    return result


def fetch_user_creation_date(user_id):
    """
    Fetches user creation date from Keycloak Admin API using client credentials access token.

    """
    try:
        user = get_user(user_id)
        data = user.get("joined_date")
        if data:
            return data
    except Exception as e:
        logger.debug(
            "Error while fetching user creation date: %s", str(e), exc_info=True
        )
        return None