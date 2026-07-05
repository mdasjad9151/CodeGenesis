import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from schema.auth import *
from core.configs import ConfigLoader
from services.auth_service import AuthService

router = APIRouter()
config =  ConfigLoader()
bearer_scheme = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    jwt_config = config.jwt_config()
    try:
        payload = jwt.decode(
            credentials.credentials,
            jwt_config["secret_key"],
            algorithms=[jwt_config["algorithm"]],
        )
        email = payload.get("sub")
        is_active = payload.get("is_active")
        token_type = payload.get("token_type")
        if not email or is_active is not True or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "id": payload.get("user_id"),
            "email": email,
            "is_verified": payload.get("is_verified", False),
            "is_active": is_active,
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/api/v1/auth/register")
async def register_user(request: RegisterRequest):
    auth_service = AuthService(config, request)
    return await auth_service.register_user()


@router.post("/api/v1/auth/verify-otp")
async def verify_otp(request: VerifyOTPRequest):
    auth_service = AuthService(config, request)
    return await auth_service.verify_otp()


@router.post("/api/v1/auth/login")
async def login_user(request: LoginRequest):
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
