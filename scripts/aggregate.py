"""
Aggregate real swegemma evaluation outputs (task_results.jsonl, paired_progress.jsonl,
and ATIF v1.7 traces/trace_<instance_id>.json) into summary tables, statistical tests,
stage-transition token measurements, and deterministic failure classifications.

Strictly no synthetic, estimated, or hand-edited numbers.
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, List, Optional, Tuple


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> Tuple[float, float]:
    """Compute 95% Wilson score confidence interval for binomial proportion k/n."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + (z * z) / n
    center = (p + (z * z) / (2.0 * n)) / denom
    half = (z * math.sqrt((p * (1.0 - p) + (z * z) / (4.0 * n)) / n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def mcnemar_exact_pvalue(b: int, c: int) -> float:
    """Exact two-sided McNemar test p-value for discordant pairs (b, c)."""
    n_disc = b + c
    if n_disc == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n_disc, i) for i in range(0, k + 1)) * (0.5 ** n_disc)
    return min(1.0, 2.0 * tail)


def paired_bootstrap_diff_ci(
    outcomes_a: List[int],
    outcomes_b: List[int],
    n_boot: int = 10000,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Paired bootstrap 95% CI for mean(outcomes_a) - mean(outcomes_b)."""
    if len(outcomes_a) != len(outcomes_b) or len(outcomes_a) == 0:
        return (0.0, 0.0, 0.0)
    n = len(outcomes_a)
    diffs = [a - b for a, b in zip(outcomes_a, outcomes_b)]
    obs_diff = sum(diffs) / n
    rng = random.Random(seed)
    boot_means = []
    for _ in range(n_boot):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    lo = boot_means[int(0.025 * n_boot)]
    hi = boot_means[int(0.975 * n_boot)]
    return (obs_diff, lo, hi)


def parse_atif_trace(trace_path: Path) -> Dict[str, Any]:
    """Extract per-call and per-stage token and tool metrics from an ATIF v1.7 trace file."""
    data = json.loads(trace_path.read_text(encoding="utf-8"))
    steps = data.get("steps", [])
    final_metrics = data.get("final_metrics", {})

    call_prompt_tokens: List[int] = []
    call_completion_tokens: List[int] = []
    call_total_tokens: List[int] = []
    stage_first_prompt: Dict[str, int] = {}
    stage_max_prompt: Dict[str, int] = defaultdict(int)
    stage_call_counts: Dict[str, int] = defaultdict(int)
    tool_names_used: List[str] = []

    for step in steps:
        extra = step.get("extra", {}) or {}
        author = extra.get("author", "unknown")
        metrics = step.get("metrics")
        if isinstance(metrics, dict) and "prompt_tokens" in metrics:
            pt = int(metrics.get("prompt_tokens", 0))
            ct = int(metrics.get("completion_tokens", 0))
            tt = int(metrics.get("total_tokens", pt + ct))
            call_prompt_tokens.append(pt)
            call_completion_tokens.append(ct)
            call_total_tokens.append(tt)
            if author not in stage_first_prompt:
                stage_first_prompt[author] = pt
            if pt > stage_max_prompt[author]:
                stage_max_prompt[author] = pt
            stage_call_counts[author] += 1

        for tc in step.get("tool_calls", []) or []:
            fn = tc.get("function_name")
            if fn:
                tool_names_used.append(fn)

    peak_prompt = max(call_prompt_tokens) if call_prompt_tokens else 0
    peak_total = max(call_total_tokens) if call_total_tokens else 0
    cum_prompt = int(final_metrics.get("total_prompt_tokens", sum(call_prompt_tokens)))
    cum_completion = int(final_metrics.get("total_completion_tokens", sum(call_completion_tokens)))
    cum_total = int(final_metrics.get("total_tokens", cum_prompt + cum_completion))

    return {
        "llm_calls": len(call_prompt_tokens),
        "peak_prompt_tokens": peak_prompt,
        "peak_total_tokens": peak_total,
        "cumulative_prompt_tokens": cum_prompt,
        "cumulative_completion_tokens": cum_completion,
        "cumulative_total_tokens": cum_total,
        "stage_first_prompt": dict(stage_first_prompt),
        "stage_max_prompt": dict(stage_max_prompt),
        "stage_call_counts": dict(stage_call_counts),
        "tool_names_used": tool_names_used,
        "context_overflow": peak_total >= 32768,
    }


def classify_failure(rec: Dict[str, Any]) -> str:
    """Deterministic rule-based failure taxonomy for unresolved tasks."""
    if rec.get("resolved"):
        return "resolved"
    err = str(rec.get("error") or "")
    if rec.get("context_overflow") or "maximum context length" in err.lower() or "context_length_exceeded" in err.lower():
        return "context_overflow"
    if int(rec.get("patch_chars", 0)) == 0:
        return "timeout_or_budget_no_patch"
    if "failed to apply agent patch" in err.lower():
        return "patch_apply_failed"
    if int(rec.get("test_exit_code", -1)) != 0:
        return "test_verification_failed"
    return "runtime_or_harness_error"


def load_all_runs(traces_root: Path) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Load task outcomes and ATIF trace metrics from traces_root.
    Expected structure under traces_root:
      - paired_progress.jsonl (or shard*/eval_results/paired_progress.jsonl)
      - <config>/task_results.jsonl
      - <config>/traces/trace_<instance_id>.json
    Returns:
      by_config[config_name][instance_id] = merged record dict
    """
    by_config: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)

    # 1. Scan paired_progress.jsonl files
    for prog_file in sorted(traces_root.rglob("paired_progress.jsonl")):
        base_dir = prog_file.parent
        for line in prog_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            cfg = row["config"]
            iid = row["instance_id"]
            trace_file = base_dir / cfg / "traces" / f"trace_{iid}.json"
            trace_metrics = parse_atif_trace(trace_file) if trace_file.is_file() else {
                "llm_calls": 0,
                "peak_prompt_tokens": 0,
                "peak_total_tokens": 0,
                "cumulative_prompt_tokens": 0,
                "cumulative_completion_tokens": 0,
                "cumulative_total_tokens": 0,
                "stage_first_prompt": {},
                "stage_max_prompt": {},
                "stage_call_counts": {},
                "tool_names_used": [],
                "context_overflow": False,
            }
            merged = {**row, **trace_metrics}
            merged["failure_bucket"] = classify_failure(merged)
            by_config[cfg][iid] = merged

    # 2. Also scan any standalone <config>/task_results.jsonl files not in paired_progress.jsonl
    for tr_file in sorted(traces_root.rglob("task_results.jsonl")):
        cfg_dir = tr_file.parent
        cfg = cfg_dir.name
        for line in tr_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            iid = row.get("instance_id") or row.get("task_id")
            if not iid or iid in by_config[cfg]:
                continue
            trace_file = cfg_dir / "traces" / f"trace_{iid}.json"
            trace_metrics = parse_atif_trace(trace_file) if trace_file.is_file() else {
                "llm_calls": 0,
                "peak_prompt_tokens": 0,
                "peak_total_tokens": 0,
                "cumulative_prompt_tokens": 0,
                "cumulative_completion_tokens": 0,
                "cumulative_total_tokens": 0,
                "stage_first_prompt": {},
                "stage_max_prompt": {},
                "stage_call_counts": {},
                "tool_names_used": [],
                "context_overflow": False,
            }
            patch_str = (row.get("agent_patch") or "").strip()
            rec = {
                "instance_id": iid,
                "repo": row.get("repo", iid.split("_")[0]),
                "config": cfg,
                "resolved": bool(row.get("resolved", False)),
                "test_exit_code": int(row.get("test_exit_code", -1)),
                "patch_chars": len(patch_str),
                "tool_calls": int(row.get("tool_calls", 0)),
                "duration_seconds": round(float(row.get("duration_seconds", 0.0)), 2),
                "error": row.get("error"),
                **trace_metrics,
            }
            rec["failure_bucket"] = classify_failure(rec)
            by_config[cfg][iid] = rec

    return by_config


