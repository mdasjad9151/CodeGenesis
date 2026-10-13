import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from passlib.context import CryptContext
from fastapi import HTTPException, status

from core.logging import logger
from core.security import create_token, decode_token, validate_token_type
from repositories.auth_repository import AuthRepository


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated=["bcrypt"],
    pbkdf2_sha256__rounds=120000,
)


class AuthService:
    def __init__(self, config, request):
        self.config = config
        self.auth_repository = AuthRepository()
        self.request = request

    def generate_access_token(self, user: dict) -> str:
        jwt_config = self.config.jwt_config()
        return create_token(
            user=user,
            token_type="access",
            expires_delta=timedelta(minutes=jwt_config["access_token_expire_minutes"]),
        )

    def generate_refresh_token(self, user: dict, replaces_jti: str | None = None) -> str:
        """Create a refresh token and record its jti so it can be rotated/revoked later."""
        jwt_config = self.config.jwt_config()
        expires_delta = timedelta(days=jwt_config["refresh_token_expire_days"])
        jti = str(uuid4())
        saved = self.auth_repository.save_refresh_token(
            user_id=str(user["id"]),
            jti=jti,
            expires_at=datetime.now(timezone.utc) + expires_delta,
            replaces_jti=replaces_jti,
        )
        if not saved:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token already used")
        return create_token(user=user, token_type="refresh", expires_delta=expires_delta, jti=jti)

    def generate_tokens(self, user: dict, replaces_jti: str | None = None) -> dict:
        refresh_token = self.generate_refresh_token(user, replaces_jti)
        access_token = self.generate_access_token(user)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def send_otp(self, email: str, otp: str):
        # No email provider yet: the OTP is written to the service logs
        logger.info(f"[EMAIL SIMULATION] To: {email} | Your verification OTP code is {otp}")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def register_user(self):
        email = self.request.email
        password = self.request.password
        if self.auth_repository.user_exists(email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

        hashed_password = self.hash_password(password)
        otp_code = f"{secrets.randbelow(900000) + 100000}"
        self.auth_repository.create_user(email=email, password=hashed_password, otp=otp_code)
        self.send_otp(email, otp_code)
        return {"message": "User registered. Check the OTP sent to your email to verify the account."}

    def verify_otp(self):
        email = self.request.email
        otp = self.request.otp
        user = self.auth_repository.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if user["is_verified"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified")

        otp_record = self.auth_repository.get_active_registration_otp(str(user["id"]))
        if not otp_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OTP not found")

        if otp_record["otp_code"] != otp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

        expires_at = otp_record["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired")

        self.auth_repository.mark_user_as_verified(str(user["id"]), str(otp_record["id"]))
        return {"message": "User verified successfully"}

    def login_user(self):
        email = self.request.email
        password = self.request.password
        user = self.auth_repository.get_login_user_by_email(email)

        if not user or not user["hashed_password"] or not self.verify_password(password, user["hashed_password"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        if not user["is_verified"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not verified")

        if not user["is_active"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

        return self.generate_tokens(user)

    def refresh_access_token(self):
        payload = decode_token(self.request.refresh_token)
        validate_token_type(payload, "refresh")

        token_record = self.auth_repository.get_refresh_token(payload.get("jti"))
        if (
            not token_record
            or token_record["revoked_at"] is not None
            or str(token_record["user_id"]) != payload.get("user_id")
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user = self.auth_repository.get_user_by_id(payload["user_id"])
        if not user or user["email"] != payload.get("sub"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        if not user["is_active"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

        # Rotation: the old refresh token is revoked and replaced by a new one
        return self.generate_tokens(user, replaces_jti=payload["jti"])
