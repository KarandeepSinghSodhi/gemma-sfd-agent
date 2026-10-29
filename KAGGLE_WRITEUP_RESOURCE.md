# ATIF-Gemma: Diagnostic Corpus and Failure Taxonomy for Small Developer Agents

**Author:** Karandeep Singh Sodhi  
**Competition:** Kaggle Gemma 4 Developer Agent Paper Competition (Target award: Best New Resource)  
**Artifact Repository:** https://github.com/KarandeepSinghSodhi/gemma-sfd-agent (Tag: `v1.0.0-camera-ready`)  
**Companion Architecture Paper:** [Sodhi (2026)](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent/blob/v1.0.0-camera-ready/KAGGLE_WRITEUP.md)

---

## Abstract

SWE-bench benchmarks report scalar resolution rates, obscuring multi-turn failure dynamics in small developer agents. Small models plateaued at low resolution (median 5.0% across 197 teams on the official Small Model Prize leaderboard). We introduce **ATIF-Gemma**, an open diagnostic corpus of 112 multi-turn execution traces across 32 SWE-bench tasks evaluating `gemma-4-e4b-it-qat-w4a16-ct` on 4x NVIDIA L4 GPUs across three controlled architectures (`flat_starter`, `flat_controlled`, `sfd`).

Standardized under ATIF v1.7 (Harbor Framework Contributors, 2026), ATIF-Gemma links agent actions to held-out test outcomes. Primary resolution is **6/96 (6.25%)** (2/32 per config, 95% Wilson CI [1.73%, 20.15%]; cluster-bootstrap CI [1.04%, 12.50%]); pooled resolution is 8/112 (7.14%). Across 26 complete-case tasks with valid outcomes for all configurations, each resolved 2/26 (7.69%, 95% CI [2.14%, 24.14%]; 6/78 overall, cluster-bootstrap CI [1.28%, 15.38%]). We classify four failure modes: assertion failures (50.0%, 56/112), collection crashes (32.1%, 36/112), budget exhaustion (8.0%, 9/112), and harness timeouts (2.7%, 3/112). Collection errors partition into agent-attributable failures (16/36) versus sandbox defects (20/36; flagged `env_suspected=True`). Excluding suspected defects leaves 92 valid runs, yielding **6/80 (7.50%)** primary and **8/92 (8.70%)** pooled resolution. We release the corpus, the `atif_gemma` toolkit, and remediation patterns.

---

## 1. Introduction & The Diagnostic Vacuum in SWE Benchmarking

Unlike single-turn code benchmarks (HumanEval; Chen et al., 2021; MBPP; Austin et al., 2021), SWE-bench established repository-level issue resolution for coding agents (Jimenez et al., 2024). Reported resolution rates depend strongly on benchmark split, model scale, and agent harness. Although agent interfaces and architectures have advanced (Yang et al., 2024; Wang et al., 2024; Xia et al., 2024), aggregate scores alone obscure execution bottlenecks. On the competition split, compact models (`gemma-4-e4b-it-qat-w4a16-ct`) plateaued below 10% (median 5.0% across 197 teams; Holbrook, 2026). ATIF-Gemma addresses this diagnostic vacuum through 112 standardized traces, a 4-tier failure taxonomy, a rerun audit, and the open `atif_gemma` toolkit.

---

## 2. Related Work: Trajectory Corpora & Agent Diagnostics

### 2.1 SWE Agent Trajectories & Diagnostics
Prior work established repair benchmarks (SWE-bench; Jimenez et al., 2024), agent interfaces (SWE-agent; Yang et al., 2024; OpenHands; Wang et al., 2024; Agentless; Xia et al., 2024), and training data on real tasks (SWE-Gym; Pan et al., 2024) or synthetic tasks (SWE-smith; Yang et al., 2025). Public Gemma 4 datasets also provide traces (Rajak, 2026). ATIF-Gemma complements these with an exit-code failure taxonomy, suspected-environment attribution, and a rerun audit for compact Gemma 4 agents under version-pinned ATIF v1.7 (Harbor Framework Contributors, 2026).

