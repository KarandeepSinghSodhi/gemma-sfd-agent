# State-Filtered Deliberation: Stage-Isolated Context Management for Small Open-Weight Software Engineering Agents

**Author:** Karandeep Singh Sodhi (Independent Researcher — `https://github.com/KarandeepSinghSodhi/gemma-sfd-agent`)  
**Track:** Google — The Gemma 4 Developer Agent Competition (Paper Track)  
**Artifact Repository:** `https://github.com/KarandeepSinghSodhi/gemma-sfd-agent` (Tag: `v1.0.1-camera-ready`)  
**Companion Resource Paper:** [Sodhi (2026)](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent/blob/v1.0.1-camera-ready/KAGGLE_WRITEUP_RESOURCE.md)

---

## Abstract

On the Gemma 4 Developer Agent Challenge Small Model Prize leaderboard (197 teams, 2026-10-24 UTC), public resolution rates on 4-bit quantized E2B/E4B models range from 0.0% to 10.0% (median 5.0%), compared to 22.0%–24.0% for 31B models. We study **State-Filtered Deliberation (SFD)**, a declarative three-stage `SequentialAgent` architecture in Google ADK and `swegemma` (`TriageAgent` → `PatchAgent` → `VerifierAgent`) that configures `include_contents: "none"` on downstream stages to slice out prior tool observations while passing structured state variables (`localization_packet` and `patch_manifest`). Across n = 16 paired tasks on `gemma-4-e4b-it-qat-w4a16-ct` (64 total runs on 4x NVIDIA L4 GPUs) against the official starter kit (`flat_starter`) and a controlled single-agent baseline (`flat_controlled`), SFD resets stage-entry prompts from a mean `TriageAgent` peak of 10,922.1 tokens to 1,500.9 tokens at `PatchAgent` entry (-86.3%), lowers per-task peak prompt length relative to `flat_controlled` on 13/16 tasks (sign test p = 0.0213, mean 11291.9 vs 13550.8 tokens; 13029.3 on flat_starter), and reduces cumulative total tokens by 25.7% vs `flat_controlled` (88,909.5 vs 119,664.4, sign test p = 0.0213). In this 16-task sample, `flat_starter` bypasses its discretionary `code_analyzer` sub-agent on 13/16 tasks (81.2%). End-to-end task resolution shows a null difference: 1/16 (6.2%, 95% Wilson CI [1.1%, 28.3%]) for `sfd` and `flat_starter`, and 0/16 (0.0%, CI [0.0%, 19.4%]) for `flat_controlled` (McNemar p = 1.0000).

---

## 1. Introduction & Motivating Hypotheses

Repository-level software engineering benchmarks such as SWE-bench (Jimenez et al., 2024) evaluate autonomous coding agents on bug localization, patch synthesis, and regression testing. While 31B models achieve up to 24.0% public resolution, compact models face severe capability constraints. On the official Small Model Prize leaderboard (E2B/E4B models, 197 teams), scores range from 0.0% to 10.0% (mean 4.23%, median 5.0%), with 92.9% of teams scoring ≤ 6.0%.

We formulate and evaluate three hypotheses on `gemma-4-e4b-it-qat-w4a16-ct`:
1. **Prompt-Length Error Correlation (H1):** As per-call prompt length P_t increases with accumulated tool observations, non-budget tool errors and duplicate file reads occur more frequently.
2. **Discretionary Sub-Agent Under-Utilization (H2):** In the official starter kit, discretionary delegation to `code_analyzer` is underutilized by the 4B model in favor of unpruned root reads.
3. **Stage-Entry Context Reset & Role Partitioning (H3):** A declarative `SequentialAgent` pipeline (`TriageAgent` → `PatchAgent` → `VerifierAgent`) with `include_contents: "none"` deterministically bounds stage-entry prompt length, lowering typical per-task peak prompts while isolating localization from patch editing.

---

## 2. Context Mechanics in `swegemma` and `google-adk`

