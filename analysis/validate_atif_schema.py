"""
analysis/validate_atif_schema.py: Dual-mode schema validation for ATIF-Gemma traces.
1. Concrete Repository Schema: Validates 100% of traces against dataset_resource/atif_schema_v1_7.json.
2. Upstream Specification Interoperability: Audits conformance to standard upstream ATIF v1.7 fields,
   verifying reasoning representation (message + extra.event_type: "thinking") and tool call structures.
"""

import json
from pathlib import Path
import jsonschema

ROOT = Path(r"d:\AI Research\gemma_paper")
SCHEMA_PATH = ROOT / "dataset_resource" / "atif_schema_v1_7.json"
TRACES_DIR = ROOT / "dataset_resource" / "traces"

# Upstream standard ATIF v1.7 reference schema (Draft-07)
UPSTREAM_ATIF_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Upstream ATIF v1.7 Interoperability Schema",
    "type": "object",
    "required": ["schema_version", "agent", "steps", "final_metrics"],
    "properties": {
        "schema_version": {"type": "string"},
        "agent": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "model_name": {"type": "string"}
            }
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["step_id", "source"],
                "properties": {
                    "step_id": {"type": "integer"},
                    "source": {"type": "string", "enum": ["system", "user", "agent"]},
                    "message": {"type": "string"},
                    "reasoning_content": {"type": ["string", "null"]},
                    "tool_calls": {"type": "array"},
                    "observation": {"type": "object"},
                    "metrics": {"type": "object"},
                    "extra": {"type": "object"}
                }
            }
        },
        "final_metrics": {
            "type": "object",
            "required": ["total_tokens", "total_prompt_tokens", "total_completion_tokens"],
            "properties": {
                "total_tokens": {"type": "integer"},
                "total_prompt_tokens": {"type": "integer"},
                "total_completion_tokens": {"type": "integer"},
                "total_steps": {"type": "integer"},
                "total_duration_seconds": {"type": "number"}
            }
        }
    }
}

def main():
    concrete_schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    traces = sorted(list(TRACES_DIR.glob("*.json")))
    assert len(traces) == 112, f"Expected 112 traces, found {len(traces)}"
    
    concrete_passed = 0
    upstream_passed = 0
    reasoning_steps_found = 0
    total_steps_audited = 0
    
    for t in traces:
        data = json.loads(t.read_text(encoding="utf-8"))
        
        # 1. Concrete schema validation
        jsonschema.validate(instance=data, schema=concrete_schema)
        concrete_passed += 1
        
        # 2. Upstream schema interoperability validation
        # Map extra.event_type == 'thinking' to upstream reasoning_content representation
        upstream_data = json.loads(json.dumps(data))
        for step in upstream_data.get("steps", []):
            total_steps_audited += 1
            extra = step.get("extra", {})
            if extra.get("event_type") == "thinking":
                step["reasoning_content"] = step.get("message", "")
                reasoning_steps_found += 1
            else:
                step["reasoning_content"] = None
                
        jsonschema.validate(instance=upstream_data, schema=UPSTREAM_ATIF_SCHEMA)
        upstream_passed += 1
            
    print("=" * 65)
    print("  DUAL ATIF v1.7 SCHEMA VALIDATION & INTEROPERABILITY REPORT")
    print("=" * 65)
    print(f"Total Traces Evaluated: {len(traces)}")
    print(f"Concrete Repository Schema Pass: {concrete_passed} / {len(traces)} (100.0%)")
    print(f"Upstream ATIF v1.7 Interoperability Pass: {upstream_passed} / {len(traces)} (100.0%)")
    print(f"Total Steps Audited: {total_steps_audited}")
    print(f"Deliberative Reasoning Turns Verified: {reasoning_steps_found}")
    print("=" * 65)
    
    out_report = {
        "total_traces": len(traces),
        "concrete_schema_passed": concrete_passed,
        "concrete_schema_pass_rate_pct": 100.0,
        "upstream_atif_interoperability_passed": upstream_passed,
        "upstream_atif_pass_rate_pct": 100.0,
        "total_steps_audited": total_steps_audited,
        "deliberative_reasoning_steps": reasoning_steps_found,
        "provenance_mapping": {
            "model_reasoning_field": "message (with extra.event_type == 'thinking')",
            "upstream_standard_field": "reasoning_content",
            "extensions_storage": "extra block (timestamp, elapsed_s, author)"
        }
    }
    (ROOT / "results" / "schema_validation_report.json").write_text(json.dumps(out_report, indent=2), encoding="utf-8")
    print("Report written to results/schema_validation_report.json")

if __name__ == "__main__":
    main()
