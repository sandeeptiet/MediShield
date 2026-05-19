"""Auth service — Google login flow + JWT issuance."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.security import (
    InvalidTokenError,
    create_access_token,
    verify_google_id_token,
)
from app.models.user import User
from app.services.audit import write_audit


class AccessDeniedError(Exception):
    """Raised when the verified Google email is not in the user allowlist."""


def login_with_google(db: Session, google_id_token: str) -> tuple[User, str, int]:
    """Verify a Google ID token, look up the user, issue a MediShield JWT.

    Returns (user, access_token, expires_in_seconds).
    Raises InvalidTokenError or AccessDeniedError.
    """
    payload = verify_google_id_token(google_id_token)
    email = payload["email"].lower()
    google_sub = payload.get("sub")
    name = payload.get("name") or email

    user = db.query(User).filter(User.email == email).first()

    if user is None or not user.is_active:
        write_audit(
            db,
            action="LOGIN_DENIED",
            status="BLOCKED",
            details={"email": email, "reason": "not_in_allowlist_or_inactive"},
        )
        raise AccessDeniedError("Email not authorized")

    if not user.google_sub and google_sub:
        user.google_sub = google_sub
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    token, expires_in = create_access_token(
        user_id=user.id, role=user.role, email=user.email
    )

    write_audit(
        db,
        action="LOGIN_SUCCESS",
        status="SUCCESS",
        user_id=user.id,
        role=user.role,
        details={"email": email, "name": name},
    )

    return user, token, expires_in


__all__ = ["login_with_google", "AccessDeniedError", "InvalidTokenError"]
