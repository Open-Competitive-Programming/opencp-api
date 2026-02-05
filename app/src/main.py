from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging


logger = logging.getLogger(__name__)
origins = [
    "https://dev.open-cp.eu:8880",   
    "https://dev.open-cp.eu",
]

# Configuration context
from config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


# create FastAPI app
api = FastAPI(
    title="Open-CP API",
    version="0.0.1",
    root_path=config.settings["CONTEXT_PATH"],
    lifespan=lifespan,
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Length"],
)

if __name__ == "__main__":
    # Run Uvicorn programmatically using the configuration
    uvicorn.run(
        "main:api",
        host=config.settings["HOST"],
        port=config.settings["PORT"],
        reload=config.settings["DEBUG"],
    )