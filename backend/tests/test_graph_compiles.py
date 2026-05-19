"""Smoke tests: the LangGraph orchestrator compiles and runs all 6 nodes.

These tests use the Phase 3 pass-through agents — no external services are
hit (no Claude, no Qdrant, no models loaded). Phase 4 will replace each agent
with the real implementation; these tests should keep passing.
"""
from __future__ import annotations

from app.services.ai.orchestrator import build_graph, get_graph, run_pipeline
from app.services.ai.state import AgentState


def test_graph_compiles() -> None:
    graph = build_graph()
    assert graph is not None


def test_graph_singleton() -> None:
    assert get_graph() is get_graph()


def test_pipeline_runs_all_pass_through_agents() -> None:
    out: AgentState = run_pipeline(
        case_id="test-case-001",
        document_path="/tmp/fake.jpg",
        uploaded_by=42,
    )

    # Every agent ran and wrote its slot.
    assert "classifier" in out and out["classifier"]["doc_type"] == "UNKNOWN"
    assert "kyc" in out and out["kyc"]["kyc_passed"] is False
    assert "claims" in out and out["claims"]["schema_valid"] is False
    assert "policy" in out and out["policy"]["covered"] is False
    assert "fraud" in out and out["fraud"]["risk_level"] == "LOW"

    # decide_node aggregated and produced a final decision.
    # With all stubs at 0 confidence + not-covered, we expect REJECT.
    assert out["decision"] == "REJECT"
    assert out["status"] == "DECIDED"
    assert "justification" in out
    assert out["case_id"] == "test-case-001"


def test_state_carries_inputs_through() -> None:
    out = run_pipeline("c2", "/tmp/x.png", uploaded_by=7)
    assert out["case_id"] == "c2"
    assert out["document_path"] == "/tmp/x.png"
    assert out["uploaded_by"] == 7
