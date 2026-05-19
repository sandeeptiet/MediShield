"""Liveness / readiness probes for the v1 API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

router = APIRouter()


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, object]:
    """Returns 200 if all required dependencies are reachable; 503 otherwise."""
    components: dict[str, str] = {}

    # 1. MySQL
    try:
        db.execute(text("SELECT 1"))
        components["mysql"] = "ok"
    except Exception as exc:  # pragma: no cover — exercised in deployment, not unit tests
        components["mysql"] = f"down: {exc.__class__.__name__}"

    # 2. Qdrant
    try:
        from app.services.ai.vector_store import get_qdrant
        get_qdrant().get_collections()
        components["qdrant"] = "ok"
    except Exception as exc:
        components["qdrant"] = f"down: {exc.__class__.__name__}"

    # 3. Anthropic key present (we don't make a real call — that would be wasteful per probe)
    components["anthropic_key"] = "ok" if settings.anthropic_api_key else "missing"

    ok = all(v == "ok" for v in components.values())
    payload = {"status": "ready" if ok else "degraded", "components": components}
    if not ok:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=payload)
    return payload
