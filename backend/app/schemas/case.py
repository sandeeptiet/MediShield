"""Case request/response schemas (filled in Phase 5)."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

Decision = Literal["APPROVE", "REJECT", "ESCALATE"]
CaseStatus = Literal["RECEIVED", "CLASSIFIED", "PROCESSING", "DECIDED", "FAILED"]


class CaseOut(BaseModel):
    case_id: str
    status: CaseStatus
    document_type: str | None
    decision: Decision | None
    confidence: float | None
    justification: str | None
    agent_outputs: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class UploadResponse(BaseModel):
    case_id: str
    status: CaseStatus
