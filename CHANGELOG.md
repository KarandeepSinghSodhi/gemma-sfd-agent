# CHANGELOG.md

Log of every quantitative and claim change made in the pursuit of absolute empirical rigor.
Format:
- Timestamp
- Task ID
- What Changed
- Evidence File
- Numbers Before / After

---

## [Init] 2026-10-27 18:40 UTC
- Task: Initialized rigorous review protocol under `/goal`.
- Scope: Transitioning ATIF-Gemma from promotional tone to hostile-reviewer-grade academic rigor.

---

## [T0 Complete] 2026-10-27 18:45 UTC
- **Task ID**: T0
- **What Changed**: Tables 1-3 reproduced directly from 112 raw ATIF trace JSON files with `analysis/reproduce_tables.py`. Total tool calls updated from 1,182 (pre-filtered progress log count) to 1,328 (exact step-level invocations in ATIF traces). Explicit mathematical definition of "Mean Peak $P_t$" added to paper and writeup.
- **Evidence Files**: `analysis/reproduce_tables.py`, `results/table1_corpus.csv`, `results/table2_taxonomy.csv`, `results/table3_configs.csv`, `results/summary_metrics.json`.
- **Numbers Before / After**:
  - Total Tool Invocations: 1,182 -> 1,328
  - Cohort Tool Calls: [236, 269, 155, 270, 252] -> [265, 298, 172, 309, 284]
  - Definition Added: $\text{Mean Peak } P_t \equiv \frac{1}{N}\sum_{i=1}^N \max_t P_{i,t}$

---

## [T1 Complete] 2026-10-27 18:50 UTC
- **Task ID**: T1
- **What Changed**: All 36 Exit Code 2 (pytest collection crash) runs deterministically classified into 4 mechanisms:
  1. Syntactic & Indentation Corruption: 13 runs (36.1%) across 7 tasks
  2. Virtual Environment & Path Shadowing: 10 runs (27.8%) across 2 tasks (`httpx_3672`, `fastapi_15661`)
  3. Missing Sandbox Dependencies: 10 runs (27.8%) across 4 tasks (`fastapi_14361`, `fastapi_14371`, `fastapi_14455`, `fastapi_14459`)
  4. Missing New Source Module: 3 runs (8.3%) on `rich_3930`
  Zero unclassified runs remaining.
- **Evidence Files**: `analysis/classify_exit2.py`, `results/exit2_breakdown.json`, `results/exit2_breakdown.csv`.
- **Numbers Before / After**:
  - Unclassified Exit Code 2 runs: 36 -> 0 (100% deterministically classified)
  - Tasks broken down by exact failure cause.

---

## [T2 Status: BLOCKED] 2026-10-27 18:55 UTC
- **Task ID**: T2 (Gold-Patch Control)
- **Status**: BLOCKED per Rule 2 (No simulation, local environment is Windows without `swegemma`, repo snapshots, or Linux offline wheelhouse).
- **Action Taken**: Authored `analysis/gold_patch_control.py` to run in the Kaggle environment. Explicitly documented that oracle ceiling remains uncomputed until executed on Kaggle Linux sandbox. Zero numbers simulated.
- **Evidence File**: `analysis/gold_patch_control.py`.

---

## [T3 Complete] 2026-10-27 19:00 UTC
- **Task ID**: T3
- **What Changed**: Deterministically classified all 56 Exit Code 1 runs (50.0% of corpus) into four structural categories by comparing agent edited files against author ground-truth diffs:
  1. Right-File, Wrong-Logic: 24 runs (42.9%)
  2. Wrong-File Localization: 17 runs (30.4%)
  3. Partial Multi-File Localization: 14 runs (25.0%)
  4. Empty or Unparsed Patch: 1 run (1.8%)
  Added Section 3.2 to paper and writeup; zero manual or LLM judgment labels used.
- **Evidence Files**: `analysis/subclassify_exit1.py`, `results/exit1_breakdown.json`, `results/exit1_breakdown.csv`.
- **Numbers Before / After**: Exit Code 1 unquantified -> 100% deterministically classified.

---

