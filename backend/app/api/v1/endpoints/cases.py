"""Case ingestion and management endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models.case import Case
from app.models.user import User
from app.schemas.case import (
    CaseDetail,
    CaseListItem,
    CaseListResponse,
    OverrideRequest,
    UploadResponse,
)
from app.services.audit import write_audit
from app.services.pipeline import run_pipeline_for_case
from app.services.storage import save_upload

router = APIRouter()


# --- Upload -----------------------------------------------------------------


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_case(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UploadResponse:
    """Accept a document upload and kick off the LangGraph pipeline."""
    case_id = uuid.uuid4().hex
    path = save_upload(case_id, file.filename or "upload.bin", file.file)

    case = Case(
        case_id=case_id,
        uploaded_by=user.id,
        document_path=str(path),
        document_mime=file.content_type,
        status="RECEIVED",
    )
    db.add(case)
    db.commit()

    write_audit(
        db,
        action="UPLOAD",
        status="SUCCESS",
        user_id=user.id,
        role=user.role,
        case_id=case_id,
        details={"filename": file.filename, "mime": file.content_type},
    )

    background_tasks.add_task(run_pipeline_for_case, case_id, user.id)

    return UploadResponse(case_id=case_id, status="RECEIVED")


# --- List -------------------------------------------------------------------


@router.get("", response_model=CaseListResponse)
def list_cases(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> CaseListResponse:
    """Return cases visible to the current user."""
    query = db.query(Case)

    # REVIEWER sees only their own; ADMIN sees everything.
    if user.role != "ADMIN":
        query = query.filter(Case.uploaded_by == user.id)

    if status_filter:
        query = query.filter(Case.status == status_filter)

    total = query.count()
    rows = (
        query.order_by(Case.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return CaseListResponse(
        items=[CaseListItem.model_validate(r) for r in rows],
        total=total,
    )


# --- Detail -----------------------------------------------------------------


def _load_case(db: Session, user: User, case_id: str) -> Case:
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    if user.role != "ADMIN" and case.uploaded_by != user.id:
        # Same 404 for unauthorized as for missing — don't leak existence.
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CaseDetail:
    case = _load_case(db, user, case_id)
    return CaseDetail.model_validate(case)


# --- Override ---------------------------------------------------------------


@router.post("/{case_id}/override", response_model=CaseDetail)
def override_case(
    case_id: str,
    payload: OverrideRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("ADMIN")),
) -> CaseDetail:
    """Admin overrides the decision on an escalated case."""
    case = _load_case(db, user, case_id)

    if case.status != "DECIDED":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"Cannot override a case in status {case.status}",
        )

    previous_decision = case.decision
    case.decision = payload.decision
    case.justification = (
        f"[OVERRIDDEN by {user.email}] {payload.decision}. "
        f"Reviewer note: {payload.note or '(none)'}. "
        f"Previous: {previous_decision}. "
        f"Original justification: {case.justification or ''}"
    )
    db.commit()
    db.refresh(case)

    write_audit(
        db,
        action="OVERRIDE",
        status="SUCCESS",
        user_id=user.id,
        role=user.role,
        case_id=case_id,
        details={
            "from": previous_decision,
            "to": payload.decision,
            "note": payload.note,
        },
    )

    return CaseDetail.model_validate(case)
