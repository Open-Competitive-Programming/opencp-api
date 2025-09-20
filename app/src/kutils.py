"""
Keycloak utils for opencp
"""

import os

from keycloak import KeycloakAdmin, KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakConnectionError


def get_kc_admin() -> KeycloakAdmin:
    """
    Creates a keycloak admin.
    """

    kc_admin = KeycloakAdmin(
        server_url=os.getenv("KEYCLOAK_URL"),
        realm_name=os.getenv("REALM_NAME"),
        username=os.getenv("KC_BOOTSTRAP_ADMIN_USERNAME"),
        password=os.getenv("KC_BOOTSTRAP_ADMIN_PASSWORD"),
        client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
        client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET"),
        verify=True,
    )
    return kc_admin


def is_username_unique(username: str) -> bool:
    """
    Checks if the given username already exists.
    """

    kc_admin = get_kc_admin()
    existing_users = kc_admin.get_users({"username": username})

    print(existing_users)

    return False if existing_users else True


def get_token(username: str, password: str) -> dict:
    """
    Returns a token for a user in Keycloak by using username and password.

    Args:
        username: The username of the user in Keycloak
        password The secret password of the user in Keycloak

    Returns:
        str: The access_token
        null: Error return

    """
    kopenid = KeycloakOpenID(
        server_url=os.getenv("KEYCLOAK_URL"),
        client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
        realm_name=os.getenv("REALM_NAME"),
        client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET"),
        verify=True,
    )
    try:
        token = kopenid.token(username, password)
        return token
    except (KeycloakAuthenticationError, KeycloakConnectionError):
        return None
