# Compute Plan & Executed Hardware Budget

## 1. Physical Hardware & Execution Environments

### 1.1 Local Workstation
- **OS:** Windows 11 (build 26100), 12 physical cores (16 logical threads), 15.68 GB RAM, no local CUDA GPU.
- **Role:** Trace aggregation (`scripts/aggregate.py`), paper rendering (`scripts/render_paper.py`), consistency verification (`scripts/check_consistency.py`), and Typst PDF compilation (`typst compile paper.typ paper.pdf`).

### 1.2 Kaggle 4x NVIDIA L4 GPU Execution Environment (Used for All 64 Paper Runs)
- **Executed Kernels:**
  1. `karandeepsinghsodhi/sfd-state-filtered-deliberation-agent-gemma-4` (Version 4: 24 Cohort 1 paired runs in `traces/eval_results/`; Version 5: 16 Cohort 1 rerun reproducibility runs in `traces/rerun_results/`, `KernelWorkerStatus.COMPLETE`)
  2. `karandeepsinghsodhi/sfd-paired-eval-shard-2-gemma-4` (Version 1: 24 Cohort 2 disjoint seeded-random paired runs in `traces/shard2_results/`, `KernelWorkerStatus.COMPLETE`)
- **Docker Image:** `gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461` (Python 3.12 matching the competition wheelhouse `cp312` wheels)
- **Hardware (`machine_shape: "NvidiaL4"`):** 4x NVIDIA L4 GPUs (96 GB total VRAM, `tensor_parallel_size=4`).
- **vLLM Server Configuration:**
  - Model: `/kaggle/input/models/google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`
  - Context length: `max_model_len=32768`, `gpu_memory_utilization=0.80`
  - Parsers: `--enable-auto-tool-choice --tool-call-parser gemma4 --reasoning-parser gemma4`
- **Task Evaluation Budgets (`eval_config.yaml`):**
  - `max_tool_calls: 15`, `max_turns: 20`, `max_time_minutes: 2.5`, `timeout_seconds: 60`, `verification_timeout_seconds: 120`

---

## 2. Measured Wall-Clock Timing & Token Consumption ($n = 16$ Paired Tasks = 48 Primary Runs + 16 Reruns = 64 Total Runs)

Across the 48 primary paired two-phase `swegemma` evaluations (`traces/eval_results/` and `traces/shard2_results/`):
- **`flat_starter` (16 runs):** Resolved `1/16` (`6.25%`), mean duration `97.34s` (median `86.26s`), mean LLM calls `11.56`, mean budget-counted tool calls `9.88`, mean single-call peak prompt `13,029.3` tokens (max `15,281`), mean cumulative total tokens `103,350.1`.
- **`flat_controlled` (16 runs):** Resolved `0/16` (`0.00%` in Run 1; `1/8` in Cohort 1 rerun), mean duration `92.19s` (median `83.99s`), mean LLM calls `12.69`, mean budget-counted tool calls `10.50`, mean single-call peak prompt `13,550.8` tokens (max `16,154`), mean cumulative total tokens `119,664.4`.
- **`sfd` (16 runs):** Resolved `1/16` (`6.25%`), mean duration `89.37s` (median `93.36s`), mean LLM calls `15.94`, mean budget-counted tool calls `11.19`, mean single-call peak prompt `11,291.9` tokens (max `16,146`), mean cumulative total tokens `88,909.5`.
- **Rerun Reproducibility Study (16 runs across Cohort 1):** `sfd_rerun` (8 runs) and `flat_controlled_rerun` (8 runs) executed on identical 4x L4 GPUs (`temperature=0.0, seed=42`), stored in `traces/rerun_results/`.
