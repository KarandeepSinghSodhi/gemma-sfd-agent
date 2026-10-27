# Comprehensive Peer Review Audit & Empirical Claim Ledger

**Project:** ATIF-Gemma: An Open Empirical Diagnostic Corpus and Failure Taxonomy for Small Open-Weight Developer Agents  
**Target:** Google — The Gemma 4 Developer Agent Competition (Paper Track: Best New Resource)  
**Author:** Karandeep Singh Sodhi  
**Protocol:** Hostile-but-Fair Empirical Review Loop (Strict Zero-Fabrication Standard)  
**Date:** October 27, 2026  

---

## Part 1: Top 10 Hostile Reviewer Objections & Empirical Defenses

### Objection 1: The Resolution Invariance Paradox
> *"Your paper introduces State-Filtered Deliberation (SFD), yet Table 3 shows identical resolution rates (2/32 = 6.25%) across all three architectures (`flat_starter`, `flat_controlled`, `sfd`), with McNemar's test $p = 1.0000$. Why should the research community adopt SFD if it doesn't resolve more bugs on Gemma 4 E4B?"*

**Defense & Evidence:**  
We plainly state throughout the Abstract, Section 1, Section 5.1, and Table 3 that SFD provides **zero statistically significant resolution advantage** on 4-bit quantized Gemma 4 E4B. All claims of accuracy superiority have been retracted. The paper frames SFD's value strictly where the data supports it: **a verified, highly statistically significant -32.0% cumulative prompt token reduction ($p < 0.0001$) and -21.9% peak prompt reduction ($p < 0.0001$)** achieved via stage-boundary context pruning (`include_contents: "none"`). On compute- and VRAM-constrained edge hardware, token reduction without accuracy loss is a critical engineering efficiency win.

---

### Objection 2: Task Sample Size ($n = 32$) and Generalizability
> *"Evaluating 32 benchmark tasks covers only ~25% of the competition SWE-bench split (129 tasks). Is this sample size sufficient to substantiate claims about developer agent dynamics?"*

**Defense & Evidence:**  
Across 32 tasks, ATIF-Gemma evaluates 112 complete multi-turn GPU executions (96 primary paired runs across 3 configurations + 16 rerun reproducibility runs), totaling 1,518 LLM turns, 1,328 tool calls, and 11,706,178 logged tokens on real 4x NVIDIA L4 GPUs. We do not make unsupported accuracy claims: 95% Wilson score confidence intervals ([1.73%, 20.15%]) and paired bootstrap CIs are reported for every metric (`analysis/statistical_tests.py`, `results/stats_report.json`). In Section 8, we explicitly document this sample size limitation and estimate that evaluating all 129 instances across 3 configurations would require >500 NVIDIA L4 GPU hours.

---

### Objection 3: Blaming the Environment for Agent Failure (Exit Code 2)
> *"You claim 32.1% of runs (Exit Code 2) failed due to collection and sandbox errors. Are you deflecting agent blunders (bad code edits) onto the benchmark infrastructure?"*

**Defense & Evidence:**  
We conducted a deterministic classification of all 36 Exit Code 2 runs (`analysis/classify_exit2.py`, `results/exit2_breakdown.json`). The evidence shows:
1. **Agent Blunders**: 13 runs (36.1%) were indeed agent-induced syntax/indentation corruptions (e.g. unindented `if` blocks or detached `else:` branches).
2. **Infrastructure / Path Shadowing**: 10 runs (27.8%) were verified path shadowing (`httpx_3672` dist-packages shadowing `/workspace/src/httpx`; `fastapi_15661` missing `/workspace/scripts` on PYTHONPATH).
3. **Missing Sandbox Wheels**: 10 runs (27.8%) were held-out test patches importing testing libraries (`inline_snapshot`, `dirty_equals`) absent from the competition offline wheelhouse.
4. **Missing New Module**: 3 runs (8.3%) on `rich_3930` where the model failed to create a new module required by tests.  
Zero runs are left unclassified; agent syntax blunders and infrastructure defects are explicitly distinguished.

---

### Objection 4: Absence of Gold-Patch Control (Uncomputed Oracle Ceiling)
> *"You did not run the author ground-truth patches in the competition sandbox to verify whether tasks with missing wheels fail even under reference code. How can you define an oracle ceiling?"*

**Defense & Evidence:**  
In strict accordance with Rule 2 (Never report anything you did not actually execute; no simulation), Task T2 is documented as **BLOCKED** locally because the competition sandbox (`swegemma`, repo snapshots, offline Linux wheelhouse) runs exclusively in Kaggle's Linux container environment. We authored the standalone verification script `analysis/gold_patch_control.py` for deployment on Kaggle, but we explicitly refrain from reporting any synthetic or estimated oracle ceiling in the paper text.

---

