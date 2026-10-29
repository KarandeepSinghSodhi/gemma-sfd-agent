# ATIF-Gemma: Diagnostic Corpus and Failure Taxonomy for Small Developer Agents

**Author:** Karandeep Singh Sodhi  
**Competition:** Kaggle Gemma 4 Developer Agent Paper Competition (Target award: Best New Resource)  
**Artifact Repository:** https://github.com/KarandeepSinghSodhi/gemma-sfd-agent (Tag: `v1.0.1-camera-ready`)  
**Companion Architecture Paper:** [Sodhi (2026)](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent/blob/v1.0.1-camera-ready/KAGGLE_WRITEUP.md)

---

## Abstract

SWE-bench benchmarks report scalar resolution rates, obscuring multi-turn failure dynamics in small developer agents. Small models plateaued at low resolution (median 5.0% across 197 teams on the official Small Model Prize leaderboard). We introduce **ATIF-Gemma**, an open diagnostic corpus of 112 multi-turn execution traces across 32 SWE-bench tasks evaluating `gemma-4-e4b-it-qat-w4a16-ct` on 4x NVIDIA L4 GPUs across three controlled architectures (`flat_starter`, `flat_controlled`, `sfd`).

Standardized under ATIF v1.7 (Harbor Framework Contributors, 2026), ATIF-Gemma links agent actions to held-out test outcomes. Primary resolution is **6/96 (6.25%)** (2/32 per config, 95% Wilson CI [1.73%, 20.15%]; cluster-bootstrap CI [1.04%, 12.50%]); across all 112 records, including reruns, 8 traces resolved (7.14%). Across 26 complete-case task clusters, each configuration resolved 2/26 tasks (7.69%, 95% Wilson CI [2.14%, 24.14%]); combined, the three configurations resolved 6/78 primary runs (95% task-cluster bootstrap CI [1.28%, 15.38%]). We classify four failure modes: assertion failures (50.0%, 56/112), collection crashes (32.1%, 36/112), budget exhaustion (8.0%, 9/112), and harness timeouts (2.7%, 3/112). Collection errors partition into agent-attributable failures (16/36) and environment-suspected failures (20/36; flagged `env_suspected=True`). In sensitivity analysis excluding the 20 flagged runs, resolution is **6/80 (7.50%)** primary and **8/92 (8.70%)** pooled. We release the corpus, `atif_gemma` toolkit, and remediations.

---

## 1. Introduction & The Diagnostic Vacuum in SWE Benchmarking

Unlike single-turn benchmarks (HumanEval; Chen et al., 2021; MBPP; Austin et al., 2021), SWE-bench established repository repair for coding agents (Jimenez et al., 2024). Resolution rates depend on split, model scale, and harness. Although agent interfaces have advanced (Yang et al., 2024; Wang et al., 2024; Xia et al., 2024), aggregate scores obscure execution failures. On the competition split, compact models (`gemma-4-e4b-it-qat-w4a16-ct`) plateaued ≤ 10% (median 5.0% across 197 teams; Holbrook, 2026). ATIF-Gemma resolves this diagnostic vacuum via 112 standardized traces, a 4-tier failure taxonomy, a rerun audit, and the open `atif_gemma` toolkit.

---

## 2. Related Work: Trajectory Corpora & Agent Diagnostics

### 2.1 SWE Agent Trajectories & Diagnostics
Prior work established repair benchmarks (SWE-bench; Jimenez et al., 2024), agent interfaces (SWE-agent; Yang et al., 2024; OpenHands; Wang et al., 2024; Agentless; Xia et al., 2024), and training data on real tasks (SWE-Gym; Pan et al., 2024) or synthetic tasks (SWE-smith; Yang et al., 2025). Public datasets also offer Gemma traces (Rajak, 2026). ATIF-Gemma complements these via an exit-code failure taxonomy, suspected-environment attribution, and a rerun audit for compact Gemma 4 agents under version-pinned ATIF v1.7 (Harbor Framework Contributors, 2026).

