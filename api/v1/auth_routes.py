from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from schema.auth import *
from core.configs import ConfigLoader
from core.security import decode_token, validate_token_type
from services.auth_service import AuthService
from repositories.auth_repository import AuthRepository

router = APIRouter()
config =  ConfigLoader()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    validate_token_type(payload, "access")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = AuthRepository().get_user_by_id(user_id)
    if not user or user["email"] != payload.get("sub") or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": str(user["id"]),
        "email": user["email"],
        "is_verified": bool(user["is_verified"]),
        "is_active": bool(user["is_active"]),
    }


async def parse_login_request(
    request: Request,
    login_body: Annotated[LoginRequest | None, Body()] = None,
):
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        if login_body is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body is required",
            )
        return login_body

    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="username and password are required",
        )

    return LoginRequest(email=username, password=password)

@router.post("/api/v1/auth/register")
async def register_user(request: RegisterRequest):
    auth_service = AuthService(config, request)
    return await auth_service.register_user()


@router.post("/api/v1/auth/verify-otp")
async def verify_otp(request: VerifyOTPRequest):
    auth_service = AuthService(config, request)
    return await auth_service.verify_otp()


@router.post("/api/v1/auth/login")
async def login_user(request: LoginRequest = Depends(parse_login_request)):
    auth_service = AuthService(config, request)
    return await auth_service.login_user()


@router.post("/api/v1/auth/refresh-token")
async def refresh_token(request: RefreshTokenRequest):
    auth_service = AuthService(config, request)
    return await auth_service.refresh_access_token()


@router.get("/api/v1/auth/home")
async def home(current_user=Depends(get_current_user)):
    return {
        "message": "Welcome",
        "user": current_user
    }
