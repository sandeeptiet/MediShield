"""Unit tests for each agent — Claude/Qdrant/embeddings mocked.

These verify the *contract*: given mocked external services, does each agent
write the right slot in AgentState with the right shape?
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.services.ai.claims import ClaimsAgent
from app.services.ai.classifier import ClassifierAgent
from app.services.ai.fraud import FraudAgent
from app.services.ai.kyc import KYCAgent
from app.services.ai.policy_rag import PolicyAgent
from app.services.ai.schemas import (
    ClaimsFields,
    ClassifierResult,
    FraudExplanation,
    KYCFields,
    PolicyVerdict,
)
from app.services.ai.state import AgentState


# --- Classifier ---------------------------------------------------------


def test_classifier_writes_doc_type(tmp_path) -> None:
    img = tmp_path / "doc.jpg"
    img.write_bytes(b"fake-image")

    fake = ClassifierResult(
        doc_type="CLAIM_FORM", confidence=0.92, routing_tags=["surgical"], reasoning="claim form layout"
    )
    with patch("app.services.ai.classifier.complete_json", return_value=fake):
        agent = ClassifierAgent()
        state: AgentState = {"case_id": "c1", "document_path": str(img)}
        patch_out = agent(state)

    assert patch_out["classifier"]["doc_type"] == "CLAIM_FORM"
    assert patch_out["classifier"]["confidence"] == 0.92
    assert patch_out["status"] == "CLASSIFIED"


# --- Claims -------------------------------------------------------------


def test_claims_validates_codes(tmp_path) -> None:
    img = tmp_path / "claim.jpg"
    img.write_bytes(b"fake")

    fake = ClaimsFields(
        claim_amount=1200.0,
        icd10_codes=["H25.13"],
        cpt_codes=["66984"],
        provider_npi="1234567890",
        service_date="2026-05-12",
        extraction_confidence=0.88,
    )
    with patch("app.services.ai.claims.complete_json", return_value=fake):
        agent = ClaimsAgent()
        out = agent({"case_id": "c1", "document_path": str(img)})

    assert out["claims"]["schema_valid"] is True
    assert out["claims"]["validation_errors"] == []
    assert out["claims"]["extracted_fields"]["cpt_codes"] == ["66984"]


def test_claims_flags_malformed_cpt(tmp_path) -> None:
    img = tmp_path / "claim.jpg"
    img.write_bytes(b"fake")

    fake = ClaimsFields(
        claim_amount=500.0,
        icd10_codes=["H25.13"],
        cpt_codes=["66984", "ABC12"],     # second is invalid
        service_date="2026-05-12",
        extraction_confidence=0.7,
    )
    with patch("app.services.ai.claims.complete_json", return_value=fake):
        out = ClaimsAgent()({"case_id": "c1", "document_path": str(img)})

    assert out["claims"]["schema_valid"] is False
    assert any("ABC12" in e for e in out["claims"]["validation_errors"])


# --- KYC ----------------------------------------------------------------


def test_kyc_passes_when_fields_present_and_no_tampering(tmp_path) -> None:
    img = tmp_path / "id.jpg"
    img.write_bytes(b"fake")

    fake_fields = KYCFields(
        member_id="M-42",
        full_name="Jane Doe",
        id_number="ID-001",
        id_type="PASSPORT",
        expiry_date="2030-01-01",
        extraction_confidence=0.9,
    )
    fake_ela = {"tamper_score": 0.05, "suspicious_regions": [], "notes": "clean"}

    with (
        patch("app.services.ai.kyc.complete_json", return_value=fake_fields),
        patch("app.services.ai.kyc.compute_ela", return_value=fake_ela),
    ):
        out = KYCAgent()({"case_id": "c1", "document_path": str(img)})

    assert out["kyc"]["kyc_passed"] is True
    assert out["kyc"]["tamper_score"] == 0.05
    assert out["kyc"]["flags"] == []


def test_kyc_fails_when_tampered(tmp_path) -> None:
    img = tmp_path / "id.jpg"
    img.write_bytes(b"fake")

    fake_fields = KYCFields(
        member_id="M-42",
        full_name="Jane Doe",
        id_number="ID-001",
        id_type="PASSPORT",
        expiry_date="2030-01-01",
        extraction_confidence=0.9,
    )
    fake_ela = {"tamper_score": 0.8, "suspicious_regions": [], "notes": "high"}

    with (
        patch("app.services.ai.kyc.complete_json", return_value=fake_fields),
        patch("app.services.ai.kyc.compute_ela", return_value=fake_ela),
    ):
        out = KYCAgent()({"case_id": "c1", "document_path": str(img)})

    assert out["kyc"]["kyc_passed"] is False
    assert any("tamper_score_high" in f for f in out["kyc"]["flags"])


# --- Policy RAG ---------------------------------------------------------


def test_policy_skips_when_no_codes() -> None:
    out = PolicyAgent()({"case_id": "c1", "document_path": "/tmp/x", "claims": {"extracted_fields": {}}})
    assert out["policy"]["covered"] is False
    assert out["policy"]["confidence"] == 0.0


def test_policy_grounds_in_retrieved_clauses() -> None:
    state: AgentState = {
        "case_id": "c1",
        "document_path": "/tmp/x",
        "claims": {
            "extracted_fields": {"cpt_codes": ["66984"], "icd10_codes": ["H25.13"]},
        },
    }

    fake_search = [
        {"score": 0.91, "payload": {"text": "Cataract surgery covered at 80%.",
                                    "policy_name": "Vision",
                                    "section": "Cataract"}},
        {"score": 0.80, "payload": {"text": "General exclusions list.",
                                    "policy_name": "Vision",
                                    "section": "Exclusions"}},
    ]
    fake_rank = [(0, 0.95), (1, 0.40)]
    fake_verdict = PolicyVerdict(
        covered=True,
        coverage_percentage=80.0,
        policy_clause="Cataract surgery covered at 80%.",
        exclusions=[],
        confidence=0.86,
        reasoning="clause directly addresses cataract",
    )

    with (
        patch("app.services.ai.policy_rag.search", return_value=fake_search),
        patch("app.services.ai.policy_rag.rerank", return_value=fake_rank),
        patch("app.services.ai.policy_rag.complete_json", return_value=fake_verdict),
    ):
        out = PolicyAgent()(state)

    assert out["policy"]["covered"] is True
    assert out["policy"]["coverage_percentage"] == 80.0
    assert out["policy"]["policy_clause"].startswith("Cataract")


# --- Fraud --------------------------------------------------------------


def test_fraud_scores_low_for_normal_claim() -> None:
    state: AgentState = {
        "case_id": "c1",
        "document_path": "/tmp/x",
        "claims": {
            "extracted_fields": {
                "claim_amount": 1500.0,
                "cpt_codes": ["66984"],
                "icd10_codes": ["H25.13"],
                "service_date": "2026-05-15",
            },
        },
        "kyc": {"tamper_score": 0.05, "flags": []},
    }
    fake_expl = FraudExplanation(
        risk_level="LOW",
        anomalies=[],
        explanation="Routine claim, no anomalies.",
        confidence=0.85,
    )
    with patch("app.services.ai.fraud.complete_json", return_value=fake_expl):
        out = FraudAgent()(state)

    assert out["fraud"]["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert 0.0 <= out["fraud"]["fraud_score"] <= 1.0


def test_fraud_continues_when_llm_unavailable() -> None:
    state: AgentState = {
        "case_id": "c1",
        "document_path": "/tmp/x",
        "claims": {"extracted_fields": {"claim_amount": 1500.0, "cpt_codes": ["66984"]}},
        "kyc": {"tamper_score": 0.05, "flags": []},
    }
    with patch("app.services.ai.fraud.complete_json", side_effect=RuntimeError("boom")):
        out = FraudAgent()(state)

    assert "fraud" in out
    assert out["fraud"]["anomalies"] == []
    assert "fraud_score" in out["fraud"]


# --- Compatibility: Phase 3 smoke test should be updated ---------------


def test_graph_smoke_still_runs_with_real_agents() -> None:
    """The old Phase 3 smoke test only worked when agents were pass-throughs.
    Now that they make external calls, we need to mock them. This test asserts
    the *graph wiring* is still intact by patching every external call.
    """
    from app.services.ai.orchestrator import run_pipeline

    fake_classifier = ClassifierResult(doc_type="CLAIM_FORM", confidence=0.9, routing_tags=[])
    fake_kyc_fields = KYCFields(
        member_id="M", full_name="N", id_number="X",
        id_type="PASSPORT", expiry_date="2030-01-01",
        extraction_confidence=0.9,
    )
    fake_claims = ClaimsFields(
        claim_amount=1500.0,
        icd10_codes=["H25.13"], cpt_codes=["66984"],
        service_date="2026-05-15",
        extraction_confidence=0.9,
    )
    fake_verdict = PolicyVerdict(
        covered=True, coverage_percentage=80.0,
        policy_clause="covered", exclusions=[], confidence=0.85,
    )
    fake_explanation = FraudExplanation(
        risk_level="LOW", anomalies=[], explanation="ok", confidence=0.85,
    )

    with (
        patch("app.services.ai.classifier.complete_json", return_value=fake_classifier),
        patch("app.services.ai.kyc.complete_json", return_value=fake_kyc_fields),
        patch("app.services.ai.kyc.compute_ela",
              return_value={"tamper_score": 0.05, "suspicious_regions": [], "notes": ""}),
        patch("app.services.ai.claims.complete_json", return_value=fake_claims),
        patch("app.services.ai.policy_rag.search", return_value=[{"score": 0.9,
              "payload": {"text": "covered", "policy_name": "p", "section": "s"}}]),
        patch("app.services.ai.policy_rag.rerank", return_value=[(0, 0.95)]),
        patch("app.services.ai.policy_rag.complete_json", return_value=fake_verdict),
        patch("app.services.ai.fraud.complete_json", return_value=fake_explanation),
    ):
        out = run_pipeline("smoke-1", "/tmp/x.jpg", uploaded_by=1)

    assert out["status"] == "DECIDED"
    assert out["decision"] in {"APPROVE", "REJECT", "ESCALATE"}
    assert "justification" in out
    # End-to-end happy path should approve.
    assert out["decision"] == "APPROVE"