def aggregate(traces_dir: str = "traces", results_dir: str = "results") -> Dict[str, Any]:
    os.makedirs(results_dir, exist_ok=True)
    traces_root = Path(traces_dir)
    by_config = load_all_runs(traces_root)

    summary_rows: List[Dict[str, Any]] = []
    failure_taxonomy: Dict[str, Dict[str, List[str]]] = {}
    per_repo_breakdown: Dict[str, Dict[str, Dict[str, Any]]] = {}
    stage_reset_stats: Dict[str, Any] = {}

    for cfg in sorted(by_config.keys()):
        records = [by_config[cfg][iid] for iid in sorted(by_config[cfg].keys())]
        n = len(records)
        if n == 0:
            continue
        k = sum(1 for r in records if r["resolved"])
        rate_pct = (k / n) * 100.0
        ci_lo, ci_hi = wilson_ci(k, n)

        peak_prompts = [r["peak_prompt_tokens"] for r in records]
        cum_prompts = [r["cumulative_prompt_tokens"] for r in records]
        cum_totals = [r["cumulative_total_tokens"] for r in records]
        llm_calls_list = [r["llm_calls"] for r in records]
        tool_calls_list = [r["tool_calls"] for r in records]
        durations = [r["duration_seconds"] for r in records]
        patches_submitted = sum(1 for r in records if r["patch_chars"] > 0)
        overflows = sum(1 for r in records if r["context_overflow"])

        summary_rows.append({
            "config": cfg,
            "model": "gemma-4-e4b-it-qat-w4a16-ct",
            "n_tasks": n,
            "resolved_k": k,
            "resolved_pct": round(rate_pct, 2),
            "wilson_95_lo": round(ci_lo * 100.0, 2),
            "wilson_95_hi": round(ci_hi * 100.0, 2),
            "patches_generated_k": patches_submitted,
            "patches_generated_pct": round((patches_submitted / n) * 100.0, 2),
            "mean_peak_prompt_tokens": round(mean(peak_prompts), 1),
            "median_peak_prompt_tokens": round(median(peak_prompts), 1),
            "max_peak_prompt_tokens": max(peak_prompts),
            "mean_cumulative_prompt_tokens": round(mean(cum_prompts), 1),
            "mean_cumulative_total_tokens": round(mean(cum_totals), 1),
            "mean_llm_calls": round(mean(llm_calls_list), 2),
            "mean_tool_calls": round(mean(tool_calls_list), 2),
            "mean_duration_sec": round(mean(durations), 2),
            "median_duration_sec": round(median(durations), 2),
            "overflow_k": overflows,
            "overflow_pct": round((overflows / n) * 100.0, 2),
        })

        # Failure taxonomy
        buckets: Dict[str, List[str]] = defaultdict(list)
        for r in records:
            if not r["resolved"]:
                buckets[r["failure_bucket"]].append(r["instance_id"])
        failure_taxonomy[cfg] = dict(buckets)

        # Per-repo breakdown
        repo_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in records:
            repo_groups[r["repo"]].append(r)
        per_repo_breakdown[cfg] = {
            repo: {
                "n": len(items),
                "resolved_k": sum(1 for x in items if x["resolved"]),
                "resolved_pct": round((sum(1 for x in items if x["resolved"]) / len(items)) * 100.0, 2),
                "mean_peak_prompt_tokens": round(mean(x["peak_prompt_tokens"] for x in items), 1),
            }
            for repo, items in sorted(repo_groups.items())
        }

        # Stage-boundary prompt token analysis for SFD
        if cfg == "sfd":
            triage_max = [r["stage_max_prompt"].get("TriageAgent", 0) for r in records if "TriageAgent" in r["stage_max_prompt"]]
            patch_first = [r["stage_first_prompt"].get("PatchAgent", 0) for r in records if "PatchAgent" in r["stage_first_prompt"]]
            patch_max = [r["stage_max_prompt"].get("PatchAgent", 0) for r in records if "PatchAgent" in r["stage_max_prompt"]]
            verifier_first = [r["stage_first_prompt"].get("VerifierAgent", 0) for r in records if "VerifierAgent" in r["stage_first_prompt"]]
            verifier_max = [r["stage_max_prompt"].get("VerifierAgent", 0) for r in records if "VerifierAgent" in r["stage_max_prompt"]]
            per_task_stage = {}
            for r in records:
                per_task_stage[r["instance_id"]] = {
                    "triage_entry": r["stage_first_prompt"].get("TriageAgent", 0),
                    "triage_peak": r["stage_max_prompt"].get("TriageAgent", 0),
                    "patch_entry": r["stage_first_prompt"].get("PatchAgent", 0),
                    "patch_peak": r["stage_max_prompt"].get("PatchAgent", 0),
                    "verifier_entry": r["stage_first_prompt"].get("VerifierAgent", 0),
                    "verifier_peak": r["stage_max_prompt"].get("VerifierAgent", 0),
                }
            stage_reset_stats.update({
                "n_triage_observed": len(triage_max),
                "mean_triage_peak_prompt_tokens": round(mean(triage_max), 1) if triage_max else 0.0,
                "max_triage_peak_prompt_tokens": max(triage_max) if triage_max else 0,
                "n_patch_observed": len(patch_first),
                "mean_patch_entry_prompt_tokens": round(mean(patch_first), 1) if patch_first else 0.0,
                "max_patch_entry_prompt_tokens": max(patch_first) if patch_first else 0,
                "mean_patch_peak_prompt_tokens": round(mean(patch_max), 1) if patch_max else 0.0,
                "max_patch_peak_prompt_tokens": max(patch_max) if patch_max else 0,
                "n_verifier_observed": len(verifier_first),
                "mean_verifier_entry_prompt_tokens": round(mean(verifier_first), 1) if verifier_first else 0.0,
                "max_verifier_entry_prompt_tokens": max(verifier_first) if verifier_first else 0,
                "mean_verifier_peak_prompt_tokens": round(mean(verifier_max), 1) if verifier_max else 0.0,
                "max_verifier_peak_prompt_tokens": max(verifier_max) if verifier_max else 0,
                "mean_triage_to_patch_reduction_pct": round((1.0 - (mean(patch_first) / mean(triage_max))) * 100.0, 1) if triage_max and patch_first else 0.0,
                "per_task": per_task_stage,
            })
        if cfg == "flat_starter":
            ca_tasks = [r["instance_id"] for r in records if "code_analyzer_agent" in r["tool_names_used"]]
            ca_calls = sum(r["tool_names_used"].count("code_analyzer_agent") for r in records)
            tot_tc = sum(len(r["tool_names_used"]) for r in records)
            stage_reset_stats["flat_starter_code_analyzer"] = {
                "tasks_invoking_code_analyzer_k": len(ca_tasks),
                "tasks_invoking_code_analyzer_ids": ca_tasks,
                "tasks_bypassing_code_analyzer_k": n - len(ca_tasks),
                "tasks_bypassing_code_analyzer_pct": round(((n - len(ca_tasks)) / n) * 100.0, 1),
                "code_analyzer_calls": ca_calls,
                "total_recorded_tool_calls": tot_tc,
                "code_analyzer_call_share_pct": round((ca_calls / tot_tc) * 100.0, 1) if tot_tc else 0.0,
            }

    # Paired comparisons across configurations
    paired_tests: List[Dict[str, Any]] = []
    configs = sorted(by_config.keys())
    for i in range(len(configs)):
        for j in range(i + 1, len(configs)):
            c1, c2 = configs[i], configs[j]
            common_ids = sorted(set(by_config[c1].keys()) & set(by_config[c2].keys()))
            if not common_ids:
                continue
            out1 = [1 if by_config[c1][iid]["resolved"] else 0 for iid in common_ids]
            out2 = [1 if by_config[c2][iid]["resolved"] else 0 for iid in common_ids]
            b = sum(1 for x, y in zip(out1, out2) if x == 1 and y == 0)
            c = sum(1 for x, y in zip(out1, out2) if x == 0 and y == 1)
            pval = mcnemar_exact_pvalue(b, c)
            diff_mean, diff_lo, diff_hi = paired_bootstrap_diff_ci(out1, out2)

            peak1 = [by_config[c1][iid]["peak_prompt_tokens"] for iid in common_ids]
            peak2 = [by_config[c2][iid]["peak_prompt_tokens"] for iid in common_ids]

            paired_tests.append({
                "config_a": c1,
                "config_b": c2,
                "n_paired": len(common_ids),
                "a_only_resolved_b": b,
                "b_only_resolved_c": c,
                "mcnemar_p_value": round(pval, 4),
                "diff_pct": round(diff_mean * 100.0, 2),
                "bootstrap_95_lo_pct": round(diff_lo * 100.0, 2),
                "bootstrap_95_hi_pct": round(diff_hi * 100.0, 2),
                "mean_peak_prompt_diff": round(mean(p1 - p2 for p1, p2 in zip(peak1, peak2)), 1),
            })

    # Write CSV summary
    csv_path = os.path.join(results_dir, "summary_table.csv")
    if summary_rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)

    # Per-task paired matrix
    all_task_ids = sorted({iid for cfg_map in by_config.values() for iid in cfg_map.keys()})
    task_matrix: List[Dict[str, Any]] = []
    for iid in all_task_ids:
        row_entry: Dict[str, Any] = {"instance_id": iid}
        for cfg in sorted(by_config.keys()):
            if iid in by_config[cfg]:
                r = by_config[cfg][iid]
                row_entry["repo"] = r["repo"]
                row_entry[f"{cfg}_resolved"] = r["resolved"]
                row_entry[f"{cfg}_patch_chars"] = r["patch_chars"]
                row_entry[f"{cfg}_peak_prompt_tokens"] = r["peak_prompt_tokens"]
                row_entry[f"{cfg}_cum_total_tokens"] = r["cumulative_total_tokens"]
                row_entry[f"{cfg}_tool_calls"] = r["tool_calls"]
                row_entry[f"{cfg}_duration_sec"] = r["duration_seconds"]
                row_entry[f"{cfg}_failure_bucket"] = r["failure_bucket"]
        task_matrix.append(row_entry)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary_rows": summary_rows,
        "paired_tests": paired_tests,
        "stage_reset_stats": stage_reset_stats,
        "per_repo_breakdown": per_repo_breakdown,
        "failure_taxonomy": failure_taxonomy,
        "task_matrix": task_matrix,
    }
    json_path = os.path.join(results_dir, "summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return payload


if __name__ == "__main__":
    res = aggregate()
    print(f"Aggregated {len(res['summary_rows'])} configurations across {len(res['task_matrix'])} unique tasks.")
