import ast
import json
from pathlib import Path

DOCKER_IMAGE = "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
MACHINE_SHAPE = "NvidiaL4"

cell1_env = """import glob
import importlib
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

os.environ['TRANSFORMERS_NO_TF'] = '1'
os.environ['TRANSFORMERS_NO_FLAX'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['VLLM_NO_USAGE_STATS'] = '1'
os.environ['VLLM_WORKER_MULTIPROC_METHOD'] = 'spawn'
os.environ['VLLM_ENGINE_READY_TIMEOUT_S'] = '1200'
os.environ['VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS'] = '1'
os.environ['NCCL_DEBUG'] = 'WARN'
os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'True'
os.environ['LITELLM_TELEMETRY'] = 'False'
os.environ['LITELLM_LOG'] = 'WARNING'
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'EMPTY')
os.environ['LOCAL_API_KEY'] = os.environ.get('LOCAL_API_KEY', 'EMPTY')
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
os.environ['OTEL_SDK_DISABLED'] = 'true'
os.environ['OTEL_PYTHON_DISABLED'] = 'true'

def configure_logging() -> None:
    for name in (
        'LiteLLM', 'LiteLLM Router', 'LiteLLM Proxy', 'litellm',
        'httpx', 'httpcore', 'openai', 'urllib3',
        'opentelemetry', 'opentelemetry.context',
    ):
        lg = logging.getLogger(name)
        lg.setLevel(logging.WARNING)
        if 'litellm' in name.lower():
            lg.propagate = False
            lg.handlers.clear()

configure_logging()

# Locate wheelhouse directory whether mounted at /kaggle/input/datasets/metric/... or /kaggle/input/...
WHEELHOUSE_CANDIDATES = [
    Path('/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse'),
    Path('/kaggle/input/gemma-4-developer-agent-wheelhouse'),
]
WHEELHOUSE_DIR = next((p for p in WHEELHOUSE_CANDIDATES if p.exists() and list(p.glob('*.whl'))), None)
if WHEELHOUSE_DIR is None:
    for p in Path('/kaggle/input').rglob('adk_submission*.whl'):
        WHEELHOUSE_DIR = p.parent
        break
assert WHEELHOUSE_DIR is not None, f'Could not find wheelhouse under /kaggle/input: {list(Path(\"/kaggle/input\").rglob(\"*\"))[:30]}'

for pth_pattern in (
    '/usr/local/lib/python*/dist-packages/*cutlass*.pth',
    '/usr/local/lib/python*/site-packages/*cutlass*.pth',
):
    for pth in glob.glob(pth_pattern):
        try:
            os.unlink(pth)
        except OSError:
            pass

tmp_whl = Path('/tmp/wheelhouse')
tmp_whl.mkdir(parents=True, exist_ok=True)
for w in WHEELHOUSE_DIR.glob('*.whl'):
    if 'cutlass' in w.name.lower():
        continue
    target_name = (
        w.name.replace('cu128', '+cu128')
        if ('cu128' in w.name and '+' not in w.name)
        else w.name
    )
    target = tmp_whl / target_name
    if not target.exists():
        try:
            os.symlink(w, target)
        except OSError:
            shutil.copyfile(w, target)

wheels = sorted(str(w) for w in tmp_whl.glob('*.whl'))
print(f'Installing {len(wheels)} wheels from {WHEELHOUSE_DIR} (Python {sys.version.split()[0]})...')
subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '-q', '--no-deps', '--force-reinstall', *wheels],
    check=True,
)
importlib.invalidate_caches()
configure_logging()
print('Wheelhouse installation complete.')
"""

