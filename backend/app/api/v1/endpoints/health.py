"""Liveness / readiness probes for the v1 API."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict[str, str]:
    # TODO (Phase 2+): check MySQL, Qdrant, Anthropic before reporting ready.
    return {"status": "ready"}
