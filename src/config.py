import os

class Config:
    def __init__(self):
        self.settings = {}

    def setup(self):
        # Read environment variables and store them in the settings dictionary
        self.settings["HOST"] = os.getenv("HOST", "127.0.0.1")
        self.settings["PORT"] = int(os.getenv("PORT", 8000))
        self.settings["DEBUG"] = os.getenv("DEBUG", "true").lower() == "true"
        self.settings["CONTEXT_PATH"] = os.getenv("CONTEXT_PATH", "")
        self.settings["APP_EXT_DOMAIN"] = os.getenv("APP_EXT_DOMAIN", "http://dev.open-cp.eu:8880")
        self.settings["ELASTIC_HOST"] = os.getenv(
            "ELASTIC_HOST", "http://elasticsearch:9200"
        )
        self.settings["ES_DIM"] = int(os.getenv("ES_DIM", 384))
        self.settings["MINIO_ENDPOINT"] = os.getenv(
            "MINIO_ENDPOINT", "http://minio:9000"
        )
        self.settings["MINIO_ROOT"] = os.getenv("MINIO_ROOT", "root")
        self.settings["MINIO_ROOT_PASSWORD"] = os.getenv(
            "MINIO_ROOT_PASSWORD", "minioadmin"
        )
        self.settings["MINIO_EXT_URL_CONSOLE"] = os.getenv(
            "MINIO_EXT_URL_CONSOLE", "http://dev.open-cp.eu:8882/console"
        )
        self.settings["MINIO_EXT_URL_API"] = os.getenv(
            "MINIO_EXT_URL_API", "http://dev.open-cp.eu:8882"
        )
        self.settings["MINIO_BUCKET"] = os.getenv("MINIO_BUCKET", "system")
        self.settings["KEYCLOAK_URL"] = os.getenv(
            "KEYCLOAK_URL", "http://keycloak:8080"
        )
        self.settings["KEYCLOAK_EXT_URL"] = os.getenv(
            "KEYCLOAK_EXT_URL", "http://dev.open-cp.eu:8881"
        )
        self.settings["KEYCLOAK_ISSUER_URL"] = os.getenv(
            "KEYCLOAK_ISSUER_URL", "http://dev.open-cp.eu:8881/realms/master"
        )
        self.settings["KEYCLOAK_REALM"] = os.getenv("KEYCLOAK_REALM", "master")
        self.settings["KEYCLOAK_CLIENT_ID"] = os.getenv(
            "KEYCLOAK_CLIENT_ID", "opencp-api"
        )
        self.settings["KEYCLOAK_CLIENT_SECRET"] = os.getenv(
            "KEYCLOAK_CLIENT_SECRET", "secret"
        )
        self.settings["CACHE_ENABLED"] = (
            os.getenv("CACHE_ENABLED", "false").lower() == "true"
        )
        self.settings["REDIS_HOST"] = os.getenv("REDIS_HOST", "redis")
        self.settings["REDIS_PORT"] = int(os.getenv("REDIS_PORT", 6379))
        self.settings["POSTGRES_HOST"] = os.getenv("POSTGRES_HOST", "localhost")
        self.settings["POSTGRES_PORT"] = int(os.getenv("POSTGRES_PORT", 5432))
        self.settings["POSTGRES_USER"] = os.getenv("POSTGRES_USER", "postgres")
        self.settings["POSTGRES_PASSWORD"] = os.getenv("POSTGRES_PASSWORD", "postgres")
        self.settings["POSTGRES_DB"] = os.getenv("POSTGRES_DB", "opencp")
        self.settings["POSTGRES_POOL_SIZE"] = int(os.getenv("POSTGRES_POOL_SIZE", 10))
        self.settings["POSTGRES_MAX_OVERFLOW"] = int(
            os.getenv("POSTGRES_MAX_OVERFLOW", 20)
        )


# Configure application settings
config = Config()
config.setup()