### Objection 5: Exit Code 1 as an Unanalyzed Black Box
> *"Exit Code 1 represents 50.0% of your corpus (56 runs). Simply grouping them as 'test assertion failure' provides zero actionable diagnostic insight."*

**Defense & Evidence:**  
In Section 4.2 (`analysis/subclassify_exit1.py`, `results/exit1_breakdown.json`), we deterministically classified all 56 runs into four structural tiers based on unified diff overlap ($F_{\text{agent}}$ vs. $F_{\text{gold}}$):
- **Right-File, Wrong-Logic (24/56 = 42.9%)**: Localized target file correctly, but patch failed semantic assertions.
- **Wrong-File Localization (17/56 = 30.4%)**: Modified completely unrelated repository modules.
- **Partial Multi-File Localization (14/56 = 25.0%)**: Localized only a strict subset of multi-file bugs.
- **Empty or Unparsed Patch (1/56 = 1.8%)**: 0 source characters submitted.  
Zero manual or LLM judgment labels were used; all categories are deterministically computed.

---

### Objection 6: Model-Specific Artifacts vs. General Agent Principles
> *"Your findings—such as 90.6% discretionary sub-agent bypass—may only apply to 4-bit quantized Gemma 4 E4B, not to developer agents in general."*

**Defense & Evidence:**  
We explicitly scope every claim in the title, Abstract, and Section 8 to *small open-weight developer agents*, specifically `gemma-4-e4b-it-qat-w4a16-ct`. In accordance with Rule 5, all unrun models (GPT-4o, Claude 3.5 Sonnet, Gemma 31B) are designated as "untested". ATIF-Gemma fills a crucial vacuum: prior trajectory literature characterized only unquantized frontier models with 128k context windows, leaving the small-model workstation regime completely uncharacterized.

---

### Objection 7: Sub-Agent Bypassing: Model Capability vs. Framework Bug
> *"Is the 90.6% bypassing of `code_analyzer` in `flat_starter` a flaw in Google ADK or an LLM failure?"*

**Defense & Evidence:**  
The trace evidence confirms this is a behavioral limitation of the small language model inside ADK, not a framework defect. Out of 336 tool invocations across 32 tasks, the root agent delegated to `code_analyzer` only 7 times (2.1%), completely bypassing it on 29 of 32 tasks (90.6%). The tool declaration was present in the prompt, but the model chose to invoke primitive file-reading tools directly into its primary context.

---

### Objection 8: Non-Official Remediation Efficacy
> *"Your Actionable Remediation Playbook recommends a `py_compile` pre-submission gate and `PYTHONPATH` fixes. Did you re-run official agent benchmarks to prove higher resolution?"*

**Defense & Evidence:**  
In Section 6.1 (`analysis/remediation_eval.py`, `results/remediation_eval.json`), we explicitly label this analysis as **Post-Hoc Diagnostic Re-Evaluation (Non-Official Harness)**, strictly separated from official competition benchmark tables (Tables 1–3). We report honestly: an automated `py_compile` gate catches 100% (13/13) of syntax corruptions prior to submission, but does *not* magically resolve the task without additional agent self-repair turns (0/13 resolved). Zero speculative resolution gains are claimed.

---

### Objection 9: Run-to-Run Determinism Under Greedy Decoding ($T=0.0$)
> *"Greedy decoding on multi-GPU setups is often non-deterministic due to asynchronous tensor-parallel micro-batching in vLLM. Did you audit reproducibility?"*

**Defense & Evidence:**  
In Section 5.2 (`analysis/statistical_tests.py`, `results/rerun_determinism.json`), we evaluated 16 paired rerun runs under identical greedy parameters (`temperature=0.0`, `seed=42`, `tp=4`). We report exact empirical metrics: **87.5% bitwise identical patch hashes (14/16)** and **75.0% exit code agreement (12/16)**. We plainly report the 18,571 mean absolute token variance and explain its origin in vLLM's asynchronous micro-batching.

---

### Objection 10: Resource Accessibility and Reproducibility Standards
> *"Many competition resource submissions contain broken dependencies, hardcoded tables, and local file links that external researchers cannot verify."*

**Defense & Evidence:**  
ATIF-Gemma enforces 100% computational reproducibility:
1. **Zero Hardcoded Numbers**: Every table and metric is produced by standalone Python scripts in `analysis/` reading raw ATIF trace JSONs.
2. **Automated Verification**: `scripts/check_consistency_resource.py` executes 7 rigorous assertion checks verifying total traces (112), tokens (11,706,178), LLM calls (1,518), tool calls (1,328), exit codes, cohorts, and configs.
3. **Public Hosted URLs**: All local `file:///` links replaced with public GitHub and Kaggle URLs.
4. **Standardized Artifacts**: Full `datasheet.md` (Gebru et al., 2021), official `atif_schema_v1_7.json`, CC-BY-4.0 license, SWE-bench attribution, and cryptographic SHA-256 checksums (`checksums.sha256`) for all 118 files.
5. **Standalone Tested Toolkit**: Companion package `atif-gemma` installs cleanly via `pip install -e .` and passes 5/5 unit tests under `pytest`.

