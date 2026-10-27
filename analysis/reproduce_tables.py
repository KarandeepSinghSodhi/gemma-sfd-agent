"""
reproduce_tables.py: Deterministic extraction of Tables 1, 2, and 3 from raw ATIF v1.7 trace files.
Never reads from intermediate summaries or simulated outputs.
Outputs CSVs to results/ and verifies consistency.
"""
import csv
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
TRACES_DIR = ROOT / "traces"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Explicit mappings of progress files to cohorts
COHORT_MAPPINGS = [
    ("Cohort 1 (Canonical Paired)", TRACES_DIR / "eval_results" / "paired_progress.jsonl", TRACES_DIR / "eval_results"),
    ("Cohort 2 (Stratified Random)", TRACES_DIR / "shard2_results" / "eval_results" / "paired_progress.jsonl", TRACES_DIR / "shard2_results" / "eval_results"),
    ("Cohort 1 Rerun (Reproducibility)", TRACES_DIR / "rerun_results" / "eval_results" / "paired_progress.jsonl", TRACES_DIR / "rerun_results" / "eval_results"),
    ("Cohort 3 (Stratified Disjoint)", TRACES_DIR / "shard3_results" / "eval_results" / "paired_progress.jsonl", TRACES_DIR / "shard3_results" / "eval_results"),
    ("Cohort 4 (Stratified Disjoint)", TRACES_DIR / "shard4_results" / "eval_results" / "paired_progress.jsonl", TRACES_DIR / "shard4_results" / "eval_results"),
]

def parse_trace(trace_file: Path) -> Dict[str, Any]:
    """Parse raw ATIF v1.7 JSON trace."""
    data = json.loads(trace_file.read_text(encoding="utf-8"))
    steps = data.get("steps", [])
    
    prompt_tokens: List[int] = []
    completion_tokens: List[int] = []
    tool_names: List[str] = []
    code_analyzer_calls = 0
    edit_file_errors = 0
    
    for s in steps:
        m = s.get("metrics")
        if isinstance(m, dict) and "prompt_tokens" in m:
            pt = int(m.get("prompt_tokens", 0))
            ct = int(m.get("completion_tokens", 0))
            prompt_tokens.append(pt)
            completion_tokens.append(ct)
            
        tcs = s.get("tool_calls", []) or []
        for tc in tcs:
            fn = tc.get("function_name")
            if fn:
                tool_names.append(fn)
                if fn == "code_analyzer_agent":
                    code_analyzer_calls += 1
                    
        obs = s.get("observation") or {}
        obs_c = obs.get("content", "") if isinstance(obs, dict) else ""
        if isinstance(obs_c, str) and ("FileEditError" in obs_c or "could not find old_string" in obs_c.lower()):
            edit_file_errors += 1

    peak_prompt = max(prompt_tokens) if prompt_tokens else 0
    cum_prompt = sum(prompt_tokens)
    cum_comp = sum(completion_tokens)
    
    return {
        "llm_calls": len(prompt_tokens),
        "tool_calls": len(tool_names),
        "peak_prompt": peak_prompt,
        "cum_prompt": cum_prompt,
        "cum_completion": cum_comp,
        "cum_total": cum_prompt + cum_comp,
        "tool_names": tool_names,
        "code_analyzer_calls": code_analyzer_calls,
        "edit_file_errors": edit_file_errors,
    }

