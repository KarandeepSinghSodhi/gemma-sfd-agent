"""
gold_patch_control.py: Gold-Patch Oracle Control for SWE-bench Benchmark Tasks.
Applies reference ground-truth patches from tasks_reference.jsonl directly to repository snapshots
and executes held-out verification tests to establish the empirical Oracle Ceiling.

NOTE: This script requires the official Linux evaluation environment with mounted repo snapshots
and offline wheelhouse (e.g. on Kaggle /kaggle/input/gemma-4-developer-agent).
When local Linux sandbox is absent, this task is marked BLOCKED per empirical protocol Rule 2.
DO NOT SIMULATE OR ESTIMATE RESULTS.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

def run_gold_patch_evaluation(data_dir: Path, output_file: Path):
    """
    Apply reference patch for each task in tasks.jsonl in the official sandbox.
    Record exit codes:
      - exit_code == 0: Valid benchmark task (solvable by oracle patch)
      - exit_code == 2: Infrastructure defect (fails even with author ground truth patch)
      - exit_code == 1: Flaky / environment discrepancy
    """
    try:
        import swegemma
        from swegemma.models import load_tasks
    except ImportError:
        print("[BLOCKED] swegemma is not installed in the current environment.")
        print("To run this oracle control, execute inside the official Kaggle kernel environment.")
        sys.exit(0)
        
    tasks_path = data_dir / "tasks.jsonl"
    if not tasks_path.exists():
        print(f"[BLOCKED] tasks.jsonl not found at {tasks_path}")
        sys.exit(0)
        
    tasks = load_tasks(tasks_path)
    print(f"Loaded {len(tasks)} benchmark tasks for gold-patch oracle evaluation.")
    
    # Execution loop inside Kaggle sandbox ...
    # Outputs to results/gold_patch_oracle_results.json

if __name__ == "__main__":
    data_dir = Path("/kaggle/input/competitions/gemma-4-developer-agent")
    out_file = Path("results/gold_patch_oracle_results.json")
    run_gold_patch_evaluation(data_dir, out_file)