## [T4 Complete] 2026-10-27 19:10 UTC
- **Task ID**: T4
- **What Changed**: Added full inferential statistics:
  - 95% Wilson score CIs for resolution proportions: 2/32 (6.25%) [1.73%, 20.15%] across all 3 architectures.
  - McNemar's exact two-sided test ($p = 1.0000$) plainly stated: zero resolution rate advantage on E4B.
  - Paired bootstrap 95% CIs and Wilcoxon signed-rank tests for prompt tokens: SFD vs controlled (-32.0%, 95% CI `[-52,214.6, -23,755.2]`, $p < 0.0001$, lower on 25/32 tasks).
  - Duration differences (-4.2s / -7.7s) plainly reported as not statistically significant (Wilcoxon $p = 0.454$ and $p = 0.443$).
  - Rerun determinism audited across 16 paired runs: 87.5% exact patch hash agreement, 75.0% exit code agreement.
- **Evidence Files**: `analysis/statistical_tests.py`, `results/stats_report.json`, `results/rerun_determinism.json`.
- **Numbers Before / After**: Added formal CIs, p-values, and determinism rates; removed unsupported claims of resolution superiority.

---

## [T5 Complete] 2026-10-27 19:25 UTC
- **Task ID**: T5
- **What Changed**: Empirical claim audit completed across all 112 traces and paper text updated:
  1. "cross-references every step against ground-truth patches" softened to "cross-references final agent patches and localized file targets against author ground-truth patches and held-out test suites".
  2. "~15% cascading localization" replaced by "17/112 runs (15.2% overall; 30.4% of Exit 1)" and labeled as wrong-file localization.
  3. "100 FileEditErrors" audited across all 1,328 tool calls: mean 0.89/run, affecting 37.5% of runs (64 StringNotFound, 36 Malformed/Syntax corruption).
  4. "100% of flat agents" prompt bloat replaced by "32/32 flat runs (100% exhibit monotonic prompt accumulation; SFD lowers peak on 28/32 tasks [87.5%])".
  5. SFD "50% fewer tool calls / 35% faster" example on `fastapi_14077` labeled as an $n=1$ illustrative anecdote, noting that overall duration differences across the 32 tasks are not statistically significant ($p = 0.4540$).
  6. "-86.3% reset" replaced by empirical distribution across all 32 primary SFD runs: median reset 87.43%, mean 81.95%, IQR [75.72%, 89.46%], range [44.95%, 92.49%], dropping from mean triage peak of 10,473.9 tokens to 1,536.9 tokens at PatchAgent entry.
  7. Updated `README.md` to reflect complete 32-task (112-run) corpus instead of old 16-task cohort.
- **Evidence Files**: `analysis/claim_audit.py`, `results/tool_errors_breakdown.json`, `results/stage_resets_distribution.json`.
- **Numbers Before / After**:
  - Single "-86.3%" mean -> Empirical distribution: Mean 81.95%, Median 87.43%, IQR [75.72%, 89.46%], Range [44.95%, 92.49%]
  - "100 FileEditErrors" loose claim -> Exactly 100 FileEditErrors (64 StringNotFound, 36 Malformed/Syntax) across 1,328 calls
  - README cohort: 16 tasks (64 runs) -> 32 tasks (112 runs) reconciled.

---

## [T6 Complete] 2026-10-27 19:35 UTC
- **Task ID**: T6
- **What Changed**: Authored `analysis/figures.py` to generate publication-grade vector graphics (SVG, PDF, PNG) using an Okabe-Ito colorblind-safe palette:
  1. `figures/fig1_exit_codes`: Stacked horizontal bar chart showing Phase 2 exit-code distributions overall and by configuration.
  2. `figures/fig2_prompt_resets`: Turn-step prompt token expansion curves with 95% bootstrap confidence bands comparing monotonic flat accumulation against SFD stage-boundary context pruning (~82% reset).
  3. `figures/fig3_delegation_funnel`: Two-panel diagnostic graphic displaying the tool invocation funnel (336 -> 304 -> 7) and 90.6% discretionary bypass rate.
  Embedded figures into `paper_resource.typ` and `KAGGLE_WRITEUP_RESOURCE.md`. Recompiled `paper_resource.pdf` (9 pages, 0 errors).
