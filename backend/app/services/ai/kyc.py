"""KYC Agent — identity field extraction + tamper detection.

Sub-tasks:
  1. Claude Sonnet vision reads the ID image, extracts fields.
  2. OpenCV runs ELA (Error Level Analysis) to flag tampered regions.
Output: {kyc_passed, flags, confidence}
Phase 4 implements this.
"""
