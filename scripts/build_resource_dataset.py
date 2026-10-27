import json
import csv
import shutil
from pathlib import Path
from collections import defaultdict
import sys

ROOT = Path(r"d:\AI Research\gemma_paper")
sys.path.insert(0, str(ROOT / "scripts"))
from aggregate import parse_atif_trace, classify_failure

TRACES_DIR = ROOT / "traces"
RESULTS_DIR = ROOT / "results"
DATASET_DIR = ROOT / "dataset_resource"
DATASET_DIR.mkdir(parents=True, exist_ok=True)
(DATASET_DIR / "traces").mkdir(parents=True, exist_ok=True)

# 1. Scan paired_progress.jsonl files
cohort_mapping = [
    ("Cohort 1 (Canonical)", TRACES_DIR / "eval_results" / "paired_progress.jsonl", TRACES_DIR / "eval_results"),
    ("Cohort 2 (Stratified Random)", TRACES_DIR / "shard2_results" / "eval_results" / "paired_progress.jsonl", TRACES_DIR / "shard2_results" / "eval_results"),
    ("Cohort 1 Rerun (Reproducibility)", TRACES_DIR / "rerun_results" / "eval_results" / "paired_progress.jsonl", TRACES_DIR / "rerun_results" / "eval_results"),
]

records = []
total_prompt_tokens = 0
total_completion_tokens = 0
total_tokens = 0
total_llm_calls = 0
total_tool_calls = 0
total_duration_sec = 0.0

exit_code_counts = defaultdict(int)
failure_bucket_counts = defaultdict(int)
config_counts = defaultdict(int)
repo_counts = defaultdict(int)
cohort_counts = defaultdict(int)
tool_error_counts = defaultdict(int)

for cohort_name, prog_file, base_dir in cohort_mapping:
    assert prog_file.exists(), f"Missing progress file: {prog_file}"
    for line in prog_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        cfg = row["config"]
        iid = row["instance_id"]
        trace_file = base_dir / cfg / "traces" / f"trace_{iid}.json"
        
        if trace_file.is_file():
            metrics = parse_atif_trace(trace_file)
            # Copy trace file into dataset_resource/traces with unique prefix
            clean_cohort = cohort_name.split()[0].lower() + ("_rerun" if "rerun" in cohort_name.lower() else "")
            dest_trace_name = f"{clean_cohort}_{cfg}_{iid}.json"
            shutil.copy2(trace_file, DATASET_DIR / "traces" / dest_trace_name)
        else:
            raise FileNotFoundError(f"Trace file not found: {trace_file}")

        merged = {**row, **metrics}
        merged["failure_bucket"] = classify_failure(merged)

        # Aggregate tool errors across prompt bucket events
        for pbe in metrics.get("prompt_bucket_events", []):
            if pbe.get("edit_file_errors", 0) > 0:
                tool_error_counts["FileEditError"] += pbe["edit_file_errors"]
            if pbe.get("budget_errors", 0) > 0:
                tool_error_counts["BudgetExceeded"] += pbe["budget_errors"]

        resolved = bool(row.get("resolved", False))
        exit_code = row.get("test_exit_code")
        if exit_code is None:
            exit_code = -1
        exit_code_counts[exit_code] += 1
        failure_bucket_counts[merged["failure_bucket"]] += 1
        config_counts[cfg] += 1
        cohort_counts[cohort_name] += 1
        repo_prefix = iid.split("_")[0]
        repo_counts[repo_prefix] += 1

        pt = metrics.get("cumulative_prompt_tokens", 0)
        ct = metrics.get("cumulative_completion_tokens", 0)
        tt = metrics.get("cumulative_total_tokens", pt + ct)
        llm_c = metrics.get("llm_calls", 0)
        tool_c = row.get("tool_calls", 0)
        dur = float(row.get("duration_seconds", 0.0))

        total_prompt_tokens += pt
        total_completion_tokens += ct
        total_tokens += tt
        total_llm_calls += llm_c
        total_tool_calls += tool_c
        total_duration_sec += dur

        records.append({
            "cohort": cohort_name,
            "instance_id": iid,
            "repo": row.get("repo", repo_prefix),
            "config": cfg,
            "resolved": resolved,
            "test_exit_code": exit_code,
            "failure_bucket": merged["failure_bucket"],
            "patch_chars": row.get("patch_chars", 0),
            "tool_calls": tool_c,
            "llm_calls": llm_c,
            "duration_seconds": round(dur, 2),
            "peak_prompt_tokens": metrics.get("peak_prompt_tokens", 0),
            "cumulative_prompt_tokens": pt,
            "cumulative_completion_tokens": ct,
            "cumulative_total_tokens": tt,
            "dataset_trace_file": dest_trace_name
        })

assert len(records) == 64, f"Expected 64 records, got {len(records)}"

print("=" * 70)
print("  ATIF-GEMMA DIAGNOSTIC CORPUS AUDIT COMPLETE (n=64 Traces)")
print("=" * 70)
print(f"Total Traces: {len(records)}")
print(f"Cohort Breakdown: {dict(cohort_counts)}")
print(f"Configuration Breakdown: {dict(config_counts)}")
print(f"Repository Breakdown: {dict(repo_counts)}")
print(f"Resolved Count: {sum(1 for r in records if r['resolved'])}/64 ({sum(1 for r in records if r['resolved'])/64*100:.1f}%)")
print(f"Phase 2 Exit Code Distribution:")
for ec, cnt in sorted(exit_code_counts.items()):
    print(f"  exit_code {ec:2d}: {cnt:2d} ({cnt/64*100:.1f}%)")
print(f"Failure Taxonomy Breakdown: {dict(failure_bucket_counts)}")
print(f"Total LLM Turns: {total_llm_calls:,}")
print(f"Total Tool Invocations: {total_tool_calls:,}")
print(f"Total Tokens Logged: {total_tokens:,} (Prompt: {total_prompt_tokens:,}, Completion: {total_completion_tokens:,})")
print(f"Total GPU Wall-Clock Time: {total_duration_sec:.1f}s ({total_duration_sec/3600:.2f} hours)")
print(f"Tool Error Counts in Traces: {dict(tool_error_counts)}")
print("=" * 70)

# Export results/resource_summary.json
resource_summary = {
    "corpus_name": "ATIF-Gemma",
    "version": "1.7.0",
    "total_traces": len(records),
    "total_llm_calls": total_llm_calls,
    "total_tool_calls": total_tool_calls,
    "total_tokens": total_tokens,
    "total_prompt_tokens": total_prompt_tokens,
    "total_completion_tokens": total_completion_tokens,
    "total_duration_seconds": round(total_duration_sec, 2),
    "total_gpu_hours": round(total_duration_sec / 3600.0, 3),
    "resolved_count": sum(1 for r in records if r["resolved"]),
    "exit_code_counts": dict(exit_code_counts),
    "failure_bucket_counts": dict(failure_bucket_counts),
    "cohort_counts": dict(cohort_counts),
    "config_counts": dict(config_counts),
    "repo_counts": dict(repo_counts),
    "tool_error_counts": dict(tool_error_counts),
    "records": records
}

(RESULTS_DIR / "resource_summary.json").write_text(json.dumps(resource_summary, indent=2), encoding="utf-8")
print(f"Saved resource summary to {RESULTS_DIR / 'resource_summary.json'}")

# Export dataset_resource/corpus_metadata.csv
csv_path = DATASET_DIR / "corpus_metadata.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)

print(f"Saved dataset metadata table to {csv_path}")
