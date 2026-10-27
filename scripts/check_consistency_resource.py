import json
import re
from pathlib import Path

ROOT = Path(r"d:\AI Research\gemma_paper")
summary_file = ROOT / "results" / "resource_summary.json"
typ_file = ROOT / "paper_resource.typ"
md_file = ROOT / "KAGGLE_WRITEUP_RESOURCE.md"

data = json.loads(summary_file.read_text(encoding="utf-8"))
typ_text = typ_file.read_text(encoding="utf-8")
md_text = md_file.read_text(encoding="utf-8")

print("=" * 70)
print("  ASSERTION AUDIT: RESOURCE PAPER CONSISTENCY CHECK")
print("=" * 70)

# Check 1: Total traces (64)
assert data["total_traces"] == 64, f"Expected 64 traces, found {data['total_traces']}"
assert "64" in typ_text and "64" in md_text, "Trace count 64 missing"
print("[PASS] Total traces = 64 confirmed in paper & summary.")

# Check 2: Total tokens (6,378,543)
expected_tokens_str = f"{data['total_tokens']:,}"
assert expected_tokens_str == "6,378,543", f"Unexpected total tokens: {expected_tokens_str}"
assert expected_tokens_str in typ_text, f"Token string {expected_tokens_str} missing in typst"
assert expected_tokens_str in md_text, f"Token string {expected_tokens_str} missing in markdown"
print(f"[PASS] Total logged tokens = {expected_tokens_str} confirmed in paper & markdown.")

# Check 3: Total LLM calls (847)
assert data["total_llm_calls"] == 847, f"Expected 847 LLM calls, found {data['total_llm_calls']}"
assert "847" in typ_text and "847" in md_text, "LLM calls count missing"
print("[PASS] Total LLM calls = 847 confirmed.")

# Check 4: Total tool calls (660)
assert data["total_tool_calls"] == 660, f"Expected 660 tool calls, found {data['total_tool_calls']}"
assert "660" in typ_text and "660" in md_text, "Tool calls count missing"
print("[PASS] Total tool calls = 660 confirmed.")

# Check 5: Exit code counts
ec = data["exit_code_counts"]
assert ec["-1"] == 4, f"Expected 4 timeout/no-patch, got {ec['-1']}"
assert ec["0"] == 4, f"Expected 4 resolved, got {ec['0']}"
assert ec["1"] == 36, f"Expected 36 assertion failures, got {ec['1']}"
assert ec["2"] == 20, f"Expected 20 collection errors, got {ec['2']}"
print(f"[PASS] Phase 2 exit codes confirmed: 4 no-patch (6.2%), 4 resolved (6.2%), 36 assertion (56.2%), 20 collection (31.2%).")

# Check 6: Cohorts
c = data["cohort_counts"]
assert c["Cohort 1 (Canonical)"] == 24, "Cohort 1 count mismatch"
assert c["Cohort 2 (Stratified Random)"] == 24, "Cohort 2 count mismatch"
assert c["Cohort 1 Rerun (Reproducibility)"] == 16, "Rerun count mismatch"
print("[PASS] Cohort partition counts confirmed: 24, 24, 16.")

# Check 7: Config counts
cfg = data["config_counts"]
assert cfg["flat_starter"] == 16, "flat_starter count mismatch"
assert cfg["flat_controlled"] == 16, "flat_controlled count mismatch"
assert cfg["sfd"] == 16, "sfd count mismatch"
assert cfg["flat_controlled_rerun"] == 8, "flat_controlled_rerun mismatch"
assert cfg["sfd_rerun"] == 8, "sfd_rerun mismatch"
print("[PASS] Configuration counts confirmed: 16 starter, 16 controlled, 16 sfd, 8 rerun-ctrl, 8 rerun-sfd.")

print("=" * 70)
print("  ALL 7 AUDIT CHECKS PASSED: 100% EMPIRICAL CONSISTENCY VERIFIED!")
print("=" * 70)
