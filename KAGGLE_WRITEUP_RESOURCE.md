# ATIF-Gemma: An Open Empirical Diagnostic Corpus and Failure Taxonomy for Small Open-Weight Developer Agents

**Author:** Karandeep Singh Sodhi (Independent Researcher)  
**Track:** Google — The Gemma 4 Developer Agent Competition (Paper Track: Best New Resource)  
**Dataset:** [ATIF-Gemma SWE Agent Traces (Kaggle)](https://www.kaggle.com/datasets/karandeepsinghsodhi/atif-gemma-swe-agent-traces) | **Code:** [gemma-sfd-agent (GitHub)](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent)  
**Notebook:** [Diagnostic Exploration (Kaggle)](https://www.kaggle.com/code/karandeepsinghsodhi/atif-gemma-diagnostic-exploration) | **Manuscript:** [paper_resource.pdf](https://raw.githubusercontent.com/KarandeepSinghSodhi/gemma-sfd-agent/main/paper_resource.pdf)  

---

## Abstract

Software engineering (SWE) agent benchmarks commonly summarize performance using scalar task-resolution rates, obscuring why agents succeed or fail. For compact, 4-bit quantized open-weight models such as Gemma 4 E4B, diagnosing why agents plateau at low resolution rates (median 5.0% across 197 teams on the official Small Model Prize leaderboard) is hindered by a lack of public execution trace data. We introduce **ATIF-Gemma**, an open empirical diagnostic corpus of 112 full-fidelity multi-turn execution traces comprising 1,518 LLM calls, 1,328 tool invocations, and 11,706,178 logged tokens across 32 paired SWE-bench tasks on 4x NVIDIA L4 GPUs in the official Google ADK and `swegemma` harness.

Formatted under the Agent Trajectory Interchange Format (ATIF v1.7, 100% schema-validated), ATIF-Gemma cross-references trajectories and patches against ground-truth solutions and held-out test suites. Across 112 runs, 8 achieve full resolution (7.1%). We define four principal failure mechanisms: test assertion failures (50.0%, 56/112), test collection failures (32.1%, 36/112), pre-submission budget exhaustion (8.0%, 9/112), and verification timeouts (2.7%, 3/112). Further analysis partitions collection crashes into agent-attributable syntax errors (44.4%) versus environment/dependency defects (55.6%), classifies assertion failures via a formal mutually exclusive localization decision tree, and documents context dynamics and rerun stability. We release the trace corpus, the `atif_gemma` analysis package, and an actionable remediation guide to support reproducible diagnosis of compact developer agents.

---

## 1. Introduction & The Diagnostic Vacuum in SWE Benchmarking

Autonomous software engineering agents powered by large language models have advanced rapidly on repository benchmarks such as SWE-bench (Jimenez et al., 2024). However, evaluations remain **outcome-centric**: benchmarks report scalar resolution rates, discarding the multi-turn trajectories of tool calls, prompt expansions, and sandbox interactions that preceded the outcome.

For large frontier models, high resolution rates allow researchers to treat the agent loop as a black box. In contrast, for compact, 4-bit quantized open-weight models suitable for local developer workstations (such as `gemma-4-e4b-it-qat-w4a16-ct`), scalar benchmarking reveals an acute capability cliff without explaining its origins. On the official Small Model Prize leaderboard (Holbrook, 2026), public scores across $N = 197$ teams range from 0.0% to 10.0% (median 5.0%, mean 4.23%), with 92.9% scoring $\le 6.0\%$.

When an agent fails, developers cannot currently determine whether failure stemmed from:
1. **Localization Failure**: Searching incorrect directories or inspecting irrelevant modules.
2. **Syntax Corruption**: Prompt bloat degrading instruction following, yielding malformed edits.
3. **Sandbox Artifacts**: Missing third-party packages or environment path shadowing.
4. **Tool Exhaustion**: Reaching global turn, time, or tool limits before applying an edit.

To bridge this diagnostic gap, we introduce **ATIF-Gemma**, an open, full-fidelity diagnostic trajectory corpus and software toolkit for small open-weight developer agents, providing 112 complete execution traces (11.7M tokens, 1,518 LLM turns, 1,328 tool calls) across 32 unique benchmark tasks under ATIF v1.7.

---

## 2. Related Work: Trajectory Corpora & Agent Diagnostics

Understanding small open-weight agent failure mechanics intersects three research areas:

### 2.1 SWE Agent Trajectories & Failure Analysis
SWE-bench (Jimenez et al., 2024) established repository-level evaluation for language models. SWE-agent (Yang et al., 2024) and OpenHands (Wang et al., 2024) introduced specialized agent-computer interfaces and execution sandboxes. To standardize trajectory representations, the Agent Trajectory Interchange Format (ATIF v1.7; SWE-bench Working Group, 2024) established a unified JSON schema for multi-turn tool invocations, observations, and token metrics.

In failure analysis, Xia et al. (2024) demonstrated with *Agentless* that complex autonomous loops often degrade performance relative to structured two-phase pipelines. Lindenbauer et al. (2025) identified the "complexity trap", showing that unpruned tool observations bloat prompts and degrade reasoning. While prior trajectory studies primarily examined large proprietary models in cloud environments, we introduce an open execution-trace corpus focused on a compact, quantized Gemma agent operating in the competition's software-repair harness, with explicit linkage between trajectory failures and evaluation outcomes.

### 2.2 Small Open-Weight Developer Agents
The Gemma 4 family (Gemma Team, 2026) introduced compact models optimized for local developer workstations, including 4-bit quantized checkpoints (`gemma-4-e4b-it-qat-w4a16-ct`). While small models demonstrate strong performance on isolated code synthesis benchmarks such as HumanEval (Chen et al., 2021) and MBPP (Austin et al., 2021), multi-turn repository repair exposes a severe capability cliff (median 5.0% resolution across 197 teams; Holbrook, 2026). Prior to ATIF-Gemma, researchers lacked the trajectory data needed to distinguish whether this low resolution ceiling stemmed from model reasoning limitations, context exhaustion, or infrastructure collection failures.

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

The corpus spans 32 unique SWE-bench instances across four Python repositories: `fastapi` (51 runs), `rich` (37 runs), `requests` (19 runs), and `httpx` (5 runs). All experiments were served using vLLM 0.19.1 under tensor parallel 4 (`tp=4`, 96 GB aggregate VRAM) hosting `gemma-4-e4b-it-qat-w4a16-ct` with Google ADK 1.36.1 and `swegemma`.

Each trace conforms strictly to the **ATIF v1.7 JSON Schema**:
- **Metadata Block**: Records `instance_id`, `repo`, `base_commit`, `agent_config_name`, vLLM sampling parameters (`temperature=0.0`, `seed=42`, `max_output_tokens=8192`, `thinking_budget=1536`), and hardware fingerprints.
- **Step Sequence**: Interaction turns containing: `metrics` (per-call prompt, completion, and total tokens), `tool_calls` (tool name, JSON arguments, author), `observation` (stdout/stderr, error types: `FileEditError`, `CommandError`, `FileReadError`, `BudgetExceeded`), and `message` (model response text with deliberative reasoning tagged in `extra.event_type: "thinking"`).
- **Final Metrics**: Cumulative token counts (`total_prompt_tokens`, `total_completion_tokens`, `total_tokens`, `total_steps`), duration, patch string, and Phase 2 test exit codes.

All 112 traces (100.0%) pass formal validation against `dataset_resource/atif_schema_v1_7.json` using the standard `jsonschema` Draft-07 validator (`analysis/validate_atif_schema.py`).

---

## 4. Failure Taxonomy & Phase 2 Outcome Breakdown

In SWE-bench, patch verification is executed in an isolated verification sandbox using `pytest`. In ATIF-Gemma, cross-referencing agent traces against Phase 2 test runner outputs reveals that treating unresolved runs as a monolithic failure category conceals fundamentally different failure mechanics. We define four principal failure mechanisms—patch/assertion failure, test-collection failure, pre-submission budget exhaustion, and verification timeout—and report successful resolution as a separate outcome:

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
A key diagnostic finding enabled by ATIF-Gemma is that **nearly one-third of all agent runs (36/112 = 32.1%) failed before unit tests could execute**. Deterministic classification (`analysis/classify_exit2.py`) separates these into agent-attributable versus environment-attributable failures:

1. **Agent-Attributable Failures (16/36 = 44.4%)**:
   - **Syntactic & Indentation Corruption (13/36 = 36.1%)**: Across 7 tasks (e.g., `fastapi_14099`, `rich_3894`), patches inserted unindented blocks or unclosed brackets, raising `IndentationError` or `SyntaxError` during collection.
   - **Missing Source Module (3/36 = 8.3%)**: On `rich_3930` (3 runs), omitting required new module `rich/_unicode_data.py` caused `ModuleNotFoundError`.

2. **Environment-Attributable Failures (20/36 = 55.6%)**:
   - **Environment & Path Shadowing (10/36 = 27.8%)**: On `httpx_3672` (5 runs), pre-installed packages in `/usr/local/lib/python3.12/dist-packages` shadowed `/workspace/src/httpx`. On `fastapi_15661` (5 runs), tests imported `scripts.prepare_release` while `/workspace/scripts` was omitted from `PYTHONPATH`.
   - **Missing Sandbox Dependencies (10/36 = 27.8%)**: On 4 tasks (`fastapi_14361`, `14371`, `14455`, `14459`), tests required external libraries (`inline_snapshot`, `dirty_equals`) absent from the offline wheelhouse.

This distinction highlights the dual diagnostic value of execution traces: identifying agent patch deficiencies while pinpointing execution harness anomalies.

### 4.2 Deterministic Sub-Classification of Assertion Failures (Exit Code 1: 56 Runs)
Representing 50.0% of the corpus (56/112), Exit Code 1 runs pass syntax checks but fail pytest assertions. Using a formal mutually exclusive decision tree (`analysis/subclassify_exit1.py`), we assign every run to one tier:

1. **Empty Patch (1/56 = 1.8%)**: Evaluated first: $|F_{\text{agent}}| = 0$ (on `fastapi_5624`, 0 modified characters).
2. **Wrong-File Localization (17/56 = 30.4%)**: Evaluated second: $F_{\text{agent}} \cap F_{\text{gold}} = \emptyset$. The agent edited unrelated files (e.g., in `fastapi_15589`, modifying `params.py` instead of `dependencies/utils.py`).
3. **Partial Multi-File Localization (14/56 = 25.0%)**: Evaluated third: $|F_{\text{gold}}| > 1$ and $F_{\text{agent}} \subsetneq F_{\text{gold}}$. The bug spanned multiple modules, but the agent edited only a strict subset (e.g., in `requests_7505`, modifying `models.py` but omitting `sessions.py`).
4. **Right-File, Wrong-Logic (24/56 = 42.9%)**: Evaluated fourth: remaining runs where $F_{\text{agent}} \cap F_{\text{gold}} \neq \emptyset$. File localized, but synthesized logic failed assertions (e.g., `requests_7502`, `rich_3043`).

*Methodological note:* Gold-patch file overlap serves as an objective structural proxy for localization; valid alternative patches modifying different files are possible in rare cases (Section 8).

### 4.3 Ground-Truth Resolved Runs
Across the 112 runs, 8 runs resolved held-out tests across 4 tasks: `rich_4077` (3 runs: `sfd`, `sfd_rerun`, `flat_controlled_rerun`), `fastapi_9753` (1 run: `flat_starter`), `fastapi_14077` (2 runs: `sfd`, `flat_controlled`), and `rich_3894` (2 runs: `flat_starter`, `flat_controlled`).
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
Across all 32 benchmark tasks, resolution rates are identical at 2/32 (6.25%, 95% Wilson CI [1.73%, 20.15%]) across `flat_starter`, `flat_controlled`, and `sfd`. McNemar's exact test yields $p = 1.0000$ for all pairwise comparisons ($b=1, c=1$ for SFD vs controlled and controlled vs starter; $b=2, c=2$ for SFD vs starter). **No statistically significant resolution advantage exists between architectures on this small model.**

In contrast, SFD's stage isolation produces significant token efficiency gains:
- **Cumulative Prompt Tokens**: SFD consumes 37,797.4 fewer prompt tokens per task than `flat_controlled` (-32.0%, 95% bootstrap CI: `[-52,214.6, -23,755.2]`, Wilcoxon $p < 0.0001$; lower on 25/32 tasks). Compared to `flat_starter`, SFD consumes 25,441.9 fewer tokens (-24.0%, 95% bootstrap CI: `[-42,485.1, -9,031.4]`, Wilcoxon $p = 0.0061$; lower on 24/32 tasks).
- **Peak Prompt Tokens ($P_t$)**: SFD reduces peak prompt size by 3,051.6 tokens (-21.9%, 95% bootstrap CI: `[-4,142.9, -1,968.2]`, Wilcoxon $p < 0.0001$; lower on 28/32 tasks).
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
In `sfd` traces, setting `include_contents: "none"` on downstream stages resets entry prompts from a mean TriageAgent peak of 10,473.9 tokens (median 9,863.0) to 1,536.9 tokens (median 1,503.0) at PatchAgent entry. Across all 32 primary SFD runs, this yields a prompt reset distribution with median 87.43%, mean 81.95%, IQR [75.72%, 89.46%], and range [44.95%, 92.49%], driving the overall 32.0% prompt token reduction relative to single-agent baselines (Wilcoxon $p < 0.0001$).

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
To evaluate the practical efficacy of the proposed remediations, we conducted an offline post-hoc re-evaluation of stored patches (`analysis/remediation_eval.py`, `results/remediation_eval.json`). **These results are an offline diagnostic assessment and do not alter the official Phase 2 competition evaluation benchmarks reported in Section 4 and Tables 1–3.**

1. **Pre-Submission `py_compile` Gate**: Tested against all 13 Exit Code 2 runs exhibiting syntactic corruption, an automated syntax validation gate intercepts 100% (13/13) of syntax-broken patches prior to calling `submit_patch`. Intercepting malformed patches prevents blind collection crashes (Exit Code 2), but does *not* resolve the underlying task without additional self-repair turns (resolution remains 0/13 without re-prompting).
2. **`PYTHONPATH` Priority Enforcement**: Auditing all 10 environment-shadowed runs on `httpx_3672` and `fastapi_15661`, prepending repository source paths (`PYTHONPATH=/workspace/src:/workspace`) eliminates collection crashes from site-package shadowing. Full evaluation requires the offline Linux `swegemma` container; thus, no speculative resolution gains are claimed.

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

1. **Task Sample Size ($n = 32$)**: Evaluating 32 unique benchmark instances covers 25% of the 129 competition tasks. Evaluating the full split across three configurations would require >500 NVIDIA L4 GPU hours.
2. **Single Model & Quantization**: All traces were generated on `gemma-4-e4b-it-qat-w4a16-ct` (INT4). Behaviors such as 90.6% sub-agent bypassing and syntax corruption rates are specific to this model; larger models (e.g., Gemma 4 31B) may behave differently.
3. **Repository Diversity**: Concentrated on four Python libraries (`fastapi`, `rich`, `requests`, `httpx`). Statically typed languages or different test runners may exhibit different failure dynamics.
4. **Greedy Decoding ($T = 0.0$)**: All runs used greedy decoding with `seed = 42`. While 87.5% of rerun patches were bitwise identical, vLLM micro-batching causes minor token variance.
5. **File-Level Structural Proxy**: Our taxonomy evaluates file-level diff overlap ($F_{\text{agent}} \cap F_{\text{gold}}$). While objective, valid alternative solutions modifying different files remain possible.
6. **Harness Environment**: Artifacts (e.g., missing wheelhouse packages, path shadowing) reflect Kaggle's offline Linux container environment.

---

## 9. Conclusion & Resource Availability

ATIF-Gemma provides an open, reproducible diagnostic foundation for compact coding agents. By moving beyond scalar pass/fail rates to an open 112-trace corpus, a structured failure taxonomy, an Actionable Remediation Playbook, and open diagnostic Python tooling, this resource enables researchers to target the true bottlenecks of small developer agents: collection crashes, context bloat, and localization drift.

- **Kaggle Dataset:** [ATIF-Gemma SWE Agent Traces](https://www.kaggle.com/datasets/karandeepsinghsodhi/atif-gemma-swe-agent-traces) (CC BY 4.0)  
- **GitHub Repository:** [gemma-sfd-agent](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent) (Apache 2.0)  
- **Interactive Kernel:** [Diagnostic Exploration](https://www.kaggle.com/code/karandeepsinghsodhi/atif-gemma-diagnostic-exploration)  
- **Manuscript PDF:** [paper_resource.pdf](https://raw.githubusercontent.com/KarandeepSinghSodhi/gemma-sfd-agent/main/paper_resource.pdf)
