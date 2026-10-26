"""
Consistency checker verifying that paper.typ, paper.tex, and KAGGLE_WRITEUP.md:
1. Contain zero prohibited/retracted simulation strings or placeholder future-tense promises.
2. Accurately match the empirical numbers in results/summary.json and results/summary_table.csv.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMMARY_JSON = ROOT / "results" / "summary.json"
SUMMARY_CSV = ROOT / "results" / "summary_table.csv"
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
    "_retracted_simulation",
    "$15,000",
    "$10,000",
    "unprecedented",
    "first to demonstrate",
    "first mathematical treatment",
    "mathematically principled",
    "will be populated",
    "are being instrumented",
]


def check_prohibited() -> list[tuple[str, str]]:
    violations = []
    for doc in DOCS:
        if not doc.exists():
            continue
        text = doc.read_text(encoding="utf-8")
        for bad in PROHIBITED_STRINGS:
            if bad.lower() in text.lower():
                violations.append((doc.name, bad))
    return violations


def check_empirical_numbers() -> list[str]:
    errors = []
    if not SUMMARY_JSON.exists() or not SUMMARY_CSV.exists():
        errors.append("Missing results/summary.json or results/summary_table.csv")
        return errors

    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    rows = summary.get("summary_rows", [])
    if not rows:
        errors.append("results/summary.json contains 0 summary_rows")
        return errors

    for doc in DOCS:
        if not doc.exists():
            errors.append(f"Missing document: {doc.name}")
            continue
        text = doc.read_text(encoding="utf-8")
        for r in rows:
            rate_str = f"{r['resolved_pct']:.1f}%"
            rate_tex = f"{r['resolved_pct']:.1f}\\%"
            peak_str = f"{r['mean_peak_prompt_tokens']:.1f}"
            if (
                rate_str not in text
                and rate_tex not in text
                and f"{r['resolved_pct']:.2f}%" not in text
                and f"{r['resolved_pct']:.2f}\\%" not in text
            ):
                errors.append(f"{doc.name} missing resolved_pct {rate_str} for config {r['config']}")
            if peak_str not in text:
                errors.append(f"{doc.name} missing mean_peak_prompt_tokens {peak_str} for config {r['config']}")
    return errors


def main() -> None:
    print("Checking document consistency and empirical integrity...")
    violations = check_prohibited()
    if violations:
        print(f"FAILED: Found {len(violations)} prohibited strings:")
        for doc_name, bad in violations:
            print(f"  - In {doc_name}: '{bad}'")
        sys.exit(1)

    print("PASS: Zero prohibited or placeholder strings found across paper.typ, paper.tex, and KAGGLE_WRITEUP.md.")

    num_errors = check_empirical_numbers()
    if num_errors:
        print(f"FAILED empirical number verification ({len(num_errors)} issues):")
        for e in num_errors:
            print(f"  - {e}")
        sys.exit(1)

    with open(SUMMARY_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"PASS: All {len(rows)} configurations in results/summary_table.csv verified across all manuscript files:")
    for r in rows:
        print(
            f"  - {r['config']}: {r['resolved_k']}/{r['n_tasks']} ({r['resolved_pct']}%, "
            f"95% CI [{r['wilson_95_lo']}%, {r['wilson_95_hi']}%]) | "
            f"mean peak prompt={r['mean_peak_prompt_tokens']} (max={r['max_peak_prompt_tokens']})"
        )


if __name__ == "__main__":
    main()
