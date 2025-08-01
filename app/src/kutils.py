"""
Keycloak utils for opencp
"""

from keycloak import KeycloakAdmin


def initialize_keycloak_admin() -> KeycloakAdmin:
    """
    Creates a keycloak admin.
    """
    kc_admin = KeycloakAdmin()

    return kc_admin
