# Pre-Registered Experiment Plan: State-Filtered Deliberation (SFD)

**Date:** October 26, 2026  
**Primary Target Model:** `gemma-4-e4b-it-qat-w4a16-ct`  
**Execution Environment:** Kaggle 4x NVIDIA L4 GPUs (`machine_shape: "NvidiaL4"`, 96 GB total VRAM, `vLLM` server on `:8000`, `swegemma` two-phase subprocess sandbox)

---

## 1. Experimental Configurations & Research Questions

Our objective is to evaluate whether **mandatory stage-isolated sequential decomposition** (`SequentialAgent` with `include_contents: "none"` and role-partitioned tool subsets) improves patch generation, context efficiency, or task resolution on a 4-bit quantized 4B model (`gemma-4-e4b-it-qat-w4a16-ct`) relative to:
1. The official competition starter kit (`flat_starter`), which already binds all 9 built-in `swegemma` tools (including `search_similar_code`, `get_code_neighbors`, `get_code_subgraph`) to a root `LlmAgent` and attaches `sub_agents/code_analyzer.yaml` as an optional `AgentTool` (`skip_summarization: true`).
2. A controlled single-agent baseline (`flat_controlled`) given the exact same prompt rules, tool set, and generation parameters as SFD, running inside a single continuous `LlmAgent` context (`include_contents: "default"`).

### 1.1 Primary Paired Configurations
All three configurations are evaluated on the exact same task subset using identical generation parameters (`temperature: 0.0`, `seed: 42`, `max_output_tokens: 8192`, `thinking_budget: 1536`, `include_thoughts: true`) and identical `eval_config.yaml` session budgets (`max_tool_calls: 15`, `max_turns: 20`, `max_time_minutes: 2.5`, `timeout_seconds: 60`, `verification_timeout_seconds: 120`):

- **Config 1 (`flat_starter`):** Official competition starter kit (`sample_submission/agent.yaml`, `prompts/system.md`, `prompts/analyzer.md`, `sub_agents/code_analyzer.yaml` wrapped as an `AgentTool` with `skip_summarization: true`), adapted to `gemma-4-e4b-it-qat-w4a16-ct` by removing the 31B-shaped sample LoRA adapters. Includes all 9 built-in `swegemma` tools (`run_command`, `read_file`, `edit_file`, `write_file`, `get_status`, `submit_patch`, `get_code_neighbors`, `search_similar_code`, `get_code_subgraph`).
- **Config 2 (`flat_controlled`):** Single `LlmAgent` equipped with the exact same 9 built-in `swegemma` tools (no `code_analyzer` `AgentTool`) and a unified system prompt (`prompts/controlled_system.md`) combining the exact localization, surgical patching, and targeted verification instructions of SFD into a single continuous history (`include_contents: "default"`). Directly isolates the effect of `SequentialAgent` + `include_contents: "none"` + stage-level tool partitioning.
- **Config 3 (`sfd`):** Three-stage `SequentialAgent` (`TriageAgent` $\to$ `PatchAgent` $\to$ `VerifierAgent`):
  - `TriageAgent` (`include_contents: "default"`, `output_key: "localization_packet"`): restricted in YAML config to read-only tools (`search_similar_code`, `get_code_neighbors`, `get_code_subgraph`, `read_file`, `get_status`).
  - `PatchAgent` (`include_contents: "none"`, `output_key: "patch_manifest"`): restricted in YAML config to workspace edit tools (`read_file`, `edit_file`, `write_file`, `get_status`), receiving `{problem_description?}` and `{localization_packet?}` via `session.state`.
  - `VerifierAgent` (`include_contents: "none"`): equipped with `run_command`, `read_file`, `edit_file`, `get_status`, and `submit_patch`, receiving `{problem_description?}`, `{localization_packet?}`, and `{patch_manifest?}` via `session.state`.

---

## 2. Deterministic Stratified Benchmark Subset

To prevent cherry-picking while executing within a single Kaggle 4x L4 session, tasks are selected deterministically by taking the first $k_r$ tasks per repository in canonical `tasks.jsonl` order across all four repositories in the 129-task benchmark:
- **Shard 1 (`n = 8` tasks across all 4 repositories):**
  - `fastapi/fastapi` (first 3): `fastapi_15661`, `fastapi_15588`, `fastapi_15589`
  - `Textualize/rich` (first 2): `rich_4070`, `rich_4077`
  - `psf/requests` (first 2): `requests_7505`, `requests_7502`
  - `encode/httpx` (first 1): `httpx_3672`
- **Shard 2 (next `n = 8` tasks in canonical order, if completed within session quota):**
  - `fastapi/fastapi` (next 3): `fastapi_15030`, `fastapi_14962`, `fastapi_15280`
  - `Textualize/rich` (next 3): `rich_4079`, `rich_4076`, `rich_4075`
  - `psf/requests` (next 2): `requests_7433`, `requests_7427`

---

## 3. Pre-Registered Statistical & Trace Analysis (`scripts/aggregate.py`)

Every number in the manuscript is computed exclusively by `scripts/aggregate.py` from the real `swegemma` output files (`paired_progress.jsonl`, `task_results.jsonl`, and ATIF v1.7 `traces/trace_<instance_id>.json`):

1. **Resolution Rate:** $k/n$ with exact 95% Wilson score confidence intervals.
2. **Paired Significance Tests:** Exact two-sided McNemar test on discordant pairs $(b, c)$ and 95% paired bootstrap confidence intervals (10,000 resamples, `seed=42`) on the resolution rate difference $\Delta$.
3. **Single-Call Peak Prompt Tokens ($\max_t P_t$):** Mean, median, and maximum across tasks of each trajectory's highest single-call `prompt_tokens`.
4. **Stage-Boundary Prompt Token Reset (for `sfd`):** Mean and maximum `prompt_tokens` at `TriageAgent` peak vs. `PatchAgent` call 1 entry and `VerifierAgent` call 1 entry.
5. **Deterministic Failure Taxonomy:** Each unresolved task (`resolved == False`) is classified by rule into:
   - `context_overflow`: Peak call total tokens $\ge 32,768$ or context-length error.
   - `timeout_or_budget_no_patch`: `patch_chars == 0` (no source modification produced before timeout or budget limit).
   - `patch_apply_failed`: `patch_chars > 0` and error contains `"Failed to apply agent patch"`.
   - `test_verification_failed`: `patch_chars > 0` and Phase 2 `pytest` exited non-zero (`test_exit_code != 0`).
   - `runtime_or_harness_error`: Any other unexpected runtime exception.