### 2.2 Small Open-Weight Developer Agents
Gemma 4 (Gemma Team, 2026) introduced compact edge models (`gemma-4-e4b-it-qat-w4a16-ct`). In multi-turn agents, managing observation bloat is critical (Lindenbauer et al., 2025). While our companion SFD paper (Sodhi, 2026) addressed prompt bloat across 16 tasks, ATIF-Gemma provides the diagnostic corpus, failure taxonomy, and reproducibility audit across 32 tasks and 112 runs.

---

## 3. Corpus Architecture & ATIF v1.7 Schema Specifications

### Table 1: Composition of the ATIF-Gemma Diagnostic Corpus

| Corpus Partition | Traces | Tasks | LLM Calls | Tool Calls | Total Tokens |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Cohort 1 (Canonical)** | 24 | 8 | 304 | 265 | 2,270,463 |
| **Cohort 2 (Stratified Random)** | 24 | 8 | 339 | 298 | 2,720,322 |
| **Cohort 1 Rerun** | 16 | 8 | 204 | 172 | 1,387,758 |
| **Cohort 3 (Stratified Disjoint)** | 24 | 8 | 349 | 309 | 2,771,960 |
| **Cohort 4 (Stratified Disjoint)** | 24 | 8 | 322 | 284 | 2,555,675 |
| **Total ATIF-Gemma Corpus** | **112** | **32** | **1,518** | **1,328** | **11,706,178** |

*Note: 32 unique tasks; Cohort 1 Rerun replicates Cohort 1 for reproducibility.*

Covering 32 tasks across 4 repos (`fastapi`: 51, `rich`: 37, `requests`: 19, `httpx`: 5) on 4x NVIDIA L4 GPUs via vLLM (`tp=4`) hosting `gemma-4-e4b-it-qat-w4a16-ct` under Google ADK and `swegemma`, traces record tool calls, thoughts (`extra.event_type: "thinking"`), token metrics, and exit codes.

**Schema Conformance, Datasheet & Governance (Gebru et al., 2021):** All 112 traces pass formal validation against our version-pinned ATIF v1.7 schema (`dataset_resource/atif_schema_v1_7.json`; Harbor Framework Contributors, 2026; `analysis/validate_atif_schema.py`; full sheet in `dataset_resource/datasheet.md`):
- *Data Access & Licensing*: Code competition data (`gemma-4-developer-agent`) are accessed under Sections 1.7 & 2.4.a.1 of the [Official Rules](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules) (*"may access and use the Competition Data for any purpose... including for academic research and education"*). Evaluated tasks originate from open-source repositories under MIT, Apache-2.0, and BSD-3-Clause licenses (`NOTICE`).
- *Data Security & Derived Labels (Rule 2.4.b.1)*: Code competition Rule 2.4.b.1 restricts Competition Data redistribution. ATIF-Gemma distributes only model-generated trajectories and metadata; proprietary `test_patch` files are strictly omitted. On the forum ([Topic 749803](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/749803)), Host Elan Markowitz confirmed: *"Yes, publishing derived labels is okay."* Gold-patch file lists serve solely as internal ground truth for derived localization tiers (`analysis/subclassify_exit1.py`) and are not redistributed. Step 0 problem statements derive from public GitHub issues. Traces: CC BY 4.0; companion code: Apache-2.0.
- *Dual-Submission Allowance (Rule 2.2.b)*: Under Section 2.2.b of the [Paper Rules](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/rules) (*"You may select up to two (2) Final Submissions for judging"*), Host Elan Markowitz confirmed ([Topic 743255](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/743255)): *"A team can submit at most two write-ups. There is only one submission track, and the judges will determine the eligibility for each prize."* ATIF-Gemma serves as empirical companion to our SFD architecture paper (Sodhi, 2026), contributing the diagnostic corpus, failure taxonomy, and reproducibility audit.

---

## 4. Failure Taxonomy & Phase 2 Outcome Breakdown

**Cross-Paper Taxonomy Concordance & Scope:** While companion SFD (Sodhi, 2026) evaluated 16 paired tasks (48 runs) across three coarse categories, ATIF-Gemma evaluates 32 tasks across 5 cohorts (112 runs) decomposed into exact container exit codes:
- `timeout_or_budget_no_patch` (15 runs) = pre-submission budget exhaustion (Exit -1, 9 runs) + zero-byte runs without code edits (Exit 1, 6 runs; e.g. `rich_3944` flat_starter).
- `test_verification_failed` (89 runs) = test-collection crashes (Exit 2, 36 runs: 16 agent-attributable vs 20 `env_suspected`) + non-empty assertion failures (Exit 1 Tiers 2–4, 50 runs) + verification timeouts (Exit 124, 3 runs).
- `resolved` (8 runs) = clean execution passing all unit assertions without regressions (Exit 0; 6 primary, 2 reruns). Total: 15 + 89 + 8 = 112 runs.