### 2.2 Small Open-Weight Developer Agents
Gemma 4 (Gemma Team, 2026) introduced edge models (`gemma-4-e4b-it-qat-w4a16-ct`). In multi-turn agents, managing observation bloat is critical (Lindenbauer et al., 2025). While companion SFD (Sodhi, 2026) addressed prompt bloat on 16 tasks, ATIF-Gemma contributes the diagnostic corpus, failure taxonomy, and reproducibility audit across 32 tasks and 112 runs.

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

*Note: The Cohort 1 Rerun repeats the flat_controlled and sfd configurations across the same eight tasks, yielding 16 rerun traces. The flat_starter configuration was not rerun.*

The 112 traces span 32 unique tasks across four repositories: `fastapi` (51 traces), `rich` (37), `requests` (19), and `httpx` (5). Experiments ran on 4 NVIDIA L4 GPUs via vLLM (`tp=4`) using `gemma-4-e4b-it-qat-w4a16-ct`. Traces record tool calls, deliberative thoughts (`extra.event_type: "thinking"`), token metrics, and Phase 2 exit codes.

**Schema Conformance, Datasheet & Governance (Gebru et al., 2021):** All 112 traces pass formal validation against version-pinned ATIF v1.7 (`dataset_resource/atif_schema_v1_7.json`; Harbor Framework Contributors, 2026; `analysis/validate_atif_schema.py`; sheet in `dataset_resource/datasheet.md`):
- *Data Access & Licensing*: Task data from the code competition (`gemma-4-developer-agent`) are accessed under Sections 1.7 & 2.4.a.1 of the [Official Rules](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules) (*"may access and use the Competition Data for any purpose... including for academic research and education"*). Repositories are open-source (MIT, Apache-2.0, BSD-3-Clause; `NOTICE`).
- *Data Security & Derived Labels (Rule 2.4.b.1)*: Per Rule 2.4.b.1, proprietary `test_patch` files are omitted. On the forum ([Topic 749803](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/749803)), Host Elan Markowitz confirmed: *"Yes, publishing derived labels is okay."* Gold-patch diffs are not redistributed; localization metrics record file counts and overlap. CC BY 4.0 covers original annotations/metadata; third-party code snippets in traces remain subject to upstream licenses (`NOTICE`); code: Apache-2.0.
- *Dual-Submission Allowance (Rule 2.2.b)*: Per Section 2.2.b of the [Paper Rules](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/rules), Host Elan Markowitz confirmed ([Topic 743255](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/743255)): *"A team can submit at most two write-ups. There is only one submission track, and the judges will determine the eligibility for each prize."* ATIF-Gemma is the empirical companion to SFD (Sodhi, 2026).

---

## 4. Failure Taxonomy & Phase 2 Outcome Breakdown

**Cross-Paper Taxonomy Concordance & Scope:** While SFD (Sodhi, 2026) evaluated 16 paired tasks (48 runs) on context efficiency, ATIF-Gemma evaluates 32 tasks across 5 cohorts (112 runs) for failure diagnosis, mapped to container exit codes:
- `timeout_or_budget_no_patch` (15 runs) = pre-submission budget exhaustion (Exit -1, 9 runs) + zero-byte runs without an applied edit (Exit 1, 6 runs; e.g. `rich_3944` flat_starter).
- `test_verification_failed` (89 runs) = collection crashes (Exit 2, 36 runs: 16 agent-attributable vs 20 `env_suspected`) + non-empty assertion failures (Exit 1 Tiers 2–4, 50 runs) + timeouts (Exit 124, 3 runs).
- `resolved` (8 runs) = clean execution passing unit assertions without regressions (Exit 0; 6 primary, 2 reruns). Total: 15 + 89 + 8 = 112 runs.

### Table 2: Phase 2 Exit Code Failure Taxonomy Across 112 GPU Traces

