# State-Filtered Deliberation: Stage-Isolated Context Management for Small Open-Weight Software Engineering Agents

**Author:** Karandeep Singh Sodhi (Independent Researcher)  
**Track:** Google — The Gemma 4 Developer Agent Competition (Paper Track)

---

## Abstract

Autonomous software engineering (SWE) agents built on small open-weight language models (such as 4-bit quantized Gemma 4 E2B and E4B) face severe operational constraints when executing multi-turn debugging trajectories. On the official `gemma-4-developer-agent` benchmark, while 31B submissions with fine-tuned LoRA adapters reach resolution rates of 22.0%–24.0%, all 24 participating teams on the official Small Model Prize leaderboard (E2B/E4B) score between 0.0% and 6.0% (median 3.0%). In standard single-agent loops, tool observations from file reads, graph queries, and test executions accumulate in the prompt history unless isolated or compacted.

We study **State-Filtered Deliberation (SFD)**, a declarative three-stage `SequentialAgent` architecture built on Google's Agent Development Kit (ADK) and the `swegemma` harness. SFD partitions the repair workflow into three role-restricted sub-agents—`TriageAgent` (read-only localization), `PatchAgent` (code editing), and `VerifierAgent` (targeted testing and submission)—and configures `include_contents: "none"` on `PatchAgent` and `VerifierAgent` so that intermediate tool calls and observations from preceding stages are sliced out of the prompt context at stage boundaries while passing structured text state variables (`localization_packet` and `patch_manifest`) through `session.state`. We evaluate SFD on `gemma-4-e4b-it-qat-w4a16-ct` across a deterministic stratified subset of $n = 8$ benchmark tasks spanning all four competition repositories against both the official competition starter kit (`flat_starter`, using an optional `code_analyzer` `AgentTool`) and an unconfounded single-agent baseline (`flat_controlled`, sharing identical tools, prompts, and sampling parameters). On this $n = 8$ paired sample, SFD resolves 1/8 tasks (12.5%, 95% Wilson CI [2.2%, 47.1%]) compared to 0/8 (0.0%) for `flat_starter` (McNemar $p = 1.0000$) and 0/8 (0.0%) for `flat_controlled` (McNemar $p = 1.0000$), while achieving a mean single-call peak prompt length of 9298.1 tokens (vs. 12855.2 for `flat_starter` and 12456.4 for `flat_controlled`) and resetting stage-entry prompt tokens from a mean triage peak of 8558.5 tokens down to 1534.9 tokens at `PatchAgent` entry and 1559.4 tokens at `VerifierAgent` entry.

---

## 1. Introduction & Motivating Hypotheses

While frontier models and 31B open-weight models with task-specific LoRA adapters achieve 22.0%–24.0% resolution on the `gemma-4-developer-agent` benchmark, small quantized edge models (`gemma-4-e4b-it-qat-w4a16-ct` and `gemma-4-e2b-it-qat-w4a16-ct`) score between 0.0% and 6.0% (median 3.0%) across all 24 teams on the official Small Model Prize leaderboard (`ryanholbrook/gemma-4-developer-agent-small-model-leaderboard`, October 2026).

We formulate and test three operational hypotheses for small open-weight developer agents:
1. **Context Growth & Signal Dilution Hypothesis:** In a continuous single-agent trajectory, appending raw tool outputs increases per-turn prompt length $P_t$. A possible mechanism is that dispersion of attention over growing key-value histories in 4-bit quantized weights increases repetitive reasoning loops or tool-call procrastination.
2. **Discretionary Sub-Agent Under-Utilization Hypothesis:** The official competition starter kit (`sample_submission/agent.yaml`) provides a read-only `code_analyzer` sub-agent wrapped as an `AgentTool` (`skip_summarization: true`) alongside all nine built-in `swegemma` tools on the root `coder` agent. Because calling `code_analyzer` is discretionary, a small 4B model may bypass it and execute exploratory file reads directly inside its root context window.
3. **Stage-Isolated Sequential Decomposition Hypothesis:** Replacing discretionary delegation with a mandatory `SequentialAgent` pipeline (`TriageAgent` $\to$ `PatchAgent` $\to$ `VerifierAgent`) that sets `include_contents: "none"` at stage boundaries deterministically bounds stage-entry prompt length and enforces separation between localization, editing, and verification.