### Table 2: Phase 2 Exit Code Failure Taxonomy Across 112 GPU Traces

| Category | Exit Code | Count (%) | Empirical Mechanism & Operational Diagnosis |
| :--- | :---: | :---: | :--- |
| **Resolved** | `0` | 8 (7.1%) | Patch applied cleanly; all pytest unit assertions passed with zero regressions. |
| **Assertion Failure** | `1` | 56 (50.0%) | Patch applied (or empty zero-byte diff); pytest collected test suite, but $\ge 1$ assertion failed. |
| **Collection Crash** | `2` | 36 (32.1%) | Pytest crashed during test collection (syntax errors, missing modules, import shadowing). |
| **Turn Budget / No-Patch** | `-1` | 9 (8.0%) | Exhausted tool/time budget (`max_tool_calls=15`, `max_turns=20`, `max_time_minutes=2.5`) without generating diff (0 patch characters). |
| **Harness Timeout** | `124` | 3 (2.7%) | Pytest execution exceeded container wall-clock limit (>120s execution timeout). |

### 4.1 Deterministic Mechanism Breakdown of Collection Errors (Exit Code 2: 36 Runs)
32.1% of runs (36/112) failed before unit tests executed (`analysis/classify_exit2.py`):
1. **Agent Causes (16/36 = 44.4%)**: Syntax corruption (13/36 across 7 tasks) and missing modules (3/36 on `rich_3930`).
2. **Environment Causes (20/36 = 55.6%; `env_suspected=True`)**: Path shadowing (10/36 on `httpx_3672`, `fastapi_15661`) and missing wheels (`inline_snapshot`, `dirty_equals` on 10 runs across 4 tasks). Gold-patch controls (`analysis/gold_patch_control.py`) require offline containers (future work).

Excluding 20 suspected sandbox defects leaves 92 valid runs (80 primary, 12 reruns). Across 26 complete-case tasks (78 paired runs), each configuration resolved 2/26 (7.69%, 95% Wilson CI [2.14%, 24.14%]; 6/78 overall, 95% cluster-bootstrap CI [1.28%, 15.38%]). No statistically significant resolution difference was detected by exact McNemar tests ($p=1.000$). Given the small number of tasks and low resolution counts, this should not be interpreted as statistical equivalence. Across all 80 valid primary runs, resolution is **6/80 (7.50%, unadjusted 95% CI [3.48%, 15.41%])** (`flat_starter` 2/27, `flat_controlled` 2/27, `sfd` 2/26); pooled across 92 valid runs, resolution is **8/92 (8.70%, unadjusted 95% CI [4.47%, 16.23%])**.

### 4.2 Deterministic Sub-Classification of Assertion Failures (Exit Code 1: 56 Runs)
Exit Code 1 represents 50.0% of runs (56/112). A decision tree (`analysis/subclassify_exit1.py`) partitions them:
1. **Empty / Zero-Byte Patch (6/56 = 10.7%)**: $|F_{\text{agent}}| = 0$. Zero-byte diffs where pytest ran without edits from tool errors (`rich_3043` sfd, `rich_3944` flat_starter, `requests_7502` sfd_rerun), budget limits (`fastapi_14372` flat_starter, `requests_7315` flat_controlled), or unattempted edits (`fastapi_5624` flat_controlled).
2. **Wrong-File Localization (15/56 = 26.8%)**: $F_{\text{agent}} \cap F_{\text{gold}} = \emptyset$ with applied diff (e.g. `fastapi_15589`).
3. **Partial Multi-File (14/56 = 25.0%)**: $|F_{\text{gold}}| > 1$ and $F_{\text{agent}} \subsetneq F_{\text{gold}}$ (e.g. `requests_7505`).
4. **Right-File, Wrong-Logic (21/56 = 37.5%)**: $F_{\text{agent}} \cap F_{\text{gold}} \neq \emptyset$. Correct file(s), but failed unit assertions (e.g. `rich_3471`).

