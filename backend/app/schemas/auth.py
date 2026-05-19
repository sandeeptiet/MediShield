"""Auth request/response schemas (filled in Phase 2)."""
from pydantic import BaseModel


class GoogleLoginRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
