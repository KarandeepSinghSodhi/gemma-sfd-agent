import json
from pathlib import Path

p = Path("dataset_resource/traces")
traces = list(p.glob("*.json"))
print(f"Total traces found: {len(traces)}")

sample = json.loads(traces[0].read_text(encoding="utf-8"))
print("Trace root keys:", list(sample.keys()))
print("Schema version in trace:", sample.get("schema_version"))
print("Number of steps in sample:", len(sample.get("steps", [])))

all_step_keys = set()
for t in traces:
    data = json.loads(t.read_text(encoding="utf-8"))
    for s in data.get("steps", []):
        all_step_keys.update(s.keys())

print("All step keys observed across all 112 traces:", sorted(all_step_keys))

for i, s in enumerate(sample.get("steps", [])[:5]):
    print(f"Step {i} (source={s.get('source')}): keys={list(s.keys())}")
    if "thought" in s:
        print(f"  thought: len={len(s['thought'])}")
    if "reasoning_content" in s:
        print(f"  reasoning_content: len={len(s['reasoning_content'])}")
    if "message" in s and isinstance(s["message"], str):
        print(f"  message: len={len(s['message'])}, sample={s['message'][:60]!r}")
    if "tool_calls" in s:
        print(f"  tool_calls count: {len(s['tool_calls'])}")
    if "observation" in s:
        print(f"  observation keys: {list(s['observation'].keys())}")
    if "metrics" in s:
        print(f"  metrics: {s['metrics']}")
