from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.generic import install_error_handler
from contextlib import asynccontextmanager
from sqlalchemy import text
import uvicorn
import logsys
import logging


logger = logging.getLogger(__name__)
origins = [
    "https://dev.open-cp.eu:8880",   
    "https://dev.open-cp.eu",
]

# Configuration context
from config import config

# Configure logging
logsys.configure()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info("App startup: warming up DB")
    from backend.postgres import POSTGRES_ASYNC_ENGINE
    eng = POSTGRES_ASYNC_ENGINE()
    async with eng.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection OK")

    # yield control to the application runtime
    yield

    # --- SHUTDOWN ---
    logger.info("App shutdown: closing DB connections")
    from backend.postgres import PostgresConnectionSingleton
    await PostgresConnectionSingleton.close()
    logger.info("DB connections closed")

# create FastAPI app
api = FastAPI(
    title="Open-CP API",
    version="0.0.1",
    root_path=config.settings["CONTEXT_PATH"],
    lifespan=lifespan,
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # list of allowed origins (or ["*"] for any origin)
    allow_credentials=True,           # set True if you send cookies / Authorization headers
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],              # or list specific headers
    expose_headers=["Content-Length"],# optionally expose headers to browser
)

# Initialize exception handlers
install_error_handler(api)

# Register routers
from routers.core import router as core_router
from routers.problems import router as problems_router


api.include_router(core_router)
api.include_router(problems_router)

if __name__ == "__main__":
    # Run Uvicorn programmatically using the configuration
    uvicorn.run(
        "main:api",
        host=config.settings["HOST"],
        port=config.settings["PORT"],
        reload=config.settings["DEBUG"],
    )