"""
analysis/validate_atif_schema.py: Formal schema validation and specification audit for ATIF-Gemma traces.

Validates all 112 multi-turn execution traces against the version-pinned ATIF v1.7 specification
(Harbor Framework Contributors, 2026; https://github.com/harbor-framework/harbor) using the formal
Draft 2020-12 / Draft-07 JSON Schema at dataset_resource/atif_schema_v1_7.json.
"""

from __future__ import annotations

import json
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "dataset_resource" / "atif_schema_v1_7.json"
TRACES_DIR = ROOT / "dataset_resource" / "traces"
REPORT_PATH = ROOT / "results" / "schema_validation_report.json"


def main():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    traces = sorted(list(TRACES_DIR.glob("*.json")))
    assert len(traces) == 112, f"Expected 112 traces, found {len(traces)}"

    passed_count = 0
    total_steps_audited = 0
    deliberative_reasoning_steps = 0
    tool_calls_audited = 0
    v1_7_extra_metadata_verified = 0

    for t in traces:
        data = json.loads(t.read_text(encoding="utf-8"))

        # 1. Formal JSON Schema Validation
        jsonschema.validate(instance=data, schema=schema)
        passed_count += 1

        # 2. Specification Audit: ATIF v1.7 Core Properties
        assert data.get("schema_version") in ("ATIF-v1.7", "1.7", "v1.7"), (
            f"Invalid schema_version in {t.name}: {data.get('schema_version')}"
        )
        assert "agent" in data and "name" in data["agent"], f"Missing agent block in {t.name}"
        assert "final_metrics" in data, f"Missing final_metrics in {t.name}"

        steps = data.get("steps", [])
        for step in steps:
            total_steps_audited += 1
            assert "step_id" in step, f"Missing step_id in {t.name} step {step}"
            assert "source" in step, f"Missing source in {t.name} step {step}"

            extra = step.get("extra", {})
            if extra.get("event_type") == "thinking":
                deliberative_reasoning_steps += 1

            for tc in step.get("tool_calls", []):
                tool_calls_audited += 1
                assert "function_name" in tc, f"Missing function_name in {t.name} tool call"
                assert "arguments" in tc, f"Missing arguments in {t.name} tool call"
                if "extra" in tc:
                    v1_7_extra_metadata_verified += 1

            obs = step.get("observation", {})
            if isinstance(obs, dict) and "extra" in obs:
                v1_7_extra_metadata_verified += 1

    print("=" * 70)
    print("  ATIF v1.7 FORMAL SCHEMA VALIDATION & SPECIFICATION AUDIT")
    print("=" * 70)
    print(f"Specification: Harbor ATIF v1.7 (Harbor Framework Contributors, 2026)")
    print(f"Schema File:   dataset_resource/atif_schema_v1_7.json")
    print(f"Traces Evaluated:           {len(traces)}")
    print(f"Formal Schema Validation:   {passed_count} / {len(traces)} (100.0% PASS)")
    print(f"Total Steps Audited:        {total_steps_audited}")
    print(f"Deliberative Reasoning:     {deliberative_reasoning_steps} turns")
    print(f"Tool Calls Audited:         {tool_calls_audited}")
    print(f"v1.7 Extra Metadata Blocks: {v1_7_extra_metadata_verified}")
    print("=" * 70)

    report = {
        "specification": "Harbor ATIF Specification v1.7 (Harbor Framework Contributors, 2026)",
        "specification_url": "https://github.com/harbor-framework/harbor",
        "pinned_version": "ATIF-v1.7",
        "schema_path": "dataset_resource/atif_schema_v1_7.json",
        "total_traces": len(traces),
        "schema_passed": passed_count,
        "schema_pass_rate_pct": 100.0,
        "total_steps_audited": total_steps_audited,
        "deliberative_reasoning_steps": deliberative_reasoning_steps,
        "tool_calls_audited": tool_calls_audited,
        "v1_7_extra_metadata_verified": v1_7_extra_metadata_verified,
        "provenance_structure": {
            "model_reasoning_field": "message (with extra.event_type == 'thinking')",
            "extensions_storage": "extra block on tool_calls, observations, and steps"
        }
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report successfully saved to {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
