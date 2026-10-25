"""
Official aggregation engine for SWE-gemma developer agent benchmarks.
THIS SCRIPT IS THE ONLY SOURCE OF NUMBERS FOR THE RESEARCH PAPER.
Reads verifiable raw JSON trace files from traces/ and computes exact metrics.
"""

import argparse
import glob
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np


def wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Computes exact Wilson score confidence interval."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1.0 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    margin = (z * math.sqrt((p * (1 - p) / n) + (z**2) / (4 * (n**2)))) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def mcnemar_exact(b: int, c: int) -> float:
    """Exact two-tailed McNemar test using binomial distribution."""
    from scipy.stats import binom
    n_discordant = b + c
    if n_discordant == 0:
        return 1.0
    k_min = min(b, c)
    # Two-sided p-value is 2 * P(X <= k_min) where X ~ Binomial(n_discordant, 0.5)
    p_val = 2.0 * binom.cdf(k_min, n_discordant, 0.5)
    return min(1.0, p_val)


def load_traces(trace_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Loads all JSON trace files grouped by config_name."""
    configs: Dict[str, List[Dict[str, Any]]] = {}
    files = list(trace_dir.glob("*.json"))
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            cfg = data.get("config_name", "unknown")
            configs.setdefault(cfg, []).append(data)
        except Exception as e:
            print(f"Warning: Failed to parse trace {f}: {e}", file=sys.stderr)
    return configs


def summarize_config(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes statistical summary for a set of traces under one configuration."""
    n = len(traces)
    if n == 0:
        return {}

    resolved_count = sum(1 for t in traces if t.get("resolved", False))
    overflow_count = sum(1 for t in traces if t.get("context_overflow", False))
    cap_count = sum(1 for t in traces if len(t.get("cap_triggers", [])) > 0)

    peak_tokens = [t.get("peak_prompt_tokens", 0) for t in traces]
    cum_tokens = [t.get("cumulative_tokens", 0) for t in traces]
    durations = [t.get("duration_seconds", 0.0) for t in traces]

    low_ci, high_ci = wilson_ci(resolved_count, n)

    # Error analysis
    all_errors: Dict[str, int] = {}
    for t in traces:
        for err in t.get("errors", []):
            all_errors[err] = all_errors.get(err, 0) + 1

    return {
        "n_tasks": n,
        "resolved": resolved_count,
        "pass_rate": resolved_count / n,
        "pass_rate_pct": round((resolved_count / n) * 100, 2),
        "wilson_ci_low_pct": round(low_ci * 100, 2),
        "wilson_ci_high_pct": round(high_ci * 100, 2),
        "overflow_count": overflow_count,
        "overflow_rate_pct": round((overflow_count / n) * 100, 2),
        "cap_trigger_count": cap_count,
        "cap_trigger_rate_pct": round((cap_count / n) * 100, 2),
        "mean_peak_prompt_tokens": round(float(np.mean(peak_tokens)), 1),
        "max_peak_prompt_tokens": int(np.max(peak_tokens)),
        "mean_cumulative_tokens": round(float(np.mean(cum_tokens)), 1),
        "mean_duration_seconds": round(float(np.mean(durations)), 2),
        "errors": all_errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Aggregate trace metrics for SWE-gemma")
    parser.add_argument("--trace-dir", type=Path, default=Path("traces"), help="Directory containing trace JSONs")
    parser.add_argument("--out-dir", type=Path, default=Path("results"), help="Directory to save summary tables")
    args = parser.parse_args()

    configs = load_traces(args.trace_dir)
    if not configs:
        print(f"No traces found in {args.trace_dir}.")
        return

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summaries: Dict[str, Dict[str, Any]] = {}

    print("\n" + "=" * 90)
    print(f"{'Config Name':<28} | {'Resolved':<10} | {'Pass@1 (95% CI)':<20} | {'Overflow %':<10} | {'Peak Toks':<10}")
    print("-" * 90)

    rows = []
    for cfg, traces in sorted(configs.items()):
        s = summarize_config(traces)
        summaries[cfg] = s
        ci_str = f"{s['pass_rate_pct']:.1f}% [{s['wilson_ci_low_pct']:.1f}, {s['wilson_ci_high_pct']:.1f}]"
        print(f"{cfg:<28} | {s['resolved']}/{s['n_tasks']:<8} | {ci_str:<20} | {s['overflow_rate_pct']:>9.1f}% | {s['mean_peak_prompt_tokens']:>9.0f}")
        rows.append({
            "config": cfg,
            "n": s["n_tasks"],
            "resolved": s["resolved"],
            "pass_rate_pct": s["pass_rate_pct"],
            "ci_low_pct": s["wilson_ci_low_pct"],
            "ci_high_pct": s["wilson_ci_high_pct"],
            "overflow_pct": s["overflow_rate_pct"],
            "cap_trigger_pct": s["cap_trigger_rate_pct"],
            "mean_peak_tokens": s["mean_peak_prompt_tokens"],
            "max_peak_tokens": s["max_peak_prompt_tokens"],
            "mean_cumulative_tokens": s["mean_cumulative_tokens"],
            "mean_duration_sec": s["mean_duration_seconds"],
        })

    print("=" * 90 + "\n")

    # Save to JSON and CSV
    json_path = args.out_dir / "summary.json"
    json_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(args.out_dir / "summary.csv", index=False)
    print(f"Saved aggregated results to {json_path} and {args.out_dir / 'summary.csv'}")


if __name__ == "__main__":
    main()
