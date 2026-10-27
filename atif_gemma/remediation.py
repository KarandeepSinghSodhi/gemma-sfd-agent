"""
Actionable Remediation Playbook: Architectural and Prompt Engineering Solutions
for Known Small Model Failure Modes on SWE Benchmarks.
"""
from typing import Dict, Any, List

REMEDIATION_RULES = {
    "COLLECTION_OR_IMPORT_ERROR": {
        "symptom": "Pytest exits with returncode 2 during collection before any assertion runs (32.1% of failures).",
        "root_cause": (
            "1. Missing optional test dependencies (e.g. inline_snapshot, trio) in the offline evaluation sandbox.\n"
            "2. Global venv shadowing where system site-packages shadow /workspace source code."
        ),
        "remediation_code": (
            "# Rule: In verification command, enforce local path priority and skip collection if unavailable:\n"
            "PYTHONPATH=/workspace/src:/workspace pytest tests/test_target.py -k <test_name> -o addopts=''\n"
            "# Rule: Pre-check imports with python -c before running full pytest suites."
        ),
        "architectural_fix": "Add sandbox pre-flight isolation guard in Evaluator harness."
    },
    "SYNTAX_OR_UNPARSED_PATCH": {
        "symptom": "Model emits invalid python syntax or malformed diff resulting in immediate test failure (100 FileEditErrors).",
        "root_cause": "Small models (4B) hallucinate indentation or drop bracket closures when editing without context.",
        "remediation_code": (
            "# Rule: In VerifierAgent prompt, mandate pre-submission validation:\n"
            "python -m py_compile /workspace/path/to/modified_file.py\n"
            "# Only call submit_patch if py_compile returns 0."
        ),
        "architectural_fix": "Harness-level verification hook rejecting non-compiling patches before scoring."
    },
    "CASCADING_LOCALIZATION_FAILURE": {
        "symptom": "Stage 1 (Triage) identifies wrong file; downstream Stage 2 blind patching fails completely.",
        "root_cause": "Context isolation (include_contents: 'none') prevents Stage 2 from accessing original issue text.",
        "remediation_code": (
            "# Two-way verification loop:\n"
            "# PatchAgent inspects target_symbol against problem_description keywords.\n"
            "# If symbol does not appear in repo, trigger re-triage fallback."
        ),
        "architectural_fix": "Conditional Stage Fallback Transition in SequentialAgent pipeline."
    },
    "TOKEN_BLAT_AND_CONTEXT_EXHAUSTION": {
        "symptom": "Single-agent context explodes past 28,000 tokens with repeated redundant reads.",
        "root_cause": "Accumulation of full tool observation outputs across multi-turn deliberation.",
        "remediation_code": (
            "# Slicing policy in Google ADK:\n"
            "include_contents: 'none'\n"
            "output_key: 'localization_packet'\n"
            "# Resets prompt tokens from 10,900+ down to <1,500 at stage boundaries (-86%)."
        ),
        "architectural_fix": "State-Filtered Deliberation (SFD) stage-isolated context pruning."
    }
}

def get_remediation_playbook() -> Dict[str, Any]:
    """Return dictionary of diagnostic symptoms, root causes, and production fixes."""
    return REMEDIATION_RULES
