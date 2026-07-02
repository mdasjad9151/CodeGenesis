from fastapi import APIRouter
from schema.auth import *
from core.configs import ConfigLoader

router = APIRouter()
config =  ConfigLoader()

@router.get("/auth/user")
async def get_auth_user():
    print("get_auth_user called")