| Category | Exit Code | Count (%) | Empirical Mechanism & Operational Diagnosis |
| :--- | :---: | :---: | :--- |
| **Resolved** | `0` | 8 (7.1%) | Patch applied cleanly; all pytest unit assertions passed with zero regressions. |
| **Assertion Failure** | `1` | 56 (50.0%) | Patch applied (or empty zero-byte diff); pytest collected test suite, but ≥ 1 assertion failed. |
| **Collection Crash** | `2` | 36 (32.1%) | Pytest crashed during test collection (syntax errors, missing modules, import shadowing). |
| **Turn Budget / No-Patch** | `-1` | 9 (8.0%) | Exhausted tool/time budget (`max_tool_calls=15`, `max_turns=20`, `max_time_minutes=2.5`) without generating diff (0 patch characters). |
| **Harness Timeout** | `124` | 3 (2.7%) | Pytest execution exceeded container wall-clock limit (>120s execution timeout). |

*Note on Taxonomy Duality:* Table 2 uses mutually exclusive exit codes. Companion SFD reassigns the 6 Exit 1 zero-byte cases to `timeout_or_budget_no_patch`, shifting category totals while preserving 112 runs overall.

### 4.1 Deterministic Mechanism Breakdown of Collection Errors (Exit Code 2: 36 Runs)
32.1% of runs (36/112) failed before unit tests executed (`analysis/classify_exit2.py`):
1. **Agent Causes (16/36 = 44.4%)**: Syntax corruption (13/36 across 7 tasks) and missing modules (3/36 on `rich_3930`).
2. **Environment-Suspected Cases (20/36 = 55.6%; `env_suspected=True`)**: Path shadowing (10/36 on `httpx_3672`, `fastapi_15661`) and missing wheels (`inline_snapshot`, `dirty_equals` on 10 runs across 4 tasks). Gold-patch controls (`analysis/gold_patch_control.py`) require offline containers (future work).

Excluding the 20 flagged cases in sensitivity analysis leaves 92 runs (80 primary, 12 reruns). Across 26 complete-case clusters (78 primary runs evaluated across all 3 configs), each resolved 2/26 (7.69%, 95% Wilson CI [2.14%, 24.14%]; 6/78 overall, 95% cluster-bootstrap CI [1.28%, 15.38%]). No significant resolution difference was detected by exact McNemar tests (p = 1.000), reflecting limited power rather than equivalence. Across 80 sensitivity primary runs, resolution is **6/80 (7.50%, unadjusted 95% CI [3.48%, 15.41%])** (`flat_starter` 2/27, `flat_controlled` 2/27, `sfd` 2/26); pooled across 92 sensitivity runs, resolution is **8/92 (8.70%, unadjusted 95% CI [4.47%, 16.23%])**.

### 4.2 Deterministic Sub-Classification of Assertion Failures (Exit Code 1: 56 Runs)
Exit Code 1 represents 50.0% of runs (56/112). A decision tree (`analysis/subclassify_exit1.py`) partitions them:
1. **Empty / Zero-Byte Patch (6/56 = 10.7%)**: |F_agent| = 0. Zero-byte diffs without edits from tool errors (`rich_3043` sfd, `rich_3944` flat_starter, `requests_7502` sfd_rerun), budget limits (`fastapi_14372` flat_starter, `requests_7315` flat_controlled), or unattempted edits (`fastapi_5624` flat_controlled).
2. **Wrong-File Localization (15/56 = 26.8%)**: F_agent ∩ F_gold = ∅ with applied diff (e.g. `fastapi_15589`).
3. **Partial Multi-File (14/56 = 25.0%)**: |F_gold| > 1 and F_agent ⊂ F_gold (e.g. `requests_7505`, modifying `models.py` while omitting a companion module).
4. **Right-File, Wrong-Logic (21/56 = 37.5%)**: F_agent ∩ F_gold ≠ ∅. Correct file(s), but failed unit assertions (e.g. `rich_3471`).

*Caveat:* File overlap (F_agent ∩ F_gold) is a structural proxy; alternative valid patches exist.

