from pathlib import Path
import json

transcript_path = Path(r"C:\Users\karan\.gemini\antigravity\brain\058bf272-78bf-42b6-a0f1-8e60051e558b\.system_generated\logs\transcript.jsonl")
if transcript_path.exists():
    for line in transcript_path.read_text(encoding="utf-8").splitlines():
        if "writeup" in line.lower() or "53116" in line:
            obj = json.loads(line)
            c = str(obj.get("content", ""))[:200].replace("\n", " ")
            print(f"Step {obj.get('step_index')}: {c}")
