"""Fraud Agent — IsolationForest anomaly score + Claude explanation.

Phase 3: pass-through stub.
Phase 4: feature build from claim history + IsolationForest score + Claude explanation.
"""
from __future__ import annotations

from typing import Any

from app.services.ai.base import BaseAgent
from app.services.ai.state import AgentState, FraudOutput


class FraudAgent(BaseAgent):
    name = "fraud"

    def process(self, state: AgentState) -> dict[str, Any]:
        output: FraudOutput = {
            "fraud_score": 0.0,
            "risk_level": "LOW",
            "anomalies": [],
            "explanation": "stub",
            "confidence": 0.0,
        }
        return {"fraud": output}
