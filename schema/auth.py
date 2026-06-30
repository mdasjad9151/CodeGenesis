from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class OAuthLoginRequest(BaseModel):
    provider: str
    access_token: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str