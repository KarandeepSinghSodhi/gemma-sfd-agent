# ATIF-Gemma: An Open Empirical Diagnostic Corpus and Failure Taxonomy for Small Open-Weight Developer Agents

**Author:** Karandeep Singh Sodhi (Independent Researcher)  
**Track:** Google — The Gemma 4 Developer Agent Competition (Paper Track: Best New Resource)  
**Dataset:** [ATIF-Gemma SWE Agent Traces (Kaggle)](https://www.kaggle.com/datasets/karandeepsinghsodhi/atif-gemma-swe-agent-traces) | **Code:** [gemma-sfd-agent (GitHub)](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent)  
**Notebook:** [Diagnostic Exploration (Kaggle)](https://www.kaggle.com/code/karandeepsinghsodhi/atif-gemma-diagnostic-exploration) | **Manuscript:** [paper_resource.pdf](https://raw.githubusercontent.com/KarandeepSinghSodhi/gemma-sfd-agent/main/paper_resource.pdf)  

---

## Abstract

Software engineering (SWE) agent benchmarks commonly report scalar resolution rates while discarding execution trajectories, obscuring failure causes. For compact, 4-bit quantized models such as Gemma 4 E4B, diagnosing why agents plateau at low resolution rates (median 5.0% across 197 teams on the official Small Model Prize leaderboard) is hindered by a lack of public trace data. We introduce **ATIF-Gemma**, an open empirical diagnostic corpus of 112 multi-turn execution traces comprising 1,518 LLM turns, 1,328 tool calls, and 11,706,178 logged tokens across 32 paired SWE-bench tasks on 4x NVIDIA L4 GPUs using Google ADK and `swegemma`.

Formatted under ATIF v1.7 (100% dual schema-validated), ATIF-Gemma links agent actions and patches to held-out test outcomes. Across 112 runs, 8 achieve resolution (7.1%). We define four failure mechanisms: assertion failures (50.0%, 56/112), collection errors (32.1%, 36/112), budget exhaustion (8.0%, 9/112), and verification timeouts (2.7%, 3/112). Analysis partitions collection crashes into agent-attributable collection failures (44.4%) versus environment/dependency failures (55.6%), classifies assertion failures via a formal localization decision tree, and documents context dynamics and rerun stability. We release the trace corpus, the `atif_gemma` package, and an actionable remediation guide.

---

## 1. Introduction & The Diagnostic Vacuum in SWE Benchmarking

Autonomous software engineering agents have advanced on repository benchmarks such as SWE-bench (Jimenez et al., 2024). However, evaluations remain largely **outcome-centric**: reporting scalar resolution rates while discarding multi-turn trajectories of tool calls, prompt expansions, and sandbox interactions preceding the outcome.

For large frontier models, higher resolution rates allow treating the agent loop as a black box. In contrast, for compact, 4-bit quantized open-weight models suitable for developer workstations (`gemma-4-e4b-it-qat-w4a16-ct`), scalar benchmarking reveals an acute capability cliff without explaining its origins. On the official Small Model Prize leaderboard (Holbrook, 2026), public scores across $N = 197$ teams range from 0.0% to 10.0% (median 5.0%, mean 4.23%), with 92.9% scoring $\le 6.0\%$.

When an agent fails, developers cannot determine whether failure stemmed from:
1. **Localization Failure**: Inspecting incorrect directories or irrelevant modules.
2. **Syntax Degradation**: Generating malformed tool arguments, unindented blocks, or detached edits.
3. **Sandbox Artifacts**: Missing third-party packages or virtual environment path shadowing.
4. **Tool Exhaustion**: Reaching global turn, time, or tool limits before applying an edit.

To bridge this gap, we introduce **ATIF-Gemma**, an open diagnostic trajectory corpus and software toolkit for small open-weight developer agents, providing 112 complete execution traces (11.7M tokens, 1,518 LLM turns, 1,328 tool calls) across 32 benchmark tasks under ATIF v1.7.

---

## 2. Related Work: Trajectory Corpora & Agent Diagnostics

Understanding small open-weight agent failure mechanics intersects two primary research areas:

### 2.1 SWE Agent Trajectories & Diagnostics
SWE-bench (Jimenez et al., 2024) established repository-level evaluation for language models. SWE-agent (Yang et al., 2024) and OpenHands (Wang et al., 2024) introduced specialized agent-computer interfaces and sandboxes. The Agent Trajectory Interchange Format (ATIF v1.7; SWE-bench Working Group, 2024) standardized JSON logging for multi-turn tool calls and token metrics. In diagnostics, Xia et al. (2024) showed with *Agentless* that complex autonomous loops can degrade performance relative to structured pipelines, while Lindenbauer et al. (2025) showed unpruned observations bloat prompts and impair reasoning.

Public trajectory releases (such as 50 multi-turn Gemma SWE-bench trajectories on Kaggle; Rajak, 2026) provide valuable execution-level evidence. However, systematic analysis linking compact-agent traces to test-collection failures, patch-localization outcomes, and harness defects remains an open need. ATIF-Gemma addresses this by providing paired architectural comparisons across 112 traces, a deterministic failure taxonomy with agent versus environment attribution, localization analysis, and open diagnostic tooling.

### 2.2 Small Open-Weight Developer Agents
The Gemma 4 family (Gemma Team, 2026) introduced compact models for local workstations (`gemma-4-e4b-it-qat-w4a16-ct`). While small models excel on isolated synthesis benchmarks like HumanEval (Chen et al., 2021) and MBPP (Austin et al., 2021), multi-turn repository repair exposes a capability cliff (median 5.0% resolution across 197 teams; Holbrook, 2026). Prior to structured diagnostic analysis, researchers lacked the trace data needed to distinguish whether this low ceiling stemmed from reasoning limits, context accumulation, or test-collection failures.

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

*Note: The 40 cohort entries span 32 unique benchmark tasks; Cohort 1 Rerun re-executes the 8 tasks of Cohort 1 for empirical reproducibility verification.*

The corpus spans 32 unique SWE-bench instances across four Python repositories: `fastapi` (51 runs), `rich` (37 runs), `requests` (19 runs), and `httpx` (5 runs). All experiments were served using vLLM 0.19.1 (`tp=4`, 96 GB VRAM) hosting `gemma-4-e4b-it-qat-w4a16-ct` with Google ADK 1.36.1 and `swegemma`.

Each trace conforms to **ATIF v1.7 JSON Schema**:
- **Metadata**: Records `instance_id`, `repo`, `base_commit`, configuration, sampling parameters (`temp=0.0`, `seed=42`, `max_output_tokens=8192`, `thinking_budget=1536`), and hardware specs.
- **Steps**: Captures `metrics` (tokens), `tool_calls` (arguments, author), `observation` (outputs, error types: `FileEditError`, `CommandError`, `FileReadError`, `BudgetExceeded`), and `message` (deliberative reasoning under `extra.event_type: "thinking"`).
- **Final Metrics**: Cumulative tokens (`total_prompt_tokens`, `total_completion_tokens`, `total_tokens`), duration, patch, and Phase 2 exit codes.

**Dual Schema Validation:** All 112 traces (100.0%) pass validation against the repository schema (`dataset_resource/atif_schema_v1_7.json`). An upstream interoperability audit (`analysis/validate_atif_schema.py`) confirms that all 1,942 audited steps and 1,503 deliberative reasoning turns map cleanly to upstream standard ATIF v1.7 representations (`reasoning_content` with provenance in `extra`), achieving 100.0% dual validation.

---

## 4. Failure Taxonomy & Phase 2 Outcome Breakdown

In SWE-bench, patch verification runs in an isolated sandbox with `pytest`. Cross-referencing agent traces against Phase 2 test outputs reveals that treating unresolved runs as monolithic conceals distinct failure mechanics. We define four principal failure mechanisms—assertion failure, collection error, budget exhaustion, and verification timeout—and report resolution separately:

### Table 2: Phase 2 Exit Code Failure Taxonomy Across 112 GPU Traces

| Category | Exit Code | Count (%) | Empirical Mechanism & Observable Symptoms |
| :--- | :---: | :---: | :--- |
| **Resolved** | `0` | 8 (7.1%) | Patch passes all Phase 2 held-out unit tests with zero regressions. |
| **Assertion Failure** | `1` | 56 (50.0%) | Patch syntactically valid and executes under pytest, but fails assertions due to wrong logic or incomplete multi-file edits. |
| **Collection Error** | `2` | 36 (32.1%) | Pytest crashes during test collection prior to assertion evaluation (ModuleNotFoundError, SyntaxError, venv shadowing). |
| **Budget / Timeout** | `-1` | 9 (8.0%) | Agent exhausted 15 tool calls or 2.5 min wall time; 0 patch characters submitted. |
| **Verification Timeout** | `124` | 3 (2.7%) | Verification harness timed out (120s limit) due to daemon process or infinite loop in test runner. |

![Figure 1: Phase 2 Exit Code Distribution](figures/fig1_exit_codes.png)
*Figure 1: Distribution of Phase 2 evaluation outcomes across all 112 ATIF-Gemma runs and individual configurations. Colorblind-safe palette (Okabe-Ito).*

### 4.1 Deterministic Mechanism Breakdown of Collection Errors (Exit Code 2: 36 Runs)
Nearly one-third of runs (36/112 = 32.1%) failed before unit tests could execute. Deterministic classification (`analysis/classify_exit2.py`) separates these into agent versus environment causes:

1. **Agent-Attributable Collection Failures (16/36 = 44.4%)**:
   - *Syntax & Indentation Corruption (13/36 = 36.1%)*: Across 7 tasks (e.g., `fastapi_14099`, `rich_3894`), patches inserted unindented blocks or detached syntax, raising `IndentationError` or `SyntaxError`.
   - *Missing Source Module (3/36 = 8.3%)*: On `rich_3930` (3 runs), omitting required new module `rich/_unicode_data.py` caused `ModuleNotFoundError`.

2. **Environment-Attributable Failures (20/36 = 55.6%)**:
   - *Path & Virtualenv Shadowing (10/36 = 27.8%)*: On `httpx_3672` (5 runs), `/usr/local/lib/python3.12/dist-packages` shadowed local repository source. On `fastapi_15661` (5 runs), `PYTHONPATH` omitted `/workspace/scripts`.
   - *Missing Sandbox Dependencies (10/36 = 27.8%)*: On 4 tasks (`fastapi_14361`, `14371`, `14455`, `14459`), tests required external libraries (`inline_snapshot`, `dirty_equals`) absent from the offline wheelhouse.

This distinction demonstrates trace utility: diagnosing model patch flaws while identifying harness anomalies.

### 4.2 Deterministic Sub-Classification of Assertion Failures (Exit Code 1: 56 Runs)
Exit Code 1 represents 50.0% of the corpus (56/112). Using a mutually exclusive decision tree (`analysis/subclassify_exit1.py`), we assign every assertion failure to one tier:

1. **Empty Patch (1/56 = 1.8%)**: Evaluated first: $|F_{\text{agent}}| = 0$ (`fastapi_5624`, 0 modified characters).
2. **Wrong-File Localization (17/56 = 30.4%)**: Evaluated second: $F_{\text{agent}} \cap F_{\text{gold}} = \emptyset$. The agent edited unrelated files (e.g., `params.py` instead of `dependencies/utils.py` in `fastapi_15589`).
3. **Partial Multi-File Localization (14/56 = 25.0%)**: Evaluated third: $|F_{\text{gold}}| > 1$ and $F_{\text{agent}} \subsetneq F_{\text{gold}}$. The bug spanned multiple modules, but the agent edited a strict subset (e.g., in `requests_7505`, editing `models.py` but omitting `sessions.py`).
4. **Right-File, Wrong-Logic (24/56 = 42.9%)**: Evaluated fourth: remaining runs where $F_{\text{agent}} \cap F_{\text{gold}} \neq \emptyset$. Target files localized, but synthesized logic failed assertions (e.g., `requests_7502`, `rich_3043`).

*Methodological note:* Gold-patch file overlap provides an objective structural proxy for localization; valid alternative multi-file patches remain possible in rare cases (Section 8).

### 4.3 Ground-Truth Resolved Runs
Across the 112 runs, 8 runs resolved held-out tests across 4 tasks: `rich_4077` (3 runs), `fastapi_9753` (1 run), `fastapi_14077` (2 runs), and `rich_3894` (2 runs).

---

## 5. Quantitative Audit Across Agent Architectures

### Table 3: Architectural Comparison Across All 112 ATIF-Gemma Runs

| Configuration | Runs | Resolved (95% Wilson CI) | Mean Peak $P_t$ | Mean Prompt | Mean Duration |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Official Starter (`flat_starter`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 13,359.7 | 105,817.6 | 94.2s |
| **Single-Agent (`flat_controlled`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 13,959.0 | 118,173.0 | 90.8s |
| **State-Filtered Deliberation (`sfd`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 10,907.5 | 80,375.7 | 86.6s |
| **Rerun: `flat_controlled`** | 8 | 1/8 (12.5%) [2.2%, 47.1%] | 12,557.5 | 93,135.6 | 107.4s |
| **Rerun: `sfd`** | 8 | 1/8 (12.5%) [2.2%, 47.1%] | 9,306.4 | 67,710.1 | 96.4s |

*Metric Definition:* **Mean Peak $P_t$** is defined as $\frac{1}{N}\sum_{i=1}^N \max_t P_{i,t}$, representing the per-run maximum prompt token length ($P_t$) reaching the model context window across turn steps $t$, averaged over all $N$ benchmark runs in the configuration.

### 5.1 Statistical Tests & Resolution Invariance
Across all 32 benchmark tasks, resolution rates are identical at 2/32 (6.25%, 95% Wilson CI [1.73%, 20.15%]) across `flat_starter`, `flat_controlled`, and `sfd` (McNemar exact test $p = 1.0000$ for all pairs). **No architecture demonstrates a statistically significant resolution advantage on this small model.**

In contrast, SFD's stage isolation produces significant token efficiency gains:
- **Cumulative Prompt Tokens**: SFD consumes 37,797.4 fewer prompt tokens per task than `flat_controlled` (-32.0%, 95% bootstrap CI: `[-52,214.6, -23,755.2]`, Wilcoxon $p < 0.0001$; lower on 25/32 tasks) and 25,441.9 fewer than `flat_starter` (-24.0%, bootstrap CI: `[-42,485.1, -9,031.4]`, Wilcoxon $p = 0.0061$; lower on 24/32 tasks).
- **Peak Prompt Tokens ($P_t$)**: SFD reduces peak prompt size by 3,051.6 tokens (-21.9%, bootstrap CI: `[-4,142.9, -1,968.2]`, Wilcoxon $p < 0.0001$; lower on 28/32 tasks).
- **Execution Speed**: Wall-clock differences (-4.2s vs controlled, -7.7s vs starter) are not statistically significant (Wilcoxon $p = 0.4540$ and $p = 0.4429$). Reduced prompt tokens reflect resource efficiency rather than improved problem solving.

### 5.2 Rerun Reproducibility & Determinism Audit
Cohort 1 was re-executed across 8 tasks $\times$ 2 configs (16 paired runs; `analysis/statistical_tests.py`):
- **Patch Identity**: 14 of 16 runs (87.5%) produced bitwise identical patches (identical SHA-256).
- **Exit Code Agreement**: 12 of 16 runs (75.0%) matched exact exit codes.
- **Token Stability**: Mean absolute token difference was 18,571 tokens, arising from asynchronous vLLM micro-batching on 4x L4 GPUs.

### 5.3 Sub-Agent Bypassing in the Starter Kit
In the official starter kit (`flat_starter`), the root agent wraps `code_analyzer` as an `AgentTool`. Across all 32 traces:
- Out of 336 tool calls, the model delegated to `code_analyzer` only **7 times (2.1%)**.
- The model **bypassed `code_analyzer` on 29 of 32 tasks (90.6%)**, reading large files directly into root context.

![Figure 3: Sub-Agent Delegation Funnel](figures/fig3_delegation_funnel.png)
*Figure 3: Sub-agent discretionary delegation breakdown in the official starter kit (`flat_starter`). Small models bypassed `code_analyzer` on 29 of 32 tasks (90.6%), with only 7 delegations out of 336 total tool calls (2.1%).*

### 5.4 Cross-Stage Prompt Resets
In `sfd` traces, configuring `include_contents: "none"` on downstream stages resets entry prompts from a mean TriageAgent peak of 10,473.9 tokens (median 9,863.0) to 1,536.9 tokens (median 1,503.0) at PatchAgent entry. Across all 32 primary SFD runs, this yields an 81.95% mean prompt reset (median 87.43%, IQR [75.72%, 89.46%]), driving the 32.0% prompt token reduction relative to single-agent baselines (Wilcoxon $p < 0.0001$).

![Figure 2: Prompt Token Expansion & Stage Resets](figures/fig2_prompt_resets.png)
*Figure 2: Prompt token trajectories across trajectory steps $t$ (mean with 95% bootstrap confidence bands). While monolithic flat agents accumulate context monotonically, SFD's stage boundary resets prompt tokens by an empirical median of 87.43%.*

---

## 6. Actionable Remediation Playbook for Developer Agents

Converting diagnostic failure classifications into actionable remediation patterns provides practical guidance for engineering small coding agents:

| Failure Mode | Prevalence | Recommended Production Remediation Pattern |
| :--- | :---: | :--- |
| **Collection / Import Crash** | 36/112 (32.1%) | Enforce `PYTHONPATH=/workspace/src:/workspace` priority in test execution commands and execute pre-flight dependency imports with `python -c` before running test suites. |
| **Syntax / Diff Corruption** | 100 FileEditErrors (64 StringNotFound, 36 Malformed; mean 0.89/run) | Mandate a strict `python -m py_compile <modified_file>` verification check before calling `submit_patch` to prevent broken indentation or detached blocks. |
| **Wrong-File Localization** | 17/112 runs (15.2% overall; 30.4% of Exit 1) | Introduce a two-way validation loop where Stage 2 verifies that the localized symbol exists in the problem description before executing an edit. |
| **Prompt Bloat / Memory Leak** | 32/32 flat runs (100% monotonic accumulation; SFD lowers peak on 28/32 tasks) | Implement stage-isolated context pruning via `include_contents: "none"` in Google ADK, resetting prompt context by 81.9% mean (87.4% median) across pipeline boundaries. |

### 6.1 Post-Hoc Diagnostic Re-Evaluation (Non-Official Harness)
To evaluate proposed remediations, we conducted an offline diagnostic assessment of stored patches (`analysis/remediation_eval.py`, `results/remediation_eval.json`). **These offline results do not alter the official competition benchmarks reported in Section 4 and Tables 1–3.**

1. **Pre-Submission `py_compile` Gate**: Tested on all 13 Exit Code 2 runs with syntax corruption, an automated `py_compile` gate intercepts 100% (13/13) of malformed patches before calling `submit_patch`. Intercepting malformed patches prevents blind collection crashes (Exit Code 2), but does *not* resolve the task without self-repair turns (0/13 resolved without re-prompting).
2. **`PYTHONPATH` Priority Enforcement**: Prepending repository source paths (`PYTHONPATH=/workspace/src:/workspace`) eliminates collection crashes from site-package shadowing across all 10 environment-shadowed runs (`httpx_3672`, `fastapi_15661`). Evaluating semantic assertions requires the offline Linux `swegemma` container; thus, no speculative resolution gains are claimed.

---

## 7. The `atif_gemma` Python Package & CLI

Along with the dataset, we release a standalone Python package (`atif-gemma`) installable from GitHub:

```bash
pip install git+https://github.com/KarandeepSinghSodhi/gemma-sfd-agent.git
# Or local editable install: git clone ... && cd gemma-sfd-agent && pip install -e .
```

The package provides automated diagnostic modules:
- `atif_gemma.audit`: Parses ATIF v1.7 directories, extracting token trajectories, tool error frequencies, and exit codes.
- `atif_gemma.taxonomy`: Classifies Phase 2 test runner exit codes and file localization tiers.
- `atif_gemma.remediation`: Programmatic interface to the remediation playbook.
- CLI: `python -m atif_gemma.cli audit traces/` and `python -m atif_gemma.cli playbook`.

---

## 8. Limitations & Threats to Validity

1. **Task Sample Size ($n = 32$)**: Covers 25% of the 129 competition instances; full evaluation across three configurations requires >500 NVIDIA L4 GPU hours.
2. **Single Model & Quantization**: All traces were generated on `gemma-4-e4b-it-qat-w4a16-ct` (INT4). Sub-agent bypassing and syntax corruption rates are specific to this model; larger models (e.g., Gemma 4 31B) may behave differently.
3. **Repository Diversity**: Concentrated on four Python libraries (`fastapi`, `rich`, `requests`, `httpx`). Statically typed codebases or alternative test runners may exhibit different collection dynamics.
4. **Greedy Decoding ($T = 0.0$)**: All runs used greedy decoding with `seed = 42`. While 87.5% of rerun patches were bitwise identical, vLLM micro-batching causes minor token variance.
5. **File-Level Structural Proxy**: We evaluate file overlap ($F_{\text{agent}} \cap F_{\text{gold}}$). While objective, valid alternative multi-file patches remain possible in rare cases.
6. **Harness Environment**: Artifacts (missing wheelhouse packages, path shadowing) reflect Kaggle's offline Linux container setup.

---

## 9. Conclusion & Resource Availability

ATIF-Gemma provides an open diagnostic foundation for compact coding agents. Moving beyond scalar pass/fail rates to an open 112-trace corpus, a structured failure taxonomy, an Actionable Remediation Playbook, and open Python tooling, this resource enables researchers to target primary bottlenecks in small developer agents: collection crashes, context bloat, and localization drift.

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
- Holbrook, R. (2026). Gemma 4 Developer Agent Competition: Small Model Prize Leaderboard. *Kaggle*.
- Jimenez, C. E., et al. (2024). SWE-bench: Can language models resolve real-world GitHub issues? *ICLR 2024*.
- Lindenbauer, T., et al. (2025). The complexity trap: Simple observation masking is as efficient as LLM summarization. *arXiv:2508.21433*.
- Rajak, R. (2026). Gemma 4 TFD Agentic Trajectories & Benchmark: 50 multi-turn SWE-bench trajectories. *Kaggle*.
- SWE-bench Working Group. (2024). Agent Trajectory Interchange Format (ATIF v1.7). *GitHub*.
- Wang, X., et al. (2024). OpenHands: An open platform for AI software developers. *arXiv:2407.16741*.
- Xia, C. S., et al. (2024). Agentless: Demystifying LLM-based software engineering agents. *arXiv:2407.01489*.
- Yang, J., et al. (2024). SWE-agent: Agent-computer interfaces enable automated software engineering. *arXiv:2405.15793*.
