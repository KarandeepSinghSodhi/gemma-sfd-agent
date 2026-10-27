"""
ATIF v1.7 Trace Parser and Quantitative Corpus Auditor.
"""
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Union

def parse_trace_file(trace_path: Union[str, Path]) -> Dict[str, Any]:
    """Parse a single ATIF v1.7 JSON trace file and extract step-by-step metrics."""
    path = Path(trace_path)
    if not path.is_file():
        raise FileNotFoundError(f"Trace file does not exist: {path}")
    
    data = json.loads(path.read_text(encoding="utf-8"))
    steps = data.get("steps", [])
    
    prompt_tokens: List[int] = []
    completion_tokens: List[int] = []
    total_tokens: List[int] = []
    tool_names: List[str] = []
    edit_file_errors = 0
    budget_errors = 0
    
    for step in steps:
        metrics = step.get("metrics")
        if isinstance(metrics, dict) and "prompt_tokens" in metrics:
            pt = int(metrics.get("prompt_tokens", 0))
            ct = int(metrics.get("completion_tokens", 0))
            prompt_tokens.append(pt)
            completion_tokens.append(ct)
            total_tokens.append(pt + ct)
            
        for tc in step.get("tool_calls", []) or []:
            fn = tc.get("function_name")
            if fn:
                tool_names.append(fn)
                
        obs = step.get("observation") or {}
        obs_c = obs.get("content", "") if isinstance(obs, dict) else ""
        if obs_c and isinstance(obs_c, str):
            if "FileEditError" in obs_c or "could not find old_string" in obs_c.lower():
                edit_file_errors += 1
            if "budget exceeded" in obs_c.lower() or "maximum tool calls" in obs_c.lower():
                budget_errors += 1
                
    peak_prompt = max(prompt_tokens) if prompt_tokens else 0
    cum_prompt = sum(prompt_tokens)
    cum_completion = sum(completion_tokens)
    
    return {
        "trace_file": path.name,
        "llm_calls": len(prompt_tokens),
        "total_tool_calls": len(tool_names),
        "tool_names": tool_names,
        "peak_prompt_tokens": peak_prompt,
        "cumulative_prompt_tokens": cum_prompt,
        "cumulative_completion_tokens": cum_completion,
        "cumulative_total_tokens": cum_prompt + cum_completion,
        "edit_file_errors": edit_file_errors,
        "budget_errors": budget_errors,
    }

def audit_corpus(traces_dir: Union[str, Path]) -> Dict[str, Any]:
    """Scan a directory of ATIF v1.7 trace files and compute corpus-wide summary statistics."""
    root = Path(traces_dir)
    trace_files = [f for f in root.rglob("*.json") if not f.name.endswith(("-metadata.json", "schema.json"))]
    
    parsed = [parse_trace_file(f) for f in trace_files]
    
    total_llm = sum(p["llm_calls"] for p in parsed)
    total_tools = sum(p["total_tool_calls"] for p in parsed)
    total_prompt = sum(p["cumulative_prompt_tokens"] for p in parsed)
    total_completion = sum(p["cumulative_completion_tokens"] for p in parsed)
    total_edits_err = sum(p["edit_file_errors"] for p in parsed)
    total_budget_err = sum(p["budget_errors"] for p in parsed)
    
    tool_counts = defaultdict(int)
    for p in parsed:
        for t in p["tool_names"]:
            tool_counts[t] += 1
            
    return {
        "num_traces": len(parsed),
        "total_llm_turns": total_llm,
        "total_tool_calls": total_tools,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_tokens": total_prompt + total_completion,
        "tool_distribution": dict(tool_counts),
        "edit_file_errors": total_edits_err,
        "budget_errors": total_budget_err,
    }
