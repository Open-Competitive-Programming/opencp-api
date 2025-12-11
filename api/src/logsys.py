import logging
import logging.config
import os

_override = os.getenv("FASTAPI_DEBUG", "false").lower() in ["true", "1", "yes"]


def override_level(level: str):
    global _override
    if _override:
        return "DEBUG"
    return level


def configure():
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "simple": {"format": "%(name)s:%(levelname)s:%(message)s"},
                "uvicorn": {"format": "%(levelname)s: %(message)s"},
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "level": override_level("INFO"),
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                },
                "uvicorn_access": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "uvicorn",
                    "stream": "ext://sys.stdout",
                },
                "uvicorn_error": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stderr",
                },
            },
            "root": {
                "level": override_level("INFO"),
                "handlers": ["default"],
            },
            "loggers": {
                "uvicorn": {
                    "level": override_level("INFO"),
                    "handlers": ["uvicorn_error"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": override_level("INFO"),
                    "handlers": ["uvicorn_access"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": override_level("INFO"),
                    "handlers": ["uvicorn_error"],
                    "propagate": False,
                },
                "httpx": {"level": override_level("WARNING"), "propagate": False},
                "urllib3": {"level": override_level("WARNING"), "propagate": False},
                "fastapi": {"level": override_level("INFO"), "propagate": True},
            },
        }
    )