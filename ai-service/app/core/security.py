"""JWT verification only (tokens are issued by auth-service) + service-token check for internal callers."""
import secrets
from typing import Any

import jwt
from fastapi import Header, HTTPException, status

from core.configs import ConfigLoader


config = ConfigLoader()


def decode_token(token: str) -> dict[str, Any]:
    jwt_config = config.jwt_config()
    if not jwt_config["secret_key"]:
        raise RuntimeError("JWT configuration is incomplete.")
    try:
        return jwt.decode(token, jwt_config["secret_key"], algorithms=[jwt_config["algorithm"]])
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_admin_or_service(
    authorization: str = Header(default=""),
    x_service_token: str = Header(default=""),
) -> str:
    """Allow other services (X-Service-Token) or an admin user (Bearer JWT). Returns the caller kind."""
    expected = config.service_token()
    if x_service_token:
        if expected and secrets.compare_digest(x_service_token, expected):
            return "service"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid service token")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    if payload.get("token_type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return "admin"
