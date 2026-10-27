"""
analysis/validate_atif_schema.py: Validates all 112 ATIF trace files against the ATIF v1.7 JSON Schema.
"""

import json
from pathlib import Path
import jsonschema

ROOT = Path(r"d:\AI Research\gemma_paper")
SCHEMA_PATH = ROOT / "dataset_resource" / "atif_schema_v1_7.json"
TRACES_DIR = ROOT / "dataset_resource" / "traces"

def main():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    traces = sorted(list(TRACES_DIR.glob("*.json")))
    assert len(traces) == 112, f"Expected 112 traces, found {len(traces)}"
    
    passed = 0
    failed = 0
    errors = []
    
    for t in traces:
        data = json.loads(t.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(instance=data, schema=schema)
            passed += 1
        except jsonschema.ValidationError as e:
            failed += 1
            errors.append(f"{t.name}: {e.message}")
            
    print("=" * 60)
    print("  ATIF v1.7 SCHEMA VALIDATION REPORT")
    print("=" * 60)
    print(f"Total Traces Validated: {len(traces)}")
    print(f"Passed Schema Validation: {passed} / {len(traces)} ({passed/len(traces)*100:.1f}%)")
    print(f"Failed Schema Validation: {failed}")
    if errors:
        for err in errors[:5]:
            print(f"  [ERROR] {err}")
    print("=" * 60)
    
    out_report = {
        "total_traces": len(traces),
        "passed": passed,
        "failed": failed,
        "validation_rate_pct": round(passed / len(traces) * 100, 1),
        "schema_version": schema["properties"]["schema_version"]["enum"]
    }
    (ROOT / "results" / "schema_validation_report.json").write_text(json.dumps(out_report, indent=2), encoding="utf-8")
    assert failed == 0, f"Schema validation failed on {failed} traces"

if __name__ == "__main__":
    main()
