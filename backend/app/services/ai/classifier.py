"""Classifier Agent — Vision LLM that decides document type.

Phase 3: pass-through stub (always returns UNKNOWN).
Phase 4: real Claude-vision call returning {doc_type, confidence, routing_tags}.
"""
from __future__ import annotations

from typing import Any

from app.services.ai.base import BaseAgent
from app.services.ai.state import AgentState, ClassifierOutput


class ClassifierAgent(BaseAgent):
    name = "classifier"

    def process(self, state: AgentState) -> dict[str, Any]:
        output: ClassifierOutput = {
            "doc_type": "UNKNOWN",
            "confidence": 0.0,
            "routing_tags": [],
        }
        return {"classifier": output, "status": "CLASSIFIED"}
