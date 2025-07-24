import os
import pytest

from kutils.functions import *

config = {
    "KEYCLOAK_REALM": os.getenv("KEYCLOAK_REALM", None),
    "KEYCLOAK_URL": os.getenv("KEYCLOAK_URL", None),
    "KEYCLOAK_CLIENT_ID": os.getenv("KEYCLOAK_CLIENT_ID", None),
    "KEYCLOAK_CLIENT_SECRET": os.getenv("KEYCLOAK_CLIENT_SECRET", None)
}

def test_initialize_admin_client():
    
    kcadmin = initialize_admin_client(config["KEYCLOAK_URL"], config["KEYCLOAK_REALM"], config["KEYCLOAK_CLIENT_ID"], config["KEYCLOAK_CLIENT_SECRET"])
    assert kcadmin is not None