---

## 2. Exact Stage-Boundary Slicing in `google-adk` and `swegemma`

All configurations run inside the competition's `swegemma` harness, which provides nine built-in tools (`run_command`, `read_file`, `edit_file`, `write_file`, `get_status`, `submit_patch`, and the pre-computed NetworkX AST call-graph and `.npz` node-embedding tools `search_similar_code`, `get_code_neighbors`, `get_code_subgraph`).

In `google-adk==1.36.1` (`google/adk/flows/llm_flows/contents.py` and `functions.py`):
- Tool calls and tool responses created during a sub-agent's execution have `event.author = invocation_context.agent.name`.
- When `include_contents: "none"` is set on `PatchAgent` and `VerifierAgent` inside a `SequentialAgent`, `_get_current_turn_contents()` scans `session.events` backward from `len(events) - 1` and slices `session.events[k:]` at the first event where `_is_other_agent_reply(agent.name, event)` is `True`—which is the immediately preceding sub-agent's final text emission event.
- This slices out all prior sub-agent tool calls, tool responses, thoughts, and `events[0]` (the initial `build_agent_prompt` with the 200-entry workspace directory tree), while `inject_session_state()` (`google/adk/utils/instructions_utils.py`) interpolates `{problem_description?}`, `{localization_packet?}`, and `{patch_manifest?}` from `session.state` into the active sub-agent's system prompt.

| Mechanism / Rule | Enforced in Code / YAML Config | Prompt-Requested Only (Unenforced) |
| :--- | :--- | :--- |
| **Stage execution & tool separation** | `SequentialAgent` order; per-stage `tools:` lists in `sub_agents/*.yaml` | Adhering to $\le 3$ tool calls in `TriageAgent` / `PatchAgent` |
| **Cross-stage context reset** | `include_contents: "none"` slices `events[k:]` at stage entry | Within-stage turn count (bounded only by global `max_turns=20`) |
| **State packet handoff** | `output_key` writes final text to `session.state`; `{var?}` interpolation | Formatting text inside `<localization_packet>` / `<patch_manifest>` tags |
| **Observation size caps** | `read_file` $\le 150$ lines / 10k chars; `run_command` stdout $\le 5$k chars | Reading narrow `start_line`..`end_line` slices |
| **Test & workspace hygiene** | `strip_protected_files_from_patch` strips edits to `tests/*`, `pytest.ini`, `conftest.py` | Running targeted `pytest` (not bare `pytest`); putting scratch scripts in `/tmp/` |
| **Task session budgets** | `eval_config.yaml`: `max_tool_calls=15`, `max_turns=20`, `max_time_minutes=2.5` | Calling `submit_patch` before budget exhaustion (harness has auto-diff fallback) |

---

## 3. Paired Empirical Evaluation (`gemma-4-e4b-it-qat-w4a16-ct`)

All experiments were executed on Kaggle's 4x NVIDIA L4 GPU environment (`machine_shape: "NvidiaL4"`, 96 GB total VRAM, `tensor_parallel_size=4`, `vLLM` serving `gemma-4-e4b-it-qat-w4a16-ct`, `temperature=0.0`, `seed=42`, `max_output_tokens=8192`, `thinking_budget=1536`, `max_tool_calls=15`, `max_turns=20`, `max_time_minutes=2.5`) across a deterministic stratified subset of $n = 8$ tasks (first $k_r$ tasks per repository in canonical `tasks.jsonl` order across `fastapi/fastapi`, `Textualize/rich`, `psf/requests`, and `encode/httpx`).

