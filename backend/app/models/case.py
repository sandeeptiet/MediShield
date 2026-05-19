"""Case model — one row per submitted document.

Phase 2 + Phase 5 fill out the columns:
  - case_id (UUID)
  - uploaded_by (FK to users)
  - document_path (S3 / local)
  - document_type (classifier output)
  - status (RECEIVED | CLASSIFIED | PROCESSING | DECIDED | FAILED)
  - decision (APPROVE | REJECT | ESCALATE | null)
  - confidence (float)
  - agent_outputs (JSON: per-agent structured results)
  - justification (text)
  - created_at, updated_at
"""
