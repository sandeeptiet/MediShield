"""Audit logging helper — single write path for ai_audit_logs."""
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AIAuditLog


def write_audit(
    db: Session,
    *,
    action: str,
    status: str,
    user_id: int | None = None,
    role: str | None = None,
    case_id: str | None = None,
    agent_name: str | None = None,
    tool_name: str | None = None,
    details: dict[str, Any] | None = None,
) -> AIAuditLog:
    entry = AIAuditLog(
        action=action,
        status=status,
        user_id=user_id,
        role=role,
        case_id=case_id,
        agent_name=agent_name,
        tool_name=tool_name,
        details=details,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
