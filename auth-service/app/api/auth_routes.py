from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from schema.auth import (
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    UserResponse,
    VerifyOTPRequest,
)
from schema.token import TokenPairResponse
from core.configs import ConfigLoader
from core.security import decode_token, validate_token_type
from services.auth_service import AuthService
from repositories.auth_repository import AuthRepository

router = APIRouter()
config =  ConfigLoader()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
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
        "role": user["role"],
        "is_verified": bool(user["is_verified"]),
        "is_active": bool(user["is_active"]),
    }


async def parse_login_request(request: Request) -> LoginRequest:
    """Accept JSON {email, password} or an OAuth2 form {username, password} (used by Swagger's Authorize button)."""
    content_type = request.headers.get("content-type", "")

    try:
        if "application/json" in content_type:
            data = await request.json()
        else:
            form = await request.form()
            data = {"email": form.get("username"), "password": form.get("password")}
        return LoginRequest(**data)
    except (ValueError, TypeError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="email/username and password are required",
        ) from exc


@router.post("/api/v1/auth/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register_user(request: RegisterRequest):
    auth_service = AuthService(config, request)
    return auth_service.register_user()


@router.post("/api/v1/auth/verify-otp", response_model=MessageResponse)
def verify_otp(request: VerifyOTPRequest):
    auth_service = AuthService(config, request)
    return auth_service.verify_otp()


@router.post("/api/v1/auth/login", response_model=TokenPairResponse)
def login_user(request: LoginRequest = Depends(parse_login_request)):
    auth_service = AuthService(config, request)
    return auth_service.login_user()


@router.post("/api/v1/auth/refresh-token", response_model=TokenPairResponse)
def refresh_token(request: RefreshTokenRequest):
    auth_service = AuthService(config, request)
    return auth_service.refresh_access_token()


@router.get("/api/v1/auth/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return current_user
