"""Case request/response schemas."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Decision = Literal["APPROVE", "REJECT", "ESCALATE"]
CaseStatus = Literal["RECEIVED", "CLASSIFIED", "PROCESSING", "DECIDED", "FAILED"]


class UploadResponse(BaseModel):
    case_id: str
    status: CaseStatus


class CaseListItem(BaseModel):
    case_id: str
    status: CaseStatus
    document_type: str | None
    decision: Decision | None
    confidence: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    items: list[CaseListItem]
    total: int


class CaseDetail(BaseModel):
    case_id: str
    uploaded_by: int
    status: CaseStatus
    document_type: str | None
    document_path: str
    decision: Decision | None
    confidence: float | None
    justification: str | None
    agent_outputs: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OverrideRequest(BaseModel):
    decision: Decision
    note: str = Field(default="", description="Reviewer's reason for the override.")