### 4.3 Ground-Truth Resolved Runs & Task Clustering
Across 112 runs, 8 runs resolved the held-out tests, across 4 tasks: `rich_4077` (3 runs), `fastapi_9753` (1), `fastapi_14077` (2), `rich_3894` (2). In primary runs (n = 96), 4/32 tasks (12.5%) resolved at least once; 0/32 resolved across all 3 configs. Runs sharing tasks are clustered.

---

## 5. Quantitative Audit Across Agent Architectures

### Table 3: Architectural Metrics — 32 Primary Runs per Configuration and 8 Rerun Runs per Configuration

| Configuration | Runs | Resolved (95% Wilson CI) | Mean Peak P_t | Mean Cumulative Prompt | Mean Duration |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Official Starter (`flat_starter`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 13,359.7 | 105,817.6 | 94.2s |
| **Single-Agent (`flat_controlled`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 13,959.0 | 118,173.0 | 90.8s |
| **State-Filtered Deliberation (`sfd`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 10,907.5 | 80,375.7 | 86.6s |
| **Rerun: `flat_controlled`** | 8 | 1/8 (12.5%) [2.2%, 47.1%] | 12,557.5 | 93,135.6 | 107.4s |
| **Rerun: `sfd`** | 8 | 1/8 (12.5%) [2.2%, 47.1%] | 9,306.4 | 67,710.1 | 96.4s |

*Note:* Primary resolution: unadjusted outcomes across n = 32 tasks; complete-case analysis (2/26 per config, 6/78 overall) in Section 4.1. **Peak P_t**: max prompt length. **Cumulative Prompt**: sum of prompt tokens (n = 32 primary runs).

### 5.1 Statistical Tests & Resolution Invariance
Across 32 primary tasks, resolution shows identical marginal counts at 2/32 (6.25%, 95% Wilson CI [1.73%, 20.15%]) across `flat_starter`, `flat_controlled`, and `sfd` (McNemar p = 1.0000 for all pairs; 6/96 overall, 95% cluster-bootstrap CI [1.04%, 12.50%]). Given small sample size, this reflects limited statistical power rather than equivalence.

In contrast, SFD achieves significant token reductions over flat baselines (exploratory paired comparisons):
- **Cumulative Prompt Tokens**: vs `flat_controlled`: **-37,797.4 (-32.0%)** (95% CI [-52,214.6, -23,755.2], Wilcoxon p < 0.0001; lower in 25/32); vs `flat_starter`: **-25,441.9 (-24.0%)** (95% CI [-42,485.1, -9,031.4], p = 0.0061; lower in 24/32).
- **Peak Prompt Tokens**: vs `flat_controlled`: **-3,051.6 (-21.9%)** (95% CI [-4,142.9, -1,968.2], p < 0.0001; lower in 28/32); vs `flat_starter`: **-2,452.2 (-18.4%)** (95% CI [-3,795.9, -1,111.8], p = 0.0008; lower in 26/32).
- **Cumulative Total Tokens**: vs `flat_controlled`: **-36,786.3 (-29.7%)** (95% CI [-51,715.4, -22,346.4], p < 0.0001); vs `flat_starter`: **-24,585.3 (-22.0%)** (95% CI [-41,948.3, -8,026.9], p = 0.0073).
- **Duration**: Non-significant (vs `flat_controlled`: -4.2s, -4.7%, p = 0.4540; vs `flat_starter`: -7.7s, -8.1%, p = 0.4429).

### 5.2 Rerun Reproducibility & Determinism Audit
Cohort 1 was re-executed across 8 tasks × 2 configs (16 paired runs; `analysis/statistical_tests.py`):
- **Exit Code Agreement**: 12/16 runs (75.0%) matched exit codes (4 flips: `rich_4077` ctrl 1->0; `fastapi_15588` sfd 1->2; `fastapi_15589` ctrl 1->2; `fastapi_15589` sfd -1->1).
- **Patch Presence Agreement**: 14/16 runs (87.5%) agreed on patch presence (8/8 `flat_controlled`, 6/8 `sfd`; discordant on `fastapi_15589`, `requests_7502`).
- **Recorded Edit Payload Hash Agreement**: Serialized sequences of recorded `write_file`, `edit_file`, and `submit_patch` payloads matched in 0/16 rerun pairs (0.0%). This measures recorded tool payloads, not final repository patches. Manual diff analysis identified semantic convergence in selected cases (`rich_4077`), despite differences in recorded operations and context.
- **Concordance Observations**:
  1. *Target-File Localization*: 10/16 pairs (62.5%) touched the same source files.
  2. *Comment-Stripped Replacement Logic*: 1/16 pairs (6.3%; `requests_7505` `flat_controlled`, applying identical single-line logic `elif isinstance(fp, _SupportsRead): fdata = fp.read()`, differing only by comments; companion SFD evaluated SFD's distinct edit).
  3. *Semantic Resolution Convergence*: 1/16 pairs (6.3%; `rich_4077` `sfd`, converging on resolution via `def isatty(self) -> bool: return self.__file.isatty()`).
- **Token Drift**: Mean absolute difference was **18,571.0 total tokens** between paired runs.

### 5.3 Sub-Agent Bypassing in the Starter Kit
In `flat_starter`, root wraps `code_analyzer` as an `AgentTool`. Across 32 traces:
- Out of 336 tool calls, the model delegated only **7 times (2.1%)**.
- The model **bypassed delegation on 26 of 32 tasks (81.2%)**, reading files directly into root context (6/32 delegated).

![Figure 3: Sub-Agent Delegation Funnel](https://raw.githubusercontent.com/KarandeepSinghSodhi/gemma-sfd-agent/v1.0.1-camera-ready/figures/fig3_delegation_funnel.png)
*Figure 3: Sub-agent delegation in `flat_starter`: 81.2% bypassed delegation; 2.1% calls delegated.*

### 5.4 Cross-Stage Prompt Resets
In `sfd`, `include_contents: "none"` resets entry prompts from a mean TriageAgent peak of 10,473.9 tokens (n = 32 primary runs, median 9,863.0; vs 10,922.1 for n = 16 in SFD) to 1,536.9 tokens at PatchAgent entry. Across 32 primary runs, the mean of per-run percentage resets was 81.95% (median 87.43%, IQR [75.72%, 89.46%]); the ratio of aggregate means corresponds to an 85.3% reduction (a different summary statistic). This drives the 32.0% prompt reduction over flat baselines (p < 0.0001).

![Figure 2: Prompt Token Expansion & Stage Resets](https://raw.githubusercontent.com/KarandeepSinghSodhi/gemma-sfd-agent/v1.0.1-camera-ready/figures/fig2_prompt_resets.png)
*Figure 2: Prompt trajectories across steps t (mean with 95% bootstrap bands). Flat runs expand monotonically; SFD resets prompt tokens by 87.43% median.*

---

## 6. Candidate Remediations (Untested Unless Stated)

Diagnostic classifications suggest actionable engineering patterns:

| Failure Mode | Prevalence | Candidate Remediation Pattern |
| :--- | :---: | :--- |
| **Collection Crash** | 36/112 (32.1%) | Enforce `PYTHONPATH` priority; pre-flight dependency checks. |
| **Edit Failures** | 100 errors (64 NotFound, 36 Malformed) | Validate edit targets against buffer; handle errors explicitly. |
| **Syntax Corruption** | 13/112 (11.6%) | Mandate `py_compile` gate before `submit_patch` with self-repair. |
| **Wrong-File Localization** | 15/112 (13.4% overall) | Two-way symbol verification loop (untested) prior to edit. |
| **Unbounded Context** | 64/64 flat runs (100% monotonic) | Stage context pruning (`include_contents: "none"`), resetting context 81.95% mean (reduces tokens; no resolution gain). |

### 6.1 Post-Hoc Diagnostic Evaluation (Non-Official Harness)
Offline diagnostic checks (`analysis/remediation_eval.py`) do not alter official benchmarks:
1. **Pre-Submission `py_compile` Gate**: Catches 100% (13/13) of syntax-corrupted patches before `submit_patch` by construction; recovery without repair turns was 0/13.
2. **`PYTHONPATH` Priority**: Prepending source paths (`PYTHONPATH=/workspace/src:/workspace`) is predicted to avoid collection crashes across all 10 path-shadowed runs (`httpx_3672`, `fastapi_15661`); evaluation requires container execution (no speculative gains claimed).

---

## 7. The `atif_gemma` Python Package & CLI

We release the standalone Python package `atif-gemma`:
```bash
pip install git+https://github.com/KarandeepSinghSodhi/gemma-sfd-agent.git@v1.0.1-camera-ready
```
Modules provide trajectory auditing (`audit`), deterministic exit-code and localization classification (`taxonomy`), and remediations (`remediation`). CLI: `python -m atif_gemma.cli audit traces/` and `python -m atif_gemma.cli playbook`.

---

## 8. Limitations & Threats to Validity

1. **Task Sample (n = 32)**: Covers ~25% of the benchmark split (evaluating all 129 tasks across 3 configurations requires ~13 hours on 4x L4, or ~52 GPU-hours, exceeding remaining quota).
2. **Model & Quantization**: Specific to `gemma-4-e4b-it-qat-w4a16-ct` (INT4); larger models may differ.
3. **Repository Scope**: Evaluates 4 Python repos; runs sharing tasks are paired and clustered.
4. **Non-Determinism**: Under temperature T = 0.0, 12/16 exit codes matched on rerun; edit hashes diverged (mean drift: 18,571 tokens).
5. **Structural Proxy**: File overlap (F_agent ∩ F_gold) is a proxy; alternative valid patches exist.
6. **Sandbox Sensitivity (`env_suspected=True`)**: 20 runs exhibited collection failures consistent with container constraints (missing wheels, path shadowing); confirmation requires offline container controls (future work).

---

## 9. Conclusion & Resource Availability

ATIF-Gemma shows raw resolution rates mask critical execution bottlenecks (50.0% assertion failures, 32.1% collection crashes). All 112 traces, metadata, and tools are open-sourced:
- **GitHub Repository**: [gemma-sfd-agent, tag `v1.0.1-camera-ready`](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent/tree/v1.0.1-camera-ready)
- **Kaggle Dataset**: [ATIF-Gemma: Diagnostic Traces for SWE Agents](https://www.kaggle.com/datasets/karandeepsinghsodhi/atif-gemma-swe-agent-traces)
- **Kaggle Notebook**: [ATIF-Gemma: Diagnostic Exploration](https://www.kaggle.com/code/karandeepsinghsodhi/atif-gemma-diagnostic-exploration)
- **Manuscript PDF**: [paper_resource.pdf](https://raw.githubusercontent.com/KarandeepSinghSodhi/gemma-sfd-agent/v1.0.1-camera-ready/paper_resource.pdf)

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
- Sodhi, K. S. (2026). State-Filtered Deliberation: Stage-Isolated Context Management for Small Open-Weight Software Engineering Agents. *Kaggle Gemma 4 Developer Agent Paper Competition*. [Companion Paper](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent/blob/v1.0.1-camera-ready/KAGGLE_WRITEUP.md).
- Wang, X., et al. (2024). OpenHands: An Open Platform for AI Software Developers as Generalist Agents. [*arXiv:2407.16741*](https://arxiv.org/abs/2407.16741)
- Xia, C. S., et al. (2024). Agentless: Demystifying LLM-based Software Engineering Agents. [*arXiv:2407.01489*](https://arxiv.org/abs/2407.01489)
- Yang, J., et al. (2024). SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering. *NeurIPS 2024*. [*arXiv:2405.15793*](https://arxiv.org/abs/2405.15793)
- Yang, J., et al. (2025). SWE-smith: Scaling Data for Software Engineering Agents. [*arXiv:2504.21798*](https://arxiv.org/abs/2504.21798)
