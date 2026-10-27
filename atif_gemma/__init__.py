"""
ATIF-Gemma: Diagnostic Toolkit for Small Open-Weight Software Engineering Agents.
Provides automated ATIF v1.7 trace parsing, 4-tier Phase 2 failure classification,
token trajectory auditing, and architectural remediation suggestions.
"""
__version__ = "1.7.0"
__author__ = "Karandeep Singh Sodhi"

from .taxonomy import classify_trace_exit_code, classify_failure_bucket, TAXONOMY_BUCKETS
from .audit import parse_trace_file, audit_corpus
from .remediation import get_remediation_playbook

__all__ = [
    "classify_trace_exit_code",
    "classify_failure_bucket",
    "TAXONOMY_BUCKETS",
    "parse_trace_file",
    "audit_corpus",
    "get_remediation_playbook",
]