*Caveat:* File overlap ($F_{\text{agent}} \cap F_{\text{gold}}$) is a structural proxy; alternative valid patches exist.

### 4.3 Ground-Truth Resolved Runs & Task Clustering
Across 112 runs, 8 resolved held-out tests on 4 tasks: `rich_4077` (3 runs), `fastapi_9753` (1), `fastapi_14077` (2), `rich_3894` (2). In primary runs ($n=96$), 4/32 tasks (12.5%) resolved at least once; 0/32 resolved across all 3 configs. Runs sharing tasks are clustered.

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

*Note:* Primary resolution: unadjusted outcomes across 32 tasks; complete-case analysis (2/26 per config, 6/78 overall) in Section 4.1. **Peak $P_t$**: max prompt length. **Cumulative Prompt**: sum of input prompt tokens.

### 5.1 Statistical Tests & Resolution Invariance
Across 32 primary tasks, resolution shows identical marginal counts at 2/32 (6.25%, 95% Wilson CI [1.73%, 20.15%]) across `flat_starter`, `flat_controlled`, and `sfd` (McNemar $p = 1.0000$ for all pairs; 6/96 overall, 95% cluster-bootstrap CI [1.04%, 12.50%]). Given small sample sizes, this reflects limited statistical power rather than equivalence.

In contrast, SFD achieves significant token reductions over flat baselines across 32 tasks (paired comparisons exploratory without multiplicity adjustment):
- **Cumulative Prompt Tokens**: vs `flat_controlled`: **-37,797.4 (-32.0%)** (95% CI [-52,214.6, -23,755.2], Wilcoxon $p < 0.0001$; lower in 25/32); vs `flat_starter`: **-25,441.9 (-24.0%)** (95% CI [-42,485.1, -9,031.4], $p = 0.0061$; lower in 24/32).
- **Peak Prompt Tokens**: vs `flat_controlled`: **-3,051.6 (-21.9%)** (95% CI [-4,142.9, -1,968.2], $p < 0.0001$; lower in 28/32); vs `flat_starter`: **-2,452.2 (-18.4%)** (95% CI [-3,795.9, -1,111.8], $p = 0.0008$; lower in 26/32).
- **Cumulative Total Tokens**: vs `flat_controlled`: **-36,786.3 (-29.7%)** (95% CI [-51,715.4, -22,346.4], $p < 0.0001$); vs `flat_starter`: **-24,585.3 (-22.0%)** (95% CI [-41,948.3, -8,026.9], $p = 0.0073$).
- **Duration**: Differences are not statistically significant (vs `flat_controlled`: -4.2s, -4.7%, $p = 0.4540$; vs `flat_starter`: -7.7s, -8.1%, $p = 0.4429$).

### 5.2 Rerun Reproducibility & Determinism Audit
Cohort 1 was re-executed across 8 tasks $\times$ 2 configs (16 paired runs; `analysis/statistical_tests.py`):
- **Exit Code Agreement**: 12/16 runs (75.0%) matched exit codes (4 flips: `rich_4077` ctrl 1->0; `fastapi_15588` sfd 1->2; `fastapi_15589` ctrl 1->2; `fastapi_15589` sfd -1->1).
- **Patch Presence Agreement**: 14/16 runs (87.5%) agreed on patch presence (8/8 `flat_controlled`, 6/8 `sfd`; discordant on `fastapi_15589`, `requests_7502`).
- **Normalized Edit-Operation Hash Agreement**: Hashes of recorded edit and patch payloads matched in 0/16 pairs (0.0%), showing run-to-run edit divergence despite greedy decoding ($T=0.0$).
- **Semantic Concordance Across Reruns**:
  - *Resolution Convergence (`rich_4077`)*: All three resolved runs (`flat_controlled_rerun`, `sfd_orig`, `sfd_rerun`) converged to identical 3-line logic (`def isatty(self) -> bool: return self.__file.isatty()`), differing only by anchor (after line 18 `fileno()` vs before line 23 `write()`; diffs in `results/rich_4077_diffs.md`).
  - *Unresolved Concordance (`requests_7505`)*: Across both `flat_controlled` runs on `requests_7505`, original and rerun applied identical logic (`elif isinstance(fp, _SupportsRead): fdata = fp.read()`), differing only by comments. Both failed (Exit 1, Tier 3) because the task required modifying `src/requests/_types.py` (defining `has_read()`) and `models.py`.
  - *Cohort-Wide Concordance*: 10/16 pairs (62.5%) touched identical files; 1 pair (`requests_7505` `flat_controlled`) matched 100% on normalized replacement code; recorded edit sequences diverged in all 16 pairs due to context lines and anchors.