### 2.1 Prompt Growth and the Token Signal Ratio
Consider an agent trajectory across LLM calls t ∈ {1, 2, ..., T}. In a continuous single-agent session (`include_contents: "default"`), prompt P_t concatenates the system instruction s_0, initial harness task prompt u_0, and all prior turns a_i and observations o_i:
```text
P_t = |s_0| + |u_0| + Σ_{i=1}^{t-1} (|a_i| + |o_i|)
```
In `swegemma`, even at t = 1, |s_0| + |u_0| spans ~1,900–4,800 tokens because `build_agent_prompt()` embeds the problem statement, budget rules, tool schemas, and up to 200 directory tree entries under `/workspace`.

### 2.2 Exact Stage-Boundary Slicing via `include_contents: "none"`
Inspection of `google-adk==1.36.1` reveals the exact runtime behavior:
- When `include_contents: "none"` is configured on `PatchAgent` or `VerifierAgent`, `_ContentLlmRequestProcessor` calls `_get_current_turn_contents()`.
- This function scans backward through `session.events` to the immediately preceding sub-agent's final emission event e_k, slicing `session.events[k:]`.
- This deterministically excludes all previous intermediate tool calls, observations, and initial workspace layouts, bounding **stage-entry** prompt length by construction. Crucially, within-stage tool history accumulates normally.

---

## 3. Architecture: Runtime-Enforced vs. Prompt-Requested Rules

SFD chains three sub-agents under a root `SequentialAgent`:
1. **`TriageAgent` (`output_key: "localization_packet"`):** Restricted in YAML to 5 read-only tools (`search_similar_code`, `get_code_neighbors`, `get_code_subgraph`, `read_file`, `get_status`).
2. **`PatchAgent` (`include_contents: "none"`, `output_key: "patch_manifest"`):** Restricted to 4 workspace tools (`read_file`, `edit_file`, `write_file`, `get_status`). Interpolates `{problem_description?}` and `{localization_packet?}`.
3. **`VerifierAgent` (`include_contents: "none"`):** Equipped with `run_command`, `read_file`, `edit_file`, `get_status`, and `submit_patch`.

### Table 1: Runtime-Enforced Constraints vs. Prompt-Level Directives

| Mechanism / Rule | Enforced in Code / YAML Config | Prompt-Requested Only (Unenforced) |
| :--- | :--- | :--- |
| **Stage & Tool Separation** | `SequentialAgent` order; per-stage `tools:` lists | Stopping after ≤ 3 tool calls per stage |
| **Cross-Stage Context Reset** | `include_contents: "none"` slices `events[k:]` | Within-stage prompt growth & turn duration |
| **State Packet Handoff** | `output_key` writes to `session.state`; `{var?}` injection | Formatting text inside `<localization_packet>` tags |
| **Observation Caps** | `read_file` ≤ 150 lines / 10k chars; stdout ≤ 5k chars | Reading narrow `start_line`..`end_line` slices |
| **Hygiene & Budgets** | Protected files stripped from patch; global 15-tool cap | Targeted `pytest` runs; calling `submit_patch` in time |

---

## 4. Experimental Setup & Paired Evaluation Results

Experiments ran on 4x NVIDIA L4 GPUs (96 GB VRAM, `tensor_parallel_size=4`, vLLM, `gemma-4-e4b-it-qat-w4a16-ct`, `temperature=0.0`, `seed=42`, `thinking_budget=1536`, `max_tool_calls=15`, `max_turns=20`, `max_time_minutes=2.5`).
- **Two-Cohort Sampling (n = 16 tasks, 64 runs):** Cohort 1 (canonical, n = 8) yielded 1/8 for `sfd` (`rich_4077`), 0/8 for `flat_starter`, 0/8 for `flat_controlled`. Cohort 2 (seeded-random, n = 8) yielded 0/8 for `sfd`, 1/8 for `flat_starter` (`fastapi_9753`), 0/8 for `flat_controlled`.
- **Controlled Baseline (`flat_controlled`):** Matches SFD's 9 tools, combined prompt text, and sampling parameters in a single `LlmAgent` (`include_contents: "default"`).

### Table 2: Aggregate Paired Results (n = 16 Tasks)

