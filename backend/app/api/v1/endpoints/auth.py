"""Google OAuth + JWT auth endpoints (stubs for Phase 2)."""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.post("/google")
def google_login() -> dict:
    """Exchange a Google ID token for a MediShield JWT.

    Phase 2 will:
      1. Verify the Google ID token via google-auth.
      2. Look up the email in the users table (allowlist).
      3. Issue a MediShield JWT with role baked in.
    """
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.get("/me")
def me() -> dict:
    """Return the currently authenticated user."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")