### Table 2: Aggregate Paired Results ($n = 8$)

| Configuration | Resolved ($k/n$) | 95% Wilson CI | Non-Empty Patch | Mean Peak $P_t$ | Max Peak $P_t$ | Mean Cum. Tokens | Mean Tools | Mean Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Official Starter Kit (`agent_tool` pattern) | 0/8 (0.0%) | [0.0%, 32.4%] | 6/8 (75.0%) | 12855.2 | 14736 | 93509.9 | 8.9 | 103.2s |
| Controlled Single-Agent (`LlmAgent`) | 0/8 (0.0%) | [0.0%, 32.4%] | 8/8 (100.0%) | 12456.4 | 14912 | 109507.1 | 9.8 | 89.0s |
| State-Filtered Deliberation (`SequentialAgent`) | 1/8 (12.5%) | [2.2%, 47.1%] | 7/8 (87.5%) | 9298.1 | 14454 | 80790.9 | 10.9 | 92.7s |

- **`sfd` vs. `flat_starter`:** $\Delta = +12.50%$, 95% paired bootstrap CI $[-0.00%, +37.50%]$, discordant pairs $(b=1, c=0)$, exact two-sided McNemar $p = 1.0000$.
- **`sfd` vs. `flat_controlled`:** $\Delta = +12.50%$, 95% paired bootstrap CI $[-0.00%, +37.50%]$, discordant pairs $(b=1, c=0)$, exact two-sided McNemar $p = 1.0000$.
- **Measured Stage-Boundary Prompt Reset (`sfd`):** Mean `TriageAgent` peak prompt is **8558.5 tokens** (max 14454), which resets to **1534.9 tokens** (max 2126, a **-82.1%** reduction from `TriageAgent` peak) at `PatchAgent` entry, reaches a mean `PatchAgent` peak of **5730.1 tokens** (max 12680), and resets again to **1559.4 tokens** (max 2165) at `VerifierAgent` entry. Across all three configurations, zero tasks hit the 32,768-token hardware overflow ceiling (`0.0%` overflow rate) under the 15-tool-call budget.

---

## 4. Per-Task Trace Analysis & Failure Taxonomy

### Table 3: Task-by-Task Paired Outcomes and Peak Prompt Tokens ($\max_t P_t$)

| Task ID | Repository | `flat_starter` (Peak $P_t$) | `flat_controlled` (Peak $P_t$) | `sfd` (Peak $P_t$) |
| :--- | :--- | :--- | :--- | :--- |
| `fastapi_15588` | `fastapi/fastapi` | Fail (`test_verification_failed`) (13083) | Fail (`test_verification_failed`) (10785) | Fail (`test_verification_failed`) (7291) |
| `fastapi_15589` | `fastapi/fastapi` | Fail (`test_verification_failed`) (14711) | Fail (`test_verification_failed`) (14912) | Fail (`timeout_or_budget_no_patch`) (14454) |
| `fastapi_15661` | `fastapi/fastapi` | Fail (`test_verification_failed`) (11099) | Fail (`test_verification_failed`) (14445) | Fail (`test_verification_failed`) (7180) |
| `httpx_3672` | `encode/httpx` | Fail (`test_verification_failed`) (14736) | Fail (`test_verification_failed`) (13010) | Fail (`test_verification_failed`) (8140) |
| `requests_7502` | `psf/requests` | Fail (`test_verification_failed`) (10436) | Fail (`test_verification_failed`) (11238) | Fail (`test_verification_failed`) (14446) |
| `requests_7505` | `psf/requests` | Fail (`test_verification_failed`) (10800) | Fail (`test_verification_failed`) (12318) | Fail (`test_verification_failed`) (10659) |
| `rich_4070` | `Textualize/rich` | Fail (`timeout_or_budget_no_patch`) (13298) | Fail (`test_verification_failed`) (14826) | Fail (`test_verification_failed`) (8499) |
| `rich_4077` | `Textualize/rich` | Fail (`timeout_or_budget_no_patch`) (14679) | Fail (`test_verification_failed`) (8117) | Pass (3716) |

