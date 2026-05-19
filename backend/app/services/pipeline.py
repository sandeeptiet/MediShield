"""Async pipeline runner.

Called from FastAPI BackgroundTasks after a successful upload. Owns its own
DB session — never share the request's session, since the request returns
before the pipeline finishes.

Flow:
    1. Mark case PROCESSING.
    2. Invoke the LangGraph orchestrator.
    3. Persist agent outputs + decision + justification.
    4. Write a DECIDE / FAILED audit row.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.core.metrics import cases_processed
from app.database import SessionLocal
from app.models.case import Case
from app.services.ai.orchestrator import run_pipeline as run_graph
from app.services.audit import write_audit

logger = get_logger(__name__)


def _set_case(case: Case, **fields: Any) -> None:
    for k, v in fields.items():
        setattr(case, k, v)


def run_pipeline_for_case(case_id: str, uploaded_by: int | None) -> None:
    """Run the agent pipeline for a case and persist results."""
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if case is None:
            logger.error("pipeline.case_missing", case_id=case_id)
            return

        _set_case(case, status="PROCESSING", error_message=None)
        db.commit()

        try:
            result = run_graph(
                case_id=case_id,
                document_path=case.document_path,
                uploaded_by=uploaded_by,
            )
        except Exception as exc:
            logger.exception("pipeline.unhandled_error", case_id=case_id)
            _set_case(case, status="FAILED", error_message=str(exc))
            db.commit()
            write_audit(
                db,
                action="DECIDE",
                status="FAILED",
                user_id=uploaded_by,
                case_id=case_id,
                details={"error": str(exc)},
            )
            cases_processed.labels(decision="FAILED").inc()
            return

        agent_outputs = _collect_agent_outputs(result)
        decision = result.get("decision")
        confidence = result.get("overall_confidence")
        justification = result.get("justification")

        if not decision:
            _set_case(case, status="FAILED", error_message="orchestrator returned no decision")
            cases_processed.labels(decision="FAILED").inc()
            db.commit()
            write_audit(
                db,
                action="DECIDE",
                status="FAILED",
                user_id=uploaded_by,
                case_id=case_id,
                details={"reason": "no_decision"},
            )
            return

        _set_case(
            case,
            status="DECIDED",
            decision=decision,
            confidence=confidence,
            justification=justification,
            agent_outputs=agent_outputs,
            document_type=(result.get("classifier") or {}).get("doc_type"),
        )
        db.commit()

        write_audit(
            db,
            action="DECIDE",
            status="SUCCESS",
            user_id=uploaded_by,
            case_id=case_id,
            details={
                "decision": decision,
                "confidence": confidence,
                "errors": result.get("errors", []),
            },
        )
        cases_processed.labels(decision=decision).inc()
        logger.info(
            "pipeline.done",
            case_id=case_id,
            decision=decision,
            confidence=confidence,
        )
    finally:
        db.close()


def _collect_agent_outputs(state: dict[str, Any]) -> dict[str, Any]:
    """Pull the per-agent slots out of the final LangGraph state for persistence."""
    return {
        k: state.get(k)
        for k in ("classifier", "kyc", "claims", "policy", "fraud", "errors")
        if state.get(k) is not None
    }


__all__ = ["run_pipeline_for_case"]
