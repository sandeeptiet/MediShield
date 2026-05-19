"""Orchestrator — LangGraph state machine for the claims-triage pipeline.

Flow:

    START
      ↓
    classifier
      ↓
    ┌─────────┬─────────┐
    │   kyc   │ claims  │      (parallel — independent of each other)
    └─────────┴────┬────┘
                   ↓
                policy            (depends on claims.cpt_codes — agentic RAG)
                   ↓
                fraud             (waits for kyc + policy)
                   ↓
                decide            (Orchestrator aggregation)
                   ↓
                  END

Why Policy runs AFTER Claims (not in parallel with it): Policy RAG forms its
retrieval query from the CPT/ICD codes that Claims extracts. That structured
upstream signal is what makes this "agentic RAG" rather than plain RAG.

Aggregation rules in `decide_node`:
    APPROVE   : KYC pass + claim valid + covered + fraud < 0.3
    REJECT    : KYC fail OR not covered OR schema invalid
    ESCALATE  : fraud >= 0.3 OR any agent confidence < 0.6
"""
from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.core.logging import get_logger
from app.services.ai.claims import ClaimsAgent
from app.services.ai.classifier import ClassifierAgent
from app.services.ai.fraud import FraudAgent
from app.services.ai.kyc import KYCAgent
from app.services.ai.policy_rag import PolicyAgent
from app.services.ai.state import AgentState

logger = get_logger(__name__)


# --- Final aggregator ---------------------------------------------------


CONFIDENCE_FLOOR = 0.6
FRAUD_ESCALATE_THRESHOLD = 0.3


def decide_node(state: AgentState) -> dict[str, Any]:
    """Aggregate per-agent outputs into a single Approve/Reject/Escalate decision."""
    kyc = state.get("kyc", {})
    claims = state.get("claims", {})
    policy = state.get("policy", {})
    fraud = state.get("fraud", {})

    kyc_passed = bool(kyc.get("kyc_passed"))
    schema_valid = bool(claims.get("schema_valid"))
    covered = bool(policy.get("covered"))
    fraud_score = float(fraud.get("fraud_score", 1.0))

    confidences = [
        float(state.get("classifier", {}).get("confidence", 0.0)),
        float(kyc.get("confidence", 0.0)),
        float(claims.get("confidence", 0.0)),
        float(policy.get("confidence", 0.0)),
        float(fraud.get("confidence", 0.0)),
    ]
    overall_conf = min(confidences) if confidences else 0.0

    if not kyc_passed or not schema_valid or not covered:
        decision = "REJECT"
        why = "Hard rule failed (KYC / schema / coverage)."
    elif fraud_score >= FRAUD_ESCALATE_THRESHOLD or overall_conf < CONFIDENCE_FLOOR:
        decision = "ESCALATE"
        why = "Fraud risk above threshold or low agent confidence."
    else:
        decision = "APPROVE"
        why = "All checks passed with sufficient confidence."

    justification = (
        f"{why} kyc_passed={kyc_passed} schema_valid={schema_valid} "
        f"covered={covered} fraud_score={fraud_score:.2f} overall_conf={overall_conf:.2f}"
    )
    logger.info(
        "orchestrator.decision",
        case_id=state.get("case_id"),
        decision=decision,
        overall_conf=overall_conf,
        fraud_score=fraud_score,
    )

    return {
        "decision": decision,
        "overall_confidence": overall_conf,
        "justification": justification,
        "status": "DECIDED",
    }


# --- Graph builder ------------------------------------------------------


def build_graph():
    """Compile the LangGraph StateGraph. Cache the result at the call site."""
    builder = StateGraph(AgentState)

    builder.add_node("classifier", ClassifierAgent())
    builder.add_node("kyc", KYCAgent())
    builder.add_node("claims", ClaimsAgent())
    builder.add_node("policy", PolicyAgent())
    builder.add_node("fraud", FraudAgent())
    builder.add_node("decide", decide_node)

    # Linear start → classifier
    builder.add_edge(START, "classifier")

    # Classifier fans out — kyc and claims are independent and run in parallel
    builder.add_edge("classifier", "kyc")
    builder.add_edge("classifier", "claims")

    # Policy depends on Claims (needs cpt_codes / icd10_codes for retrieval).
    builder.add_edge("claims", "policy")

    # Fraud waits for both KYC and Policy (which itself waited for Claims).
    builder.add_edge("kyc", "fraud")
    builder.add_edge("policy", "fraud")

    # Aggregate + finish.
    builder.add_edge("fraud", "decide")
    builder.add_edge("decide", END)

    return builder.compile()


_graph = None


def get_graph():
    """Return a singleton compiled graph."""
    global _graph
    if _graph is None:
        _graph = build_graph()
        logger.info("orchestrator.graph.compiled")
    return _graph


def run_pipeline(case_id: str, document_path: str, *, uploaded_by: int | None = None) -> AgentState:
    """Synchronously run a case through the pipeline. Used by BackgroundTasks."""
    initial: AgentState = {
        "case_id": case_id,
        "document_path": document_path,
        "status": "RECEIVED",
    }
    if uploaded_by is not None:
        initial["uploaded_by"] = uploaded_by

    return get_graph().invoke(initial)


__all__ = ["build_graph", "get_graph", "run_pipeline", "decide_node"]
