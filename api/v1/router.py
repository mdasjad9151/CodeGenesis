from fastapi import APIRouter

router = APIRouter()

@router.get("/auth/user")
async def get_auth_user():
    print("get_auth_user called")