from fastapi import APIRouter
from schema.auth import *
from core.configs import ConfigLoader
from services.auth_service import AuthService

router = APIRouter()
config =  ConfigLoader()

@router.post("/api/v1/auth/register")
async def register_user(request: RegisterRequest):
    auth_service = AuthService(config, request)
    return await auth_service.register_user()


@router.post("/api/v1/auth/verify-otp")
async def verify_otp(request: VerifyOTPRequest):
    auth_service = AuthService(config, request)
    return await auth_service.verify_otp()
