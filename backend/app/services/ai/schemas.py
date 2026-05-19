"""Pydantic schemas used with `llm.complete_json` to force structured Claude output.

Each agent has one schema. The schema is what Anthropic's tool-use API forces
the model to emit; the agent then converts the validated Pydantic object into
the appropriate slot in AgentState.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.services.ai.state import DocumentType, RiskLevel


# --- Classifier ---------------------------------------------------------


class ClassifierResult(BaseModel):
    doc_type: DocumentType = Field(description="One of the allowed document types")
    confidence: float = Field(ge=0.0, le=1.0)
    routing_tags: list[str] = Field(
        default_factory=list,
        description="Short tags that help downstream agents, e.g. 'inpatient', 'surgical'.",
    )
    reasoning: str = Field(
        default="",
        description="One-sentence rationale for the classification (audit trail).",
    )


# --- KYC ----------------------------------------------------------------


class KYCFields(BaseModel):
    member_id: str | None = None
    full_name: str | None = None
    date_of_birth: str | None = Field(default=None, description="ISO format if extractable.")
    id_number: str | None = None
    id_type: str | None = Field(default=None, description="e.g. PASSPORT, DRIVER_LICENSE, AADHAAR")
    expiry_date: str | None = Field(default=None, description="ISO format if extractable.")
    extraction_confidence: float = Field(ge=0.0, le=1.0)
    notes: str = Field(default="", description="Free-form observations Claude wants to surface.")


# --- Claims -------------------------------------------------------------


class ClaimsFields(BaseModel):
    claim_amount: float | None = Field(default=None, ge=0.0)
    currency: str = Field(default="USD")
    icd10_codes: list[str] = Field(default_factory=list)
    cpt_codes: list[str] = Field(default_factory=list)
    provider_npi: str | None = Field(default=None, description="10-digit US NPI if extractable.")
    provider_name: str | None = None
    service_date: str | None = Field(default=None, description="ISO format if extractable.")
    patient_name: str | None = None
    member_id: str | None = None
    extraction_confidence: float = Field(ge=0.0, le=1.0)
    notes: str = ""


# --- Policy RAG ---------------------------------------------------------


class PolicyVerdict(BaseModel):
    covered: bool
    coverage_percentage: float = Field(ge=0.0, le=100.0, default=0.0)
    policy_clause: str = Field(
        default="",
        description="The exact clause text from retrieved context that drives the decision.",
    )
    exclusions: list[str] = Field(
        default_factory=list,
        description="Specific exclusions or pre-authorization requirements found in context.",
    )
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(
        default="",
        description="Brief rationale grounded in retrieved clauses (audit trail).",
    )


# --- Fraud --------------------------------------------------------------


class FraudExplanation(BaseModel):
    risk_level: RiskLevel
    anomalies: list[str] = Field(
        default_factory=list,
        description="Plain-language list of suspicious signals found.",
    )
    explanation: str = Field(
        description="Short reviewer-friendly narrative of why this case scored as it did."
    )
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
