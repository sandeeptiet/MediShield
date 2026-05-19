"""Claims Agent — extracts ICD-10, CPT, amounts, provider NPI, dates.

Input:  document image bytes (claim form or discharge summary)
Output: {extracted_fields, schema_valid, validation_errors}
Phase 4 implements this.
"""
