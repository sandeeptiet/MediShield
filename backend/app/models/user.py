"""User model — Google OAuth allowlist + role.

Phase 2 fleshes out the columns and adds the Alembic migration.
"""
# from datetime import datetime
# from sqlalchemy import String, Boolean, DateTime
# from sqlalchemy.orm import Mapped, mapped_column
#
# from app.database import Base
#
#
# class User(Base):
#     __tablename__ = "users"
#
#     id: Mapped[int] = mapped_column(primary_key=True)
#     email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
#     name: Mapped[str] = mapped_column(String(255))
#     role: Mapped[str] = mapped_column(String(20))           # REVIEWER | ADMIN
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
