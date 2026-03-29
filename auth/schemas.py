from pydantic import BaseModel


class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    token: str
    user_id: str
    role: str


class LogoutResponse(BaseModel):
    ok: bool
