"""
statistical_tests.py: Rigorous inferential statistics, paired tests, and rerun determinism audit.
Computes:
1. Wilson score 95% confidence intervals for binomial resolution rates.
2. McNemar's exact two-sided test for paired resolution outcomes (n=32).
3. Wilcoxon signed-rank tests and 10,000-sample paired bootstrap 95% CIs for:
   - Cumulative prompt tokens
   - Peak prompt tokens
   - Cumulative total tokens
   - Execution duration
4. Rerun determinism analysis on Cohort 1 (original vs rerun across 8 tasks x 2 configs = 16 pairs).
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
    return (max(0.0, round(center - half, 4)), min(1.0, round(center + half, 4)))

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
    # b: a=True, b=False; c: a=False, b=True
    b = sum(1 for x, y in zip(outcomes_a, outcomes_b) if x and not y)
    c = sum(1 for x, y in zip(outcomes_a, outcomes_b) if not x and y)
    n_disc = b + c
    if n_disc == 0:
        return (0, 0, 1.0)
    # Binomial test with p=0.5
    res = stats.binomtest(min(b, c), n_disc, 0.5, alternative="two-sided")
    return (b, c, round(res.pvalue, 4))

def get_trace_patch_hash(trace_file: str) -> tuple[str, int]:
    p = TRACES_DIR / trace_file
    if not p.is_file():
        return ("", 0)
    data = json.loads(p.read_text(encoding="utf-8"))
    for s in data.get("steps", []):
        for tc in s.get("tool_calls", []):
            if tc.get("function_name") == "submit_patch":
                patch_str = tc.get("arguments", {}).get("patch", "")
                h = hashlib.sha256(patch_str.encode("utf-8")).hexdigest()[:12]
                return (h, len(patch_str))
    return ("NO_PATCH", 0)

def main():
    df = pd.read_csv(METADATA_PATH)
    
    print("=" * 70)
    print("  INFERENTIAL STATISTICAL AUDIT (n=112 Traces)")
    print("=" * 70)
    
    # --- 1. Wilson CIs for Resolution Proportions ---
    print("\n--- 1. Wilson 95% Confidence Intervals for Resolution ---")
    wilson_results = {}
    for cfg in ["flat_starter", "flat_controlled", "sfd", "flat_controlled_rerun", "sfd_rerun", "ALL"]:
        if cfg == "ALL":
            sub = df
            k = int(sub["resolved"].sum())
            n = len(sub)
        else:
            sub = df[df["config"] == cfg]
            k = int(sub["resolved"].sum())
            n = len(sub)
        lo, hi = wilson_ci(k, n)
        wilson_results[cfg] = {
            "resolved": k,
            "n": n,
            "rate_pct": round(k / n * 100, 2),
            "ci_95_lo_pct": round(lo * 100, 2),
            "ci_95_hi_pct": round(hi * 100, 2)
        }
        print(f"  {cfg:24s}: {k:2d}/{n:2d} ({k/n*100:5.2f}%) | 95% CI: [{lo*100:5.2f}%, {hi*100:5.2f}%]")

    # --- 2. Paired Comparisons across 32 Primary Benchmark Tasks ---
    # Filter to primary 32 tasks (Cohorts 1, 2, 3, 4; exclude rerun)
    primary_df = df[df["cohort"].isin([
        "Cohort 1 (Canonical)", "Cohort 2 (Stratified Random)",
        "Cohort 3 (Stratified Disjoint)", "Cohort 4 (Stratified Disjoint)"
    ])]
    
    # Pivot by instance_id
    piv_resolved = primary_df.pivot(index="instance_id", columns="config", values="resolved")
    piv_prompt = primary_df.pivot(index="instance_id", columns="config", values="cumulative_prompt_tokens")
    piv_peak = primary_df.pivot(index="instance_id", columns="config", values="peak_prompt_tokens")
    piv_total = primary_df.pivot(index="instance_id", columns="config", values="cumulative_total_tokens")
    piv_dur = primary_df.pivot(index="instance_id", columns="config", values="duration_seconds")
    
    # Assert 32 complete rows across all 3 primary configs
    for piv in [piv_resolved, piv_prompt, piv_peak, piv_total, piv_dur]:
        assert len(piv) == 32
        assert set(piv.columns) >= {"flat_starter", "flat_controlled", "sfd"}
        
    print("\n--- 2. McNemar's Exact Test for Resolution (n=32 paired tasks) ---")
    mcnemar_results = {}
    pairs = [
        ("sfd", "flat_controlled"),
        ("sfd", "flat_starter"),
        ("flat_controlled", "flat_starter")
    ]
    for c1, c2 in pairs:
        b, c, pval = mcnemar_exact(piv_resolved[c1].tolist(), piv_resolved[c2].tolist())
        mcnemar_results[f"{c1}_vs_{c2}"] = {"b_c1_only": b, "c_c2_only": c, "p_value": pval}
        print(f"  {c1} vs {c2}: discordant=({b}, {c}) | exact p-value = {pval:.4f}")

    print("\n--- 3. Paired Differences: SFD vs Flat Baselines (n=32 paired tasks) ---")
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
            
            # Wilcoxon signed-rank test
            try:
                w_res = stats.wilcoxon(sfd_vals, base_vals, alternative="two-sided")
                w_stat = float(w_res.statistic)
                w_pval = float(w_res.pvalue)
            except Exception as e:
                w_stat = 0.0
                w_pval = 1.0
                
            # Bootstrap CI on difference
            mean_diff, ci_lo, ci_hi = paired_bootstrap_diff_ci(sfd_vals, base_vals)
            
            # Sign test: how many tasks lower in SFD?
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

    # --- 4. Rerun Determinism Analysis (Cohort 1 Original vs Rerun) ---
    print("\n--- 4. Rerun Determinism Audit on Cohort 1 (8 tasks x 2 configs = 16 pairs) ---")
    rerun_pairs = []
    c1_orig = df[df["cohort"] == "Cohort 1 (Canonical)"]
    c1_rerun = df[df["cohort"] == "Cohort 1 Rerun (Reproducibility)"]
    
    rerun_config_map = {
        "flat_controlled": "flat_controlled_rerun",
        "sfd": "sfd_rerun"
    }
    
    identical_exit_codes = 0
    identical_patch_hashes = 0
    token_differences = []
    
    for base_cfg, rerun_cfg in rerun_config_map.items():
        for iid in sorted(c1_orig["instance_id"].unique()):
            row_orig = c1_orig[(c1_orig["config"] == base_cfg) & (c1_orig["instance_id"] == iid)].iloc[0]
            row_rerun = c1_rerun[(c1_rerun["config"] == rerun_cfg) & (c1_rerun["instance_id"] == iid)].iloc[0]
            
            orig_hash, orig_plen = get_trace_patch_hash(row_orig["dataset_trace_file"])
            rerun_hash, rerun_plen = get_trace_patch_hash(row_rerun["dataset_trace_file"])
            
            ec_match = (row_orig["test_exit_code"] == row_rerun["test_exit_code"])
            hash_match = (orig_hash == rerun_hash and orig_hash != "NO_PATCH")
            tok_diff = int(row_rerun["cumulative_total_tokens"] - row_orig["cumulative_total_tokens"])
            token_differences.append(abs(tok_diff))
            
            if ec_match:
                identical_exit_codes += 1
            if hash_match:
                identical_patch_hashes += 1
                
            rerun_pairs.append({
                "instance_id": str(iid),
                "config": str(base_cfg),
                "orig_exit_code": int(row_orig["test_exit_code"]),
                "rerun_exit_code": int(row_rerun["test_exit_code"]),
                "exit_code_match": bool(ec_match),
                "orig_resolved": bool(row_orig["resolved"]),
                "rerun_resolved": bool(row_rerun["resolved"]),
                "orig_patch_hash": str(orig_hash),
                "rerun_patch_hash": str(rerun_hash),
                "patch_hash_match": bool(hash_match),
                "orig_total_tokens": int(row_orig["cumulative_total_tokens"]),
                "rerun_total_tokens": int(row_rerun["cumulative_total_tokens"]),
                "token_diff": int(tok_diff)
            })
            
    print(f"  Exit code consistency: {identical_exit_codes}/16 ({identical_exit_codes/16*100:.1f}%)")
    print(f"  Exact patch hash match: {identical_patch_hashes}/16 ({identical_patch_hashes/16*100:.1f}%)")
    print(f"  Mean absolute token deviation: {np.mean(token_differences):,.1f} tokens")
    
    # Save results
    stats_report = {
        "wilson_cis": wilson_results,
        "mcnemar_exact": mcnemar_results,
        "metric_comparisons_n32": metric_results,
        "rerun_summary": {
            "total_pairs": 16,
            "identical_exit_codes": identical_exit_codes,
            "exit_code_agreement_pct": round(identical_exit_codes / 16 * 100, 2),
            "identical_patch_hashes": identical_patch_hashes,
            "patch_hash_agreement_pct": round(identical_patch_hashes / 16 * 100, 2),
            "mean_abs_token_diff": round(float(np.mean(token_differences)), 1)
        }
    }
    (RESULTS_DIR / "stats_report.json").write_text(json.dumps(stats_report, indent=2), encoding="utf-8")
    (RESULTS_DIR / "rerun_determinism.json").write_text(json.dumps(rerun_pairs, indent=2), encoding="utf-8")
    
    print("\n[SUCCESS] Statistical tests and rerun determinism audit complete.")
    print(f"Saved to {RESULTS_DIR / 'stats_report.json'} and {RESULTS_DIR / 'rerun_determinism.json'}")

if __name__ == "__main__":
    main()
