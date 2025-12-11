from fastapi import APIRouter, Request, Depends 
from routers.generic import render
from auth import auth
from schemas import LoginSchema
import kutils
from exceptions import AuthenticationError
from api.v1.problems import PROBLEM
router = APIRouter(prefix="/api/v1/problems", tags=["Problem Operations"])

@router.get("/{entity_id}")
@render()
def api_get_problems(request: Request, entity_id: str):
    return PROBLEM.get_entity(entity_id)