cell2_configs = """import re
import zipfile
from adk_submission import validate_directory
from adk_submission.discovery import discover_declared_models
from swegemma.config import ALLOWED_SUBMISSION_EXTENSIONS, MAX_SUBMISSION_SIZE_BYTES, build_submission_limits
from swegemma.models import load_tasks

DATA_CANDIDATES = [
    Path('/kaggle/input/competitions/gemma-4-developer-agent'),
    Path('/kaggle/input/gemma-4-developer-agent'),
]
DATA_DIR = next((p for p in DATA_CANDIDATES if (p / 'tasks.jsonl').exists()), None)
if DATA_DIR is None:
    for p in Path('/kaggle/input').rglob('tasks.jsonl'):
        DATA_DIR = p.parent
        break
assert DATA_DIR is not None, 'Could not find tasks.jsonl in /kaggle/input'

WORKING_DIR = Path('/kaggle/working')
WORKING_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = 'gemma-4-e4b-it-qat-w4a16-ct'
limits, gen_constraints = build_submission_limits()

SAMPLING_YAML = '''temperature: 0.0
seed: 42
max_output_tokens: 8192
thinking_config:
  include_thoughts: true
  thinking_budget: 1536
'''

EVAL_CONFIG_YAML = '''evaluation:
  timeout_seconds: 60
  max_tool_calls: 15
  max_time_minutes: 2.5
  max_turns: 20
'''

# 1. Build flat_starter (Official Starter Kit on E4B with controlled sampling & eval_config)
FLAT_STARTER_DIR = WORKING_DIR / 'sub_flat_starter'
if FLAT_STARTER_DIR.exists():
    shutil.rmtree(FLAT_STARTER_DIR)
shutil.copytree(DATA_DIR / 'sample_submission', FLAT_STARTER_DIR)
for yaml_path in [FLAT_STARTER_DIR / 'agent.yaml', *sorted((FLAT_STARTER_DIR / 'sub_agents').glob('*.yaml'))]:
    if yaml_path.is_file():
        text = yaml_path.read_text(encoding='utf-8')
        text = re.sub(r'^(\\s*model:\\s*).*$', rf'\\g<1>{MODEL_NAME}', text, flags=re.MULTILINE)
        text = re.sub(r'^\\s*adapter:\\s*.*\\n?', '', text, flags=re.MULTILINE)
        yaml_path.write_text(text, encoding='utf-8')
shutil.rmtree(FLAT_STARTER_DIR / 'adapters', ignore_errors=True)
(FLAT_STARTER_DIR / 'configs' / 'sampling.yaml').write_text(SAMPLING_YAML, encoding='utf-8')
(FLAT_STARTER_DIR / 'eval_config.yaml').write_text(EVAL_CONFIG_YAML, encoding='utf-8')
validate_directory(FLAT_STARTER_DIR, limits=limits)
print('Validated sub_flat_starter:', discover_declared_models(FLAT_STARTER_DIR))

# 2. Build sfd (3-Stage SequentialAgent: TriageAgent -> PatchAgent -> VerifierAgent)
SFD_DIR = WORKING_DIR / 'sub_sfd'
if SFD_DIR.exists():
    shutil.rmtree(SFD_DIR)
for sub in ('configs', 'prompts', 'sub_agents'):
    (SFD_DIR / sub).mkdir(parents=True, exist_ok=True)

(SFD_DIR / 'configs' / 'sampling.yaml').write_text(SAMPLING_YAML, encoding='utf-8')
(SFD_DIR / 'eval_config.yaml').write_text(EVAL_CONFIG_YAML, encoding='utf-8')

SFD_AGENT_YAML = '''agent_class: SequentialAgent
name: sfd_sequential_pipeline
description: State-Filtered Deliberation 3-stage pipeline (Triage -> Patch -> Verify)
sub_agents:
  - config_path: sub_agents/triage_agent.yaml
  - config_path: sub_agents/patch_agent.yaml
  - config_path: sub_agents/verifier_agent.yaml
'''
(SFD_DIR / 'agent.yaml').write_text(SFD_AGENT_YAML, encoding='utf-8')

TRIAGE_YAML = f'''name: TriageAgent
model: {MODEL_NAME}
description: Stage 1 read-only fault localization agent
instruction: !include ../prompts/triage.md
output_key: localization_packet
include_contents: default
generate_content_config: !include ../configs/sampling.yaml
tools:
  - search_similar_code
  - get_code_neighbors
  - get_code_subgraph
  - read_file
  - get_status
'''
(SFD_DIR / 'sub_agents' / 'triage_agent.yaml').write_text(TRIAGE_YAML, encoding='utf-8')

PATCH_YAML = f'''name: PatchAgent
model: {MODEL_NAME}
description: Stage 2 surgical code modification agent with context reset
instruction: !include ../prompts/patcher.md
output_key: patch_manifest
include_contents: none
generate_content_config: !include ../configs/sampling.yaml
tools:
  - read_file
  - edit_file
  - write_file
  - get_status
'''
(SFD_DIR / 'sub_agents' / 'patch_agent.yaml').write_text(PATCH_YAML, encoding='utf-8')

VERIFIER_YAML = f'''name: VerifierAgent
model: {MODEL_NAME}
description: Stage 3 targeted verification and patch submission agent with context reset
instruction: !include ../prompts/verifier.md
include_contents: none
generate_content_config: !include ../configs/sampling.yaml
tools:
  - run_command
  - read_file
  - edit_file
  - get_status
  - submit_patch
'''
(SFD_DIR / 'sub_agents' / 'verifier_agent.yaml').write_text(VERIFIER_YAML, encoding='utf-8')

TRIAGE_PROMPT = '''You are Stage 1 (TriageAgent) of a 3-stage software engineering pipeline.
Your sole responsibility is read-only fault localization in at most 3 tool calls.

## Problem Statement:
{problem_description?}

## Strict Localization Rules:
1. Make AT MOST 3 tool calls total (`search_similar_code`, `get_code_neighbors`, or `read_file` with explicit `start_line` and `end_line`).
2. Identify the exact source file path under `/workspace`, the target function/class name, the line range to edit, and the relevant targeted test file.
3. As soon as you identify the target file and line range, STOP calling tools and output ONLY the structured `<localization_packet>` below so Stage 2 (PatchAgent) can apply the edit:

<localization_packet>
target_file: "path/to/source_file.py"
target_symbol: "ClassOrFunctionName"
line_range: [start_line, end_line]
root_cause_and_fix: "Concise explanation of the exact code change needed"
test_command: "pytest tests/test_target.py -k test_name"
</localization_packet>
'''
(SFD_DIR / 'prompts' / 'triage.md').write_text(TRIAGE_PROMPT, encoding='utf-8')

PATCHER_PROMPT = '''You are Stage 2 (PatchAgent) of a 3-stage software engineering pipeline.
Your sole responsibility is to apply the minimal source code edit in at most 3 tool calls.

## Problem Statement:
{problem_description?}

## Stage 1 Localization Packet:
{localization_packet?}

## Strict Patching Rules:
1. Call `read_file` on `target_file` around `line_range` if you need exact lines before editing.
2. Call `edit_file` (or `write_file` if creating a new module) to apply the minimal fix to the source code.
3. NEVER modify, create, or delete any test files (`test_*.py`, `*_test.py`, or files under `tests/`) or runner config files (`pytest.ini`, `conftest.py`, `pyproject.toml`).
4. As soon as `edit_file` succeeds (`status: ok`), STOP calling tools and output ONLY the `<patch_manifest>` block below so Stage 3 (VerifierAgent) can test and submit:

<patch_manifest>
modified_file: "path/to/source_file.py"
edit_status: "APPLIED"
change_summary: "1-sentence summary of the applied code edit"
test_command: "pytest tests/test_target.py -k test_name"
</patch_manifest>
'''
(SFD_DIR / 'prompts' / 'patcher.md').write_text(PATCHER_PROMPT, encoding='utf-8')

VERIFIER_PROMPT = '''You are Stage 3 (VerifierAgent) of a 3-stage software engineering pipeline.
Your responsibility is to verify the applied patch using a targeted test and call `submit_patch`.

## Problem Statement:
{problem_description?}

## Stage 1 Localization Packet:
{localization_packet?}

## Stage 2 Patch Manifest:
{patch_manifest?}

## Strict Verification & Submission Rules:
1. Run ONLY a targeted test via `run_command` (e.g., `pytest tests/test_specific.py -k test_func` or `python3 -c "..."`). NEVER run bare `pytest` or full-repo test sweeps.
2. Any temporary reproduction script MUST be placed in `/tmp/repro.py`, NEVER inside `/workspace/`. Before calling `submit_patch`, ensure no untracked scratch files exist in `/workspace/`.
3. If the targeted test reveals a bug or syntax error in the modified source file, fix it with `edit_file` (never edit test files).
4. Call `submit_patch` as your final tool call, verify `patch_size > 0`, and emit a one-sentence completion message.
'''
(SFD_DIR / 'prompts' / 'verifier.md').write_text(VERIFIER_PROMPT, encoding='utf-8')

validate_directory(SFD_DIR, limits=limits)
print('Validated sub_sfd:', discover_declared_models(SFD_DIR))

# Also package /kaggle/working/submission.zip from sub_sfd
zip_base = WORKING_DIR / 'submission'
zip_path = Path(shutil.make_archive(str(zip_base), 'zip', root_dir=SFD_DIR))
print(f'Packaged submission.zip ({zip_path.stat().st_size} bytes)')

# 3. Build flat_controlled (Single LlmAgent with identical tools, sampling, and combined instructions)
FLAT_CTRL_DIR = WORKING_DIR / 'sub_flat_controlled'
if FLAT_CTRL_DIR.exists():
    shutil.rmtree(FLAT_CTRL_DIR)
for sub in ('configs', 'prompts'):
    (FLAT_CTRL_DIR / sub).mkdir(parents=True, exist_ok=True)

(FLAT_CTRL_DIR / 'configs' / 'sampling.yaml').write_text(SAMPLING_YAML, encoding='utf-8')
(FLAT_CTRL_DIR / 'eval_config.yaml').write_text(EVAL_CONFIG_YAML, encoding='utf-8')

FLAT_CTRL_AGENT_YAML = f'''name: flat_controlled_agent
model: {MODEL_NAME}
description: Single-agent controlled baseline with identical tools and instructions as SFD
instruction: !include prompts/controlled_system.md
include_contents: default
generate_content_config: !include configs/sampling.yaml
tools:
  - search_similar_code
  - get_code_neighbors
  - get_code_subgraph
  - read_file
  - edit_file
  - write_file
  - run_command
  - get_status
  - submit_patch
'''
(FLAT_CTRL_DIR / 'agent.yaml').write_text(FLAT_CTRL_AGENT_YAML, encoding='utf-8')

CTRL_PROMPT = '''You are an autonomous software engineering agent resolving a repository issue.
Follow the 3 phases below in sequence (Localization -> Patching -> Verification & Submission).

## Problem Statement:
{problem_description?}

## Phase 1: Fault Localization (at most 3 tool calls)
1. Use `search_similar_code`, `get_code_neighbors`, or `read_file` with explicit `start_line` and `end_line` to locate the exact source file and line range.

## Phase 2: Surgical Patching (at most 3 tool calls)
1. Call `edit_file` (or `write_file` if creating a new module) to apply the minimal fix to the source code.
2. NEVER modify, create, or delete any test files (`test_*.py`, `*_test.py`, or files under `tests/`) or runner config files (`pytest.ini`, `conftest.py`, `pyproject.toml`).

## Phase 3: Targeted Verification & Submission
1. Run ONLY a targeted test via `run_command` (e.g., `pytest tests/test_specific.py -k test_func` or `python3 -c "..."`). NEVER run bare `pytest` or full-repo test sweeps.
2. Any temporary reproduction script MUST be placed in `/tmp/repro.py`, NEVER inside `/workspace/`. Before calling `submit_patch`, ensure no untracked scratch files exist in `/workspace/`.
3. Call `submit_patch` as your final tool call, verify `patch_size > 0`, and emit a one-sentence completion message.
'''
(FLAT_CTRL_DIR / 'prompts' / 'controlled_system.md').write_text(CTRL_PROMPT, encoding='utf-8')
validate_directory(FLAT_CTRL_DIR, limits=limits)
print('Validated sub_flat_controlled:', discover_declared_models(FLAT_CTRL_DIR))
"""

