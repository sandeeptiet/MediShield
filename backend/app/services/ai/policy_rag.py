"""Policy RAG Agent — agentic retrieval over policy PDFs.

Phase 3: pass-through stub.
Phase 4: query reformulation from CPT/ICD codes → embed → search Qdrant →
rerank with BGE → ground with Claude → self-check for exclusion clauses.
"""
from __future__ import annotations

from typing import Any

from app.services.ai.base import BaseAgent
from app.services.ai.state import AgentState, PolicyOutput


class PolicyAgent(BaseAgent):
    name = "policy"

    def process(self, state: AgentState) -> dict[str, Any]:
        output: PolicyOutput = {
            "covered": False,
            "coverage_percentage": 0.0,
            "policy_clause": "",
            "exclusions": [],
            "reranked_top_k": [],
            "confidence": 0.0,
        }
        return {"policy": output}
