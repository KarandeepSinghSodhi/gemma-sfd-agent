import json
from pathlib import Path

def inspect_nb(path: Path):
    print("=" * 60)
    print(f"FILE: {path.name}")
    print("=" * 60)
    nb = json.loads(path.read_text(encoding="utf-8"))
    for i, c in enumerate(nb.get("cells", [])):
        src = "".join(c.get("source", []))
        cell_type = c.get("cell_type", "")
        keywords = ["MODEL_NAME", "agent.yaml", "sampling.yaml", "eval_config", "tools:", "SequentialAgent", "LlmAgent"]
        if any(kw in src for kw in keywords):
            print(f"\n--- Cell {i} [{cell_type}] ---")
            lines = src.splitlines()
            for line in lines[:40]:
                print("  ", line)
            if len(lines) > 40:
                print(f"   ... [{len(lines) - 40} more lines]")

inspect_nb(Path(r"d:\AI Research\gemma_paper\benchmarks_ref\lb_024\gemma-4-baseline-lb-0-24.ipynb"))
inspect_nb(Path(r"d:\AI Research\gemma_paper\benchmarks_ref\flexonafft\gemma-4-budget-aware-coding-agent-v2.ipynb"))
