import os
import time
import random
from datetime import datetime, timezone
import jwt
from passlib.context import CryptContext
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

    def build_token_payload(self, user: dict, token_type: str, expires_in_seconds: int) -> dict:
        return {
            "sub": user["email"],
            "user_id": str(user["id"]),
            "is_verified": bool(user["is_verified"]),
            "is_active": bool(user["is_active"]),
            "token_type": token_type,
            "exp": time.time() + expires_in_seconds,
        }

    def encode_jwt_token(self, payload: dict) -> str:
        jwt_config = self.config.jwt_config()
        return jwt.encode(payload, jwt_config['secret_key'], algorithm=jwt_config['algorithm'])

    def generate_access_token(self, user: dict) -> str:
        payload = self.build_token_payload(
            user=user,
            token_type="access",
            expires_in_seconds=3,
        )
        return self.encode_jwt_token(payload)

    def generate_refresh_token(self, user: dict) -> str:
        payload = self.build_token_payload(
            user=user,
            token_type="refresh",
            expires_in_seconds=4 * 24 * 60 * 60,
        )
        return self.encode_jwt_token(payload)

    def generate_tokens(self, user: dict) -> dict:
        access_token = self.generate_access_token(user)
        refresh_token = self.generate_refresh_token(user)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def send_otp(self, email: str, otp: str):
        print(f"\n[EMAIL SIMULATION] To: {email} | Message: Your verification OTP code is {otp}\n")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def register_user(self):
        email = self.request.email
        password = self.request.password
        if self.auth_repository.user_exists(email):
            return {"message": "User already exists", "status_code": 400}
        try:
            hashed_password = self.hash_password(password)
            otp_code = f"{random.randint(100000, 999999)}"
            self.auth_repository.create_user(email=email, password=hashed_password, otp=otp_code)
            self.send_otp(email, otp_code)
            return {"message": "Sending Otp ....", "status_code": 201}
        except Exception as e:
            return {"message": f"Error registering user: {str(e)}", "status_code": 500}
        
    async def verify_otp(self):
        try:
            email = self.request.email
            otp = self.request.otp
            user = self.auth_repository.get_user_by_email(email)
            if not user:
                return {"message": "User not found", "status_code": 404}

            if user["is_verified"]:
                return {"message": "User already verified", "status_code": 400}

            otp_record = self.auth_repository.get_active_registration_otp(str(user["id"]))
            if not otp_record:
                return {"message": "OTP not found", "status_code": 404}

            if otp_record["otp_code"] != otp:
                return {"message": "Invalid OTP", "status_code": 400}

            expires_at = otp_record["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at < datetime.now(timezone.utc):
                return {"message": "OTP expired", "status_code": 400}

            self.auth_repository.mark_user_as_verified(str(user["id"]), str(otp_record["id"]))
            return {"message": "User verified successfully", "status_code": 200}
        except Exception as e:
            return {"message": f"Error verifying OTP: {str(e)}", "status_code": 500}

    async def login_user(self):
        try:
            email = self.request.email
            password = self.request.password
            user = self.auth_repository.get_login_user_by_email(email)

            if not user:
                return {"message": "Invalid email or password", "status_code": 401}

            if not user["is_verified"]:
                return {"message": "User is not verified", "status_code": 403}

            if not user["is_active"]:
                return {"message": "User account is inactive", "status_code": 403}

            if not user["hashed_password"] or not self.verify_password(password, user["hashed_password"]):
                return {"message": "Invalid email or password", "status_code": 401}

            tokens = self.generate_tokens(user)
            return {
                "message": "Login successful",
                "status_code": 200,
                "data": tokens
            }
        except Exception as e:
            return {"message": f"Error logging in user: {str(e)}", "status_code": 500}

    async def refresh_access_token(self):
        try:
            jwt_config = self.config.jwt_config()
            payload = jwt.decode(
                self.request.refresh_token,
                jwt_config["secret_key"],
                algorithms=[jwt_config["algorithm"]],
            )

            if payload.get("token_type") != "refresh":
                return {"message": "Invalid refresh token", "status_code": 401}

            if payload.get("is_active") is not True or not payload.get("sub"):
                return {"message": "Invalid refresh token", "status_code": 401}

            user = {
                "id": payload.get("user_id"),
                "email": payload.get("sub"),
                "is_verified": payload.get("is_verified", False),
                "is_active": payload.get("is_active", False),
            }
            access_token = self.generate_access_token(user)
            return {
                "message": "Access token refreshed successfully",
                "status_code": 200,
                "data": {
                    "access_token": access_token,
                    "token_type": "bearer",
                }
            }
        except jwt.ExpiredSignatureError:
            return {"message": "Refresh token has expired", "status_code": 401}
        except jwt.InvalidTokenError:
            return {"message": "Invalid refresh token", "status_code": 401}

    async def home(self):
        return {"message": "Welcome to the Auth Service", "status_code": 200}
