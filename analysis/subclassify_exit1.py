"""
subclassify_exit1.py: Deterministic Sub-Classification of all 56 Exit Code 1 Runs.
Compares the agent's edited source files against the author's ground-truth reference patch.

Classification Rules:
1. EMPTY_PATCH: Agent submitted empty or zero source modifications.
2. WRONG_FILE: Zero overlap between agent edited files and gold patch files (F_agent ∩ F_gold = ∅).
3. PARTIAL_MULTI_FILE: Gold patch requires editing multiple files (|F_gold| > 1), but agent edited only a strict subset.
4. RIGHT_FILE_WRONG_LOGIC: Agent edited the exact gold file(s), but the patch failed test assertions.
"""
import csv
import json
import re
from pathlib import Path
from collections import defaultdict
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TASKS_PATH = ROOT / "dataset_resource" / "tasks_reference.jsonl"
METADATA_PATH = ROOT / "dataset_resource" / "corpus_metadata.csv"
TRACES_DIR = ROOT / "dataset_resource" / "traces"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def extract_files_from_diff(diff_str: str) -> set:
    """Extract source file paths from a unified diff string, ignoring tests and scratch files."""
    files = set()
    for line in diff_str.splitlines():
        if line.startswith("--- a/") or line.startswith("+++ b/"):
            p = line[6:].strip().replace("/workspace/", "").lstrip("/")
            if p and p != "dev/null" and not p.startswith(("tests/", "test_", "tmp/", "repro")):
                files.add(p)
    return files

def get_agent_edited_files(trace_file: str) -> set:
    """Extract source files edited by agent from ATIF v1.7 JSON trace."""
    p = TRACES_DIR / trace_file
    if not p.is_file():
        return set()
    data = json.loads(p.read_text(encoding="utf-8"))
    files = set()
    for s in data.get("steps", []):
        for tc in s.get("tool_calls", []):
            fn = tc.get("function_name")
            args = tc.get("arguments", {})
            if fn in ("edit_file", "write_file"):
                fp = args.get("filepath") or args.get("file_path") or args.get("path") or ""
                fp_clean = fp.replace("/workspace/", "").lstrip("/")
                if fp_clean and not fp_clean.startswith(("tests/", "test_", "tmp/", "repro")):
                    files.add(fp_clean)
            elif fn == "submit_patch":
                patch_str = args.get("patch", "")
                diff_files = extract_files_from_diff(patch_str)
                files.update(diff_files)
    return files

def main():
    tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in TASKS_PATH.read_text(encoding="utf-8").splitlines() if l.strip()}
    df = pd.read_csv(METADATA_PATH)
    exit1_df = df[df["test_exit_code"] == 1]
    
    assert len(exit1_df) == 56, f"Expected 56 Exit Code 1 runs, found {len(exit1_df)}"
    
    classified = []
    mechanism_counts = defaultdict(int)
    task_breakdown = defaultdict(lambda: defaultdict(int))
    config_breakdown = defaultdict(lambda: defaultdict(int))
    
    for idx, row in exit1_df.iterrows():
        iid = row["instance_id"]
        cfg = row["config"]
        cohort = row["cohort"]
        t = tasks.get(iid, {})
        gold_diff = t.get("patch", "")
        gold_files = extract_files_from_diff(gold_diff)
        
        agent_files = get_agent_edited_files(row["dataset_trace_file"])
        
        # Classification logic
        if len(agent_files) == 0:
            mech = "EMPTY_OR_UNPARSED_PATCH"
            reason = "Agent submitted empty patch or only edited temporary scratch files"
        elif len(gold_files) > 0 and len(agent_files.intersection(gold_files)) == 0:
            mech = "WRONG_FILE_LOCALIZATION"
            reason = f"Agent edited {list(agent_files)}, but gold patch requires {list(gold_files)}"
        elif len(gold_files) > 1 and agent_files.issubset(gold_files) and len(agent_files) < len(gold_files):
            mech = "PARTIAL_MULTI_FILE_LOCALIZATION"
            reason = f"Bug spans {len(gold_files)} files ({list(gold_files)}), but agent only modified {len(agent_files)} file(s)"
        else:
            mech = "RIGHT_FILE_WRONG_LOGIC"
            reason = f"Agent localized correct file(s) ({list(agent_files.intersection(gold_files))}), but patch failed unit test assertions"
            
        classified.append({
            "cohort": cohort,
            "instance_id": iid,
            "repo": row.get("repo", ""),
            "config": cfg,
            "mechanism": mech,
            "agent_files": ";".join(sorted(agent_files)),
            "gold_files": ";".join(sorted(gold_files)),
            "reason": reason
        })
        
        mechanism_counts[mech] += 1
        task_breakdown[iid][mech] += 1
        config_breakdown[cfg][mech] += 1
        
    print("=" * 70)
    print("  SUB-CLASSIFICATION REPORT: 56 EXIT CODE 1 RUNS")
    print("=" * 70)
    for m, c in sorted(mechanism_counts.items(), key=lambda x: -x[1]):
        print(f"  {m:35s}: {c:2d} ({c/len(exit1_df)*100:.1f}%)")
        
    print("\nTask-level Breakdown:")
    for tid in sorted(task_breakdown.keys()):
        print(f"  {tid:16s}: {dict(task_breakdown[tid])}")
        
    print("\nConfig-level Breakdown:")
    for cfg in sorted(config_breakdown.keys()):
        print(f"  {cfg:24s}: {dict(config_breakdown[cfg])}")
        
    out_json = {
        "total_exit1_runs": len(classified),
        "mechanism_counts": dict(mechanism_counts),
        "task_breakdown": {k: dict(v) for k, v in task_breakdown.items()},
        "config_breakdown": {k: dict(v) for k, v in config_breakdown.items()},
        "classified_runs": classified
    }
    (RESULTS_DIR / "exit1_breakdown.json").write_text(json.dumps(out_json, indent=2), encoding="utf-8")
    
    with open(RESULTS_DIR / "exit1_breakdown.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(classified[0].keys()))
        w.writeheader()
        w.writerows(classified)
        
    print(f"\n[PASS] All 56 Exit Code 1 runs classified deterministically.")
    print(f"Saved to {RESULTS_DIR / 'exit1_breakdown.json'} and {RESULTS_DIR / 'exit1_breakdown.csv'}")

if __name__ == "__main__":
    main()