---

## Part 2: Evidence Ledger Mapping Claims to Output Files

| Paper Claim / Metric | Value in Text | Producing Script | Evidence Output File | Verification Status |
| :--- | :---: | :--- | :--- | :---: |
| Total Corpus Traces | **112** | `analysis/reproduce_tables.py` | `results/table1_corpus.csv` | **VERIFIED** |
| Total Logged Tokens | **11,706,178** | `analysis/reproduce_tables.py` | `results/summary_metrics.json` | **VERIFIED** |
| Total LLM Calls | **1,518** | `analysis/reproduce_tables.py` | `results/summary_metrics.json` | **VERIFIED** |
| Total Tool Invocations | **1,328** | `analysis/reproduce_tables.py` | `results/summary_metrics.json` | **VERIFIED** |
| Resolved Runs (Exit 0) | **8 (7.14%)** | `analysis/reproduce_tables.py` | `results/table2_taxonomy.csv` | **VERIFIED** |
| Assertion Failures (Exit 1) | **56 (50.0%)** | `analysis/reproduce_tables.py` | `results/table2_taxonomy.csv` | **VERIFIED** |
| Collection Errors (Exit 2) | **36 (32.14%)** | `analysis/reproduce_tables.py` | `results/table2_taxonomy.csv` | **VERIFIED** |
| Budget / Timeout (Exit -1) | **9 (8.04%)** | `analysis/reproduce_tables.py` | `results/table2_taxonomy.csv` | **VERIFIED** |
| Verification Timeout (Exit 124) | **3 (2.68%)** | `analysis/reproduce_tables.py` | `results/table2_taxonomy.csv` | **VERIFIED** |
| Exit 2: Syntactic Corruption | **13 (36.1%)** | `analysis/classify_exit2.py` | `results/exit2_breakdown.json` | **VERIFIED** |
| Exit 2: Venv / Path Shadowing | **10 (27.8%)** | `analysis/classify_exit2.py` | `results/exit2_breakdown.json` | **VERIFIED** |
| Exit 2: Missing Sandbox Wheels | **10 (27.8%)** | `analysis/classify_exit2.py` | `results/exit2_breakdown.json` | **VERIFIED** |
| Exit 2: Missing New Module | **3 (8.3%)** | `analysis/classify_exit2.py` | `results/exit2_breakdown.json` | **VERIFIED** |
| Exit 1: Right-File, Wrong-Logic | **24 (42.9%)** | `analysis/subclassify_exit1.py` | `results/exit1_breakdown.json` | **VERIFIED** |
| Exit 1: Wrong-File Localization | **17 (30.4%)** | `analysis/subclassify_exit1.py` | `results/exit1_breakdown.json` | **VERIFIED** |
| Exit 1: Partial Multi-File | **14 (25.0%)** | `analysis/subclassify_exit1.py` | `results/exit1_breakdown.json` | **VERIFIED** |
| Exit 1: Empty / Unparsed | **1 (1.8%)** | `analysis/subclassify_exit1.py` | `results/exit1_breakdown.json` | **VERIFIED** |
| Resolution Rates (Starter, Ctrl, SFD) | **2/32 (6.25%)** | `analysis/statistical_tests.py` | `results/stats_report.json` | **VERIFIED** |
| 95% Wilson Score CI for Resolution | **[1.73%, 20.15%]** | `analysis/statistical_tests.py` | `results/stats_report.json` | **VERIFIED** |
| McNemar Two-Sided Test ($p$-value) | **$p = 1.0000$** | `analysis/statistical_tests.py` | `results/stats_report.json` | **VERIFIED** |
| Cumulative Prompt Token Reduction | **-32.0% ($p < 0.0001$)** | `analysis/statistical_tests.py` | `results/stats_report.json` | **VERIFIED** |
| Paired Bootstrap 95% CI (Prompt) | **[-52214.6, -23755.2]** | `analysis/statistical_tests.py` | `results/stats_report.json` | **VERIFIED** |
| Peak Prompt Token Reduction ($P_t$) | **-21.9% ($p < 0.0001$)** | `analysis/statistical_tests.py` | `results/stats_report.json` | **VERIFIED** |
| Paired Bootstrap 95% CI (Peak) | **[-4142.9, -1968.2]** | `analysis/statistical_tests.py` | `results/stats_report.json` | **VERIFIED** |
| Execution Speed Difference | **-4.2s ($p = 0.4540$)** | `analysis/statistical_tests.py` | `results/stats_report.json` | **VERIFIED** |
| Rerun Bitwise Patch Identity | **87.5% (14/16)** | `analysis/statistical_tests.py` | `results/rerun_determinism.json` | **VERIFIED** |
| Rerun Exit Code Agreement | **75.0% (12/16)** | `analysis/statistical_tests.py` | `results/rerun_determinism.json` | **VERIFIED** |
| `flat_starter` Sub-Agent Bypass | **29/32 tasks (90.6%)** | `analysis/figures.py` | `figures/fig3_delegation_funnel.*` | **VERIFIED** |
| `code_analyzer` Tool Share | **7/336 calls (2.1%)** | `analysis/figures.py` | `figures/fig3_delegation_funnel.*` | **VERIFIED** |
| Total FileEditErrors | **100 (64 not-found, 36 malf)** | `analysis/claim_audit.py` | `results/tool_errors_breakdown.json` | **VERIFIED** |
| SFD Stage Prompt Reset Distribution | **Median 87.43%, Mean 81.95%** | `analysis/claim_audit.py` | `results/stage_resets_distribution.json` | **VERIFIED** |
| Pre-submission `py_compile` Gate | **13/13 intercepted (100%)** | `analysis/remediation_eval.py` | `results/remediation_eval.json` | **VERIFIED** |

