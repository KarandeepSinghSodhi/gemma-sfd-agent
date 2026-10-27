"""
claim_audit.py: Produces exact empirical distributions for:
1. Tool error breakdown across all 112 traces (total vs per-run, by error type).
2. Stage-transition prompt reset distribution across all 32 SFD runs (mean, median, min, max, IQR).
Outputs:
- results/tool_errors_breakdown.json
- results/stage_resets_distribution.json
"""
import json
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

ROOT = Path(r"d:\AI Research\gemma_paper")
TRACES_DIR = ROOT / "dataset_resource" / "traces"
METADATA_PATH = ROOT / "dataset_resource" / "corpus_metadata.csv"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def audit_tool_errors():
    df = pd.read_csv(METADATA_PATH)
    error_counts = defaultdict(int)
    error_by_config = defaultdict(lambda: defaultdict(int))
    runs_with_errors = defaultdict(set)
    
    for idx, row in df.iterrows():
        tpath = TRACES_DIR / row["dataset_trace_file"]
        if not tpath.is_file():
            continue
        data = json.loads(tpath.read_text(encoding="utf-8"))
        for s in data.get("steps", []):
            obs = s.get("observation") or {}
            obs_c = obs.get("content", "") if isinstance(obs, dict) else ""
            if isinstance(obs_c, str):
                if "FileEditError" in obs_c:
                    if "could not find old_string" in obs_c.lower() or "not found" in obs_c.lower():
                        err_type = "FileEditError: StringNotFound"
                    elif "syntax" in obs_c.lower() or "indent" in obs_c.lower():
                        err_type = "FileEditError: SyntaxCorruption"
                    else:
                        err_type = "FileEditError: Other"
                    error_counts[err_type] += 1
                    error_by_config[row["config"]][err_type] += 1
                    runs_with_errors[err_type].add(row["dataset_trace_file"])
                elif "CommandError" in obs_c:
                    err_type = "CommandError: NonZeroExit"
                    error_counts[err_type] += 1
                    error_by_config[row["config"]][err_type] += 1
                    runs_with_errors[err_type].add(row["dataset_trace_file"])
                elif "FileReadError" in obs_c or "FileNotFoundError" in obs_c:
                    err_type = "FileReadError: PathNotFound"
                    error_counts[err_type] += 1
                    error_by_config[row["config"]][err_type] += 1
                    runs_with_errors[err_type].add(row["dataset_trace_file"])
                    
    total_runs = len(df)
    report = {
        "total_runs": total_runs,
        "error_counts": dict(error_counts),
        "total_tool_errors": sum(error_counts.values()),
        "mean_errors_per_run": round(sum(error_counts.values()) / total_runs, 2),
        "error_by_config": {k: dict(v) for k, v in error_by_config.items()},
        "runs_affected_pct": {k: round(len(v) / total_runs * 100, 1) for k, v in runs_with_errors.items()}
    }
    (RESULTS_DIR / "tool_errors_breakdown.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

def audit_stage_resets():
    df = pd.read_csv(METADATA_PATH)
    
    def calc_for_df(subset_df):
        resets_pct = []
        triage_peaks = []
        patch_entries = []
        for idx, row in subset_df.iterrows():
            tpath = TRACES_DIR / row["dataset_trace_file"]
            if not tpath.is_file():
                continue
            data = json.loads(tpath.read_text(encoding="utf-8"))
            steps = data.get("steps", [])
            triage_pts = []
            patch_pts = []
            for s in steps:
                author = (s.get("extra") or {}).get("author") or ""
                m = s.get("metrics")
                if isinstance(m, dict) and "prompt_tokens" in m:
                    pt = int(m.get("prompt_tokens", 0))
                    if "triage" in author.lower() or author == "TriageAgent":
                        triage_pts.append(pt)
                    elif "patch" in author.lower() or author == "PatchAgent":
                        patch_pts.append(pt)
            if triage_pts and patch_pts:
                t_peak = max(triage_pts)
                p_entry = patch_pts[0]
                reset_pct = (t_peak - p_entry) / t_peak * 100.0
                resets_pct.append(reset_pct)
                triage_peaks.append(t_peak)
                patch_entries.append(p_entry)
        resets_arr = np.array(resets_pct)
        t_peaks_arr = np.array(triage_peaks)
        p_entries_arr = np.array(patch_entries)
        return {
            "n_measured": len(resets_arr),
            "mean_reset_pct": round(float(np.mean(resets_arr)), 2),
            "median_reset_pct": round(float(np.median(resets_arr)), 2),
            "std_reset_pct": round(float(np.std(resets_arr)), 2),
            "q25_reset_pct": round(float(np.percentile(resets_arr, 25)), 2),
            "q75_reset_pct": round(float(np.percentile(resets_arr, 75)), 2),
            "min_reset_pct": round(float(np.min(resets_arr)), 2),
            "max_reset_pct": round(float(np.max(resets_arr)), 2),
            "mean_triage_peak": round(float(np.mean(t_peaks_arr)), 1),
            "median_triage_peak": round(float(np.median(t_peaks_arr)), 1),
            "mean_patch_entry": round(float(np.mean(p_entries_arr)), 1),
            "median_patch_entry": round(float(np.median(p_entries_arr)), 1)
        }
    
    primary_stats = calc_for_df(df[df["config"] == "sfd"])
    all_stats = calc_for_df(df[df["config"].isin(["sfd", "sfd_rerun"])])
    
    stats_dict = {
        "primary_sfd_n32": primary_stats,
        "all_sfd_n40": all_stats
    }
    (RESULTS_DIR / "stage_resets_distribution.json").write_text(json.dumps(stats_dict, indent=2), encoding="utf-8")
    return stats_dict

def main():
    print("=" * 70)
    print("  CLAIM AUDIT: TOOL ERRORS & STAGE RESETS")
    print("=" * 70)
    err_report = audit_tool_errors()
    print("\nTool Error Counts across 112 traces:")
    for k, v in err_report["error_counts"].items():
        print(f"  {k:35s}: {v:3d}")
    print(f"Total Tool Errors: {err_report['total_tool_errors']} (mean {err_report['mean_errors_per_run']} per run)")
    
    reset_report = audit_stage_resets()
    prim = reset_report["primary_sfd_n32"]
    print(f"\nStage Reset Distribution across {prim['n_measured']} primary SFD runs:")
    print(f"  Mean:   {prim['mean_reset_pct']}%")
    print(f"  Median: {prim['median_reset_pct']}%")
    print(f"  IQR:    [{prim['q25_reset_pct']}%, {prim['q75_reset_pct']}%]")
    print(f"  Range:  [{prim['min_reset_pct']}%, {prim['max_reset_pct']}%]")
    print(f"  Mean Triage Peak -> Patch Entry: {prim['mean_triage_peak']} -> {prim['mean_patch_entry']} tokens")
    print("=" * 70)

if __name__ == "__main__":
    main()
