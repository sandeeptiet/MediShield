"""JWT creation + verification + Google ID-token verification (Phase 2)."""
# from datetime import datetime, timedelta
# from jose import JWTError, jwt
# from google.auth.transport import requests as google_requests
# from google.oauth2 import id_token
#
# from app.config import settings
#
#
# def create_access_token(subject: dict) -> str:
#     expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
#     payload = {"sub": subject, "exp": expire}
#     return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
#
#
# def verify_access_token(token: str) -> dict:
#     return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
#
#
# def verify_google_id_token(token: str) -> dict:
#     return id_token.verify_oauth2_token(
#         token, google_requests.Request(), settings.google_client_id
#     )
