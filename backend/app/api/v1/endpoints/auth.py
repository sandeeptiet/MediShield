"""Google OAuth + JWT auth endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.metrics import auth_attempts
from app.core.security import InvalidTokenError
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import GoogleLoginRequest, TokenResponse, UserOut
from app.services.auth import AccessDeniedError, login_with_google

router = APIRouter()


@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Exchange a Google ID token for a MediShield JWT."""
    try:
        user, token, expires_in = login_with_google(db, payload.id_token)
    except InvalidTokenError as exc:
        auth_attempts.labels(outcome="invalid").inc()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except AccessDeniedError:
        auth_attempts.labels(outcome="denied").inc()
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Access denied — contact your administrator",
        )

    auth_attempts.labels(outcome="success").inc()
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Return the currently authenticated user."""
    return UserOut.model_validate(current_user)