| Configuration | Resolved (k/n) | 95% Wilson CI | Non-Empty Patch | Mean Peak P_t | Max Peak P_t | Mean Cum. Tokens | Mean Duration |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Official Starter (`flat_starter`)** | 1/16 (6.2%) | [1.1%, 28.3%] | 13/16 (81.2%) | 13029.3 | 15281 | 103,350.1 | 97.3s |
| **Single-Agent (`flat_controlled`)** | 0/16 (0.0%) | [0.0%, 19.4%] | 14/16 (87.5%) | 13550.8 | 16154 | 119,664.4 | 92.2s |
| **State-Filtered Deliberation (`sfd`)** | 1/16 (6.2%) | [1.1%, 28.3%] | 14/16 (87.5%) | 11291.9 | 16146 | 88,909.5 | 89.4s |

- **Primary Resolution vs. Cost Tests:** Paired resolution shows a null difference across all comparisons (McNemar p = 1.0000). In exploratory paired context comparisons:
  - **vs `flat_controlled`:** Peak prompt is **-2,258.8 tokens (-16.7%)** lower (95% CI [-3,734.9, -789.6], lower on **13/16 tasks**, sign test **p = 0.0213**). Cumulative tokens are **-30,754.9 tokens (-25.7%)** lower (95% CI [-52,067.0, -10,336.1], lower on **13/16 tasks**, sign test **p = 0.0213**).
  - **vs `flat_starter`:** Peak prompt is **-1,737.4 tokens (-13.3%)** lower (lower on 11/16 tasks, sign test p = 0.2101); cumulative tokens are **-14,440.6 tokens (-14.0%)** lower (lower on 11/16 tasks, p = 0.2101).
- **Rerun Reproducibility (Cohort 1, 16 runs):** Rerunning `sfd` and `flat_controlled` on Cohort 1 showed 100% and 87.5% resolution agreement. Interestingly, `flat_controlled_rerun` also resolved `rich_4077` (1/8), demonstrating that single-task resolution differences at n = 16 are within run-to-run execution variance.
- **Stage-Entry Reset vs. Trajectory Peak:** Across 16 `sfd` runs, `TriageAgent` reaches a mean peak prompt of **10,922.1 tokens** (max 16,146). At `PatchAgent` entry, prompts reset to a mean of **1,500.9 tokens** (max 2,126)—a **-86.3% reset**. `VerifierAgent` entry resets to a mean of **1,470.2 tokens**. SFD lowers typical per-task peaks on 13/16 tasks, but does not bound upper-tail peaks when `TriageAgent` loops until budget exhaustion.

---

## 5. Hypothesis Testing, Case Studies & Failure Taxonomy

### Table 3: Task-by-Task Outcomes and Peak Prompt Tokens (max_t P_t)

