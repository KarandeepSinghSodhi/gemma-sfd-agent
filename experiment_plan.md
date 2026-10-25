# Pre-Registered Experiment Plan: State-Filtered Deliberation (SFD)

**Date:** October 26, 2026  
**Status:** Awaiting User Approval (Phase 2 Checkpoint)  
**Primary Target Model:** Gemma E4B (`gemma-4-e4b-it-qat-w4a16-ct`)  
**Execution Environment:** Kaggle Cloud GPUs (NVIDIA T4 / 4x L4 cluster)  

---

## 1. Experimental Configurations & Research Questions

The primary objective is to isolate whether **hard context resetting between sub-goals** improves task completion and eliminates context exhaustion for small open-weight models, or whether observed gains are merely artifacts of code-intelligence tooling, prompt engineering, or harness hygiene.

### 1.1 Primary Comparison (Fairly Controlled Hierarchy)
All primary configurations are evaluated on the exact same task set using identical generation parameters:
- **Config A (`flat_react_starter`):** Official Kaggle starter baseline (`agent.yaml`). Flat ReAct loop, standard shell/file tools, no code graphs, append-only history.
- **Config B (`flat_controlled_baseline`):** **The Fair Control.** Flat ReAct loop equipped with:
  - The exact same code-graph tools (`search_similar_code`, `get_code_neighbors`, `get_code_subgraph`),
  - The exact same prompt instructions and scratch-hygiene rules (`/tmp/repro.py`),
  - Hard observation truncation (`MAX_OBSERVATION_TOKENS = 1200`),
  - **No context resetting** (all turns remain in a single append-only history).
  - *Purpose:* Directly isolates context resetting from tooling and hygiene.
- **Config C (`sfd_tripartite`):** State-Filtered Deliberation. Three sequential sub-agents (Triage $\to$ Patcher $\to$ Verifier) with `include_contents: "none"` enforcing hard context reset via an immutable $\sim$250-token state packet.

### 1.2 Ablation Study (On Gemma E4B)
To isolate internal components of SFD:
- **Ablation 1 (`sfd_no_reset`):** SFD pipeline with `include_contents: "default"`. Preserves the 3-stage prompts and tool restrictions, but passes complete prior history into subsequent stages.
- **Ablation 2 (`sfd_no_codegraphs`):** SFD pipeline where Triage Agent uses standard file grep/find instead of code graphs.
- **Ablation 3 (`sfd_no_verifier`):** Two-stage pipeline (Triage $\to$ Patcher) calling `submit_patch` directly, omitting the scratch-file audit and targeted pytest verification.

### 1.3 Optional Extensions (Compute Permitting)
- **Config D (`rolling_compaction`):** Flat agent with Google ADK default `EventsCompactionConfig` (15-turn interval, 14,336-token threshold).
- **Config E (`agentless_pipeline`):** Two-phase non-agentic pipeline (retrieve top-k files $\to$ generate patch).
- **Model Footprint Scaling:** Evaluating Config A vs Config B vs Config C on Gemma 12B (`gemma-4-12b-it-qat-w4a16-ct`).

---

## 2. Benchmark Task Set & Sampling

- **Full Evaluation Set:** 129 tasks from `tasks.jsonl` (FastAPI 67, Rich 48, Requests 13, HTTPX 1).
- **Pilot Evaluation Subset:**
  - Due to compute quotas on interactive GPUs, primary local/interactive runs will execute on a **fixed stratified sample of $n = 45$ tasks**:
    - `fastapi/fastapi`: 23 tasks
    - `Textualize/rich`: 17 tasks
    - `psf/requests`: 5 tasks
  - Random seed: `SEED = 20261026` (pre-registered and deterministic).
  - All configurations run on the **exact same 45 tasks**.
  - All reporting will explicitly label these results as a **Pilot Study ($n=45$)**.
  - Full-suite validation ($n=129$) will be cited strictly from the official competition submission traces.

---

## 3. Determinism & Random Seeds

- **Decoding Parameters:**
  - Temperature: $T = 0.0$ (greedy decoding).
  - Top-P: $1.0$.
  - In greedy decoding ($T=0.0$), LLM generation on fixed vLLM hardware is deterministic up to minor batch scheduling variations.
- **Seeds:**
  - Primary comparison (Configs A, B, C) will be evaluated across **3 random seeds** (`seed=42`, `seed=1337`, `seed=2026`) to quantify decoding variance.
  - If output hashes across seeds are identical, we will explicitly report that greedy decoding was deterministic and report single-run metrics without inflating sample size.

---

## 4. Pre-Registered Statistical Analysis

Every number in the paper will be produced exclusively by `scripts/aggregate.py`.

### 4.1 Primary Metrics & Definitions
1. **Resolution Rate (Pass@1):** $\frac{k}{n}$, with exact 95% Wilson Score Confidence Intervals.
2. **Peak Active Prompt Tokens:**
   - For task $i$: $P_i = \max_{t \in \text{turns}} |C_{i,t}|$, where $|C_{i,t}|$ is measured via BPE tokenizer on the exact prompt string sent to the model.
   - We report both **Mean Peak Prompt Tokens** ($\frac{1}{n} \sum P_i$) and **Maximum Peak Prompt Tokens** ($\max_i P_i$).
3. **Cumulative Tokens:** Total tokens (prompt + completion) generated across all turns of a task ($\sum_{t} (|C_{i,t}| + |A_{i,t}|)$).
4. **Context Overflow Rate:** Proportion of tasks where $|C_{i,t}| \ge 32,768$ tokens.
5. **Cap Trigger Rate:** Proportion of tasks where any hard operational cap was triggered.
6. **Wall-Clock Duration:** Mean execution time in seconds per task.

### 4.2 Statistical Significance Testing
Because all configurations are evaluated on the exact same task instances, unpaired tests are inappropriate:
- **Paired McNemar Exact Test:** Evaluates discordant task pairs between Config C (SFD) and Config B (Fair Control):
  $$p = 2 \sum_{j=0}^{\min(b,c)} \binom{b+c}{j} 0.5^{b+c}$$
  where $b$ is (Control=Pass, SFD=Fail) and $c$ is (SFD=Pass, Control=Fail).
- **Paired Bootstrap Confidence Intervals:** 95% bootstrap CI for the paired difference $\Delta = \text{Pass}_{\text{SFD}} - \text{Pass}_{\text{Control}}$ computed over 10,000 resamples.
- **Multiple Comparisons:** Bonferroni-Holm adjustment applied across the 3 primary pairwise tests.

### 4.3 Pre-Registered Failure Classification Rule
For every failed task ($resolved = False$), the failure reason will be classified by rule:
1. `TRIAGE_MISLOCALIZATION`: If target file or function in `triage_packet` does not match the files modified in ground truth `test_patch`.
2. `PATCH_LOGIC_SYNTAX_ERROR`: If triage correctly localized the file, but `agent_patch` failed unit tests or failed `git apply`.
3. `VERIFIER_TIMEOUT`: If verifier exceeded stage turn budget ($> 3$ turns).
4. `CONTEXT_OVERFLOW`: If prompt length exceeded 32,768 tokens.
