"""AI audit log model — append-only compliance trail.

Phase 2 + Phase 5 fill out the columns:
  - id, user_id, role
  - case_id (FK)
  - action (UPLOAD | DECIDE | OVERRIDE | ...)
  - agent_name (which agent emitted the row)
  - tool_name (which tool was called, if any)
  - status (SUCCESS | FAILED | BLOCKED)
  - details (JSON: structured context)
  - created_at
"""
