"""JWT issuance + verification + Google ID-token verification."""
from datetime import datetime, timedelta, timezone

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError, jwt

from app.config import settings


class InvalidTokenError(Exception):
    """Raised when a token cannot be verified."""


def create_access_token(user_id: int, role: str, email: str) -> tuple[str, int]:
    """Create a MediShield JWT.

    Returns (token, expires_in_seconds).
    """
    expires_in = settings.jwt_expire_hours * 3600
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "role": role,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_in


def verify_access_token(token: str) -> dict:
    """Decode and validate a MediShield JWT."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidTokenError(str(exc)) from exc


def verify_google_id_token(token: str) -> dict:
    """Verify a Google-issued ID token. Returns the payload (email, sub, name, ...).

    Raises InvalidTokenError on any verification failure.
    """
    if not settings.google_client_id:
        raise InvalidTokenError("GOOGLE_CLIENT_ID is not configured")
    try:
        payload = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError as exc:
        raise InvalidTokenError(str(exc)) from exc

    if not payload.get("email_verified"):
        raise InvalidTokenError("Google email is not verified")
    return payload
