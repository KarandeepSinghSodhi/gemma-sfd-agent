# Compute Plan & Executed Hardware Budget

## 1. Physical Hardware & Execution Environments

### 1.1 Local Workstation
- **OS:** Windows 11 (build 26100), 12 physical cores (16 logical threads), 15.68 GB RAM, no local CUDA GPU.
- **Role:** Trace aggregation (`scripts/aggregate.py`), paper rendering (`scripts/render_paper.py`), consistency verification (`scripts/check_consistency.py`), and Typst PDF compilation (`typst compile paper.typ paper.pdf`).

### 1.2 Kaggle 4x NVIDIA L4 GPU Execution Environment (Used for All Paper Experiments)
- **Kernel:** `karandeepsinghsodhi/sfd-state-filtered-deliberation-agent-gemma-4` (Version 4, `KernelWorkerStatus.COMPLETE`)
- **Docker Image:** `gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461` (Python 3.12 matching the competition wheelhouse `cp312` wheels)
- **Hardware (`machine_shape: "NvidiaL4"`):** 4x NVIDIA L4 GPUs (96 GB total VRAM, `tensor_parallel_size=4`).
- **vLLM Server Configuration:**
  - Model: `/kaggle/input/models/google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`
  - Context length: `max_model_len=32768`, `gpu_memory_utilization=0.80`
  - Parsers: `--enable-auto-tool-choice --tool-call-parser gemma4 --reasoning-parser gemma4`
- **Task Evaluation Budgets (`eval_config.yaml`):**
  - `max_tool_calls: 15`, `max_turns: 20`, `max_time_minutes: 2.5`, `timeout_seconds: 60`, `verification_timeout_seconds: 120`

---

## 2. Measured Wall-Clock Timing & Token Consumption ($n = 8$ Stratified Tasks, 24 Runs)

Across the 24 complete two-phase `swegemma` evaluations (`traces/eval_results/`):
- **`flat_starter` (8 runs):** Mean duration `103.19s` (median `85.41s`), mean LLM calls `10.88`, mean tool calls `8.88`, mean single-call peak prompt `12,855.2` tokens, mean cumulative total tokens `93,509.9`.
- **`flat_controlled` (8 runs):** Mean duration `88.95s` (median `84.59s`), mean LLM calls `12.00`, mean tool calls `9.75`, mean single-call peak prompt `12,456.4` tokens, mean cumulative total tokens `109,507.1`.
- **`sfd` (8 runs):** Mean duration `92.73s` (median `96.66s`), mean LLM calls `15.12`, mean tool calls `10.88`, mean single-call peak prompt `9,298.1` tokens, mean cumulative total tokens `80,790.9`.
- **Total Evaluation Wall-Clock Time:** `2,279.0s` (~38.0 minutes) for the 24 two-phase runs plus ~2.5 minutes for vLLM server startup and repository cache initialization.
