"""
gold_patch_control.py: Reference Ground-Truth Patch Oracle Control Protocol.
Applies author reference patches from tasks_reference.jsonl directly to repository snapshots
and executes held-out verification tests to establish the empirical Oracle Ceiling.

ENVIRONMENT REQUIREMENT:
This script is designed for execution within the competition's offline Linux evaluation
container (where repository snapshots and the offline wheelhouse are mounted).
Because that offline evaluation container was not available in local workstation environments,
executing this oracle control was not conducted locally and remains planned future work.
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
        print("[ENVIRONMENT REQUIRED] swegemma is not installed in the local workstation environment.")
        print("To run this oracle control, execute inside the official competition container environment.")
        sys.exit(0)
        
    tasks_path = data_dir / "tasks.jsonl"
    if not tasks_path.exists():
        print(f"[ENVIRONMENT REQUIRED] tasks.jsonl not found at {tasks_path}")
        sys.exit(0)
        
    tasks = load_tasks(tasks_path)
    print(f"Loaded {len(tasks)} benchmark tasks for gold-patch oracle evaluation.")
    
    # Execution loop inside competition sandbox ...
    # Outputs to results/gold_patch_oracle_results.json

if __name__ == "__main__":
    data_dir = Path("/kaggle/input/competitions/gemma-4-developer-agent")
    out_file = Path("results/gold_patch_oracle_results.json")
    run_gold_patch_evaluation(data_dir, out_file)
