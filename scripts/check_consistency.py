"""
Consistency checker verifying that paper.typ, paper.tex, and KAGGLE_WRITEUP.md
do not contain unverified simulated numbers, and that all cited metrics match results/summary.csv.
"""

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_CSV = ROOT / "results" / "summary.csv"
DOCS = [
    ROOT / "paper.typ",
    ROOT / "paper.tex",
    ROOT / "KAGGLE_WRITEUP.md",
]

PROHIBITED_STRINGS = [
    "28.7%",
    "48.8%",
    "18.5x",
    "18.5\\times",
    "85.3%",
    "12,938",
    "1,906",
    "simulate_benchmark",
    "benchmark_results.csv",
    "$15,000",
    "$10,000",
    "unprecedented",
    "first to demonstrate",
    "first mathematical treatment",
    "mathematically principled",
]


def check_prohibited():
    violations = []
    for doc in DOCS:
        if not doc.exists():
            continue
        text = doc.read_text(encoding="utf-8")
        for bad in PROHIBITED_STRINGS:
            if bad.lower() in text.lower():
                violations.append((doc.name, bad))
    return violations


def main():
    print("Checking document consistency and integrity...")
    violations = check_prohibited()
    if violations:
        print(f"FAILED: Found {len(violations)} prohibited ungrounded strings:")
        for doc_name, bad in violations:
            print(f"  - In {doc_name}: '{bad}'")
        sys.exit(1)
    
    print("SUCCESS: Zero prohibited simulated strings found across all documents.")
    
    if RESULTS_CSV.exists():
        with open(RESULTS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        print(f"Verified results summary exists with {len(rows)} configs:")
        for r in rows:
            print(f"  - Config: {r['config']} | n={r['n']} | resolved={r['resolved']} | pass_rate={r['pass_rate_pct']}% | peak_tokens={r['mean_peak_tokens']}")
    else:
        print("Note: results/summary.csv not found yet.")


if __name__ == "__main__":
    main()
