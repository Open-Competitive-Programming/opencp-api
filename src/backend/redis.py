import redis
from config import config

from exceptions import (
    BadGatewayError,
)
import logging
import json

class RedisClient:
    _pool = None

    @classmethod
    def _initialize_redis(cls):
        cls._pool = redis.ConnectionPool(
            host=config.settings["REDIS_HOST"],
            port=config.settings["REDIS_PORT"],
            db=2,
            decode_responses=True,
            max_connections=10,
        )
        logging.info("Initialized Redis connection pool")
        return cls._pool

    def set(self, key, value):
        """Set a value in Redis using a connection from the pool."""
        try:
            if self._pool is None:
                self._initialize_redis()
            conn = redis.Redis(connection_pool=self._pool)
            if isinstance(value, dict):
                conn.set(key, json.dumps(value))  # Serialize dict to JSON string
            else:
                conn.set(key, value)
        except Exception as e:
            raise BadGatewayError(e)

    def get(self, key):
        """Get a value from Redis using a connection from the pool."""
        try:
            if self._pool is None:
                self._initialize_redis()
            conn = redis.Redis(connection_pool=self._pool)
            value = conn.get(key)
            try:
                return json.loads(value)  # Attempt to deserialize JSON string
            except (TypeError, json.JSONDecodeError):
                return value  # Return as-is if not JSON
        except Exception as e:
            raise BadGatewayError(e)

    def delete(self, key):
        """Delete a value from Redis using a connection from the pool."""
        try:
            if self._pool is None:
                self._initialize_redis()
            conn = redis.Redis(connection_pool=self._pool)
            conn.delete(key)
        except Exception as e:
            raise BadGatewayError(e)


# Create a singleton instance of RedisClient
REDIS = RedisClient()