cell3_vllm = """import litellm
import torch
from adk_submission import VllmConfig, VllmServer, discover_adapters
from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS

litellm.drop_params = True
INFERENCE_API_KEY = os.environ.get('LOCAL_API_KEY', 'EMPTY')
MODEL_CANDIDATES = [
    Path(f'/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2'),
    Path(f'/kaggle/input/gemma-4/other/{MODEL_NAME}/2'),
]
MODEL_PATH = next((p for p in MODEL_CANDIDATES if p.exists()), None)
if MODEL_PATH is None:
    for p in Path('/kaggle/input').rglob('config.json'):
        if MODEL_NAME in str(p):
            MODEL_PATH = p.parent
            break
assert MODEL_PATH is not None, f'Model weights not found for {MODEL_NAME}'

adapters = discover_adapters(str(SFD_DIR), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 1
tp_size = 4 if gpu_count >= 4 else (2 if gpu_count >= 2 else 1)

if 'server_instance' in globals() and server_instance is not None:
    server_instance.stop()

vllm_cfg = VllmConfig(
    model=str(MODEL_PATH),
    port=8000,
    host='127.0.0.1',
    tool_call_parser='gemma4',
    reasoning_parser='gemma4',
    max_model_len=32768,
    dtype='bfloat16' if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else 'auto',
    gpu_memory_utilization=0.90,
    enable_auto_tool_choice=True,
    enable_lora=False,
    max_loras=1,
    max_lora_rank=16,
    scheduler_reserve_full_isl=False,
    tensor_parallel_size=tp_size,
    startup_timeout=60 * 20,
)
server_instance = VllmServer(vllm_cfg, adapter_manifest=adapters)
server_instance.start()
print(f'vLLM server started on {server_instance.base_url} (tp={tp_size}, gpu_count={gpu_count})')

models = server_instance.create_model_registry(
    aliases=[MODEL_NAME],
    model_prefix='openai/',
    api_key=INFERENCE_API_KEY,
)
"""

