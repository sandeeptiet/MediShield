"""Smoke tests: the LangGraph orchestrator compiles and the wiring is correct.

End-to-end behaviour with mocked external services lives in test_agents.py.
This file is now narrower: it just asserts the graph builds and is a singleton.
"""
from __future__ import annotations

from app.services.ai.orchestrator import build_graph, get_graph


def test_graph_compiles() -> None:
    graph = build_graph()
    assert graph is not None


def test_graph_singleton() -> None:
    assert get_graph() is get_graph()


def test_graph_has_expected_nodes() -> None:
    # LangGraph exposes the compiled node names via .nodes
    graph = build_graph()
    expected = {"classifier", "kyc", "claims", "policy", "fraud", "decide"}
    actual = set(graph.nodes.keys())  # type: ignore[attr-defined]
    assert expected.issubset(actual), f"missing nodes: {expected - actual}"