- **Evidence Files**: `analysis/figures.py`, `figures/fig1_exit_codes.*`, `figures/fig2_prompt_resets.*`, `figures/fig3_delegation_funnel.*`.
- **Numbers Before / After**: 0 figures in resource paper -> 3 publication vector figures embedded.

---

## [T7 Complete] 2026-10-27 19:45 UTC
- **Task ID**: T7
- **What Changed**: Post-hoc remediation re-evaluation executed on stored patches via `analysis/remediation_eval.py` and saved to `results/remediation_eval.json`:
  1. Automated `py_compile` gate tested against all 13 Exit Code 2 syntax-corrupted runs: baseline agents had 0% pre-submission verification. The gate intercepts 100% (13/13) of syntax/indentation corruptions prior to submission. Honestly reported: intercepting malformed patches halts collection crashes (Exit Code 2), but does not resolve the task without additional agent self-repair turns (resolution remains 0/13).
  2. `PYTHONPATH` priority remediation audited across all 10 environment-shadowed runs (`httpx_3672`, `fastapi_15661`): prepending `/workspace/src` and `/workspace/scripts` removes package shadowing. Semantic test execution requires full Linux `swegemma` sandbox, so zero synthetic resolution gains are claimed.
  3. Added Section 5.1 ("Post-Hoc Diagnostic Re-Evaluation (Non-Official Harness)") in `paper_resource.typ` and `KAGGLE_WRITEUP_RESOURCE.md`, keeping official competition benchmark tables (Tables 1-3) strictly separate and untouched.
- **Evidence Files**: `analysis/remediation_eval.py`, `results/remediation_eval.json`, `paper_resource.typ` Sec 5.1.
- **Numbers Before / After**: 0/13 pre-submission checks -> 13/13 intercepted; 0 speculative resolution gains claimed.

---

## [T8 Complete] 2026-10-27 19:55 UTC
- **Task ID**: T8
- **What Changed**: Added formal Section 2 ("Related Work: Trajectory Corpora & Agent Diagnostics") to `paper_resource.typ` and `KAGGLE_WRITEUP_RESOURCE.md`:
  1. Contextualized ATIF-Gemma within prior trajectory corpora (SWE-bench @jimenez2024swebench, SWE-agent @yang2024sweagent, OpenHands @wang2024openhands, ATIF v1.7 schema).
  2. Analyzed prior failure and context studies: Agentless (@xia2024agentless) and observation masking (@lindenbauer2025complexity).
  3. Scoped "first" claims strictly: "To our knowledge, ATIF-Gemma is the first open empirical trajectory corpus specifically documenting small, 4-bit quantized open-weight agents (`gemma-4-e4b-it-qat-w4a16-ct`) operating within the official Google ADK and `swegemma` execution harness."
  4. Marked uncertain references with `[CITATION NEEDED]`.
  5. Re-indexed subsequent sections from 3 through 9; recompiled `paper_resource.pdf` (11 pages, 0 errors).
- **Evidence Files**: `paper_resource.typ` Sec 2, `KAGGLE_WRITEUP_RESOURCE.md` Sec 2, `references_gemma.bib`.
- **Numbers Before / After**: 0 related work section -> 3 subsections added; all claims scoped to defensible limits.

---

## [T9 Complete] 2026-10-27 20:10 UTC
- **Task ID**: T9
- **What Changed**: Dataset hygiene, packaging, attribution, and testing completed:
  1. Authored `dataset_resource/datasheet.md` adhering to the Gebru et al. (2021) standard.
  2. Added formal SWE-bench attribution and CC-BY-4.0 licensing across dataset metadata and documentation.
  3. Added official `dataset_resource/atif_schema_v1_7.json` JSON Schema.
  4. Computed cryptographic hashes in `dataset_resource/checksums.sha256` for all 118 files via `analysis/generate_checksums.py`.
  5. Resolved setuptools flat-layout package discovery error in `pyproject.toml` by declaring explicit `atif_gemma*` package boundaries and SPDX license expression.
  6. Successfully tested `pip install -e .` and verified CLI tools (`python -m atif_gemma.cli audit`, `python -m atif_gemma.cli playbook`).
  7. Authored unit test suite in `tests/test_taxonomy.py` covering exit-code classification, bucket assignment, playbook retrieval, single-trace parsing, and full corpus reconciliation. Passed 5/5 unit tests under pytest.
