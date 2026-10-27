import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
summary_file = ROOT / "results" / "resource_summary.json"
typ_file = ROOT / "paper_resource.typ"
md_file = ROOT / "KAGGLE_WRITEUP_RESOURCE.md"

data = json.loads(summary_file.read_text(encoding="utf-8"))
typ_text = typ_file.read_text(encoding="utf-8")
md_text = md_file.read_text(encoding="utf-8")

print("=" * 70)
print("  ASSERTION AUDIT: RESOURCE PAPER CONSISTENCY CHECK (n=112 Traces)")
print("=" * 70)

# Check 1: Total traces (112)
assert data["total_traces"] == 112, f"Expected 112 traces, found {data['total_traces']}"
assert "112" in typ_text and "112" in md_text, "Trace count 112 missing"
print("[PASS] Total traces = 112 confirmed in paper & summary.")

# Check 2: Total tokens (11,706,178)
expected_tokens_str = f"{data['total_tokens']:,}"
assert expected_tokens_str == "11,706,178", f"Unexpected total tokens: {expected_tokens_str}"
assert expected_tokens_str in typ_text, f"Token string {expected_tokens_str} missing in typst"
assert expected_tokens_str in md_text, f"Token string {expected_tokens_str} missing in markdown"
print(f"[PASS] Total logged tokens = {expected_tokens_str} confirmed in paper & markdown.")

# Check 3: Total LLM calls (1,518)
assert data["total_llm_calls"] == 1518, f"Expected 1518 LLM calls, found {data['total_llm_calls']}"
assert "1,518" in typ_text and "1,518" in md_text, "LLM calls count missing"
print("[PASS] Total LLM calls = 1,518 confirmed.")

# Check 4: Total tool calls (1,328)
assert data["total_tool_calls"] == 1328, f"Expected 1328 tool calls, found {data['total_tool_calls']}"
assert "1,328" in typ_text and "1,328" in md_text, "Tool calls count missing"
print("[PASS] Total tool calls = 1,328 confirmed.")

# Check 5: Exit code counts
ec = data["exit_code_counts"]
assert ec["-1"] == 9, f"Expected 9 timeout/no-patch, got {ec['-1']}"
assert ec["0"] == 8, f"Expected 8 resolved, got {ec['0']}"
assert ec["1"] == 56, f"Expected 56 assertion failures, got {ec['1']}"
assert ec["2"] == 36, f"Expected 36 collection errors, got {ec['2']}"
assert ec["124"] == 3, f"Expected 3 verification timeouts, got {ec['124']}"
print(f"[PASS] Phase 2 exit codes confirmed: 9 no-patch (8.0%), 8 resolved (7.1%), 56 assertion (50.0%), 36 collection (32.1%), 3 timeout (2.7%).")

# Check 6: Cohorts
c = data["cohort_counts"]
assert c["Cohort 1 (Canonical)"] == 24, "Cohort 1 count mismatch"
assert c["Cohort 2 (Stratified Random)"] == 24, "Cohort 2 count mismatch"
assert c["Cohort 1 Rerun (Reproducibility)"] == 16, "Rerun count mismatch"
assert c["Cohort 3 (Stratified Disjoint)"] == 24, "Cohort 3 count mismatch"
assert c["Cohort 4 (Stratified Disjoint)"] == 24, "Cohort 4 count mismatch"
print("[PASS] Cohort partition counts confirmed: 24, 24, 16, 24, 24.")

# Check 7: Config counts
cfg = data["config_counts"]
assert cfg["flat_starter"] == 32, "flat_starter count mismatch"
assert cfg["flat_controlled"] == 32, "flat_controlled count mismatch"
assert cfg["sfd"] == 32, "sfd count mismatch"
assert cfg["flat_controlled_rerun"] == 8, "flat_controlled_rerun mismatch"
assert cfg["sfd_rerun"] == 8, "sfd_rerun mismatch"
print("[PASS] Configuration counts confirmed: 32 starter, 32 controlled, 32 sfd, 8 rerun-ctrl, 8 rerun-sfd.")

print("=" * 70)
print("  ALL 7 AUDIT CHECKS PASSED: 100% EMPIRICAL CONSISTENCY VERIFIED!")
print("=" * 70)