cell4_eval = """import asyncio
import concurrent.futures
import json
import time
from collections import defaultdict
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps._configs import EventsCompactionConfig
from swegemma.config import EvalConfig
from swegemma.evaluate import Evaluator

def run_sync(coro_or_fn, *args, **kwargs):
    if callable(coro_or_fn) and not asyncio.iscoroutine(coro_or_fn):
        fn = lambda: coro_or_fn(*args, **kwargs)
    else:
        fn = lambda: coro_or_fn
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(fn())).result()
    return asyncio.run(fn())

TASKS_PATH = DATA_DIR / 'tasks.jsonl'
all_tasks = load_tasks(TASKS_PATH)

# Deterministic stratified selection: first k_r tasks per repository in canonical tasks.jsonl order
QUOTAS = {
    'fastapi/fastapi': 3,
    'Textualize/rich': 2,
    'psf/requests': 2,
    'encode/httpx': 1,
}
counts = defaultdict(int)
BENCHMARK_TASKS = []
for t in all_tasks:
    if counts[t.repo] < QUOTAS.get(t.repo, 0):
        BENCHMARK_TASKS.append(t)
        counts[t.repo] += 1

print(f'Selected {len(BENCHMARK_TASKS)} stratified benchmark tasks:')
for idx, t in enumerate(BENCHMARK_TASKS, 1):
    print(f'  [{idx}] {t.instance_id} ({t.repo})')

CONFIGS = {
    'flat_starter': FLAT_STARTER_DIR,
    'flat_controlled': FLAT_CTRL_DIR,
    'sfd': SFD_DIR,
}

RESULTS_ROOT = WORKING_DIR / 'eval_results'
RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
PROGRESS_LOG = RESULTS_ROOT / 'paired_progress.jsonl'

evaluators = {}
for cfg_name, sub_dir in CONFIGS.items():
    cfg_res_dir = RESULTS_ROOT / cfg_name
    cfg_res_dir.mkdir(parents=True, exist_ok=True)
    ec = EvalConfig(
        tasks_path=TASKS_PATH,
        snapshots_dir=DATA_DIR / 'snapshots',
        results_dir=cfg_res_dir,
        submission_dir=sub_dir,
        models=models,
        sandbox='subprocess',
        timeout_seconds=60,
        verification_timeout_seconds=120,
        max_time_minutes=2.5,
        max_tool_calls=15,
        max_turns=20,
        limits=limits,
        generation_constraints=gen_constraints,
        adapter_manifest=adapters,
        context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=1800, cache_intervals=10),
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=15,
            overlap_size=2,
            token_threshold=14336,
            event_retention_size=5,
        ),
        graph_dir=str(DATA_DIR / 'graphs'),
        embeddings_dir=str(DATA_DIR / 'embeddings'),
        wheels_dir=DATA_DIR / 'wheels',
        verbose=False,
    )
    evaluators[cfg_name] = Evaluator(ec)

for t_idx, task in enumerate(BENCHMARK_TASKS, start=1):
    for cfg_name, ev in evaluators.items():
        print(f'=== Task [{t_idx}/{len(BENCHMARK_TASKS)}] {task.instance_id} | Config: {cfg_name} ===', flush=True)
        t0 = time.time()
        try:
            res = run_sync(
                ev.evaluate_task,
                task=task,
                task_index=t_idx,
                total_tasks=len(BENCHMARK_TASKS),
            )
            patch_str = (res.agent_patch or '').strip()
            rec = {
                'instance_id': task.instance_id,
                'repo': task.repo,
                'config': cfg_name,
                'resolved': bool(res.resolved),
                'test_exit_code': res.test_exit_code,
                'patch_chars': len(patch_str),
                'tool_calls': res.tool_calls,
                'duration_seconds': round(res.duration_seconds, 2),
                'error': res.error,
            }
            print(f'  -> resolved={rec["resolved"]} | exit={rec["test_exit_code"]} | patch_chars={rec["patch_chars"]} | tools={rec["tool_calls"]} | dur={rec["duration_seconds"]}s', flush=True)
        except Exception as exc:
            rec = {
                'instance_id': task.instance_id,
                'repo': task.repo,
                'config': cfg_name,
                'resolved': False,
                'test_exit_code': -99,
                'patch_chars': 0,
                'tool_calls': 0,
                'duration_seconds': round(time.time() - t0, 2),
                'error': str(exc),
            }
            print(f'  -> EXCEPTION: {exc}', flush=True)
        with open(PROGRESS_LOG, 'a', encoding='utf-8') as pf:
            pf.write(json.dumps(rec) + '\\n')

if 'server_instance' in globals() and server_instance is not None:
    server_instance.stop()
    print('Stopped vLLM server cleanly.')
"""