- **Evidence Files**: `dataset_resource/datasheet.md`, `dataset_resource/atif_schema_v1_7.json`, `dataset_resource/checksums.sha256`, `tests/test_taxonomy.py`, `pyproject.toml`.
- **Numbers Before / After**: 0 unit tests -> 5 passing unit tests; flat-layout packaging build fixed.

---

## [T10 Complete] 2026-10-27 20:25 UTC
- **Task ID**: T10
- **What Changed**: Documentation hygiene, cross-doc consistency, and limitations rewrite:
  1. Replaced broken local `file:///` link in `KAGGLE_WRITEUP_RESOURCE.md` with official hosted GitHub links.
  2. Reconciled numbers across typ/writeup/README: 112 traces, 32 tasks, 1,518 LLM turns, 1,328 tool calls, 11,706,178 tokens. All 7 consistency assertions verified via `scripts/check_consistency_resource.py`.
  3. Thoroughly rewrote Section 8 ("Limitations & Threats to Validity") detailing 6 structural caveats: $n=32$ task sample size, single INT4 quantized model, 4 Python repositories, greedy decoding ($T=0.0$), exit-code-level granularity, and competition sandbox specifics.
  4. Rebuilt `paper_resource.pdf` (11 pages, 0 errors).
- **Evidence Files**: `KAGGLE_WRITEUP_RESOURCE.md`, `paper_resource.typ`, `paper_resource.pdf`.
- **Numbers Before / After**: 3-sentence limitations paragraph -> 6 detailed structural limitations; 0 local links remaining.
---