| Task ID | Repo | `flat_starter` (Peak P_t) | `flat_controlled` (Peak P_t) | `sfd` (Peak P_t) | Stage 1→2 Reset |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `fastapi_14099` | `fastapi` | Fail (15,281) | Fail (13,933) | Fail (15,961) | 15,961 → 1,746 (-89.1%) |
| `fastapi_14361` | `fastapi` | Fail (10,191) | Fail (15,010) | Fail (9,831) | 9,831 → 1,192 (-87.9%) |
| `fastapi_14459` | `fastapi` | Fail (14,820) | Fail (16,154) | Fail (15,605) | 15,605 → 1,804 (-88.4%) |
| `fastapi_15588` | `fastapi` | Fail (13,083) | Fail (10,785) | Fail (7,291) | 4,979 → 1,877 (-62.3%) |
| `fastapi_15589` | `fastapi` | Fail (14,711) | Fail (14,912) | Fail (14,454) | 14,454 → 1,534 (-89.4%) |
| `fastapi_15661` | `fastapi` | Fail (11,099) | Fail (14,445) | Fail (7,180) | 3,873 → 1,505 (-61.1%) |
| `fastapi_9753` | `fastapi` | **Pass** (11,047) | Fail (11,743) | Fail (6,469) | 6,469 → 1,881 (-70.9%) |
| `httpx_3672` | `httpx` | Fail (14,736) | Fail (13,010) | Fail (8,140) | 7,842 → 1,261 (-83.9%) |
| `requests_7427` | `requests` | Fail (9,747) | Fail (15,387) | Fail (13,362) | 13,362 → 1,326 (-90.1%) |
| `requests_7502` | `requests` | Fail (10,436) | Fail (11,238) | Fail (14,446) | 14,446 → 1,480 (-89.8%) |
| `requests_7505` | `requests` | Fail (10,800) | Fail (12,318) | Fail (10,659) | 10,659 → 1,293 (-87.9%) |
| `rich_3043` | `rich` | Fail (14,789) | Fail (14,820) | Fail (14,384) | 14,384 → 1,388 (-90.4%) |
| `rich_3944` | `rich` | Fail (15,175) | Fail (15,031) | Fail (14,528) | 14,528 → 1,187 (-91.8%) |
| `rich_4070` | `rich` | Fail (13,298) | Fail (14,826) | Fail (8,499) | 8,499 → 2,126 (-75.0%) |
| `rich_4076` | `rich` | Fail (14,577) | Fail (15,083) | Fail (16,146) | 16,146 → 1,212 (-92.5%) |
| `rich_4077` | `rich` | Fail (14,679) | Fail (8,117) | **Pass** (3,716) | 3,716 → 1,203 (-67.6%) |

### 5.1 Testing Hypothesis 1: Tool Error Rates by Prompt-Length Bucket
Table 4 groups all 563 tool calls across the 48 primary runs into four prompt token buckets. Separating `BudgetExceeded` (cap rejections) from genuine tool errors shows that non-budget error rates remain flat across the first three buckets (13.0%, 15.5%, 13.8%) before rising slightly to 18.1% at P_t ≥ 12,000. Hypothesis 1 is **inconclusive** in these traces.

#### Table 4: Tool Errors & Budget Caps by Prompt Length (P_t)

| Prompt Bucket (P_t) | LLM Calls | Tool Calls | Non-Budget Tool Errors | `BudgetExceeded` | `edit_file` Errors | Duplicate Reads |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `< 4,000` | 155 | 138 | 18/138 (13.0%) | 1/138 | 4/20 (20.0%) | 6/50 (12.0%) |
| `4,000 - 7,999` | 220 | 193 | 30/193 (15.5%) | 3/193 | 12/38 (31.6%) | 3/102 (2.9%) |
| `8,000 - 11,999` | 183 | 160 | 22/160 (13.8%) | 4/160 | 11/30 (36.7%) | 6/54 (11.1%) |
| `≥ 12,000` | 85 | 72 | 13/72 (18.1%) | 1/72 | 7/17 (41.2%) | 5/25 (20.0%) |

### 5.2 Testing Hypothesis 2: Discretionary Sub-Agent Bypassing
In `flat_starter`, root made 149 non-submit tool decisions. It delegated to `code_analyzer` only **4 times (2.7%)**, completely bypassing delegation on **13 of 16 tasks (81.2%)**. This confirms **Hypothesis 2**: compact models rarely delegate voluntarily when root tools are available.

### 5.3 Case Studies & Ground-Truth Localization Audit
- **`rich_4077` (Resolved by SFD):** `flat_starter` exhausted 15 calls without editing. `flat_controlled` wrote `os.isatty(self.__file.fileno())`, failing because the mock file lacked `fileno()`. SFD's `TriageAgent` localized `rich/file_proxy.py` at 3,716 tokens and specified `def isatty(self) -> bool: return self.__file.isatty()`. `PatchAgent` entered at 1,203 tokens and applied this exact fix (`resolved=True`).
- **`fastapi_9753` (Resolved by Starter, Failed by SFD):** `flat_starter` edited `Dependant._unwrapped_call` in `fastapi/dependencies/models.py`, resolving the task. SFD's `TriageAgent` localized `utils.py` instead of `models.py`. Because `PatchAgent` operates with isolated context, it could not recover from the upstream mislocalization.

