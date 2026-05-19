"""Fraud Agent — IsolationForest anomaly score + Claude explanation.

Inputs: patient claim history (tabular), current claim features.
Outputs: {fraud_score, anomalies, risk_level: LOW|MEDIUM|HIGH, explanation}
Phase 4 implements this.
"""