### Table 4: Measured Stage-Boundary Prompt Token Resets Across All `sfd` Trajectories ($n = 8$)

| Task ID | Triage Entry | Triage Peak | Patch Entry ($\Delta$ vs. Triage Peak) | Patch Peak | Verifier Entry | Verifier Peak |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `fastapi_15588` | 3373 | 4979 | 1877 (-62.3%) | 7291 | 1818 | 2333 |
| `fastapi_15589` | 3083 | 14454 | 1534 (-89.4%) | 12680 | 1588 | 1588 |
| `fastapi_15661` | 2993 | 3873 | 1505 (-61.1%) | 7180 | 1557 | 4875 |
| `httpx_3672` | 2116 | 7842 | 1261 (-83.9%) | 5007 | 1304 | 8140 |
| `requests_7502` | 1914 | 14446 | 1480 (-89.8%) | 2714 | 1427 | 3042 |
| `requests_7505` | 2102 | 10659 | 1293 (-87.9%) | 2784 | 1362 | 1812 |
| `rich_4070` | 4829 | 8499 | 2126 (-75.0%) | 5380 | 2165 | 7542 |
| `rich_4077` | 2903 | 3716 | 1203 (-67.6%) | 2805 | 1254 | 1970 |

### Rule-Based Unresolved Failure Taxonomy
- **Official Starter Kit (`agent_tool` pattern)**: `timeout_or_budget_no_patch`: 2 (`rich_4070`, `rich_4077`); `test_verification_failed`: 6 (`fastapi_15588`, `fastapi_15589`, `fastapi_15661`, `httpx_3672`, `requests_7502`, `requests_7505`).
- **Controlled Single-Agent (`LlmAgent`)**: `test_verification_failed`: 8 (`fastapi_15588`, `fastapi_15589`, `fastapi_15661`, `httpx_3672`, `requests_7502`, `requests_7505`, `rich_4070`, `rich_4077`).
- **State-Filtered Deliberation (`SequentialAgent`)**: `timeout_or_budget_no_patch`: 1 (`fastapi_15589`); `test_verification_failed`: 6 (`fastapi_15588`, `fastapi_15661`, `httpx_3672`, `requests_7502`, `requests_7505`, `rich_4070`).

### Trace Findings on Hypotheses 1–3 & Concrete Case Studies

