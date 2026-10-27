"""
Unit tests for atif_gemma diagnostic package:
- Deterministic exit code taxonomy classifier
- Failure bucket assignment
- Trace parsing and audit aggregation
- Actionable remediation playbook
"""

from pathlib import Path
import pytest
from atif_gemma.taxonomy import classify_trace_exit_code, classify_failure_bucket
from atif_gemma.remediation import get_remediation_playbook
from atif_gemma.audit import parse_trace_file, audit_corpus

TRACES_DIR = Path(__file__).resolve().parent.parent / "dataset_resource" / "traces"


def test_classify_trace_exit_code():
    assert "PASS" in classify_trace_exit_code(0)
    assert "SEMANTIC_REGRESSION" in classify_trace_exit_code(1)
    assert "COLLECTION_OR_IMPORT_ERROR" in classify_trace_exit_code(2)
    assert "NO_PATCH_SUBMITTED" in classify_trace_exit_code(-1)
    assert "VERIFICATION_TIMEOUT" in classify_trace_exit_code(124)
    assert "UNKNOWN_ERROR" in classify_trace_exit_code(999)


def test_classify_failure_bucket():
    # 1. Resolved
    assert classify_failure_bucket({"resolved": True, "test_exit_code": 0}) == "resolved"
    
    # 2. Timeout/budget no patch
    assert classify_failure_bucket({"resolved": False, "test_exit_code": -1, "patch_chars": 0, "error": "Budget exceeded"}) == "timeout_or_budget_no_patch"
    
    # 3. Patch apply failed
    assert classify_failure_bucket({"resolved": False, "test_exit_code": 1, "patch_chars": 100, "error": "Failed to apply agent patch"}) == "patch_apply_failed"
    
    # 4. Test verification failed
    assert classify_failure_bucket({"resolved": False, "test_exit_code": 1, "patch_chars": 500}) == "test_verification_failed"
    assert classify_failure_bucket({"resolved": False, "test_exit_code": 2, "patch_chars": 500}) == "test_verification_failed"


def test_remediation_playbook():
    pb = get_remediation_playbook()
    assert isinstance(pb, dict)
    expected_keys = {
        "COLLECTION_OR_IMPORT_ERROR",
        "SYNTAX_OR_UNPARSED_PATCH",
        "CASCADING_LOCALIZATION_FAILURE",
        "TOKEN_BLAT_AND_CONTEXT_EXHAUSTION"
    }
    assert expected_keys.issubset(set(pb.keys()))
    for k, v in pb.items():
        assert "symptom" in v
        assert "architectural_fix" in v


def test_parse_single_trace():
    sample_trace = next(TRACES_DIR.glob("*.json"))
    res = parse_trace_file(sample_trace)
    assert isinstance(res, dict)
    assert res["llm_calls"] > 0
    assert res["cumulative_total_tokens"] > 0
    assert "tool_names" in res


def test_audit_corpus_reconciliation():
    summary = audit_corpus(TRACES_DIR)
    assert summary["num_traces"] == 112
    assert summary["total_llm_turns"] == 1518
    assert summary["total_tool_calls"] == 1328
    assert summary["total_tokens"] == 11706178
    assert summary["edit_file_errors"] == 100
