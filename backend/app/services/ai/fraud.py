"""Fraud Agent — IsolationForest anomaly score + Claude explanation.

For the capstone we don't have a real historical claim-history table to train
on. Instead we lazily fit an IsolationForest on a small synthetic "normal"
baseline at first use. The features are simple, intentional signals derived
from this case:

    1. claim_amount (USD)
    2. number of distinct CPT codes
    3. number of distinct ICD-10 codes
    4. days between service_date and today (recency)
    5. KYC tamper score (already computed by the KYC agent)
    6. KYC flag count

In production this baseline would come from real historical claims joined
to known-good outcomes; the agent code below would not change.
"""
from __future__ import annotations

from datetime import date, datetime
from functools import lru_cache
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest

from app.services.ai.base import BaseAgent
from app.services.ai.llm import complete_json
from app.services.ai.schemas import FraudExplanation
from app.services.ai.state import AgentState, FraudOutput, RiskLevel

# Score thresholds — fraud_score is 0..1, higher = more suspicious.
RISK_HIGH = 0.7
RISK_MEDIUM = 0.4

SYSTEM_PROMPT = """You are MediShield's Fraud Explanation Agent.

You receive a numeric fraud score (0..1) and a structured list of signals
computed from a single claim. Your job is to translate that into a short,
reviewer-friendly explanation.

Rules:
- Be specific: cite the signals that drove the score.
- Do not invent signals that aren't in the input.
- Tone: factual, no alarmism. Recommend escalation when warranted.
- Output must conform to FraudExplanation.
"""


# --- Baseline ----------------------------------------------------------

_NORMAL_BASELINE = np.array(
    [
        # [amount,   n_cpt, n_icd, days_old, tamper, kyc_flags]
        [   500.0,     1,     1,     5,      0.05,    0],
        [   850.0,     1,     2,     7,      0.07,    0],
        [  1200.0,     2,     2,    12,      0.04,    0],
        [  2400.0,     2,     2,     3,      0.06,    0],
        [   320.0,     1,     1,    14,      0.03,    0],
        [  4500.0,     3,     3,     8,      0.06,    0],
        [   720.0,     1,     1,     1,      0.08,    0],
        [  1850.0,     2,     2,    21,      0.05,    0],
        [  3100.0,     2,     3,     5,      0.04,    0],
        [   980.0,     1,     2,     9,      0.07,    0],
        [  6200.0,     3,     3,     2,      0.05,    0],
        [  1450.0,     2,     2,    11,      0.06,    0],
    ],
    dtype=float,
)


@lru_cache(maxsize=1)
def _get_model() -> IsolationForest:
    model = IsolationForest(
        contamination=0.1,
        random_state=42,
        n_estimators=100,
    )
    model.fit(_NORMAL_BASELINE)
    return model


# --- Feature build -----------------------------------------------------


def _service_days_old(service_date: str | None) -> int:
    if not service_date:
        return 30  # conservative default
    try:
        d = datetime.fromisoformat(service_date[:10]).date()
    except ValueError:
        return 30
    return max(0, (date.today() - d).days)


def _features(state: AgentState) -> tuple[np.ndarray, dict[str, Any]]:
    claims = (state.get("claims") or {}).get("extracted_fields") or {}
    kyc = state.get("kyc") or {}

    amount = float(claims.get("claim_amount") or 0.0)
    n_cpt = len({c for c in (claims.get("cpt_codes") or [])})
    n_icd = len({c for c in (claims.get("icd10_codes") or [])})
    days_old = _service_days_old(claims.get("service_date"))
    tamper = float(kyc.get("tamper_score") or 0.0)
    n_flags = len(kyc.get("flags") or [])

    vec = np.array([[amount, n_cpt, n_icd, days_old, tamper, n_flags]], dtype=float)
    summary = {
        "claim_amount": amount,
        "n_cpt_codes": n_cpt,
        "n_icd10_codes": n_icd,
        "service_days_old": days_old,
        "kyc_tamper_score": tamper,
        "kyc_flag_count": n_flags,
    }
    return vec, summary


def _risk_level(score: float) -> RiskLevel:
    if score >= RISK_HIGH:
        return "HIGH"
    if score >= RISK_MEDIUM:
        return "MEDIUM"
    return "LOW"


# --- Agent -------------------------------------------------------------


class FraudAgent(BaseAgent):
    name = "fraud"

    def process(self, state: AgentState) -> dict[str, Any]:
        vec, signals = _features(state)
        model = _get_model()

        # IsolationForest.score_samples: higher = more normal. Map to [0..1] where
        # higher = more anomalous.
        raw = float(model.score_samples(vec)[0])  # roughly in [-0.5, 0.5]
        normalized = max(0.0, min(1.0, 0.5 - raw))
        risk = _risk_level(normalized)

        # Claude explains. If Claude is unreachable, we still return a usable result.
        try:
            explanation: FraudExplanation = complete_json(
                system=SYSTEM_PROMPT,
                user=(
                    f"Fraud score: {normalized:.2f} (risk_level={risk}). "
                    f"Signals (one claim): {signals}. "
                    "Emit a FraudExplanation."
                ),
                schema=FraudExplanation,
                max_tokens=512,
            )
            anomalies = explanation.anomalies
            explanation_text = explanation.explanation
            confidence = explanation.confidence
        except Exception as exc:
            self.logger.warning("fraud.explanation_failed", error=str(exc))
            anomalies = []
            explanation_text = (
                f"IsolationForest fraud_score={normalized:.2f} risk_level={risk}. "
                "Narrative explanation unavailable."
            )
            confidence = 0.5

        output: FraudOutput = {
            "fraud_score": round(normalized, 4),
            "risk_level": risk,
            "anomalies": anomalies,
            "explanation": explanation_text,
            "confidence": confidence,
        }
        self.logger.info(
            "fraud.result",
            fraud_score=output["fraud_score"],
            risk_level=risk,
            n_anomalies=len(anomalies),
        )
        return {"fraud": output}
