"""AI audit log model — append-only compliance trail."""
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIAuditLog(Base):
    __tablename__ = "ai_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    role: Mapped[str | None] = mapped_column(String(20), nullable=True)

    case_id: Mapped[str | None] = mapped_column(
        ForeignKey("cases.case_id"), nullable=True, index=True
    )

    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # LOGIN_SUCCESS | LOGIN_DENIED | UPLOAD | DECIDE | OVERRIDE | AGENT_CALL | ...

    agent_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)  # SUCCESS | FAILED | BLOCKED
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<AIAuditLog id={self.id} action={self.action} status={self.status}>"
