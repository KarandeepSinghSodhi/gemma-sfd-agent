"""
Deterministic Failure Taxonomy and Phase 2 Exit Code Classifier for SWE Benchmarks.
"""
from typing import Dict, Any, List

TAXONOMY_BUCKETS = {
    0: "PASS (Verification Succeeded)",
    1: "SEMANTIC_REGRESSION (Assertion or Logic Failure)",
    2: "COLLECTION_OR_IMPORT_ERROR (Missing Dependency / Sandbox Path Misconfiguration)",
    -1: "NO_PATCH_SUBMITTED (Budget Exceeded or Turn Timeout)",
    124: "VERIFICATION_TIMEOUT (Infinite Loop or Daemon Process in Test Runner)",
}

def classify_trace_exit_code(exit_code: int) -> str:
    """Return descriptive classification of a Phase 2 pytest exit code."""
    return TAXONOMY_BUCKETS.get(exit_code, f"UNKNOWN_ERROR (Exit Code {exit_code})")

def classify_failure_bucket(record: Dict[str, Any]) -> str:
    """
    Classify a benchmark run into one of four diagnostic failure categories:
      - 'resolved': Test passed (exit_code == 0 and resolved == True)
      - 'timeout_or_budget_no_patch': Agent generated empty or no patch before turn limit
      - 'patch_apply_failed': Git could not apply agent's patch to reference commit
      - 'test_verification_failed': Non-zero test runner return code
      - 'runtime_or_harness_error': General runtime error
    """
    if record.get("resolved") and int(record.get("test_exit_code", -1)) == 0:
        return "resolved"
    
    err = str(record.get("error") or "")
    patch_len = int(record.get("patch_chars", 0))
    exit_code = int(record.get("test_exit_code", -1))
    
    if patch_len == 0 and (exit_code in (-1, 124) or "timeout" in err.lower() or "budget" in err.lower()):
        return "timeout_or_budget_no_patch"
    if "failed to apply agent patch" in err.lower() or "patch does not apply" in err.lower():
        return "patch_apply_failed"
    if exit_code != 0:
        return "test_verification_failed"
    return "runtime_or_harness_error"
