# Compute Plan & Competition Resource Budget

## 1. Physical Hardware & Execution Environments

### 1.1 Local Development Machine
- **OS:** Windows 11 (build 26100)
- **CPU:** 12 physical cores, 16 logical threads
- **Memory:** 15.68 GB RAM
- **GPU / CUDA:** None (`torch.cuda.is_available() == False`).
- **Role:** Static analysis, prompt token profiling, YAML schema verification, harness instrumentation, and empirical analysis scripts (`aggregate.py`).
- **Limitation:** Cannot run quantized Gemma 4 models (e.g. 12B/31B) locally at viable inference speeds without CUDA VRAM.

### 1.2 Kaggle Cloud Execution Environment
- **Interactive Notebooks:**
  - Hardware: 1x NVIDIA T4 (16 GB VRAM) or 2x NVIDIA T4 (32 GB VRAM).
  - Quota: 30 GPU hours per week.
  - Environment: Pre-mounted competition dataset at `/kaggle/input/competitions/gemma-4-developer-agent/` containing repository snapshots, code graphs, node embeddings, and cached python wheels.
  - Supported Models in Notebook: `gemma-4-e2b-it-qat-w4a16-ct`, `gemma-4-e4b-it-qat-w4a16-ct`, and `gemma-4-12b-it-qat-w4a16-ct`.
- **Competition Evaluation Cluster (Scoring Backend):**
  - Hardware: 4x NVIDIA L4 GPUs (96 GB VRAM total).
  - Inference Server: vLLM OpenAI-compatible server (`:8000`) with `max_model_len=32768`.
  - Sandboxes: Isolated Docker containers with 4 GB RAM, 2 vCPUs, air-gapped network per task.
  - Submission Quota: 5 submissions per calendar day.

---

## 2. Timing & Latency Profiling

Based on the official competition reference (`HARNESS_README.md`):
- **Per-Task Time Quota:**
  - Agent Session (`Container A`): 60 minutes default (capped by `eval_config.yaml`).
  - Verification (`Container B`): 5 minutes (`verification_timeout_seconds: 300`).
- **Observed Inference Latency on vLLM (4x L4 GPUs):**
  - Prompt prefill: $\approx 1,200 \text{ tokens/sec}$.
  - Generation: $\approx 45 \text{ tokens/sec}$ (31B) to $\approx 110 \text{ tokens/sec}$ (E4B).
  - Average interaction turn: 8–18 seconds.
- **Estimated Task Wall-Clock Time:**
  - Flat ReAct (15–25 turns with large file reads): $\approx 4.5 \text{ minutes per task}$.
  - State-Filtered Deliberation (3 bounded stages, $\le 3$ turns each): $\approx 1.8 \text{ minutes per task}$.

---

## 3. Realistic Compute Budget & Scope

Evaluating all 129 tasks across multiple baselines requires significant GPU hours:
- Full 129-task run for 1 config $\approx 129 \times 2.5 \text{ min} \approx 5.4 \text{ GPU hours}$.
- 4 models $\times$ 3 configurations $\times$ 129 tasks $\approx 64.8 \text{ GPU hours}$ (exceeds weekly interactive quota).

### Resource-Conscious Pilot Strategy:
1. **Primary Model Target:** Focus experimental runs on **Gemma E4B** (`gemma-4-e4b-it-qat-w4a16-ct`), which represents the primary edge/consumer footprint where context wall issues manifest most acutely.
2. **Fixed Representative Subset (Pilot):**
   - Use a stratified random sample of **40 tasks** from `tasks.jsonl` (stratified across FastAPI, Rich, and Requests, seed recorded).
   - 40 tasks $\times$ 3 configs $\times$ 2.5 min $\approx 5.0 \text{ GPU hours}$ (fully fits within interactive T4 quota).
3. **Kaggle Official Submissions:**
   - Use daily competition submissions (Ref # 57643078) to validate end-to-end full 129-task execution on the official 4x L4 cluster.