for idx, src in enumerate([cell1_env, cell2_configs, cell3_vllm, cell4_eval], 1):
    ast.parse(src)
    print(f"Cell {idx} syntax verified via ast.parse()")

nb = {
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.13"},
    },
    "nbformat": 4,
    "nbformat_minor": 4,
    "cells": [
        {"id": "cell1", "cell_type": "code", "metadata": {"trusted": True}, "execution_count": None, "outputs": [], "source": cell1_env.splitlines(keepends=True)},
        {"id": "cell2", "cell_type": "code", "metadata": {"trusted": True}, "execution_count": None, "outputs": [], "source": cell2_configs.splitlines(keepends=True)},
        {"id": "cell3", "cell_type": "code", "metadata": {"trusted": True}, "execution_count": None, "outputs": [], "source": cell3_vllm.splitlines(keepends=True)},
        {"id": "cell4", "cell_type": "code", "metadata": {"trusted": True}, "execution_count": None, "outputs": [], "source": cell4_eval.splitlines(keepends=True)},
    ],
}

# Write Kernel 1: Rerun Reproducibility on Cohort 1 (8 tasks x 2 configs = 16 runs)
k1_dir = Path(r"d:\AI Research\gemma_paper\kaggle_kernel")
k1_dir.mkdir(parents=True, exist_ok=True)
nb1 = json.loads(json.dumps(nb))
c4_src1 = "".join(nb1["cells"][3]["source"])
old_cfg_block = """CONFIGS = {
    'flat_starter': FLAT_STARTER_DIR,
    'flat_controlled': FLAT_CTRL_DIR,
    'sfd': SFD_DIR,
}"""
new_cfg_block1 = """CONFIGS = {
    'flat_controlled_rerun': FLAT_CTRL_DIR,
    'sfd_rerun': SFD_DIR,
}"""
assert old_cfg_block in c4_src1
nb1["cells"][3]["source"] = c4_src1.replace(old_cfg_block, new_cfg_block1).splitlines(keepends=True)
(k1_dir / "sfd_developer_agent.ipynb").write_text(json.dumps(nb1, indent=2), encoding="utf-8")
meta1 = {
    "id": "karandeepsinghsodhi/sfd-state-filtered-deliberation-agent-gemma-4",
    "title": "SFD: State-Filtered Deliberation Agent (Gemma 4)",
    "code_file": "sfd_developer_agent.ipynb",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": False,
    "enable_gpu": True,
    "enable_tpu": False,
    "enable_internet": False,
    "keywords": ["gpu"],
    "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
    "kernel_sources": [],
    "competition_sources": ["gemma-4-developer-agent"],
    "model_sources": [
        "google/gemma-4/Other/gemma-4-e4b-it-qat-w4a16-ct/2",
        "google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2",
        "google/gemma-4/Other/gemma-4-e2b-it-qat-w4a16-ct/2",
        "google/gemma-4/Other/gemma-4-12b-it-qat-w4a16-ct/2",
    ],
    "docker_image": DOCKER_IMAGE,
    "machine_shape": MACHINE_SHAPE,
}
(k1_dir / "kernel-metadata.json").write_text(json.dumps(meta1, indent=2), encoding="utf-8")

