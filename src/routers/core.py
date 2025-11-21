from fastapi import APIRouter, Request, Depends 
from routers.generic import render
from auth import auth
from schemas import LoginSchema
import kutils
from exceptions import AuthenticationError
router = APIRouter(prefix="/api/v1/system", tags=["System Operations"])

@router.get("/ping")
@render()
def ping(request: Request):
    return "pong"

@router.get("/info")
@render()
def info(request: Request):
    from main import config
    return {
        "service": "Open-CP Core API",
        "version": "0.0.1",
        "docs": "/docs",
        "keycloak": config.settings["KEYCLOAK_EXT_URL"],
        "minio": config.settings["MINIO_EXT_URL_CONSOLE"],
    }

@router.get("/endpoints")
@render()
def endpoints(request: Request):
    from main import api
    return {
        route.name: {
            "path": route.path,
            "method": list(route.methods)[0] if hasattr(route, "methods") and route.methods else None
        }
        for route in api.routes
        if hasattr(route, "name") and hasattr(route, "path")
    }

@router.post("/login")
@render()
def login(request: Request, creds: LoginSchema):
    return kutils.get_token(username=creds.username, password=creds.password)