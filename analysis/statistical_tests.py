"""
statistical_tests.py: Rigorous inferential statistics, paired tests, and rerun determinism audit.
Computes:
1. Wilson score 95% confidence intervals for binomial resolution rates:
   - Primary 96 runs (overall & per-config)
   - Primary valid-environment 80 runs
   - Pooled 112 runs (overall & per-config)
   - Pooled valid-environment 92 runs
2. McNemar's exact two-sided test for paired resolution outcomes (n=32).
3. Wilcoxon signed-rank tests and 10,000-sample paired bootstrap 95% CIs for:
   - Cumulative prompt tokens
   - Peak prompt tokens (vs flat_controlled and flat_starter)
   - Cumulative total tokens
   - Execution duration
4. Rerun determinism analysis on Cohort 1 (original vs rerun across 8 tasks x 2 configs = 16 pairs)
   evaluating true edit sequence hashes, exit code agreement, flips, and token drift.
5. Task-level failure and resolution concentration audit across all 32 tasks.
Outputs:
- results/stats_report.json
- results/rerun_determinism.json
"""
import hashlib
import json
import math
import random
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / "dataset_resource" / "corpus_metadata.csv"
TRACES_DIR = ROOT / "dataset_resource" / "traces"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Compute Wilson score confidence interval for binomial proportion k/n."""
    if n == 0:
        return (0.0, 0.0)
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n)) / denom
    return (max(0.0, round(float(center - half), 4)), min(1.0, round(float(center + half), 4)))

def task_cluster_bootstrap_resolution_ci(df_sub: pd.DataFrame, tasks: list[str], n_boot: int = 10000, seed: int = 42, alpha: float = 0.05) -> dict[str, float]:
    """Compute task-level cluster-bootstrap confidence interval for resolution rate.
    Resamples task clusters (preserving each task's 3 configuration outcomes together).
    """
    sub = df_sub[df_sub["instance_id"].isin(tasks)]
    task_sums = sub.groupby("instance_id")["resolved"].sum().values
    n_tasks = len(tasks)
    observed_rate = float(task_sums.sum() / (n_tasks * 3))
    rng = np.random.default_rng(seed)
    boot_rates = []
    for _ in range(n_boot):
        sample = rng.choice(task_sums, size=n_tasks, replace=True)
        boot_rates.append(float(sample.sum() / (n_tasks * 3)))
    lo = float(np.percentile(boot_rates, 100 * (alpha / 2)))
    hi = float(np.percentile(boot_rates, 100 * (1 - alpha / 2)))
    return {
        "n_tasks": n_tasks,
        "n_runs": n_tasks * 3,
        "resolved_runs": int(task_sums.sum()),
        "rate_pct": round(observed_rate * 100, 2),
        "ci_95_lo_pct": round(lo * 100, 2),
        "ci_95_hi_pct": round(hi * 100, 2),
        "n_boot": n_boot,
        "seed": seed,
        "method": "task_cluster_percentile_bootstrap"
    }

def paired_bootstrap_diff_ci(a: list[float], b: list[float], n_boot: int = 10000, seed: int = 42) -> tuple[float, float, float]:
    """Compute 95% bootstrap confidence interval for mean(a) - mean(b)."""
    assert len(a) == len(b)
    diffs = np.array(a) - np.array(b)
    obs_diff = float(np.mean(diffs))
    rng = np.random.default_rng(seed)
    boot_diffs = []
    for _ in range(n_boot):
        sample = rng.choice(diffs, size=len(diffs), replace=True)
        boot_diffs.append(float(np.mean(sample)))
    boot_diffs.sort()
    lo = float(np.percentile(boot_diffs, 2.5))
    hi = float(np.percentile(boot_diffs, 97.5))
    return (round(obs_diff, 2), round(lo, 2), round(hi, 2))

def mcnemar_exact(outcomes_a: list[bool], outcomes_b: list[bool]) -> tuple[int, int, float]:
    """Exact two-sided McNemar test for discordant pairs."""
    assert len(outcomes_a) == len(outcomes_b)
    b = sum(1 for x, y in zip(outcomes_a, outcomes_b) if x and not y)
    c = sum(1 for x, y in zip(outcomes_a, outcomes_b) if not x and y)
    n_disc = b + c
    if n_disc == 0:
        return (0, 0, 1.0)
    res = stats.binomtest(min(b, c), n_disc, 0.5, alternative="two-sided")
    return (b, c, round(float(res.pvalue), 4))

def get_trace_edits_hash(trace_file: str) -> tuple[str, int]:
    """Extract and hash actual workspace modifications from trace tool calls."""
    p = TRACES_DIR / trace_file
    if not p.is_file():
        return ("NO_FILE", 0)
    data = json.loads(p.read_text(encoding="utf-8"))
    edits = []
    for s in data.get("steps", []):
        for tc in s.get("tool_calls", []):
            fn = tc.get("function_name")
            args = tc.get("arguments", {})
            if fn in ("write_file", "edit_file"):
                edits.append({
                    "fn": fn,
                    "path": args.get("filepath") or args.get("path") or args.get("file_path"),
                    "content": args.get("content") or args.get("new_string") or "",
                    "old": args.get("old_string") or ""
                })
            elif fn == "submit_patch" and args.get("patch"):
                edits.append({
                    "fn": "submit_patch",
                    "patch": args.get("patch")
                })
    if not edits:
        return ("NO_EDITS", 0)
    serialized = json.dumps(edits, sort_keys=True)
    h = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:12]
    return (h, len(edits))

def main():
    df = pd.read_csv(METADATA_PATH)
    
    print("=" * 70)
    print("  INFERENTIAL STATISTICAL AUDIT (n=112 Traces)")
    print("=" * 70)
    
    # --- 1. Wilson CIs for Resolution Proportions ---
    print("\n--- 1. Wilson 95% Confidence Intervals for Resolution ---")
    wilson_results = {}
    
    # Pooled (n=112)
    k_all = int(df["resolved"].sum())
    n_all = len(df)
    lo, hi = wilson_ci(k_all, n_all)
    wilson_results["POOLED_ALL"] = {
        "resolved": k_all, "n": n_all, "rate_pct": round(k_all / n_all * 100, 2),
        "ci_95_lo_pct": round(lo * 100, 2), "ci_95_hi_pct": round(hi * 100, 2)
    }
    
    # Primary (n=96)
    p_df = df[df["cohort"] != "Cohort 1 Rerun (Reproducibility)"]
    k_p = int(p_df["resolved"].sum())
    n_p = len(p_df)
    lo_p, hi_p = wilson_ci(k_p, n_p)
    wilson_results["PRIMARY_ALL"] = {
        "resolved": k_p, "n": n_p, "rate_pct": round(k_p / n_p * 100, 2),
        "ci_95_lo_pct": round(lo_p * 100, 2), "ci_95_hi_pct": round(hi_p * 100, 2)
    }
    
    # Primary per-config (n=32 each)
    for cfg in ["flat_starter", "flat_controlled", "sfd"]:
        sub = p_df[p_df["config"] == cfg]
        k_cfg = int(sub["resolved"].sum())
        n_cfg = len(sub)
        lo_c, hi_c = wilson_ci(k_cfg, n_cfg)
        wilson_results[f"PRIMARY_{cfg}"] = {
            "resolved": k_cfg, "n": n_cfg, "rate_pct": round(k_cfg / n_cfg * 100, 2),
            "ci_95_lo_pct": round(lo_c * 100, 2), "ci_95_hi_pct": round(hi_c * 100, 2)
        }
        
    # Valid-environment pooled (n=92)
    v_df = df[~df["env_invalid"]]
    k_vp = int(v_df["resolved"].sum())
    n_vp = len(v_df)
    lo_v, hi_v = wilson_ci(k_vp, n_vp)
    wilson_results["VALID_POOLED_ALL"] = {
        "resolved": k_vp, "n": n_vp, "rate_pct": round(k_vp / n_vp * 100, 2),
        "ci_95_lo_pct": round(lo_v * 100, 2), "ci_95_hi_pct": round(hi_v * 100, 2)
    }
    
    # Valid-environment primary (n=80)
    vp_df = p_df[~p_df["env_invalid"]]
    k_vp80 = int(vp_df["resolved"].sum())
    n_vp80 = len(vp_df)
    lo_vp80, hi_vp80 = wilson_ci(k_vp80, n_vp80)
    wilson_results["VALID_PRIMARY_ALL"] = {
        "resolved": k_vp80, "n": n_vp80, "rate_pct": round(k_vp80 / n_vp80 * 100, 2),
        "ci_95_lo_pct": round(lo_vp80 * 100, 2), "ci_95_hi_pct": round(hi_vp80 * 100, 2)
    }
    for cfg in ["flat_starter", "flat_controlled", "sfd"]:
        sub = vp_df[vp_df["config"] == cfg]
        k_cfg = int(sub["resolved"].sum())
        n_cfg = len(sub)
        lo_c, hi_c = wilson_ci(k_cfg, n_cfg)
        wilson_results[f"VALID_PRIMARY_{cfg}"] = {
            "resolved": k_cfg, "n": n_cfg, "rate_pct": round(k_cfg / n_cfg * 100, 2),
            "ci_95_lo_pct": round(lo_c * 100, 2), "ci_95_hi_pct": round(hi_c * 100, 2)
        }
        
    # --- 1b. Task-Level Cluster-Bootstrap CIs for Clustered Runs ---
    print("\n--- 1b. Task-Level Cluster Bootstrap (10,000 resamples over task clusters) ---")
    task_env = p_df.groupby("instance_id")["env_invalid"].any()
    valid_tasks_26 = sorted(task_env[~task_env].index.tolist())
    all_tasks_32 = sorted(p_df["instance_id"].unique().tolist())
    
    cluster_boot_results = {
        "complete_case_26_tasks": task_cluster_bootstrap_resolution_ci(p_df, valid_tasks_26),
        "primary_all_32_tasks": task_cluster_bootstrap_resolution_ci(p_df, all_tasks_32)
    }
    for k, v in cluster_boot_results.items():
        print(f"  {k:24s}: {v['resolved_runs']:2d}/{v['n_runs']:2d} ({v['rate_pct']:5.2f}%) | 95% Cluster-Bootstrap CI: [{v['ci_95_lo_pct']:5.2f}%, {v['ci_95_hi_pct']:5.2f}%]")

    for k, v in wilson_results.items():
        print(f"  {k:22s}: {v['resolved']:2d}/{v['n']:2d} ({v['rate_pct']:5.2f}%) | 95% CI: [{v['ci_95_lo_pct']:5.2f}%, {v['ci_95_hi_pct']:5.2f}%]")

    # --- 2. Paired Comparisons across 32 Primary Benchmark Tasks ---
    piv_resolved = p_df.pivot(index="instance_id", columns="config", values="resolved")
    piv_prompt = p_df.pivot(index="instance_id", columns="config", values="cumulative_prompt_tokens")
    piv_peak = p_df.pivot(index="instance_id", columns="config", values="peak_prompt_tokens")
    piv_total = p_df.pivot(index="instance_id", columns="config", values="cumulative_total_tokens")
    piv_dur = p_df.pivot(index="instance_id", columns="config", values="duration_seconds")
    
    print("\n--- 2. McNemar's Exact Test for Resolution (n=32 paired tasks) ---")
    mcnemar_results = {}
    pairs = [
        ("sfd", "flat_controlled"),
        ("sfd", "flat_starter"),
        ("flat_controlled", "flat_starter")
    ]
    for c1, c2 in pairs:
        b, c, pval = mcnemar_exact(piv_resolved[c1].tolist(), piv_resolved[c2].tolist())
        mcnemar_results[f"{c1}_vs_{c2}"] = {
            "c1_only_resolved (b)": b,
            "c2_only_resolved (c)": c,
            "mcnemar_exact_pvalue": pval,
            "discordant_pairs": b + c
        }
        print(f"  {c1} vs {c2}: b={b}, c={c}, discordant={b+c}, exact two-sided p={pval:.4f}")

    # --- 3. Paired Differences & Non-Parametric Tests across 32 Tasks ---
    print("\n--- 3. Paired Differences & Bootstrap CIs (n=32 tasks; exploratory without multiple-testing correction) ---")
    metric_results = {}
    for metric_name, piv_table in [
        ("cumulative_prompt_tokens", piv_prompt),
        ("peak_prompt_tokens", piv_peak),
        ("cumulative_total_tokens", piv_total),
        ("duration_seconds", piv_dur)
    ]:
        metric_results[metric_name] = {}
        for baseline in ["flat_controlled", "flat_starter"]:
            sfd_vals = piv_table["sfd"].tolist()
            base_vals = piv_table[baseline].tolist()
            
            try:
                w_res = stats.wilcoxon(sfd_vals, base_vals, alternative="two-sided")
                w_stat = float(w_res.statistic)
                w_pval = float(w_res.pvalue)
            except Exception:
                w_stat = 0.0
                w_pval = 1.0
                
            mean_diff, ci_lo, ci_hi = paired_bootstrap_diff_ci(sfd_vals, base_vals)
            sfd_lower = sum(1 for s, b in zip(sfd_vals, base_vals) if s < b)
            sfd_higher = sum(1 for s, b in zip(sfd_vals, base_vals) if s > b)
            
            metric_results[metric_name][f"sfd_vs_{baseline}"] = {
                "mean_diff": mean_diff,
                "diff_pct_of_baseline": round(mean_diff / float(np.mean(base_vals)) * 100, 2),
                "bootstrap_ci_95": [ci_lo, ci_hi],
                "wilcoxon_stat": w_stat,
                "wilcoxon_pvalue": round(w_pval, 4),
                "tasks_sfd_lower": sfd_lower,
                "tasks_sfd_higher": sfd_higher,
                "n_tasks": 32
            }
            print(f"  {metric_name} | SFD vs {baseline:15s}:")
            print(f"    Mean Diff: {mean_diff:+,.1f} ({mean_diff/np.mean(base_vals)*100:+.1f}%) | 95% Bootstrap CI: [{ci_lo:+,.1f}, {ci_hi:+,.1f}]")
            print(f"    Wilcoxon signed-rank p-value: {w_pval:.4f} | Tasks SFD lower: {sfd_lower}/{32}")

    # --- 4. Rerun Determinism Analysis on Cohort 1 (8 tasks x 2 configs = 16 pairs) ---
    print("\n--- 4. Rerun Determinism Audit on Cohort 1 (8 tasks x 2 configs = 16 pairs) ---")
    rerun_pairs = []
    c1_orig = df[df["cohort"] == "Cohort 1 (Canonical)"]
    c1_rerun = df[df["cohort"] == "Cohort 1 Rerun (Reproducibility)"]
    
    rerun_config_map = {
        "flat_controlled": "flat_controlled_rerun",
        "sfd": "sfd_rerun"
    }
    
    identical_exit_codes = 0
    identical_edit_hashes = 0
    token_differences = []
    
    for base_cfg, rerun_cfg in rerun_config_map.items():
        for iid in sorted(c1_orig["instance_id"].unique()):
            row_orig = c1_orig[(c1_orig["config"] == base_cfg) & (c1_orig["instance_id"] == iid)].iloc[0]
            row_rerun = c1_rerun[(c1_rerun["config"] == rerun_cfg) & (c1_rerun["instance_id"] == iid)].iloc[0]
            
            orig_hash, orig_edits_cnt = get_trace_edits_hash(row_orig["dataset_trace_file"])
            rerun_hash, rerun_edits_cnt = get_trace_edits_hash(row_rerun["dataset_trace_file"])
            
            ec_match = (row_orig["test_exit_code"] == row_rerun["test_exit_code"])
            hash_match = (orig_hash == rerun_hash and orig_hash != "NO_EDITS")
            tok_diff = int(row_rerun["cumulative_total_tokens"] - row_orig["cumulative_total_tokens"])
            token_differences.append(abs(tok_diff))
            
            if ec_match:
                identical_exit_codes += 1
            if hash_match:
                identical_edit_hashes += 1
                
            rerun_pairs.append({
                "instance_id": str(iid),
                "config": str(base_cfg),
                "orig_exit_code": int(row_orig["test_exit_code"]),
                "rerun_exit_code": int(row_rerun["test_exit_code"]),
                "exit_code_match": bool(ec_match),
                "orig_resolved": bool(row_orig["resolved"]),
                "rerun_resolved": bool(row_rerun["resolved"]),
                "orig_edit_hash": str(orig_hash),
                "rerun_edit_hash": str(rerun_hash),
                "orig_edits_count": orig_edits_cnt,
                "rerun_edits_count": rerun_edits_cnt,
                "edit_hash_match": bool(hash_match),
                "orig_total_tokens": int(row_orig["cumulative_total_tokens"]),
                "rerun_total_tokens": int(row_rerun["cumulative_total_tokens"]),
                "token_diff": int(tok_diff)
            })
            
    print(f"  Exit code consistency: {identical_exit_codes}/16 ({identical_exit_codes/16*100:.1f}%)")
    print(f"  Exact edit hash match: {identical_edit_hashes}/16 ({identical_edit_hashes/16*100:.1f}%)")
    print(f"  Mean absolute token deviation: {np.mean(token_differences):,.1f} tokens")
    
    # --- 5. Task-Level Concentration Analysis ---
    print("\n--- 5. Task-Level Failure & Resolution Concentration (32 tasks) ---")
    task_res = []
    for iid, g in p_df.groupby("instance_id"):
        n_res = int(g["resolved"].sum())
        repo = g["repo"].iloc[0]
        exit_codes = list(g["test_exit_code"])
        env_inv = bool(g["env_invalid"].any())
        task_res.append({
            "instance_id": iid,
            "repo": repo,
            "resolved_runs": n_res,
            "resolved_any": n_res > 0,
            "exit_codes": exit_codes,
            "has_env_invalid": env_inv
        })
    task_df = pd.DataFrame(task_res)
    print(f"  Tasks with >=1 resolution: {task_df['resolved_any'].sum()} / {len(task_df)} ({task_df['resolved_any'].mean()*100:.1f}%)")
    print(f"  Tasks with env_invalid runs: {task_df['has_env_invalid'].sum()} / {len(task_df)} ({task_df['has_env_invalid'].mean()*100:.1f}%)")

    # Save results
    stats_report = {
        "wilson_cis": wilson_results,
        "cluster_bootstrap_cis": cluster_boot_results,
        "mcnemar_exact": mcnemar_results,
        "metric_comparisons_n32": metric_results,
        "rerun_summary": {
            "total_pairs": 16,
            "identical_exit_codes": identical_exit_codes,
            "exit_code_agreement_pct": round(identical_exit_codes / 16 * 100, 2),
            "identical_edit_hashes": identical_edit_hashes,
            "edit_hash_agreement_pct": round(identical_edit_hashes / 16 * 100, 2),
            "mean_abs_token_diff": round(float(np.mean(token_differences)), 1)
        },
        "task_level_summary": {
            "total_tasks": len(task_df),
            "tasks_with_resolution": int(task_df["resolved_any"].sum()),
            "tasks_with_env_invalid": int(task_df["has_env_invalid"].sum())
        }
    }
    (RESULTS_DIR / "stats_report.json").write_text(json.dumps(stats_report, indent=2), encoding="utf-8")
    (RESULTS_DIR / "rerun_determinism.json").write_text(json.dumps(rerun_pairs, indent=2), encoding="utf-8")
    
    print("\n[SUCCESS] Statistical tests and rerun determinism audit complete.")
    print(f"Saved to {RESULTS_DIR / 'stats_report.json'} and {RESULTS_DIR / 'rerun_determinism.json'}")

if __name__ == "__main__":
    main()
