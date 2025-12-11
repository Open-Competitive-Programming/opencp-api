import threading
from keycloak.openid_connection import KeycloakOpenIDConnection, KeycloakOpenID
from keycloak.keycloak_admin import KeycloakAdmin

from config import config

class KeycloakClientSingleton:
    """Singleton class that holds a pool of Keycloak connections and clients."""

    _pool = []
    _counter = 0
    _lock = threading.Lock()

    @classmethod
    def get_admin(cls) -> KeycloakAdmin:
        """Ensure pool is initialized and return one admin client (round robin)."""
        if not cls._pool:
            cls._initialize_keycloak()
        pool_item = cls._select_pool_item()
        return pool_item["admin"]

    @classmethod
    def get_openid(cls) -> KeycloakOpenID:
        """Ensure pool is initialized and return one openid client (round robin)."""
        if not cls._pool:
            cls._initialize_keycloak()
        pool_item = cls._select_pool_item()
        return pool_item["openid"]

    @classmethod
    def _select_pool_item(cls):
        with cls._lock:
            index = cls._counter % len(cls._pool)
            cls._counter += 1
            return cls._pool[index]

    @classmethod
    def _initialize_keycloak(cls):
        """Initialize a pool of Keycloak connections."""
        pool_size = int(config.settings.get("KEYCLOAK_POOL_SIZE", 5))
        for _ in range(pool_size):
            connection = KeycloakOpenIDConnection(
                server_url=config.settings["KEYCLOAK_URL"],
                realm_name=config.settings["KEYCLOAK_REALM"],
                client_id=config.settings["KEYCLOAK_CLIENT_ID"],
                client_secret_key=config.settings["KEYCLOAK_CLIENT_SECRET"],
                verify=False,
            )
            admin = KeycloakAdmin(connection=connection)
            openid = connection.keycloak_openid
            cls._pool.append({"admin": admin, "openid": openid})

KEYCLOAK_OPENID_CLIENT = KeycloakClientSingleton.get_openid
KEYCLOAK_ADMIN_CLIENT = KeycloakClientSingleton.get_admin
