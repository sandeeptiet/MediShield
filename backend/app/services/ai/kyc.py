"""KYC Agent — identity field extraction + tamper detection.

Phase 3: pass-through stub returning kyc_passed=False.
Phase 4: Claude vision on the ID image + OpenCV ELA for tampering.
"""
from __future__ import annotations

from typing import Any

from app.services.ai.base import BaseAgent
from app.services.ai.state import AgentState, KYCOutput


class KYCAgent(BaseAgent):
    name = "kyc"

    def process(self, state: AgentState) -> dict[str, Any]:
        output: KYCOutput = {
            "kyc_passed": False,
            "flags": ["stub"],
            "extracted_fields": {},
            "tamper_score": 0.0,
            "confidence": 0.0,
        }
        return {"kyc": output}