# Write Kernel 2: Disjoint Seeded-Random Stratified Sample (seed=42, n=8 tasks x 3 configs = 24 runs)
k2_dir = Path(r"d:\AI Research\gemma_paper\kaggle_kernel_shard2")
k2_dir.mkdir(parents=True, exist_ok=True)
nb2 = json.loads(json.dumps(nb))
c4_src = "".join(nb2["cells"][3]["source"])
old_sel = """QUOTAS = {
    'fastapi/fastapi': 3,
    'Textualize/rich': 2,
    'psf/requests': 2,
    'encode/httpx': 1,
}
counts = defaultdict(int)
BENCHMARK_TASKS = []
for t in all_tasks:
    if counts[t.repo] < QUOTAS.get(t.repo, 0):
        BENCHMARK_TASKS.append(t)
        counts[t.repo] += 1"""
new_sel = """import random
COHORT1_IDS = {
    'fastapi_15661', 'fastapi_15588', 'fastapi_15589',
    'requests_7505', 'requests_7502',
    'rich_4070', 'rich_4077',
    'httpx_3672',
}
QUOTAS = {
    'fastapi/fastapi': 4,
    'Textualize/rich': 3,
    'psf/requests': 1,
    'encode/httpx': 0,
}
by_repo = defaultdict(list)
for t in all_tasks:
    if t.instance_id not in COHORT1_IDS:
        by_repo[t.repo].append(t)
rng = random.Random(42)
BENCHMARK_TASKS = []
for repo in sorted(QUOTAS.keys()):
    k_r = QUOTAS[repo]
    if k_r > 0 and len(by_repo[repo]) >= k_r:
        sampled = rng.sample(by_repo[repo], k_r)
        BENCHMARK_TASKS.extend(sampled)"""
assert old_sel in c4_src
nb2["cells"][3]["source"] = c4_src.replace(old_sel, new_sel).splitlines(keepends=True)
(k2_dir / "sfd_eval_shard2.ipynb").write_text(json.dumps(nb2, indent=2), encoding="utf-8")
meta2 = dict(meta1)
meta2["id"] = "karandeepsinghsodhi/sfd-paired-eval-shard-2-gemma-4"
meta2["title"] = "SFD Paired Eval Shard 2 Gemma 4"
meta2["code_file"] = "sfd_eval_shard2.ipynb"
(k2_dir / "kernel-metadata.json").write_text(json.dumps(meta2, indent=2), encoding="utf-8")
print("Updated Kernel 1 (Rerun Reproducibility) and Kernel 2 (Seeded-Random Stratified Cohort 2)")
