"""Claims Agent — extracts ICD-10, CPT, amounts, provider NPI, dates.

Phase 3: pass-through stub.
Phase 4: Claude vision on the claim form + Pydantic schema validation.
"""
from __future__ import annotations

from typing import Any

from app.services.ai.base import BaseAgent
from app.services.ai.state import AgentState, ClaimsOutput


class ClaimsAgent(BaseAgent):
    name = "claims"

    def process(self, state: AgentState) -> dict[str, Any]:
        output: ClaimsOutput = {
            "extracted_fields": {},
            "schema_valid": False,
            "validation_errors": ["stub"],
            "confidence": 0.0,
        }
        return {"claims": output}
