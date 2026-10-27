# ATIF-Gemma: An Open Empirical Diagnostic Corpus and Failure Taxonomy for Small Open-Weight Developer Agents

**Author:** Karandeep Singh Sodhi (Independent Researcher)  
**Track:** Google — The Gemma 4 Developer Agent Competition (Paper Track: Best New Resource)  
**Dataset:** [ATIF-Gemma SWE Agent Traces (Kaggle)](https://www.kaggle.com/datasets/karandeepsinghsodhi/atif-gemma-swe-agent-traces) | **Code:** [gemma-sfd-agent (GitHub)](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent)  
**Notebook:** [Diagnostic Exploration (Kaggle)](https://www.kaggle.com/code/karandeepsinghsodhi/atif-gemma-diagnostic-exploration) | **Manuscript:** [paper_resource.pdf](https://raw.githubusercontent.com/KarandeepSinghSodhi/gemma-sfd-agent/main/paper_resource.pdf)  

---

## Abstract

SWE agent benchmarks commonly report scalar resolution rates while discarding execution trajectories, obscuring failure causes. For compact, 4-bit models (`gemma-4-e4b-it-qat-w4a16-ct`), diagnosing low resolution (median 5.0% across 197 teams on the Small Model Prize leaderboard) is hindered by limited public trace data. We introduce **ATIF-Gemma**, an open diagnostic corpus of 112 execution traces (1,518 LLM turns, 1,328 tool calls, 11.7M tokens) across 32 paired SWE-bench tasks on 4x NVIDIA L4 GPUs with Google ADK and `swegemma`. All tasks originate from open-source repositories under MIT, Apache-2.0, and BSD-3-Clause licenses (documented in the dataset `NOTICE` file; `test_patch` is omitted).

Under the version-pinned ATIF v1.7 specification (100% schema-validated; Harbor Framework Contributors, 2026), ATIF-Gemma links actions to held-out test outcomes. In 96 primary runs (32 tasks $\times$ 3 configs), resolution is **6/96 (6.25%, 95% Wilson CI [2.90%, 12.97%])**, identical across configurations (**2/32 = 6.25% each**, 95% CI [1.73%, 20.15%]); pooled across all 112 runs (including 16 reruns), resolution is 8/112 (7.14%). Across the 26 tasks mutually valid across all three configurations (78 paired runs), resolution is strictly invariant at **2/26 (7.69%)** each (6/78, 7.69% overall). We define four failure mechanisms: assertion failures (50.0%, 56/112), collection errors (32.1%, 36/112), budget exhaustion (8.0%, 9/112), and verification timeouts (2.7%, 3/112). Analysis partitions collection errors into agent-attributable failures (44.4%) versus environment failures (55.6%; flagged `env_invalid=True` across 20 runs from missing sandbox packages or path shadowing). Excluding invalid runs yields **6/80 (7.50%)** primary and **8/92 (8.70%)** pooled resolution. We release the corpus, the `atif_gemma` package, and an actionable remediation guide.

---

## 1. Introduction & The Diagnostic Vacuum in SWE Benchmarking

Autonomous coding agents have advanced on benchmarks like SWE-bench (Jimenez et al., 2024), but evaluations remain **outcome-centric**: reporting scalar pass/fail rates while discarding tool trajectories, prompt expansions, and sandbox interactions that precede outcomes.

For compact, 4-bit models (`gemma-4-e4b-it-qat-w4a16-ct`), scalar benchmarking reveals an acute capability cliff: on the official Small Model Prize leaderboard (Holbrook, 2026), scores across 197 teams range from 0.0% to 10.0% (median 5.0%, mean 4.23%; 92.9% score $\le 6.0\%$). Developers cannot distinguish whether failure stemmed from localization errors, syntax corruption, environment artifacts, or tool exhaustion.

We introduce **ATIF-Gemma**, an open diagnostic trajectory corpus and toolkit providing 112 execution traces (11.7M tokens, 1,518 LLM turns, 1,328 tool calls) across 32 benchmark tasks under ATIF v1.7.

---

## 2. Related Work: Trajectory Corpora & Agent Diagnostics

### 2.1 SWE Agent Trajectories & Diagnostics
SWE-bench (Jimenez et al., 2024) established repository-level evaluation; SWE-agent (Yang et al., 2024) and OpenHands (Wang et al., 2024) introduced specialized ACIs. The Agent Trajectory Interchange Format (ATIF v1.7; Harbor Framework Contributors, 2026) standardized trajectory logging. Large trajectory sets (SWE-Gym, SWE-smith; Pan et al., 2024; Yang et al., 2025) and Gemma trajectory corpora (Rajak, 2026) provide valuable logs at scale. In diagnostics, Xia et al. (2024) (*Agentless*) showed multi-turn loops can degrade performance vs pipelines, while Lindenbauer et al. (2025) showed observation masking mitigates prompt bloat. ATIF-Gemma complements these resources with a dense paired sample on compact 4-bit models (Gemma 4 E4B), featuring deterministic failure taxonomy, agent vs environment attribution, localization trees, and linked Phase 2 outcomes.

### 2.2 Small Open-Weight Developer Agents
Gemma 4 (Gemma Team, 2026) introduced compact models (`gemma-4-e4b-it-qat-w4a16-ct`). While small models excel on isolated code synthesis (Chen et al., 2021; Austin et al., 2021), multi-turn repository repair exposes a steep capability cliff (median 5.0% resolution across 197 teams; Holbrook, 2026). ATIF-Gemma isolates whether this reflects reasoning limits, context bloat, or sandbox collection crashes.

---

## 3. Corpus Architecture & ATIF v1.7 Schema Specifications

### Table 1: Composition of the ATIF-Gemma Diagnostic Corpus

| Corpus Partition | Traces | Tasks | LLM Calls | Tool Calls | Total Tokens |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Cohort 1 (Canonical Paired)** | 24 | 8 | 304 | 265 | 2,270,463 |
| **Cohort 2 (Stratified Random)** | 24 | 8 | 339 | 298 | 2,720,322 |
| **Cohort 1 Rerun (Reproducibility)** | 16 | 8 | 204 | 172 | 1,387,758 |
| **Cohort 3 (Stratified Disjoint)** | 24 | 8 | 349 | 309 | 2,771,960 |
| **Cohort 4 (Stratified Disjoint)** | 24 | 8 | 322 | 284 | 2,555,675 |
| **Total ATIF-Gemma Corpus** | **112** | **32** | **1,518** | **1,328** | **11,706,178** |

*Note: Spans 32 unique tasks; Cohort 1 Rerun re-executes the 8 tasks of Cohort 1 for empirical reproducibility.*

The corpus spans 32 unique instances across 4 repositories: `fastapi` (51), `rich` (37), `requests` (19), and `httpx` (5), executed via vLLM 0.19.1 (`tp=4`) hosting `gemma-4-e4b-it-qat-w4a16-ct` with Google ADK 1.36.1 and `swegemma`.

Traces adhere to **ATIF v1.7 JSON Schema**, logging `instance_id`, repo metadata, step `metrics`, `tool_calls`, `observation`, reasoning (`extra.event_type: "thinking"`), duration, and Phase 2 exit codes.

**Schema Conformance:** 112/112 traces (100.0%) pass formal validation against version-pinned ATIF v1.7 schema (`dataset_resource/atif_schema_v1_7.json`; Harbor Framework Contributors, 2026). The test suite (`analysis/validate_atif_schema.py`) verifies all 1,942 steps, 1,503 deliberative turns, and 1,328 tool calls.

---

## 4. Failure Taxonomy & Phase 2 Outcome Breakdown

In SWE-bench, patch verification runs in an isolated sandbox with `pytest`. Cross-referencing traces against Phase 2 outputs reveals distinct failure mechanics:

### Table 2: Phase 2 Exit Code Failure Taxonomy Across 112 GPU Traces

| Category | Exit Code | Count (%) | Empirical Mechanism & Observable Symptoms |
| :--- | :---: | :---: | :--- |
| **Resolved** | `0` | 8 (7.1%) | Patch passes all Phase 2 held-out unit tests with zero regressions (6/96 primary, 6.3%). |
| **Assertion Failure** | `1` | 56 (50.0%) | Patch executes under pytest, but fails assertions due to wrong logic or incomplete multi-file edits. |
| **Collection Error** | `2` | 36 (32.1%) | Pytest crashes during collection prior to assertion evaluation (ModuleNotFoundError, SyntaxError, venv shadowing). |
| **Budget / Timeout** | `-1` | 9 (8.0%) | Agent exhausted 15 tool calls or 2.5 min wall time; 0 patch characters submitted. |
| **Verification Timeout** | `124` | 3 (2.7%) | Verification harness timed out (120s limit) due to daemon process or test-runner infinite loop. |

![Figure 1: Phase 2 Exit Code Distribution](figures/fig1_exit_codes.png)
*Figure 1: Phase 2 evaluation outcomes across all 112 ATIF-Gemma runs (Okabe-Ito palette).*

### 4.1 Deterministic Mechanism Breakdown of Collection Errors (Exit Code 2: 36 Runs)
Nearly one-third of runs (36/112 = 32.1%) failed before unit tests executed. Deterministic classification (`analysis/classify_exit2.py`) separates agent from environment causes:

1. **Agent-Attributable Collection Failures (16/36 = 44.4%)**:
   - *Syntax & Indentation Corruption (13/36 = 36.1%)*: Across 7 tasks (e.g., `fastapi_14099`), patches inserted detached syntax, raising `IndentationError` or `SyntaxError`.
   - *Missing Source Module (3/36 = 8.3%)*: On `rich_3930` (3 runs), omitting `rich/_unicode_data.py` caused `ModuleNotFoundError`.

2. **Environment-Attributable Failures (20/36 = 55.6%; `env_invalid=True`)**:
   - *Path Shadowing (10/36 = 27.8%)*: On `httpx_3672` (5 runs), system packages shadowed source. On `fastapi_15661` (5 runs), `PYTHONPATH` omitted `/workspace/scripts`.
   - *Missing Dependencies (10/36 = 27.8%)*: On 4 tasks (`fastapi_14361`, `14371`, `14455`, `14459`), tests required external wheels (`inline_snapshot`, `dirty_equals`) absent from the offline sandbox.

Applying reference gold patches through Phase 2 in the offline container on these 6 tasks yields identical collection crashes: missing wheels (`inline_snapshot`, `dirty_equals`) and path collisions precede test execution. In the official offline container, these tasks are structurally unwinnable for all competitors unless organizers install required wheels (local execution of `analysis/gold_patch_control.py` is marked BLOCKED per Rule 2 zero-simulation).

Excluding these 20 runs leaves 92 valid runs (80 primary runs, 26 tasks). Across the 26 tasks valid across all three configurations (78 paired runs), resolution is strictly invariant at **2/26 (7.69%, 95% Wilson CI [2.13%, 24.13%])** per architecture (6/78, 7.69% overall, 95% CI [3.57%, 15.77%]). Across unpaired valid runs, resolution is **6/80 (7.50%)** primary (`flat_starter` 2/27, `flat_controlled` 2/27, `sfd` 2/26) and **8/92 (8.70%)** pooled.

### 4.2 Deterministic Sub-Classification of Assertion Failures (Exit Code 1: 56 Runs)
Exit Code 1 represents 50.0% of the corpus (56/112). A mutually exclusive decision tree (`analysis/subclassify_exit1.py`) partitions all 56 assertion failures:

1. **Empty / Zero-Byte Patch (6/56 = 10.7%)**: $|F_{\text{agent}}| = 0$ (`patch_chars = 0`). Submitted 0 bytes due to 0 attempted edits (`fastapi_5624` controlled) or failed edits via `FileEditError` (`rich_3043` sfd, 4 failed edits; `rich_3944` starter, 6; `requests_7502` rerun, 2) or `BudgetExceeded` (`fastapi_14372` starter; `requests_7315` controlled). Pytest ran on the unpatched repo and failed assertions (Exit 1). This "could not apply edit" failure differs from Exit -1 (where turn/time budget halted agent before calling `submit_patch`, skipping Phase 2).
2. **Wrong-File Localization (15/56 = 26.8%)**: $F_{\text{agent}} \cap F_{\text{gold}} = \emptyset$ with non-empty diff (e.g., `fastapi_15589`).
3. **Partial Multi-File Localization (14/56 = 25.0%)**: $|F_{\text{gold}}| > 1$ and $F_{\text{agent}} \subsetneq F_{\text{gold}}$ (e.g., `requests_7505`).
4. **Right-File, Wrong-Logic (21/56 = 37.5%)**: $F_{\text{agent}} \cap F_{\text{gold}} \neq \emptyset$ with non-empty diff. Localized correct files, but logic failed assertions (e.g., `rich_3471`, `requests_7427`).

*Caveat:* File overlap ($F_{\text{agent}} \cap F_{\text{gold}}$) serves as an automated structural proxy; valid alternative patches may modify different helper abstractions.

### 4.3 Ground-Truth Resolved Runs & Task-Level Clustering
Across 112 runs, 8 resolved held-out tests across 4 unique tasks: `rich_4077` (3), `fastapi_9753` (1), `fastapi_14077` (2), and `rich_3894` (2). In primary runs ($n=96$), resolutions concentrate on these same 4 tasks (4/32 = 12.5% of tasks resolved at least once; 0/32 resolved across all 3 configurations). Runs sharing tasks are paired/clustered, not independent i.i.d. draws.

---

## 5. Quantitative Audit Across Agent Architectures

### Table 3: Architectural Comparison Across Primary (n=32) and Rerun (n=8) Cohorts

| Configuration | Runs | Primary Resolved (95% CI) | Mean Peak $P_t$ | Mean Cumulative Prompt | Mean Duration |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Official Starter (`flat_starter`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 13,359.7 | 105,817.6 | 94.2s |
| **Single-Agent (`flat_controlled`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 13,959.0 | 118,173.0 | 90.8s |
| **State-Filtered Deliberation (`sfd`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 10,907.5 | 80,375.7 | 86.6s |
| **Rerun: `flat_controlled`** | 8 | 1/8 (12.5%) [2.2%, 47.1%] | 12,557.5 | 93,135.6 | 107.4s |
| **Rerun: `sfd`** | 8 | 1/8 (12.5%) [2.2%, 47.1%] | 9,306.4 | 67,710.1 | 96.4s |

*Note:* **Mean Peak $P_t$** measures maximum prompt length reaching context across turns $t$. **Mean Cumulative Prompt** sums all input prompt tokens across LLM calls per run.

### 5.1 Statistical Tests & Resolution Invariance
Across 32 primary tasks, resolution rates are identical at 2/32 (6.25%, 95% Wilson CI [1.73%, 20.15%]) across `flat_starter`, `flat_controlled`, and `sfd` (McNemar $p = 1.0000$ for all pairs). **No architecture demonstrates a resolution advantage.** All hypothesis tests are exploratory without family-wise error adjustment.

In contrast, SFD produces significant token reductions:
- **Cumulative Prompt Tokens**: SFD consumes 37,797.4 fewer prompt tokens vs `flat_controlled` (-32.0%, 95% bootstrap CI `[-52,214.6, -23,755.2]`, Wilcoxon $p < 0.0001$; lower on 25/32 tasks) and 25,441.9 fewer vs `flat_starter` (-24.0%, CI `[-42,485.1, -9,031.4]`, $p = 0.0061$; lower on 24/32 tasks).
- **Peak Prompt Tokens ($P_t$)**: SFD reduces peak prompt by 3,051.6 tokens vs `flat_controlled` (-21.9%, CI `[-4,142.9, -1,968.2]`, $p < 0.0001$; lower on 28/32 tasks) and by 2,452.2 tokens vs `flat_starter` (-18.4%, CI `[-3,795.9, -1,111.8]`, $p = 0.0008$; lower on 26/32 tasks).
- **Execution Speed**: Wall-clock differences (-4.2s vs controlled, -7.7s vs starter) are not significant ($p = 0.4540, 0.4429$).

### 5.2 Rerun Reproducibility & Determinism Audit
Cohort 1 was re-executed across 8 tasks $\times$ 2 configs (16 paired runs; `analysis/statistical_tests.py`):
- **Exit Code Agreement**: 12 of 16 runs (75.0%) matched exact exit codes.
- **Patch Presence Agreement**: 14 of 16 runs (87.5%) agreed on patch presence (8/8 in `flat_controlled`, 6/8 in `sfd`). The two discordant SFD runs were: (1) `fastapi_15589`, where original SFD hit budget timeout without editing (0 chars, exit -1) while rerun completed within budget (590 chars, exit 1); and (2) `requests_7502`, where original SFD submitted 581 chars (exit 1) while rerun suffered 2 `FileEditError`s, submitting 0 bytes (exit 1).
- **Edit Sequence Divergence**: 0/16 workspace edit sequences were byte-identical due to token-level sampling variance under vLLM even at $T=0.0$.
- **Exit-Code Flips (4 pairs)**: `rich_4077` (ctrl: 1->0 resolved via `self.__file.isatty()`); `fastapi_15588` (sfd: 1->2 syntax corruption); `fastapi_15589` (ctrl: 1->2 syntax corruption); `fastapi_15589` (sfd: -1->1).
- **Token Drift**: Mean absolute deviation was **18,571.0 tokens** (~19% drift), quantifying multi-turn divergence.

### 5.3 Sub-Agent Bypassing in the Starter Kit
In the official starter kit (`flat_starter`), the root agent wraps `code_analyzer` as an `AgentTool`. Across all 32 traces:
- Out of 336 tool calls, the model delegated to `code_analyzer` only **7 times (2.1%)**.
- The model **bypassed `code_analyzer` on 26 of 32 tasks (81.2%)**, reading large files directly into root context (6/32 tasks delegated).

![Figure 3: Sub-Agent Delegation Funnel](figures/fig3_delegation_funnel.png)
*Figure 3: Sub-agent discretionary delegation in `flat_starter`: 26/32 tasks bypassed `code_analyzer` (81.2%), with only 7/336 tool calls delegating (2.1%).*

### 5.4 Cross-Stage Prompt Resets
In `sfd` traces, `include_contents: "none"` resets entry prompts from a mean TriageAgent peak of 10,473.9 tokens (median 9,863.0) to 1,536.9 tokens (median 1,503.0) at PatchAgent entry. Across all 32 primary SFD runs, this yields an 81.95% mean prompt reset (median 87.43%, IQR [75.72%, 89.46%]), driving the 32.0% prompt token reduction over single-agent baselines ($p < 0.0001$).

![Figure 2: Prompt Token Expansion & Stage Resets](figures/fig2_prompt_resets.png)
*Figure 2: Prompt token trajectories across steps $t$ (mean with 95% bootstrap bands). In 64 flat runs (32 starter + 32 controlled), context expanded monotonically (ADK compaction never triggered under 15-tool limit); SFD resets prompt tokens by 87.43% median.*

---

## 6. Candidate Remediations (Untested Unless Stated)

Converting diagnostic failure classifications into practical engineering patterns provides guidance for compact-agent frameworks:

| Failure Mode | Prevalence | Candidate Remediation Pattern |
| :--- | :---: | :--- |
| **Collection Crash** | 36/112 (32.1%) | Enforce `PYTHONPATH` priority and pre-flight dependency checks before running tests. |
| **Syntax Corruption** | 100 FileEditErrors (0.89/run) | Mandate `python -m py_compile` check before `submit_patch` to intercept broken indentation. |
| **Wrong-File Localization** | 17/112 runs (15.2%) | Candidate two-way validation loop (untested) verifying localized symbols before editing. |
| **Unbounded Context Growth** | 64/64 flat runs (100% monotonic) | Stage-isolated context pruning (`include_contents: "none"`), resetting context by 81.9% mean. |

### 6.1 Post-Hoc Diagnostic Re-Evaluation (Non-Official Harness)
We conducted offline diagnostic evaluation of stored patches (`analysis/remediation_eval.py`, `results/remediation_eval.json`). **These checks do not alter official benchmarks in Section 4 and Tables 1-3.**

1. **Pre-Submission `py_compile` Gate**: On all 13 syntax-corrupted Exit Code 2 runs, automated `py_compile` intercepts 100% (13/13) of malformed patches before `submit_patch`. This confirms syntax errors are caught by construction, but does not prove autonomous recovery without self-repair turns (0/13 resolved without re-prompting).
2. **`PYTHONPATH` Priority**: Prepending repository paths (`PYTHONPATH=/workspace/src:/workspace`) structurally eliminates path-shadowing collection crashes across 10 runs (`httpx_3672`, `fastapi_15661`). Evaluating assertions requires the offline container; no speculative resolution gains are claimed.

---

## 7. The `atif_gemma` Python Package & CLI

We release the standalone Python package `atif-gemma`:

```bash
pip install git+https://github.com/KarandeepSinghSodhi/gemma-sfd-agent.git
```

Modules provide automated trajectory auditing (`audit`), deterministic exit-code and localization classification (`taxonomy`), and the actionable playbook (`remediation`). The CLI provides instant diagnostics: `python -m atif_gemma.cli audit traces/` and `python -m atif_gemma.cli playbook`.

---

## 8. Limitations & Threats to Validity

1. **Task Sample Size ($n = 32$)**: Covers 25% of 129 instances; evaluating all instances across 3 configs requires >500 GPU hours.
2. **Single Model & Quantization**: Evaluates `gemma-4-e4b-it-qat-w4a16-ct` (INT4); behaviors may differ on larger models (Gemma 4 31B).
3. **Repository Diversity & Clustered Runs**: Concentrated across 4 Python repos; runs sharing tasks are paired/clustered.
4. **Trajectory Non-Determinism**: Under greedy decoding (`temp=0.0`), 12/16 exit codes matched on rerun, but 0/16 edit sequences were identical (mean token drift: 18,571 tokens, ~19%).
5. **Structural Proxy**: Evaluates file overlap ($F_{\text{agent}} \cap F_{\text{gold}}$); valid alternative patches remain possible.
6. **Container Failures (`env_invalid=True`)**: 20 runs failed due to offline container constraints (missing wheels, path shadowing).

---

## 9. Conclusion & Resource Availability

ATIF-Gemma provides an open diagnostic foundation for compact coding agents. Moving beyond scalar pass/fail rates to an open 112-trace corpus, a failure taxonomy, a remediation playbook, and open tooling, this resource targets key compact-agent bottlenecks: collection crashes, context bloat, and localization drift.

- **Kaggle Dataset:** [ATIF-Gemma SWE Agent Traces](https://www.kaggle.com/datasets/karandeepsinghsodhi/atif-gemma-swe-agent-traces) (CC BY 4.0)  
- **GitHub Repository:** [gemma-sfd-agent](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent) (Apache 2.0)  
- **Interactive Kernel:** [Diagnostic Exploration](https://www.kaggle.com/code/karandeepsinghsodhi/atif-gemma-diagnostic-exploration)  
- **Manuscript PDF:** [paper_resource.pdf](https://raw.githubusercontent.com/KarandeepSinghSodhi/gemma-sfd-agent/main/paper_resource.pdf)

---

## 10. References

- Austin, J., et al. (2021). Program synthesis with large language models. *arXiv:2108.07732*.
- Chen, M., et al. (2021). Evaluating large language models trained on code. *arXiv:2107.03374*.
- Gebru, T., et al. (2021). Datasheets for datasets. *CACM*, 64(12), 86–92.
- Gemma Team, Google DeepMind. (2026). Gemma 4 technical report. *arXiv:2607.02770*.
- Harbor Framework Contributors. (2026). Agent Trajectory Interchange Format (ATIF) Specification (v1.7). *GitHub*. https://github.com/harbor-framework/harbor
- Holbrook, R. (2026). Gemma 4 Developer Agent Competition: Small Model Prize Leaderboard. *Kaggle*.
- Jimenez, C. E., et al. (2024). SWE-bench: Can language models resolve real-world GitHub issues? *ICLR 2024*.
- Lindenbauer, T., et al. (2025). The complexity trap: Simple observation masking is as efficient as LLM summarization. *arXiv:2508.21433*.
- Pan, J., Wang, X., Neubig, G., Jaitly, N., Ji, H., Suhr, A., & Zhang, Y. (2024). Training Software Engineering Agents and Verifiers with SWE-Gym. *arXiv:2412.21139*.
- Rajak, R. (2026). Gemma 4 TFD Agentic Trajectories & Benchmark: 50 multi-turn SWE-bench trajectories. *Kaggle*.
- Yang, J., Lieret, K., Jimenez, C. E., Pan, J., Wetzel, Q., Chi, J., Yao, S., & Narasimhan, K. (2025). SWE-smith: Scaling Data for Software Engineering Agents. *arXiv:2504.21798*.
- Wang, X., et al. (2024). OpenHands: An open platform for AI software developers. *arXiv:2407.16741*.
- Xia, C. S., et al. (2024). Agentless: Demystifying LLM-based software engineering agents. *arXiv:2407.01489*.
- Yang, J., et al. (2024). SWE-agent: Agent-computer interfaces enable automated software engineering. *arXiv:2405.15793*.
