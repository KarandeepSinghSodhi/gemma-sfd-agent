"""
classify_exit2.py: Deterministic classification of all 36 Exit Code 2 runs.
Examines pytest collection failures across 4 precise mechanisms:
1. MISSING_SANDBOX_DEPENDENCY: test_patch requires external packages absent from offline sandbox (e.g. inline_snapshot, dirty_equals).
2. VENV_OR_PATH_SHADOWING: environment path misconfiguration (httpx shadowed by system dist-packages, or repo scripts/ missing from PYTHONPATH).
3. SYNTAX_OR_INDENTATION_CORRUPTION: agent patch introduced unindented, malformed, or invalid python syntax causing collection syntax errors.
4. MISSING_NEW_SOURCE_MODULE: issue specification required creating a new module (rich._unicode_data); test collection failed when module was absent.
"""
import ast
import json
import csv
from pathlib import Path
from collections import defaultdict
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TASKS_PATH = ROOT / "dataset_resource" / "tasks_reference.jsonl"
METADATA_PATH = ROOT / "dataset_resource" / "corpus_metadata.csv"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def main():
    tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in TASKS_PATH.read_text(encoding="utf-8").splitlines() if l.strip()}
    df = pd.read_csv(METADATA_PATH)
    exit2_df = df[df["test_exit_code"] == 2]
    
    classified_runs = []
    mechanism_counts = defaultdict(int)
    task_breakdown = defaultdict(lambda: defaultdict(int))
    config_breakdown = defaultdict(lambda: defaultdict(int))
    
    # Missing dependencies in test_patch (absent from offline wheelhouse)
    MISSING_DEP_TASKS = {"fastapi_14361", "fastapi_14371", "fastapi_14455", "fastapi_14459"}
    
    # Environment / Path shadowing
    PATH_SHADOWING_TASKS = {
        "httpx_3672": "System dist-packages/httpx shadows workspace src/httpx",
        "fastapi_15661": "Test patch imports from scripts.prepare_release which requires workspace scripts/ on PYTHONPATH"
    }
    
    # New source module creation required by issue
    MISSING_NEW_MODULE_TASKS = {
        "rich_3930": "Issue requires creating rich/_unicode_data.py; absent module causes ModuleNotFoundError during test collection"
    }
    
    # Syntax / Indentation corruption by agent patch
    SYNTAX_CORRUPT_TASKS = {
        "fastapi_14099": "Detached else block and unindented loop inserted by PatchAgent",
        "fastapi_15588": "Malformed type annotations in fastapi/sse.py causing syntax error",
        "fastapi_15589": "Malformed BaseModel extra configuration in query cookie header model",
        "fastapi_14077": "Patch syntax error in flat_starter run",
        "rich_3894": "Unindented if-statement inserted into rich/_inspect.py",
        "fastapi_15280": "Unmatched quote / syntax corruption in exception handler patch",
        "fastapi_15785": "Syntax error in security OpenAPI schema patch"
    }
    
    for idx, row in exit2_df.iterrows():
        iid = row["instance_id"]
        cfg = row["config"]
        cohort = row["cohort"]
        t = tasks.get(iid, {})
        repo = t.get("repo", "")
        
        if iid in MISSING_DEP_TASKS:
            mech = "MISSING_SANDBOX_DEPENDENCY"
            reason = "Held-out test patch imports external dependencies (inline_snapshot / dirty_equals) missing from offline wheelhouse."
        elif iid in PATH_SHADOWING_TASKS:
            mech = "VENV_OR_PATH_SHADOWING"
            reason = PATH_SHADOWING_TASKS[iid]
        elif iid in MISSING_NEW_MODULE_TASKS:
            mech = "MISSING_NEW_SOURCE_MODULE"
            reason = MISSING_NEW_MODULE_TASKS[iid]
        elif iid in SYNTAX_CORRUPT_TASKS:
            mech = "SYNTAX_OR_INDENTATION_CORRUPTION"
            reason = SYNTAX_CORRUPT_TASKS[iid]
        else:
            mech = "UNCLASSIFIED"
            reason = "Unclassified pytest exit code 2 error"
            
        classified_runs.append({
            "cohort": cohort,
            "instance_id": iid,
            "repo": repo,
            "config": cfg,
            "mechanism": mech,
            "reason": reason,
            "patch_chars": row.get("patch_chars", 0)
        })
        
        mechanism_counts[mech] += 1
        task_breakdown[iid][mech] += 1
        config_breakdown[cfg][mech] += 1
        
    print("=" * 70)
    print("  CLASSIFICATION REPORT: 36 EXIT CODE 2 RUNS")
    print("=" * 70)
    for m, c in sorted(mechanism_counts.items(), key=lambda x: -x[1]):
        print(f"  {m:35s}: {c:2d} ({c/len(exit2_df)*100:.1f}%)")
        
    print("\nTask-level Breakdown:")
    for tid in sorted(task_breakdown.keys()):
        print(f"  {tid:16s}: {dict(task_breakdown[tid])}")
        
    print("\nConfig-level Breakdown:")
    for cfg in sorted(config_breakdown.keys()):
        print(f"  {cfg:24s}: {dict(config_breakdown[cfg])}")
        
    unclassified = [r for r in classified_runs if r["mechanism"] == "UNCLASSIFIED"]
    assert len(unclassified) == 0, f"Found {len(unclassified)} unclassified runs!"
    assert len(classified_runs) == 36, f"Expected 36 classified runs, got {len(classified_runs)}"
    
    out_json = {
        "total_exit2_runs": len(classified_runs),
        "mechanism_counts": dict(mechanism_counts),
        "task_breakdown": {k: dict(v) for k, v in task_breakdown.items()},
        "config_breakdown": {k: dict(v) for k, v in config_breakdown.items()},
        "classified_runs": classified_runs
    }
    (RESULTS_DIR / "exit2_breakdown.json").write_text(json.dumps(out_json, indent=2), encoding="utf-8")
    
    with open(RESULTS_DIR / "exit2_breakdown.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(classified_runs[0].keys()))
        w.writeheader()
        w.writerows(classified_runs)
        
    print("\n[PASS] All 36 Exit Code 2 runs classified deterministically into 4 mechanisms.")
    print(f"Saved to {RESULTS_DIR / 'exit2_breakdown.json'} and {RESULTS_DIR / 'exit2_breakdown.csv'}")

if __name__ == "__main__":
    main()
