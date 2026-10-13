"""JWT verification only. Tokens are issued by auth-service; this service just checks them with the shared secret."""
import secrets
from typing import Any

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from core.configs import ConfigLoader


config = ConfigLoader()
# tokenUrl points at auth-service so Swagger's Authorize button works
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/api/v1/auth/login")


def decode_token(token: str) -> dict[str, Any]:
    jwt_config = config.jwt_config()
    if not jwt_config["secret_key"]:
        raise RuntimeError("JWT configuration is incomplete.")
    try:
        return jwt.decode(token, jwt_config["secret_key"], algorithms=[jwt_config["algorithm"]])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    payload = decode_token(token)
    if payload.get("token_type") != "access" or not payload.get("user_id") or not payload.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "id": payload["user_id"],
        "email": payload.get("sub"),
        "role": payload.get("role", "user"),
    }


def require_admin(current_user: dict = Depends(get_current_user)) -> dict[str, Any]:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current_user


def require_service_token(x_service_token: str = Header(default="")) -> None:
    """Guards /internal/* endpoints that only other services may call."""
    expected = config.service_token()
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="SERVICE_TOKEN is not configured")
    if not secrets.compare_digest(x_service_token, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid service token")
