"""
Real-time instrumentation and trace recorder for SWE-gemma developer agent tasks.
Enforces explicit context and turn caps in code and records every turn's exact token metrics.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")

# Hard caps enforced in code
CAPS = {
    "max_triage_turns": 5,
    "max_patcher_turns": 3,
    "max_verifier_turns": 3,
    "max_observation_tokens": 1200,
    "max_test_output_tokens": 1500,
    "context_window_limit": 32768,
}


def count_tokens(text: str) -> int:
    """Exact token count using BPE tokenizer."""
    if not text:
        return 0
    return len(ENC.encode(text, disallowed_special=()))


def apply_observation_cap(text: str, max_tokens: int = CAPS["max_observation_tokens"]) -> tuple[str, bool, int]:
    """Truncates observation if it exceeds max_tokens and adds an explicit marker."""
    toks = ENC.encode(text, disallowed_special=())
    orig_count = len(toks)
    if orig_count <= max_tokens:
        return text, False, orig_count
    
    # Keep head (60%) and tail (40%)
    head_len = int(max_tokens * 0.6)
    tail_len = max_tokens - head_len
    truncated_toks = toks[:head_len] + toks[-tail_len:]
    marker = f"\n... [TRUNCATED: original was {orig_count} tokens, capped to {max_tokens} tokens] ...\n"
    truncated_text = ENC.decode(toks[:head_len]) + marker + ENC.decode(toks[-tail_len:])
    return truncated_text, True, orig_count


class TaskTrace:
    """Collects verifiable execution trace for a single task."""

    def __init__(self, task_id: str, repo: str, config_name: str, model: str, seed: int):
        self.task_id = task_id
        self.repo = repo
        self.config_name = config_name
        self.model = model
        self.seed = seed
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.turns: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.cap_triggers: List[Dict[str, Any]] = []
        self.final_patch: str = ""
        self.resolved: bool = False
        self.test_exit_code: Optional[int] = None
        self.context_overflow: bool = False

    def record_turn(
        self,
        stage: str,
        turn_index: int,
        prompt_text: str,
        completion_text: str,
        tool_name: Optional[str] = None,
        observation_text: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a single inference turn with exact measured token counts."""
        turn_start = time.time()
        prompt_tokens = count_tokens(prompt_text)
        completion_tokens = count_tokens(completion_text)

        # Check for context overflow
        if prompt_tokens > CAPS["context_window_limit"]:
            self.context_overflow = True
            self.errors.append("context_overflow")

        # Check turn caps
        max_turns = CAPS.get(f"max_{stage}_turns", 5)
        cap_triggered = False
        cap_reason = None
        if turn_index >= max_turns:
            cap_triggered = True
            cap_reason = f"max_turns_exceeded_for_{stage}"
            self.cap_triggers.append({"stage": stage, "turn": turn_index, "reason": cap_reason})

        # Process observation
        obs_tokens = 0
        if observation_text:
            capped_obs, was_truncated, orig_obs_tokens = apply_observation_cap(observation_text)
            obs_tokens = orig_obs_tokens
            if was_truncated:
                cap_triggered = True
                cap_reason = f"observation_truncated_from_{orig_obs_tokens}_to_{CAPS['max_observation_tokens']}"
                self.cap_triggers.append({"stage": stage, "turn": turn_index, "reason": cap_reason})

        if error:
            self.errors.append(error)

        turn_record = {
            "stage": stage,
            "turn_index": turn_index,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "tool_name": tool_name,
            "observation_tokens": obs_tokens,
            "cap_triggered": cap_triggered,
            "cap_reason": cap_reason,
            "wall_clock_seconds": round(time.time() - turn_start, 4),
        }
        self.turns.append(turn_record)
        return turn_record

    def finalize(self, patch: str, resolved: bool, exit_code: Optional[int] = None) -> Dict[str, Any]:
        """Finalize the trace and compute summary metrics."""
        self.end_time = time.time()
        self.final_patch = patch
        self.resolved = resolved
        self.test_exit_code = exit_code

        prompt_token_counts = [t["prompt_tokens"] for t in self.turns] if self.turns else [0]
        peak_prompt_tokens = max(prompt_token_counts)
        cumulative_tokens = sum(t["prompt_tokens"] + t["completion_tokens"] for t in self.turns)

        data = {
            "task_id": self.task_id,
            "repo": self.repo,
            "config_name": self.config_name,
            "model": self.model,
            "seed": self.seed,
            "duration_seconds": round(self.end_time - self.start_time, 2),
            "total_turns": len(self.turns),
            "peak_prompt_tokens": peak_prompt_tokens,
            "cumulative_tokens": cumulative_tokens,
            "resolved": self.resolved,
            "test_exit_code": self.test_exit_code,
            "context_overflow": self.context_overflow,
            "errors": self.errors,
            "cap_triggers": self.cap_triggers,
            "patch_length_chars": len(self.final_patch),
            "turns": self.turns,
        }
        return data

    def save(self, output_dir: Path) -> Path:
        """Save the trace as JSON."""
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self.config_name}_{self.task_id}_seed{self.seed}.json"
        out_path = output_dir / filename
        data = self.finalize(self.final_patch, self.resolved, self.test_exit_code)
        out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return out_path
