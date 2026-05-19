"""Case ingestion and management endpoints (stubs for Phase 5)."""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
def upload_case() -> dict:
    """Accept a document upload and kick off the LangGraph pipeline.

    Phase 5 will:
      1. Save the file to upload_dir / S3.
      2. Insert a case row in MySQL (status=PROCESSING).
      3. Schedule the pipeline via FastAPI BackgroundTasks.
      4. Return {case_id, status} immediately.
    """
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 5")


@router.get("/")
def list_cases() -> dict:
    """List cases visible to the current user (with filters / pagination)."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 5")


@router.get("/{case_id}")
def get_case(case_id: str) -> dict:
    """Return one case with its full agent output trail."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 5")


@router.post("/{case_id}/override")
def override_case(case_id: str) -> dict:
    """Human reviewer overrides an escalated case decision."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 5")