1. **Discretionary `AgentTool` Bypass in `flat_starter` (Testing Hypothesis 2):** Inspection of the ATIF v1.7 traces (`traces/eval_results/flat_starter/traces/`) shows that across 8 tasks and 79 total tool invocations, `swe_baseline_agent` called `code_analyzer_agent` only **2 times (2.5% of tool calls)**, occurring on just 2/8 tasks (`requests_7505` and `rich_4077`), while **6/8 tasks (75.0%)** bypassed `code_analyzer_agent` entirely and executed all file reads and commands directly in the root context window. On both `Textualize/rich` tasks (`rich_4070` and `rich_4077`), `flat_starter` exhausted its time or tool-call budget in exploratory reads without ever calling `edit_file` (`timeout_or_budget_no_patch`, 0/2 patches generated on `Textualize/rich`).
2. **Case Study 1 — `rich_4077` (Resolved by `sfd`, Failed by `flat_starter` and `flat_controlled`):** Task `rich_4077` requires adding a missing `isatty()` method to `FileProxy` in `rich/file_proxy.py` that delegates to `self.__file.isatty()`.
   - In `flat_starter` (`trace_rich_4077.json`), the root agent spent all 15 tool calls running shell commands and reading files in its main context (`14,679` peak prompt tokens, `137,296` cumulative tokens), invoking `code_analyzer_agent` only on tool call 13 and terminating with an empty patch (`0` chars).
   - In `flat_controlled` (`trace_rich_4077.json`), the single agent localized `rich/file_proxy.py` (`8,117` peak prompt tokens, `51,036` cumulative tokens) and generated a 454-character patch, but wrote `import os` and `return os.isatty(self.__file.fileno())`, which fails Phase 2 `pytest` verification (`test_verification_failed`) when the wrapped stream does not expose an OS file descriptor.
   - In `sfd` (`trace_rich_4077.json`), `TriageAgent` read `rich/file_proxy.py` (`2,903` $\to$ `3,716` prompt tokens) and emitted a `<localization_packet>` specifying `return self.__file.isatty()`. At `PatchAgent` entry, `include_contents: "none"` reset the prompt from `3,716` to `1,203` tokens (-67.6%). `PatchAgent` read lines 1–65 of `rich/file_proxy.py`, applied `def isatty(self) -> bool: return self.__file.isatty()` (`1,990` prompt tokens, `2,805` stage peak), and emitted `<patch_manifest>`. `VerifierAgent` entered at `1,254` prompt tokens, verified `tests/test_file_proxy.py`, and called `submit_patch` (`323`-char patch, `22,695` cumulative tokens, `resolved=True`, `test_exit_code=0`).
3. **Case Study 2 — `fastapi_15589` (Runtime-Enforced Slicing vs. Unenforced Within-Stage Call Count):** On `fastapi_15589` (`trace_fastapi_15589.json`), `TriageAgent` ignored the prompt-level instruction to stop after $\le 3$ tool calls and executed 10 read-only calls (`1` `search_similar_code` + `9` `read_file`), reaching `14,454` prompt tokens. While `include_contents: "none"` still enforced a hard stage-entry reset at `PatchAgent` (`14,454` $\to$ `1,534` prompt tokens, -89.4%), `TriageAgent` had consumed 10 of the 15 global `max_tool_calls`. After `PatchAgent` read 6 file slices (`1,534` $\to$ `10,927` prompt tokens) and attempted `edit_file`, the harness blocked the edit (`Tool call limit reached (15)`), resulting in an empty patch (`timeout_or_budget_no_patch`). This trace directly illustrates the distinction in Table 1: cross-stage context slicing is enforced in code by `google-adk`, whereas preventing a single stage from exhausting the global `max_tool_calls=15` budget requires per-stage code caps rather than prompt instructions alone.
4. **Localization & Semantic Edit Accuracy Bottleneck:** Across the 6 tasks where `sfd` generated a non-empty patch that failed Phase 2 verification (`fastapi_15588`, `fastapi_15661`, `httpx_3672`, `requests_7502`, `requests_7505`, `rich_4070`), trace inspection confirms that context slicing kept `PatchAgent` entry prompts between `1,261` and `2,126` tokens, but the 4-bit quantized E4B model failed verification due to incomplete multi-site edits or subtle edge-case semantics tested by `task.test_patch`.

---

## 5. Related Work

- **Staged vs. Monolithic SWE Agents:** SWE-agent (Yang et al., 2024) and OpenHands (Wang et al., 2024) equip an LLM with an interactive bash/file environment inside a continuous trajectory. Conversely, Agentless (Xia et al., 2024) demonstrated that a fixed pipeline of localization followed by repair without autonomous shell loops is competitive on frontier models. SFD bridges these two paradigms within Google ADK: each stage (`TriageAgent`, `PatchAgent`, `VerifierAgent`) remains a tool-using `LlmAgent`, but stage transitions enforce hard context resets and role-specific tool permissions.
- **Observation Masking vs. LLM Summarization:** Recent empirical work by Lindenbauer et al. (2025) (*"The Complexity Trap"*) compares LLM-based trajectory summarization against simple environment observation masking in software engineering agents, finding that masking stale tool observations halves token costs while matching or outperforming LLM summarization on SWE-bench Verified. SFD's stage transition mechanism aligns directly with this finding: rather than invoking a separate LLM summarizer call over raw file reads, `TriageAgent` emits a compact localization packet as its natural final turn, and `include_contents: "none"` masks 100% of prior raw tool observations at the `PatchAgent` and `VerifierAgent` boundaries.