def main():
    records = []
    
    for cohort_name, prog_path, base_dir in COHORT_MAPPINGS:
        assert prog_path.exists(), f"Progress file missing: {prog_path}"
        lines = [json.loads(line) for line in prog_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        
        for row in lines:
            cfg = row["config"]
            iid = row["instance_id"]
            trace_path = base_dir / cfg / "traces" / f"trace_{iid}.json"
            assert trace_path.exists(), f"Trace file missing: {trace_path}"
            
            trace_metrics = parse_trace(trace_path)
            
            resolved = bool(row.get("resolved", False))
            exit_code = row.get("test_exit_code")
            if exit_code is None:
                exit_code = -1
                
            rec = {
                "cohort": cohort_name,
                "instance_id": iid,
                "repo": row.get("repo", iid.split("_")[0]),
                "config": cfg,
                "resolved": resolved,
                "test_exit_code": int(exit_code),
                "duration_seconds": float(row.get("duration_seconds", 0.0)),
                "patch_chars": int(row.get("patch_chars", 0)),
                **trace_metrics
            }
            records.append(rec)
            
    assert len(records) == 112, f"Expected 112 records, found {len(records)}"
    
    # --- TABLE 1: Corpus Composition ---
    cohort_stats = defaultdict(lambda: {
        "traces": 0, "tasks": set(), "llm_calls": 0, "tool_calls": 0,
        "prompt_tokens": 0, "comp_tokens": 0, "total_tokens": 0
    })
    
    for r in records:
        cs = cohort_stats[r["cohort"]]
        cs["traces"] += 1
        cs["tasks"].add(r["instance_id"])
        cs["llm_calls"] += r["llm_calls"]
        cs["tool_calls"] += r["tool_calls"]
        cs["prompt_tokens"] += r["cum_prompt"]
        cs["comp_tokens"] += r["cum_completion"]
        cs["total_tokens"] += r["cum_total"]
        
    t1_rows = []
    total_traces = 0
    total_tasks_set = set()
    total_llm = 0
    total_tools = 0
    total_tokens = 0
    total_prompt = 0
    total_comp = 0
    
    for cname, _, _ in COHORT_MAPPINGS:
        cs = cohort_stats[cname]
        total_traces += cs["traces"]
        total_tasks_set.update(cs["tasks"])
        total_llm += cs["llm_calls"]
        total_tools += cs["tool_calls"]
        total_tokens += cs["total_tokens"]
        total_prompt += cs["prompt_tokens"]
        total_comp += cs["comp_tokens"]
        t1_rows.append({
            "Corpus Partition": cname,
            "Traces": cs["traces"],
            "Tasks": len(cs["tasks"]),
            "LLM Calls": cs["llm_calls"],
            "Tool Calls": cs["tool_calls"],
            "Total Tokens": cs["total_tokens"],
            "Prompt Tokens": cs["prompt_tokens"],
            "Completion Tokens": cs["comp_tokens"]
        })
        
    t1_summary = {
        "Corpus Partition": "Total ATIF-Gemma Corpus",
        "Traces": total_traces,
        "Tasks": len(total_tasks_set),
        "LLM Calls": total_llm,
        "Tool Calls": total_tools,
        "Total Tokens": total_tokens,
        "Prompt Tokens": total_prompt,
        "Completion Tokens": total_comp
    }
    
    with open(RESULTS_DIR / "table1_corpus.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(t1_rows[0].keys()))
        w.writeheader()
        w.writerows(t1_rows)
        w.writerow(t1_summary)
        
    # --- TABLE 2: Phase 2 Exit Code Taxonomy ---
    ec_map = {
        0: ("Resolved", "Patch passes all Phase 2 held-out unit tests with zero regressions."),
        1: ("Assertion Failure", "Patch syntactically valid and executes under pytest, but fails assertions due to wrong logic or incomplete multi-file edits."),
        2: ("Collection Error", "Pytest crashes during test collection prior to assertion evaluation (ModuleNotFoundError, SyntaxError, venv shadowing)."),
        -1: ("Budget / Timeout", "Agent exhausted 15 tool calls or 2.5 min wall time; 0 patch characters submitted."),
        124: ("Verification Timeout", "Verification harness timed out (120s limit) due to daemon process or infinite loop in test runner.")
    }
    
    ec_counts = defaultdict(int)
    for r in records:
        ec_counts[r["test_exit_code"]] += 1
        
    t2_rows = []
    for ec in [0, 1, 2, -1, 124]:
        count = ec_counts[ec]
        cat, mechanism = ec_map[ec]
        t2_rows.append({
            "Category": cat,
            "Exit Code": ec,
            "Count": count,
            "Percentage (%)": round(count / 112 * 100, 1),
            "Empirical Mechanism": mechanism
        })
        
    with open(RESULTS_DIR / "table2_taxonomy.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(t2_rows[0].keys()))
        w.writeheader()
        w.writerows(t2_rows)
        
    # --- TABLE 3: Configuration Comparison ---
    config_order = ["flat_starter", "flat_controlled", "sfd", "flat_controlled_rerun", "sfd_rerun"]
    cfg_stats = defaultdict(list)
    for r in records:
        cfg_stats[r["config"]].append(r)
        
    t3_rows = []
    for cfg in config_order:
        runs = cfg_stats[cfg]
        n = len(runs)
        res = sum(1 for r in runs if r["resolved"])
        mean_peak_pt = sum(r["peak_prompt"] for r in runs) / n
        mean_prompt = sum(r["cum_prompt"] for r in runs) / n
        mean_total = sum(r["cum_total"] for r in runs) / n
        mean_dur = sum(r["duration_seconds"] for r in runs) / n
        
        t3_rows.append({
            "Configuration": cfg,
            "Runs": n,
            "Resolved": f"{res}/{n} ({res/n*100:.1f}%)",
            "Resolved Count": res,
            "Mean Peak Pt": round(mean_peak_pt, 1),
            "Mean Prompt Tokens": round(mean_prompt, 1),
            "Mean Total Tokens": round(mean_total, 1),
            "Mean Duration (s)": round(mean_dur, 1)
        })
        
    with open(RESULTS_DIR / "table3_configs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(t3_rows[0].keys()))
        w.writeheader()
        w.writerows(t3_rows)
        
    # Output overall summary JSON
    summary_metrics = {
        "total_traces": total_traces,
        "total_unique_tasks": len(total_tasks_set),
        "total_llm_calls": total_llm,
        "total_tool_calls": total_tools,
        "total_tokens": total_tokens,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_comp,
        "exit_code_counts": dict(ec_counts),
        "table1": t1_rows,
        "table2": t2_rows,
        "table3": t3_rows
    }
    (RESULTS_DIR / "summary_metrics.json").write_text(json.dumps(summary_metrics, indent=2), encoding="utf-8")
    
    print("=" * 70)
    print("  reproduce_tables.py SUCCESSFUL")
    print("=" * 70)
    print(f"Total traces: {total_traces} | Tasks: {len(total_tasks_set)} | Tokens: {total_tokens:,}")
    print(f"Table 1, Table 2, and Table 3 written to {RESULTS_DIR}")

if __name__ == "__main__":
    main()
