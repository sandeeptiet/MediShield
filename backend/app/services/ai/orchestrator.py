"""Orchestrator — LangGraph state machine for the claims-triage pipeline.

State flow:
  RECEIVED → CLASSIFIED → [parallel: KYC + CLAIMS + POLICY_RAG] → FRAUD → AGGREGATED → DECIDED

Aggregation rules:
  APPROVE   : KYC pass + claim valid + covered + fraud < 0.3
  REJECT    : KYC fail OR not covered OR schema invalid
  ESCALATE  : fraud >= 0.3 OR any agent confidence < 0.6

Phase 3 sets up the LangGraph state schema; Phase 4 wires nodes in.
"""
