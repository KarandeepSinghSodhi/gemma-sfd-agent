import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def inspect_flips():
    paths = [
        ("rich_4077_flat_controlled_orig", ROOT / "traces/eval_results/flat_controlled/traces/trace_rich_4077.json"),
        ("rich_4077_flat_controlled_rerun", ROOT / "traces/rerun_results/eval_results/flat_controlled_rerun/traces/trace_rich_4077.json"),
        ("fastapi_15588_sfd_orig", ROOT / "traces/eval_results/sfd/traces/trace_fastapi_15588.json"),
        ("fastapi_15588_sfd_rerun", ROOT / "traces/rerun_results/eval_results/sfd_rerun/traces/trace_fastapi_15588.json"),
    ]
    for label, p in paths:
        print("=" * 60)
        print(label, "Exists:", p.exists())
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        print(f"Total steps: {len(d.get('steps', []))}")
        print(f"Final metrics: {d.get('final_metrics')}")
        file_edits = []
        for s_idx, s in enumerate(d.get("steps", [])):
            for tc in s.get("tool_calls", []):
                fn = tc.get("function_name")
                args = tc.get("arguments", {})
                if fn in ("write_file", "edit_file", "submit_patch"):
                    file_edits.append((s_idx, fn, args))
        print(f"File edits ({len(file_edits)}):")
        for s_idx, fn, args in file_edits:
            print(f"  Step {s_idx}: {fn} {list(args.keys())}")
            if "patch" in args:
                print(f"    patch len: {len(args['patch'])}")
            if "filepath" in args or "path" in args or "file_path" in args:
                fp = args.get("filepath") or args.get("path") or args.get("file_path")
                print(f"    file: {fp}")

if __name__ == "__main__":
    inspect_flips()
