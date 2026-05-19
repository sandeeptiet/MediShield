"""Auth service — Google login flow + JWT issuance (Phase 2)."""
# from sqlalchemy.orm import Session
#
# from app.core.security import verify_google_id_token, create_access_token
# from app.models.user import User
#
#
# def login_with_google(db: Session, google_id_token: str) -> tuple[User, str]:
#     payload = verify_google_id_token(google_id_token)
#     email = payload["email"]
#
#     user = db.query(User).filter_by(email=email, is_active=True).first()
#     if not user:
#         raise PermissionError("Email not in allowlist")
#
#     token = create_access_token({"user_id": user.id, "role": user.role})
#     return user, token