---

## 6. Limitations & Threats to Validity

1. **Sample Size and Statistical Power:** Because each full two-phase task evaluation requires isolated container setup, multi-turn GPU inference, and hermetic `pytest` verification, our paired controlled evaluation covers $n = 8$ stratified tasks (24 total runs). At $n = 8$, Wilson confidence intervals are wide and small differences in resolution rate are not statistically significant (McNemar $p = 1.0000$). Full 129-task evaluation is required to detect small effect sizes ($\le 5\%$).
2. **Irrecoverable Triage Mislocalization & Shared Global Tool Budget:** Because `PatchAgent` has `include_contents: "none"` and lacks `search_similar_code` or `run_command`, if `TriageAgent` misidentifies `target_file`, `PatchAgent` cannot re-search the repository graph. Moreover, because `swegemma` enforces `max_tool_calls=15` globally across the session rather than per sub-agent, excessive read calls in `TriageAgent` (as observed on `fastapi_15589`) can starve `PatchAgent` of tool budget unless per-stage caps are enforced in Python callbacks.
3. **Repository Skew and Pre-Training Overlap:** In the 129-task competition dataset, 51.9% of tasks come from `fastapi/fastapi` and 37.2% from `Textualize/rich`. Furthermore, because these are public open-source repositories, historical code context may overlap with Gemma 4 pre-training corpora.

---

## 7. Conclusion & Reproducibility

We presented State-Filtered Deliberation (SFD), a declarative 3-stage `SequentialAgent` architecture for small open-weight developer agents on the `swegemma` harness, and evaluated it via real paired execution traces on `gemma-4-e4b-it-qat-w4a16-ct`. While stage-boundary context slicing via `include_contents: "none"` deterministically reduces `PatchAgent` and `VerifierAgent` entry prompts to ~1535–1559 tokens (-82.1% from `TriageAgent` peak) and reduces mean single-call peak prompt tokens by 27.7% vs. `flat_starter` (9298.1 vs. 12855.2) and 25.4% vs. `flat_controlled` (9298.1 vs. 12456.4), overall end-to-end resolution on 4-bit E4B remains tightly constrained by fault-localization accuracy and patch semantics (1/8 = 12.5% vs. 0/8 = 0.0%, McNemar $p = 1.0000$). All 24 real ATIF v1.7 traces (`traces/eval_results/`), aggregation scripts (`scripts/aggregate.py`), and consistency checks (`scripts/check_consistency.py`) are available at `https://github.com/KarandeepSinghSodhi/gemma-sfd-agent`.

---

## References

1. Jimenez, C. E., et al. (2024). *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* ICLR 2024.
2. Yao, S., et al. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models.* ICLR 2023.
3. Xia, C. S., et al. (2024). *Agentless: Demystifying LLM-based Software Engineering Agents.* arXiv:2407.01489.
4. Yang, J., et al. (2024). *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering.* arXiv:2405.15793.
5. Wang, X., et al. (2024). *OpenHands: An Open Platform for AI Software Developers as Generalist Agents.* arXiv:2407.16741.
6. Lindenbauer, T., Slinko, I., Felder, L., Bogomolov, E., & Zharov, Y. (2025). *The Complexity Trap: Simple Observation Masking Is as Efficient as LLM Summarization for Agent Context Management.* arXiv:2508.21433 (NeurIPS 2025 DL4C Workshop).
7. Gemma Team, Google DeepMind (2026). *Gemma 4 Technical Report.* arXiv:2607.02770.
