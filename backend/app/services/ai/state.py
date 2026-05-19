"""LangGraph state schema for the claims-triage workflow.

This is the single contract every agent codes against. Each agent reads its
inputs from the state and writes a single namespaced key back. The Orchestrator
node reads the aggregated outputs and emits the final decision.
"""
from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

# --- Enums (string literals) ---------------------------------------------

DocumentType = Literal[
    "CLAIM_FORM",
    "ID_DOCUMENT",
    "DISCHARGE_SUMMARY",
    "PRESCRIPTION",
    "POLICY_AMENDMENT",
    "UNKNOWN",
]

Decision = Literal["APPROVE", "REJECT", "ESCALATE"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
CaseStatus = Literal["RECEIVED", "CLASSIFIED", "PROCESSING", "DECIDED", "FAILED"]


# --- Per-agent output shapes ---------------------------------------------


class ClassifierOutput(TypedDict, total=False):
    doc_type: DocumentType
    confidence: float
    routing_tags: list[str]


class KYCOutput(TypedDict, total=False):
    kyc_passed: bool
    flags: list[str]
    extracted_fields: dict[str, Any]  # member_id, name, dob (if extractable), expiry
    tamper_score: float               # 0.0 = clean, 1.0 = clear tampering
    confidence: float


class ClaimsOutput(TypedDict, total=False):
    extracted_fields: dict[str, Any]  # icd10, cpt, amount, provider_npi, service_date
    schema_valid: bool
    validation_errors: list[str]
    confidence: float


class PolicyOutput(TypedDict, total=False):
    covered: bool
    coverage_percentage: float
    policy_clause: str                # the most relevant retrieved clause
    exclusions: list[str]
    reranked_top_k: list[dict[str, Any]]  # chunks used, for audit
    confidence: float


class FraudOutput(TypedDict, total=False):
    fraud_score: float                # 0.0 - 1.0
    risk_level: RiskLevel
    anomalies: list[str]
    explanation: str
    confidence: float


class AgentError(TypedDict):
    agent: str
    message: str
    type: str


# --- The full state passed between LangGraph nodes ----------------------


class AgentState(TypedDict):
    """LangGraph state for one case traveling through the pipeline."""

    # Inputs
    case_id: str
    document_path: str
    document_mime: NotRequired[str]
    uploaded_by: NotRequired[int]

    # Per-agent outputs (filled in by each node)
    classifier: NotRequired[ClassifierOutput]
    kyc: NotRequired[KYCOutput]
    claims: NotRequired[ClaimsOutput]
    policy: NotRequired[PolicyOutput]
    fraud: NotRequired[FraudOutput]

    # Aggregated outputs
    decision: NotRequired[Decision]
    overall_confidence: NotRequired[float]
    justification: NotRequired[str]

    # Diagnostics
    errors: NotRequired[list[AgentError]]
    status: NotRequired[CaseStatus]
