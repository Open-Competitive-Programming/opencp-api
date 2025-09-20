"""
This python script is used to initialize and configure keycloak.
"""

import os

from keycloak import KeycloakAdmin


KC_BOOTSTRAP_ADMIN_USERNAME = os.getenv("KC_BOOTSTRAP_ADMIN_USERNAME")
KC_BOOTSTRAP_ADMIN_PASSWORD = os.getenv("KC_BOOTSTRAP_ADMIN_PASSWORD")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
KEYCLOAK_TOKEN_LIFESPAN = int(os.getenv("KEYCLOAK_TOKEN_LIFESPAN"))
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_REALM_ROLES = os.getenv("KEYCLOAK_REALM_ROLES")


if __name__ == "__main__":

    kc_admin = KeycloakAdmin(
        server_url=KEYCLOAK_URL,
        username=KC_BOOTSTRAP_ADMIN_USERNAME,
        password=KC_BOOTSTRAP_ADMIN_PASSWORD,
        realm_name=KEYCLOAK_REALM,
        verify=True,
    )

    client_representation = {
        "clientId": KEYCLOAK_CLIENT_ID,
        "enabled": True,
        "rootUrl": "",
        "baseUrl": "",
        "redirectUris": ["*"],
        "attributes": {"post.logout.redirect.uris": "+"},
        "directAccessGrantsEnabled": True,
    }

    client_id = kc_admin.create_client(client_representation, skip_exists=True)
    client_secret = kc_admin.get_client_secrets(client_id)["value"]

    # Retrieve the client configuration
    client_representation = kc_admin.get_client(client_id)

    # Update the configuration to enable service accounts
    client_representation["serviceAccountsEnabled"] = True
    client_representation["authorizationServicesEnabled"] = True

    # Update the client with the modified configuration
    kc_admin.update_client(client_id, client_representation)
    print(f"Service account enabled for client with ID: {client_id}")

    role = kc_admin.get_realm_role("admin")

    service_account_user = kc_admin.get_client_service_account_user(client_id)
    service_account_user_id = service_account_user["id"]

    # Assign the admin role to the service account user
    kc_admin.assign_realm_roles(service_account_user_id, [role])

    # Save client secret.
    file = open("/usr/shared/client-secret.txt", "w")
    file.write(client_secret)
    file.close()

    exit(0)
