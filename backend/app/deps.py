"""Shared FastAPI dependencies (auth, DB, current user).

Phase 2 will wire Google OAuth + JWT verification here.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db


def get_current_user(db: Session = Depends(get_db)):
    """Returns the authenticated user from JWT in the Authorization header.

    Phase 2 will implement: extract Bearer token → verify JWT → load User from DB.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Auth not yet implemented (Phase 2)",
    )


def require_role(required: str):
    """Returns a dependency that enforces a minimum role on the current user."""
    def _checker(user=Depends(get_current_user)):
        if user.role != required and user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role {required}",
            )
        return user
    return _checker
