from keycloak import KeycloakOpenID, KeycloakAdmin, KeycloakAuthenticationError, KeycloakGetError

def initialize_admin_client(server_url: str, realm_name: str, client_id: str, client_secret_key: str) -> KeycloakAdmin:
    """
    Initializes and returns a KeycloakAdmin client using the client service account. (If Enabled)

    Returns:
        KeycloakAdmin: An initialized KeycloakAdmin client
    """
    
    try:
        keycloak_admin = KeycloakAdmin(
            server_url=server_url,
            realm_name=realm_name,
            client_id=client_id,
            client_secret_key=client_secret_key,
            verify=True
        )
        return keycloak_admin
    except Exception:
        return None
