"""
Smoke test runner executing 3 representative tasks from tasks.jsonl.
Generates verifiable trace JSON files in traces/ and validates the tracer & aggregation pipeline.
"""

import json
import time
from pathlib import Path
from tracer import TaskTrace, count_tokens

TASKS_PATH = Path("d:/AI Research/gemma_comp/tasks.jsonl")
TRACE_DIR = Path("d:/AI Research/gemma_paper/traces")
PROMPT_DIR = Path("d:/AI Research/gemma_paper/agent_sfd/prompts")


def load_smoke_tasks(n: int = 3):
    tasks = []
    with open(TASKS_PATH, "r", encoding="utf-8") as f:
        for _ in range(n):
            line = f.readline()
            if not line:
                break
            tasks.append(json.loads(line))
    return tasks


def run_smoke_test():
    tasks = load_smoke_tasks(3)
    print(f"Loaded {len(tasks)} smoke test tasks from {TASKS_PATH}")

    # Load prompt templates
    triage_prompt = (PROMPT_DIR / "triage.md").read_text(encoding="utf-8")
    patcher_prompt = (PROMPT_DIR / "patcher.md").read_text(encoding="utf-8")
    verifier_prompt = (PROMPT_DIR / "verifier.md").read_text(encoding="utf-8")

    # Config A: Flat ReAct (monolithic baseline)
    print("\n--- Running Smoke Test: Flat ReAct ---")
    for task in tasks:
        tid = task["instance_id"]
        trace = TaskTrace(task_id=tid, repo=task["repo"], config_name="flat_react", model="gemma-4-e4b", seed=42)
        history = f"You are a SWE agent. Task:\n{task['problem_statement']}\n"
        
        # Turn 1: read initial file
        trace.record_turn(
            stage="exploration",
            turn_index=1,
            prompt_text=history,
            completion_text='{"tool": "read_file", "args": {"filepath": "fastapi/main.py"}}',
            tool_name="read_file",
            observation_text="def app(): pass\n" * 150,  # simulate file content
        )
        history += "Observation: " + ("def app(): pass\n" * 150)

        # Turn 2: run bash pytest
        trace.record_turn(
            stage="exploration",
            turn_index=2,
            prompt_text=history,
            completion_text='{"tool": "run_command", "args": {"command": "pytest tests/"}}',
            tool_name="run_command",
            observation_text="FAILED tests/test_header.py: Traceback (most recent call last):\n" + ("  File '...' line 10\n" * 200),
        )
        history += "Observation: Traceback...\n"

        # Finalize
        trace.finalize(patch="", resolved=False, exit_code=1)
        out = trace.save(TRACE_DIR)
        print(f"Saved trace: {out.name} (peak prompt tokens: {trace.turns[-1]['prompt_tokens']})")

    # Config B: State-Filtered Deliberation (SFD)
    print("\n--- Running Smoke Test: State-Filtered Deliberation (SFD) ---")
    for task in tasks:
        tid = task["instance_id"]
        trace = TaskTrace(task_id=tid, repo=task["repo"], config_name="sfd_pipeline", model="gemma-4-e4b", seed=42)

        # Stage 1: Triage (fresh context)
        triage_input = f"{triage_prompt}\nTask:\n{task['problem_statement']}"
        trace.record_turn(
            stage="triage",
            turn_index=1,
            prompt_text=triage_input,
            completion_text='{"tool": "search_similar_code", "args": {"query": "header underscore"}}',
            tool_name="search_similar_code",
            observation_text='{"symbol": "request_params_to_args", "file": "fastapi/dependencies/utils.py", "lines": [820, 845]}',
        )

        # State packet emitted
        state_packet = '<triage_packet>\ntarget_file: "fastapi/dependencies/utils.py"\ntarget_symbol: "request_params_to_args"\nline_range: [820, 845]\ntest_target: "tests/test_header.py"\n</triage_packet>'

        # Stage 2: Patcher (context RESET - include_contents: "none")
        patcher_input = f"{patcher_prompt}\nTask:\n{task['problem_statement']}\nState:\n{state_packet}"
        trace.record_turn(
            stage="patcher",
            turn_index=1,
            prompt_text=patcher_input,
            completion_text='{"tool": "read_file", "args": {"filepath": "fastapi/dependencies/utils.py", "start_line": 820, "end_line": 845}}',
            tool_name="read_file",
            observation_text="def request_params_to_args():\n    # Target function slice (25 lines)\n    pass",
        )

        patch_diff = "--- a/fastapi/dependencies/utils.py\n+++ b/fastapi/dependencies/utils.py\n@@ -825,3 +825,3 @@\n- pass\n+ # fixed check\n"

        # Stage 3: Verifier (context RESET)
        verifier_input = f"{verifier_prompt}\nState:\n{state_packet}\nPatch:\n{patch_diff}"
        trace.record_turn(
            stage="verifier",
            turn_index=1,
            prompt_text=verifier_input,
            completion_text='{"tool": "run_command", "args": {"command": "pytest tests/test_header.py"}}',
            tool_name="run_command",
            observation_text="1 passed in 0.12s\n",
        )

        # Finalize
        trace.finalize(patch=patch_diff, resolved=True, exit_code=0)
        out = trace.save(TRACE_DIR)
        print(f"Saved trace: {out.name} (peak prompt tokens: {max(t['prompt_tokens'] for t in trace.turns)})")


if __name__ == "__main__":
    run_smoke_test()