## [T11 Complete] 2026-10-27 23:20 UTC
- **Task ID**: T11 (Hostile-Reviewer Feedback Remediation & Camera-Ready Submission Polish)
- **What Changed**:
  1. **Audit Trail & README Discrepancy**: Clarified relationship between 64-trace SFD ablation ($n=16$ tasks) and 112-trace ATIF-Gemma diagnostic corpus ($n=32$ unique tasks across 5 cohorts) in `README.md` with direct links to manifests and scripts.
  2. **ATIF v1.7 Schema Conformance**: Standardized schema definition in `dataset_resource/atif_schema_v1_7.json`; verified 112/112 traces (100.0%) pass formal Draft-07 `jsonschema` validation (`results/schema_validation_report.json`). Accurately documented trace structure (`message` contains thinking text under `extra.event_type: "thinking"`, `final_metrics` captures cumulative tokens and steps).
  3. **Related Work & References**: Removed all `[CITATION NEEDED]` placeholders. Added complete references to `references_gemma.bib` (`chen2021codex`, `austin2021mbpp`, `atif2024schema`, `holbrook2026leaderboard`, `gebru2021datasheets`). Adopted defensible novelty phrasing.
  4. **Kaggle Word Limit Compliance**: Trimmed `KAGGLE_WRITEUP_RESOURCE.md` from 3,588 prose words / 4,068 raw words down to 2,828 cleaned prose words (strictly compliant with Kaggle's <3,000 word limit, verified by `analysis/count_words.py`).
  5. **Taxonomy Precedence & Decision Tree**: Reframed terminology to "four principal failure mechanisms and resolution as a separate outcome". Formalized a mutually exclusive decision tree for Exit Code 1 (empty patch -> wrong file -> partial multi-file -> right file wrong logic).
  6. **Agent vs. Environment Failure Attribution**: Partitioned Exit Code 2 into Agent-Attributable (16/36 = 44.4%: 13 syntax corruption, 3 missing module) vs. Environment-Attributable (20/36 = 55.6%: 10 venv shadowing, 10 missing wheels), highlighting the dual diagnostic role of execution traces.
  7. **Package Installation Verified**: Documented exact, reproducible install command (`pip install git+https://github.com/KarandeepSinghSodhi/gemma-sfd-agent.git` and `pip install -e .`).
  8. **Editorial Polish & PDF Build**: Renamed "Camera-Ready Paper" to "Manuscript PDF"; adopted structured abstract; noted that 40 cohort entries span 32 unique benchmark tasks. Recompiled `paper_resource.pdf` (0 errors).
- **Evidence Files**: `KAGGLE_WRITEUP_RESOURCE.md`, `paper_resource.typ`, `paper_resource.pdf`, `README.md`, `dataset_resource/atif_schema_v1_7.json`, `references_gemma.bib`, `results/schema_validation_report.json`.
- **Numbers Before / After**:
  - Prose word count: 3,588 words -> 2,828 words (compliant with <3,000 word limit)
  - Missing citations: 2 `[CITATION NEEDED]` -> 0 placeholders; 5 new complete references
  - Schema validation: unvalidated claim -> 112/112 (100.0%) verified passing
  - Exit 2 classification: monolithic collection crash -> 44.4% agent-attributable / 55.6% environment-attributable
  - Exit 1 classification: overlapping definitions -> strict mutually exclusive decision tree (1 empty, 17 wrong file, 14 partial multi-file, 24 right file wrong logic).


---

## [T13 Complete] 2026-10-28 00:15 UTC
- **Task ID**: T13 (Final Camera-Ready Submission Polish & Public Artifact Sync)
- **What Changed**:
  1. **Public Repository & 48 Extra Traces Clarity**: Updated README.md to explicitly document all 5 shards/cohorts in traces/ (eval_results, shard2_results, rerun_results, shard3_results, shard4_results), detailing how Artifact 1 evaluates 64 runs on 16 tasks and Artifact 2 expands this with Cohorts 3 and 4 (+48 runs) to establish the complete 112-trace corpus across 32 unique tasks unified in dataset_resource/traces/ and corpus_metadata.csv. Updated scripts/render_paper.py to prevent clobbering the dual-artifact README.md.
  2. **Novelty Claim & Related Datasets**: Acknowledged recent public trajectory datasets, specifically citing Raja Rajak (2026) (@rajak2026tfd) 50 multi-turn Gemma SWE-bench trajectories on Kaggle in both paper_resource.typ and KAGGLE_WRITEUP_RESOURCE.md. Replaced unqualified claims with scoped language articulating ATIF-Gemma unique additions (paired architecture control across 112 runs, 4-way failure taxonomy, agent vs environment attribution, mutually exclusive localization tree, and open diagnostic tooling).
  3. **Abstract Correction**: Corrected abstract terminology in both paper_resource.typ and KAGGLE_WRITEUP_RESOURCE.md: from agent-attributable syntax errors (44.4%) to agent-attributable collection failures (44.4%) versus environment/dependency failures (55.6%) (reflecting 13 syntax errors [36.1%] and 3 missing module errors [8.3%]).
  4. **References Section**: Added formatted Section 10 References to KAGGLE_WRITEUP_RESOURCE.md. Added @misc{rajak2026tfd} to references_gemma.bib and cited in paper_resource.typ.
  5. **Dual ATIF v1.7 Schema Validation**: Authored dual-mode schema validator in analysis/validate_atif_schema.py verifying both concrete repository schema (atif_schema_v1_7.json) and upstream ATIF v1.7 specification mapping (message with extra.event_type: thinking mapped to reasoning_content), achieving 100.0% pass rate (112/112 traces, 1,942 audited steps, 1,503 deliberative turns). Output saved to results/schema_validation_report.json.
  6. **Word Limit Safety Margin**: Trimmed KAGGLE_WRITEUP_RESOURCE.md to 2,812 cleaned prose words (under Kaggle 3,000 word limit with an 188-word safety margin, including the new Section 10 References). In Section 1, separated syntax degradation from context accumulation/dynamics to avoid asserting unproven causal links.
  7. **Compilation & Consistency Verification**: Recompiled paper_resource.pdf via Typst (0 errors). Verified all 7 automated consistency checks pass via scripts/check_consistency_resource.py and 5/5 unit tests pass via tests/test_taxonomy.py.
- **Evidence Files**: KAGGLE_WRITEUP_RESOURCE.md, paper_resource.typ, paper_resource.pdf, README.md, references_gemma.bib, analysis/validate_atif_schema.py, results/schema_validation_report.json, analysis/count_words.py.
- **Numbers Before / After**:
  - Cleaned prose word count: 2,970 words -> 2,812 words (188-word safety margin under 3,000-word limit)
  - References: 0 in writeup -> 12 verified entries in Section 10; rajak2026tfd added to BibTeX
  - Dual Schema Validation: 100.0% (112/112 concrete repository, 112/112 upstream interoperability)
  - Abstract Exit 2 partition: syntax errors (44.4%) -> collection failures (44.4%)
  - README trace shards: 3 shards (64 runs) -> 5 shards (112 runs) fully documented.


---

## [T14 Complete] 2026-10-28 01:05 UTC
- **Task ID**: T14 (Harbor ATIF v1.7 Specification Conformance, Bibliographic Correction, & Strict Word-Count Ceiling)
- **What Changed**:
  1. **Substantiated ATIF Validation & Path Portability**: Removed custom in-script UPSTREAM_ATIF_SCHEMA from analysis/validate_atif_schema.py; reframed claim from dual schema validation to formal validation under the Harbor ATIF v1.7 specification (112/112 traces, 100.0% pass rate). Replaced all hardcoded Windows drive letters across all 15 analysis and scripts Python files with portable project-relative paths (Path(__file__).resolve().parents[1]).
  2. **Bibliographic Correction**: Corrected ATIF v1.7 citation in references_gemma.bib, paper_resource.typ, and KAGGLE_WRITEUP_RESOURCE.md from SWE-bench Working Group (2024) to Harbor Framework Contributors (2026), citing the Harbor repository (https://github.com/harbor-framework/harbor).
  3. **Strict Word Count Margin**: Trimmed KAGGLE_WRITEUP_RESOURCE.md so that raw whitespace count across the entire file (including markdown tables, code fences, and bibliography) is strictly 2,946 words (< 3,000 words), with cleaned whitespace at 2,381 words and prose tokens at 2,710 words.
  4. **Resolved Text Ambiguities**:
     - Abstract: replaced a lack of public trace data with limited public trace data linking compact-agent execution trajectories to test outcomes and failure diagnoses.
     - Section 6.1: changed site-package shadowing across all 10 environment-shadowed runs to environment and import-path failures across all 10 runs.
  5. **Checksum Synchronization**: Recomputed dataset_resource/checksums.sha256 for all 118 files via analysis/generate_checksums.py.
  6. **Recompilation & Verification**: Recompiled paper_resource.pdf with Typst (0 errors); all 7 consistency checks and 5 unit tests passed.
- **Evidence Files**: analysis/validate_atif_schema.py, references_gemma.bib, KAGGLE_WRITEUP_RESOURCE.md, paper_resource.typ, paper_resource.pdf, dataset_resource/datasheet.md, dataset_resource/checksums.sha256, results/schema_validation_report.json.
- **Numbers Before / After**:
  - Raw whitespace word count: 3,055 words -> 2,946 words (< 3,000 max)
  - Cleaned prose tokens: 2,812 words -> 2,710 words
  - Hardcoded Windows drive paths: 15 instances -> 0 instances across all scripts
  - ATIF citation: SWE-bench Working Group (2024) -> Harbor Framework Contributors (2026)
  - Schema validation claim: dual schema -> formal Harbor ATIF v1.7 specification validation (100.0% pass).


---

## [T15 Complete] 2026-10-28 01:30 UTC
- **Task ID**: T15 (Comprehensive Reviewer Harmonization, Invalid Environment Isolation, Rerun Edit Determinism, & Cross-Paper Reconciliations)
- **What Changed**:
  1. **Invalid Environment Flagging (`env_invalid=True`)**: Added `env_invalid` boolean column to `dataset_resource/corpus_metadata.csv` flagging 20/112 runs where Phase 2 failed due to offline container constraints (10 venv/import-path shadowing, 10 missing wheels like `inline_snapshot`/`dirty_equals`). Recomputed SHA-256 checksums across all 118 dataset files.
  2. **Primary (n=96) vs Valid (n=80/92) vs Pooled (n=112) Resolution Rates**:
     - Primary 96: 6/96 (6.25%, 95% Wilson CI [2.90%, 12.97%]; 2/32 = 6.25% across all 3 configs).
     - Valid Primary 80: 6/80 (7.50%, 95% Wilson CI [3.48%, 15.41%]).
     - Valid Pooled 92: 8/92 (8.70%, 95% Wilson CI [4.47%, 16.23%]).
     - Pooled 112: 8/112 (7.14%, 95% Wilson CI [3.66%, 13.46%]).
  3. **Task-Level Aggregation & Clustering**: 4 of 32 unique tasks resolved at least once (`rich_4077`, `fastapi_9753`, `fastapi_14077`, `rich_3894`), 0/32 resolved across all 3 configs. Acknowledged runs are paired/clustered across tasks.
  4. **True Rerun Edit Sequence Determinism**: Fixed `submit_patch` hash bug by hashing actual workspace modifications (`edit_file`/`write_file`). Confirmed 0/16 edits were byte-for-byte identical due to token-level sampling variance under vLLM, while 12/16 (75.0%) exit codes matched. Documented the 4 exact exit-code flips and the 18,571 mean token drift (~19%).
  5. **Starter Kit Delegation Numbers Corrected**: Across all 32 tasks, 6/32 tasks invoked `code_analyzer` (26/32 bypassed, 81.25%), making 7 total root delegation calls (2.1% of 336 tool invocations). Updated Fig 3 and text.
  6. **Softened Candidate Remediations**: Retitled Section 6 to "Candidate Remediations (Untested Unless Stated)"; noted circularity of `py_compile` check; noted `PYTHONPATH` priority is structurally predicted to avoid shadowing; replaced "memory leak" with "unbounded context growth".
  7. **Cross-Paper Reconciliation (Paper 1 & Paper 2)**: Reconciled Table 6 in `paper.typ` and `KAGGLE_WRITEUP.md` to classify collection errors (agent vs environment) and clarified `rich_3043` 0-byte submitted diff due to 4 consecutive `FileEditError` exceptions. Added reference to expanded 32-task corpus.
  8. **Word Count Ceiling Maintained**: `KAGGLE_WRITEUP_RESOURCE.md` raw whitespace word count is strictly **2,977 words** (< 3,000 max), with cleaned prose at **2,844 words**.
  9. **Compilation & Consistency Verification**: Both `paper_resource.pdf` and `paper.pdf` recompiled cleanly (0 errors). All 7 consistency checks for Paper 2 and all checks for Paper 1 passed. 5/5 pytest unit tests passed.
- **Evidence Files**: `dataset_resource/corpus_metadata.csv`, `dataset_resource/checksums.sha256`, `dataset_resource/datasheet.md`, `analysis/statistical_tests.py`, `analysis/figures.py`, `figures/fig*.{svg,pdf,png}`, `results/stats_report.json`, `results/rerun_determinism.json`, `KAGGLE_WRITEUP_RESOURCE.md`, `paper_resource.typ`, `paper_resource.pdf`, `paper.typ`, `paper.pdf`, `KAGGLE_WRITEUP.md`, `references_gemma.bib`.
- **Numbers Before / After**:
  - Primary resolution rate: 6/96 (6.25%, 95% Wilson CI [2.90%, 12.97%])
  - Valid-environment primary resolution: 6/80 (7.50%, 95% CI [3.48%, 15.41%])
  - Valid-environment pooled resolution: 8/92 (8.70%, 95% CI [4.47%, 16.23%])
  - Rerun edit identity: 14/16 (artifact of empty hash) -> 0/16 byte-identical (true workspace edit sequence hashing)
  - Exit code consistency: 12/16 (75.0%) with 4 documented flips
  - Mean absolute token drift on rerun: 18,571 tokens (~19% of typical run total)
  - Starter kit delegation: 3/32 tasks -> 6/32 tasks (18.8% invoking, 81.2% bypassing; 7 calls / 336 tool calls)
  - Markdown raw whitespace word count: 2,977 words (< 3,000 max)
  - Cleaned prose tokens: 2,844 words (< 3,000 max)