- **Token Drift**: Mean absolute difference was **18,571.0 total tokens** between pairs.

### 5.3 Sub-Agent Bypassing in the Starter Kit
In `flat_starter`, root wraps `code_analyzer` as an `AgentTool`. Across 32 traces:
- Out of 336 tool calls, the model delegated only **7 times (2.1%)**.
- The model **bypassed delegation on 26 of 32 tasks (81.2%)**, reading files directly into root context (6/32 delegated).

![Figure 3: Sub-Agent Delegation Funnel](figures/fig3_delegation_funnel.png)
*Figure 3: Sub-agent delegation in `flat_starter`: 81.2% bypassed delegation; 2.1% calls delegated.*

### 5.4 Cross-Stage Prompt Resets
In `sfd`, `include_contents: "none"` resets entry prompts from a mean TriageAgent peak of 10,473.9 tokens (median 9,863.0) to 1,536.9 tokens (median 1,503.0) at PatchAgent entry. Across 32 primary runs, this yields an 81.95% mean prompt reset (median 87.43%, IQR [75.72%, 89.46%]), driving 32.0% prompt reduction over flat baselines ($p < 0.0001$).

![Figure 2: Prompt Token Expansion & Stage Resets](figures/fig2_prompt_resets.png)
*Figure 2: Prompt trajectories across steps $t$ (mean with 95% bootstrap bands). Flat runs expand monotonically; SFD resets prompt tokens by 87.43% median.*

---

## 6. Candidate Remediations (Untested Unless Stated)

Diagnostic classifications suggest actionable engineering patterns:

| Failure Mode | Prevalence | Candidate Remediation Pattern |
| :--- | :---: | :--- |
| **Collection / Path Crash** | 36/112 (32.1%) | Enforce `PYTHONPATH` priority; execute pre-flight dependency checks. |
| **Edit-Tool Failures** | 100 errors (64 StringNotFound, 36 Malformed) | Validate edit targets against buffer; handle failed edits explicitly. |
| **Syntax Corruption** | 13/112 runs (11.6%) | Mandate `py_compile` check before `submit_patch` with self-repair turns. |
| **Wrong-File Localization** | 15/112 (13.4% overall; 26.8% Exit 1) | Two-way symbol verification loop (untested) prior to edit. |
| **Unbounded Context Growth** | 64/64 flat runs (100% monotonic) | Stage context pruning (`include_contents: "none"`), resetting context 81.9% mean (reduces tokens; no resolution gain). |

### 6.1 Post-Hoc Diagnostic Evaluation (Non-Official Harness)
Offline diagnostic checks (`analysis/remediation_eval.py`, `results/remediation_eval.json`) do not alter official benchmarks:
1. **Pre-Submission `py_compile` Gate**: Catches 100% (13/13) of syntax-corrupted patches before `submit_patch` by construction; recovery without repair turns was 0/13.
2. **`PYTHONPATH` Priority**: Prepending repository source (`PYTHONPATH=/workspace/src:/workspace`) is predicted to avoid collection crashes across all 10 path-shadowed runs (`httpx_3672`, `fastapi_15661`). Full evaluation requires container execution; no speculative gains are claimed.

---

## 7. The `atif_gemma` Python Package & CLI

We release the standalone Python package `atif-gemma`:
```bash
pip install git+https://github.com/KarandeepSinghSodhi/gemma-sfd-agent.git
```
Modules provide trajectory auditing (`audit`), deterministic exit-code and localization classification (`taxonomy`), and remediations (`remediation`). CLI: `python -m atif_gemma.cli audit traces/` and `python -m atif_gemma.cli playbook`.

---

## 8. Limitations & Threats to Validity