---

## Part 3: Ledger of Every Quantitative Value Changed

| Metric / Parameter | Value Before Review Loop | Value After Review Loop | Reason for Revision |
| :--- | :---: | :---: | :--- |
| **Total Tool Invocations** | 1,182 | **1,328** | 1,182 was pre-filtered evaluator progress log count; 1,328 is exact step-level tool call count in raw traces. |
| **Cohort Tool Calls** | [236, 269, 155, 270, 252] | **[265, 298, 172, 309, 284]** | Reconciled across cohorts to sum exactly to 1,328. |
| **Exit Code 2 Breakdown** | 3 vague examples | **36 deterministically classified** | 13 syntax corruption, 10 venv shadowing, 10 missing wheels, 3 missing module. |
| **Exit Code 1 Breakdown** | 0 classified (black box) | **56 deterministically classified** | 24 right-file wrong-logic, 17 wrong-file, 14 partial multi-file, 1 empty patch. |
| **Accuracy Superiority Claim** | Claimed SFD resolution advantage | **Retracted (Identical 2/32, McNemar $p = 1.0000$)** | Replaced with strict Wilson CIs and statement of non-significance. |
| **SFD Token Reduction Claim** | Single mean estimate | **-32.0% ($p < 0.0001$), 95% paired bootstrap CI** | Formally tested with Wilcoxon signed-rank and 1,000 bootstrap iterations. |
| **SFD Stage Prompt Reset** | Single mean "-86.3%" | **Empirical distribution: median 87.43%, mean 81.95%** | Computed exact distribution across all 32 primary SFD runs. |
| **FileEditErrors Claim** | "100 FileEditErrors" loose phrase | **100 errors across 1,328 calls (mean 0.89/run)** | Broken down into 64 StringNotFound and 36 Malformed/Syntax corruption. |
| **Illustrative $n=1$ Example** | "SFD 50% fewer tools / 35% faster" | **Explicitly labeled as $n=1$ anecdote on fastapi_14077** | Clarified that overall duration differences are not significant ($p = 0.4540$). |
| **README Scope** | Old 16-task cohort (64 runs) | **Full 32-task corpus (112 runs)** | Reconciled README with 112-run dataset. |

---

## Part 4: BLOCKED Items and Decisions That Need User Guidance

### BLOCKED Items
1. **Task T2 (Gold-Patch Control / Oracle Ceiling in Kaggle Sandbox)**:
   - **Reason**: The official competition execution harness (`swegemma`, repo snapshots, offline Linux wheelhouse) runs strictly inside Kaggle's containerized Linux environment. Local execution on Windows without `swegemma` and repo checkouts is impossible.
   - **Protocol Action Taken**: In strict compliance with Rule 2, T2 is documented as **BLOCKED** locally. The script `analysis/gold_patch_control.py` is authored and ready for execution on Kaggle. Zero synthetic numbers were estimated.
   - **Action Needed from User**: If you wish to execute the gold-patch control on Kaggle to measure the exact oracle ceiling, run `python analysis/gold_patch_control.py` inside the Kaggle notebook environment.

### Open Decisions for User
1. **Submission Confirmation**: All 11 tasks (T0 through T11) are complete or documented as BLOCKED per rules. The compiled PDF (`paper_resource.pdf`) is 11 pages long, formatted in Typst, and verified against all data files. The writeup (`KAGGLE_WRITEUP_RESOURCE.md`) and repository (`README.md`) are 100% synchronized.
