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
    tool_events_detailed: List[Tuple[str, str]] = []
    prompt_bucket_events: List[Dict[str, Any]] = []
    seen_reads = set()
    last_pt = 0

    for step in steps:
        extra = step.get("extra", {}) or {}
        author = extra.get("author", "unknown")
        metrics = step.get("metrics")
        has_pt = isinstance(metrics, dict) and "prompt_tokens" in metrics
        if has_pt:
            pt = int(metrics.get("prompt_tokens", 0))
            ct = int(metrics.get("completion_tokens", 0))
            tt = int(metrics.get("total_tokens", pt + ct))
            last_pt = pt
            call_prompt_tokens.append(pt)
            call_completion_tokens.append(ct)
            call_total_tokens.append(tt)
            if author not in stage_first_prompt:
                stage_first_prompt[author] = pt
            if pt > stage_max_prompt[author]:
                stage_max_prompt[author] = pt
            stage_call_counts[author] += 1

        tcs = step.get("tool_calls", []) or []
        dup_r = 0
        read_c = 0
        edit_c = 0
        for tc in tcs:
            fn = tc.get("function_name")
            args = tc.get("arguments") or {}
            tc_author = (tc.get("extra") or {}).get("author") or author
            if fn:
                tool_names_used.append(fn)
                tool_events_detailed.append((tc_author, fn))
                if fn == "edit_file":
                    edit_c += 1
                if fn == "read_file":
                    read_c += 1
                    key = (args.get("filepath"), args.get("start_line"), args.get("end_line"))
                    if key in seen_reads:
                        dup_r += 1
                    seen_reads.add(key)

        obs = step.get("observation") or {}
        obs_c = obs.get("content", "") if isinstance(obs, dict) else ""
        tool_err = 0
        tool_err_non_budget = 0
        budget_err = 0
        edit_file_err = 0
        edit_budget_err = 0
        if obs_c:
            try:
                obs_json = json.loads(obs_c)
                is_err = obs_json.get("status") == "error"
                err_type = str(obs_json.get("error_type") or "")
            except Exception:
                is_err = False
                err_type = ""
            if is_err:
                tool_err = 1
                is_budget = err_type == "BudgetExceeded" or "budget exhausted" in obs_c.lower()
                if is_budget:
                    budget_err = 1
                else:
                    tool_err_non_budget = 1
                if (obs.get("extra") or {}).get("tool_name") == "edit_file":
                    if is_budget:
                        edit_budget_err = 1
                    else:
                        edit_file_err = 1

        if has_pt or tcs or obs_c:
            prompt_bucket_events.append({
                "prompt_tokens": last_pt,
                "author": author,
                "is_llm_call": 1 if has_pt else 0,
                "tool_calls": len(tcs),
                "tool_errors": tool_err,
                "tool_errors_non_budget": tool_err_non_budget,
                "budget_errors": budget_err,
                "edit_calls": edit_c,
                "edit_errors": edit_file_err + edit_budget_err,
                "edit_file_errors": edit_file_err,
                "edit_budget_errors": edit_budget_err,
                "read_calls": read_c,
                "dup_reads": dup_r,
            })

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
        "tool_events_detailed": tool_events_detailed,
        "prompt_bucket_events": prompt_bucket_events,
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
        if cfg.endswith("_rerun"):
            continue
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
            budget_tc_total = sum(int(r["tool_calls"]) for r in records)
            root_budget_calls = 0
            child_ca_calls = 0
            free_submit_calls = 0
            free_status_calls = 0
            for r in records:
                for tc_author, fn in r.get("tool_events_detailed", []):
                    if fn == "code_analyzer_agent":
                        continue
                    elif fn == "submit_patch":
                        free_submit_calls += 1
                    elif fn == "get_status":
                        free_status_calls += 1
                    elif tc_author == "code_analyzer_agent":
                        child_ca_calls += 1
                    else:
                        root_budget_calls += 1
            root_non_submit_decisions = root_budget_calls + ca_calls
            stage_reset_stats["flat_starter_code_analyzer"] = {
                "tasks_invoking_code_analyzer_k": len(ca_tasks),
                "tasks_invoking_code_analyzer_ids": ca_tasks,
                "tasks_bypassing_code_analyzer_k": n - len(ca_tasks),
                "tasks_bypassing_code_analyzer_pct": round(((n - len(ca_tasks)) / n) * 100.0, 1),
                "code_analyzer_calls": ca_calls,
                "budget_counted_tool_calls_total": budget_tc_total,
                "root_budget_counted_calls": root_budget_calls,
                "child_code_analyzer_calls": child_ca_calls,
                "free_submit_patch_calls": free_submit_calls,
                "free_get_status_calls": free_status_calls,
                "root_non_submit_decisions": root_non_submit_decisions,
                "code_analyzer_root_decision_share_pct": round((ca_calls / root_non_submit_decisions) * 100.0, 1) if root_non_submit_decisions else 0.0,
                "total_recorded_tool_calls": tot_tc,
                "code_analyzer_call_share_pct": round((ca_calls / tot_tc) * 100.0, 1) if tot_tc else 0.0,
            }

    # Prompt-length bucket analysis across primary configurations (testing Hypothesis 1)
    bucket_defs = [
        ("< 4,000", 0, 4000),
        ("4,000 - 7,999", 4000, 8000),
        ("8,000 - 11,999", 8000, 12000),
        (">= 12,000", 12000, 100000),
    ]

    def _init_bucket_map() -> Dict[str, Dict[str, Any]]:
        return {
            b[0]: {
                "bucket": b[0],
                "llm_calls": 0,
                "tool_calls": 0,
                "tool_errors": 0,
                "tool_errors_non_budget": 0,
                "budget_errors": 0,
                "edit_calls": 0,
                "edit_errors": 0,
                "edit_file_errors": 0,
                "edit_budget_errors": 0,
                "read_calls": 0,
                "dup_reads": 0,
            }
            for b in bucket_defs
        }

    def _finalize_bucket_list(bmap: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for b_label, _, _ in bucket_defs:
            bm = bmap[b_label]
            tc = bm["tool_calls"]
            ec = bm["edit_calls"]
            rc = bm["read_calls"]
            out.append({
                **bm,
                "tool_error_pct": round((bm["tool_errors"] / tc) * 100.0, 1) if tc else 0.0,
                "tool_error_non_budget_pct": round((bm["tool_errors_non_budget"] / tc) * 100.0, 1) if tc else 0.0,
                "edit_error_pct": round((bm["edit_errors"] / ec) * 100.0, 1) if ec else 0.0,
                "edit_file_error_pct": round((bm["edit_file_errors"] / ec) * 100.0, 1) if ec else 0.0,
                "edit_budget_error_pct": round((bm["edit_budget_errors"] / ec) * 100.0, 1) if ec else 0.0,
                "dup_read_pct": round((bm["dup_reads"] / rc) * 100.0, 1) if rc else 0.0,
            })
        return out

    bucket_map = _init_bucket_map()
    by_cfg_bucket_map = {c: _init_bucket_map() for c in ("flat_starter", "flat_controlled", "sfd")}
    primary_configs = [c for c in ("flat_starter", "flat_controlled", "sfd") if c in by_config]
    for cfg in primary_configs:
        for r in by_config[cfg].values():
            for ev in r.get("prompt_bucket_events", []):
                pt = int(ev.get("prompt_tokens", 0))
                if pt <= 0:
                    continue
                bname = next(b[0] for b in bucket_defs if b[1] <= pt < b[2])
                for target_bm in (bucket_map[bname], by_cfg_bucket_map[cfg][bname]):
                    target_bm["llm_calls"] += int(ev.get("is_llm_call", 0))
                    target_bm["tool_calls"] += int(ev.get("tool_calls", 0))
                    target_bm["tool_errors"] += int(ev.get("tool_errors", 0))
                    target_bm["tool_errors_non_budget"] += int(ev.get("tool_errors_non_budget", 0))
                    target_bm["budget_errors"] += int(ev.get("budget_errors", 0))
                    target_bm["edit_calls"] += int(ev.get("edit_calls", 0))
                    target_bm["edit_errors"] += int(ev.get("edit_errors", 0))
                    target_bm["edit_file_errors"] += int(ev.get("edit_file_errors", 0))
                    target_bm["edit_budget_errors"] += int(ev.get("edit_budget_errors", 0))
                    target_bm["read_calls"] += int(ev.get("read_calls", 0))
                    target_bm["dup_reads"] += int(ev.get("dup_reads", 0))

    prompt_length_buckets = _finalize_bucket_list(bucket_map)
    prompt_length_buckets_by_config = {
        cfg: _finalize_bucket_list(by_cfg_bucket_map[cfg]) for cfg in primary_configs
    }

    # Rerun reproducibility analysis (if rerun configs are present)
    rerun_reproducibility: Dict[str, Any] = {}
    for base_cfg in ("flat_controlled", "sfd"):
        rerun_cfg = f"{base_cfg}_rerun"
        if base_cfg in by_config and rerun_cfg in by_config:
            common = sorted(set(by_config[base_cfg].keys()) & set(by_config[rerun_cfg].keys()))
            if common:
                res_matches = sum(1 for iid in common if by_config[base_cfg][iid]["resolved"] == by_config[rerun_cfg][iid]["resolved"])
                patch_matches = sum(1 for iid in common if (by_config[base_cfg][iid]["patch_chars"] > 0) == (by_config[rerun_cfg][iid]["patch_chars"] > 0))
                exact_peak_matches = sum(1 for iid in common if by_config[base_cfg][iid]["peak_prompt_tokens"] == by_config[rerun_cfg][iid]["peak_prompt_tokens"])
                peak_diffs = [abs(by_config[base_cfg][iid]["peak_prompt_tokens"] - by_config[rerun_cfg][iid]["peak_prompt_tokens"]) for iid in common]
                rerun_reproducibility[base_cfg] = {
                    "n_tasks": len(common),
                    "resolved_agreement_k": res_matches,
                    "resolved_agreement_pct": round((res_matches / len(common)) * 100.0, 1),
                    "patch_presence_agreement_k": patch_matches,
                    "patch_presence_agreement_pct": round((patch_matches / len(common)) * 100.0, 1),
                    "exact_peak_prompt_match_k": exact_peak_matches,
                    "mean_abs_peak_prompt_diff": round(mean(peak_diffs), 1),
                    "max_abs_peak_prompt_diff": max(peak_diffs),
                }

    # Cohort breakdown (Cohort 1 canonical-order vs Cohort 2 seeded-random stratified)
    cohort1_ids = {
        "fastapi_15661", "fastapi_15588", "fastapi_15589",
        "requests_7505", "requests_7502",
        "rich_4070", "rich_4077",
        "httpx_3672",
    }
    cohort_breakdown: Dict[str, Any] = {}
    for cfg in primary_configs:
        c1_recs = [r for iid, r in by_config[cfg].items() if iid in cohort1_ids]
        c2_recs = [r for iid, r in by_config[cfg].items() if iid not in cohort1_ids]
        cohort_breakdown[cfg] = {
            "cohort1_canonical": {
                "n": len(c1_recs),
                "resolved_k": sum(1 for r in c1_recs if r["resolved"]),
                "resolved_pct": round((sum(1 for r in c1_recs if r["resolved"]) / len(c1_recs)) * 100.0, 1) if c1_recs else 0.0,
                "mean_peak_prompt_tokens": round(mean(r["peak_prompt_tokens"] for r in c1_recs), 1) if c1_recs else 0.0,
            },
            "cohort2_seeded_random": {
                "n": len(c2_recs),
                "resolved_k": sum(1 for r in c2_recs if r["resolved"]),
                "resolved_pct": round((sum(1 for r in c2_recs if r["resolved"]) / len(c2_recs)) * 100.0, 1) if c2_recs else 0.0,
                "mean_peak_prompt_tokens": round(mean(r["peak_prompt_tokens"] for r in c2_recs), 1) if c2_recs else 0.0,
            },
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
            pk_diff_mean, pk_diff_lo, pk_diff_hi = paired_bootstrap_diff_ci(peak1, peak2)
            a_lower_k = sum(1 for p1, p2 in zip(peak1, peak2) if p1 < p2)
            b_lower_k = sum(1 for p1, p2 in zip(peak1, peak2) if p1 > p2)
            sign_pval = mcnemar_exact_pvalue(a_lower_k, b_lower_k)

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
                "mean_peak_prompt_diff": round(pk_diff_mean, 1),
                "peak_diff_bootstrap_95_lo": round(pk_diff_lo, 1),
                "peak_diff_bootstrap_95_hi": round(pk_diff_hi, 1),
                "a_lower_peak_k": a_lower_k,
                "b_lower_peak_k": b_lower_k,
                "peak_sign_test_p_value": round(sign_pval, 4),
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
        "prompt_length_buckets": prompt_length_buckets,
        "prompt_length_buckets_by_config": prompt_length_buckets_by_config,
        "rerun_reproducibility": rerun_reproducibility,
        "cohort_breakdown": cohort_breakdown,
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