1. **Task Sample ($n = 32$)**: Covers ~25% of benchmark (full evaluation requires >500 L4 GPU hours).
2. **Model & Quantization**: Specific to `gemma-4-e4b-it-qat-w4a16-ct` (INT4); larger models may differ.
3. **Repository Scope**: Evaluates 4 Python repos; runs sharing tasks are paired and clustered.
4. **Non-Determinism**: Under $T=0.0$, 12/16 exit codes matched on rerun, but edit hashes diverged (mean drift: 18,571 tokens).
5. **Structural Proxy**: File overlap ($F_\text{agent} \cap F_\text{gold}$) is an automated proxy; valid alternative patches exist.
6. **Sandbox Defects (`env_suspected=True`)**: 20 runs failed from container constraints (missing wheels, path shadowing).

---

## 9. Conclusion & Resource Availability

ATIF-Gemma shows raw resolution rates mask critical execution bottlenecks (50.0% assertion failures, 32.1% collection crashes). All 112 traces, metadata, and analysis tools are open-sourced:
- **GitHub Repository**: https://github.com/KarandeepSinghSodhi/gemma-sfd-agent (Tag: `v1.0.0-camera-ready`)
- **Kaggle Dataset**: `karandeepsinghsodhi/atif-gemma-swe-agent-traces`
- **Kaggle Notebook**: `karandeepsinghsodhi/atif-gemma-diagnostic-exploration`

---

## 10. References

- Austin, J., et al. (2021). Program Synthesis with Large Language Models. [*arXiv:2108.07732*](https://arxiv.org/abs/2108.07732)
- Chen, M., et al. (2021). Evaluating Large Language Models Trained on Code. [*arXiv:2107.03374*](https://arxiv.org/abs/2107.03374)
- Gebru, T., et al. (2021). Datasheets for Datasets. *Communications of the ACM*, 64(12), 86–92.
- Gemma Team. (2026). Gemma 4 Technical Report. [*arXiv:2607.02770*](https://arxiv.org/abs/2607.02770)
- Harbor Framework Contributors. (2026). Agent Trajectory Interchange Format (ATIF) Specification (v1.7). *GitHub*. [laude-institute/harbor](https://github.com/laude-institute/harbor)
- Holbrook, R. (2026). Google Gemma 4 Developer Agent Competition: Small Model Prize Leaderboard Snapshot. *Kaggle*. [Leaderboard](https://www.kaggle.com/competitions/gemma-4-developer-agent/leaderboard) (Snapshot: `results/small_model_leaderboard_2026_10_24.csv`, accessed October 24, 2026).
- Jimenez, C. E., et al. (2024). SWE-bench: Can Language Models Resolve Real-World GitHub Issues? *ICLR 2024*. [*arXiv:2310.06770*](https://arxiv.org/abs/2310.06770)
- Lindenbauer, T., et al. (2025). The Complexity Trap: Simple Observation Masking Is as Efficient as LLM Summarization for Agent Context Management. [*arXiv:2508.21433*](https://arxiv.org/abs/2508.21433)
- Pan, J., et al. (2024). Training Software Engineering Agents and Verifiers with SWE-Gym. [*arXiv:2412.21139*](https://arxiv.org/abs/2412.21139)
- Rajak, R. (2026). Gemma 4 TFD Agentic Trajectories & Benchmark: 50 multi-turn SWE-bench trajectories. *Kaggle Datasets*. [Benchmark](https://www.kaggle.com/datasets/rajarajak/gemma-4-tfd-agentic-trajectories-benchmark)
- Sodhi, K. S. (2026). State-Filtered Deliberation: Mitigating Multi-Turn Context Bloat in Small Developer Agents. *Kaggle Gemma 4 Developer Agent Paper Competition*. [Companion Paper](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent/blob/v1.0.0-camera-ready/KAGGLE_WRITEUP.md).
- Wang, X., et al. (2024). OpenHands: An Open Platform for AI Software Developers as Generalist Agents. [*arXiv:2407.16741*](https://arxiv.org/abs/2407.16741)
- Xia, C. S., et al. (2024). Agentless: Demystifying LLM-based Software Engineering Agents. [*arXiv:2407.01489*](https://arxiv.org/abs/2407.01489)
- Yang, J., et al. (2024). SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering. *NeurIPS 2024*. [*arXiv:2405.15793*](https://arxiv.org/abs/2405.15793)
- Yang, J., et al. (2025). SWE-smith: Scaling Data for Software Engineering Agents. [*arXiv:2504.21798*](https://arxiv.org/abs/2504.21798)
