"""Policy RAG Agent — agentic retrieval over policy PDFs.

Driven by CPT/ICD codes from the Claims agent (not raw user text).
Steps:
  1. Formulate retrieval queries from structured procedure codes.
  2. Embed → search Qdrant → top-K.
  3. Rerank with BGE cross-encoder.
  4. Generate grounded coverage decision with Claude Sonnet.
  5. Self-check: was an exclusion clause retrieved?

Output: {covered, coverage_percentage, policy_clause, exclusions}
Phase 4 implements this.
"""