#### Table 5: Ground-Truth File Localization Taxonomy Across 16 SFD Runs

| Localization Category | Count (%) | Empirical Diagnosis across SFD Runs (`traces/`) |
| :--- | :---: | :--- |
| **Exact Single File** | 4/16 (25.0%) | `rich_4077` (resolved), `fastapi_15588` (wrong error string), `fastapi_15589` (budget limit before edit), `rich_3043` (4 `edit_file` string mismatches). |
| **Partial Multi-File** | 6/16 (37.5%) | Localized 1 file of a multi-file reference patch: `fastapi_14099`, `fastapi_14459`, `httpx_3672`, `requests_7502`, `requests_7505`, `rich_4070`. |
| **Wrong File / Symbol** | 6/16 (37.5%) | Misidentified target module: `fastapi_14361`, `fastapi_15661`, `fastapi_9753`, `requests_7427`, `rich_3944`, `rich_4076`. |

---

## 6. Related Work

- **Staged vs. Monolithic Agents:** SWE-agent (Yang et al., 2024) and OpenHands (Wang et al., 2024) execute continuous bash/file loops. Agentless (Xia et al., 2024) demonstrated that a two-phase pipeline without shell loops is competitive on frontier models. SFD combines tool-using sub-agents with declarative stage-boundary context slicing.
- **Observation Masking:** Lindenbauer et al. (2025) (*"The Complexity Trap"*, arXiv:2508.21433) show that observation masking matches or beats LLM summarization. SFD's `include_contents: "none"` operates as a coarse stage-boundary observation mask.

---

## 7. Limitations & Threats to Validity

1. **Sample Size & Power (n = 16):** With small samples, detecting a 10% resolution difference requires N ≈ 115–130 paired tasks. Single-task differences are within run-to-run execution variance.
2. **Budget Confounding:** 7/48 primary runs failed due to global tool/time caps (`max_tool_calls=15`, 2.5 min), confounding context effects with budget exhaustion.
3. **Error Propagation:** Strict stage isolation prevents `PatchAgent` from recovering when `TriageAgent` misidentifies the target file.

---

## 8. Conclusion & Reproducibility

Across 64 execution runs on `gemma-4-e4b-it-qat-w4a16-ct`, State-Filtered Deliberation demonstrates that:
1. Compact models bypass discretionary delegation in 81.2% of tasks.
2. Configuring `include_contents: "none"` deterministically resets stage-entry prompts by 86.3% (10,922 to 1,501 tokens), reducing per-task peak prompts on 13/16 tasks (p = 0.0213) and cumulative tokens by 25.7% (p = 0.0213).
3. End-to-end task resolution shows a null difference (6.2% vs 0.0%, p = 1.0000), dominated by upstream localization and editing errors.

All code, traces, and scripts are open-sourced:
- **Repository:** `https://github.com/KarandeepSinghSodhi/gemma-sfd-agent` (Tag: `v1.0.1-camera-ready`)
- **Companion Diagnostic Resource Paper:** [ATIF-Gemma](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent/blob/v1.0.1-camera-ready/KAGGLE_WRITEUP_RESOURCE.md)
- **Kaggle Kernel:** `https://www.kaggle.com/code/karandeepsinghsodhi/sfd-state-filtered-deliberation-agent-gemma-4`

---

## References

1. Jimenez, C. E., et al. (2024). *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* ICLR 2024.
2. Yao, S., et al. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models.* ICLR 2023.
3. Xia, C. S., et al. (2024). *Agentless: Demystifying LLM-based Software Engineering Agents.* arXiv:2407.01489.
4. Yang, J., et al. (2024). *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering.* arXiv:2405.15793.
5. Wang, X., et al. (2024). *OpenHands: An Open Platform for AI Software Developers as Generalist Agents.* arXiv:2407.16741.
6. Lindenbauer, T., et al. (2025). *The Complexity Trap: Simple Observation Masking Is as Efficient as LLM Summarization for Agent Context Management.* arXiv:2508.21433.
7. Gemma Team, Google DeepMind (2026). *Gemma 4 Technical Report.* arXiv:2607.02770.