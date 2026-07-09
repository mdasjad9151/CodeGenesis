from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
from fastapi import HTTPException, status

from core.configs import ConfigLoader


config = ConfigLoader()


def _jwt_settings() -> dict[str, Any]:
    jwt_config = config.jwt_config()
    secret_key = jwt_config.get("secret_key")
    algorithm = jwt_config.get("algorithm")

    if not secret_key or not algorithm:
        raise RuntimeError("JWT configuration is incomplete.")

    return jwt_config


def create_token(*, user: dict[str, Any], token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["email"],
        "user_id": str(user["id"]),
        "is_verified": bool(user["is_verified"]),
        "is_active": bool(user["is_active"]),
        "token_type": token_type,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid4()),
    }
    jwt_config = _jwt_settings()
    return jwt.encode(payload, jwt_config["secret_key"], algorithm=jwt_config["algorithm"])


def decode_token(token: str) -> dict[str, Any]:
    jwt_config = _jwt_settings()
    try:
        return jwt.decode(
            token,
            jwt_config["secret_key"],
            algorithms=[jwt_config["algorithm"]],
        )
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


def validate_token_type(payload: dict[str, Any], expected_token_type: str) -> None:
    if payload.get("token_type") != expected_token_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid {expected_token_type} token",
            headers={"WWW-Authenticate": "Bearer"},
        )
