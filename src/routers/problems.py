from fastapi import APIRouter, Request, Depends 
from routers.generic import render
from auth import auth
from schemas import LoginSchema
import kutils
from exceptions import AuthenticationError
router = APIRouter(prefix="/api/v1/problems", tags=["Problem Operations"])

@router.get("/")
@render()
def api_get_problems(request: Request):
    return "problems endpoint"

