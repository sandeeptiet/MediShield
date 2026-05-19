"""Case model — one row per submitted document."""
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _new_case_id() -> str:
    return uuid.uuid4().hex


class Case(Base):
    __tablename__ = "cases"

    case_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_case_id)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    document_path: Mapped[str] = mapped_column(String(512), nullable=False)
    document_mime: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # CLAIM_FORM | ID_DOCUMENT | DISCHARGE_SUMMARY | PRESCRIPTION | POLICY_AMENDMENT | UNKNOWN

    status: Mapped[str] = mapped_column(String(20), default="RECEIVED", nullable=False, index=True)
    # RECEIVED | CLASSIFIED | PROCESSING | DECIDED | FAILED

    decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # APPROVE | REJECT | ESCALATE

    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_outputs: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Case {self.case_id} status={self.status} decision={self.decision}>"
