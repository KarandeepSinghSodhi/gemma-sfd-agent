# State-Filtered Deliberation (SFD): Stage-Isolated Context Management for Small Open-Weight Software Engineering Agents

[![Paper](https://img.shields.io/badge/Paper-PDF-red.svg)](paper.pdf)
[![Kaggle Competition](https://img.shields.io/badge/Kaggle-Gemma--4--Developer--Agent-blue.svg)](https://www.kaggle.com/competitions/gemma-4-developer-agent)
[![Kaggle Paper Track](https://img.shields.io/badge/Kaggle-Paper--Track-orange.svg)](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper)
[![Kaggle Kernel](https://img.shields.io/badge/Kaggle-Live_Notebook-20BEFF.svg)](https://www.kaggle.com/code/karandeepsinghsodhi/sfd-state-filtered-deliberation-agent-gemma-4)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)

**Author:** Karandeep Singh Sodhi (`https://github.com/KarandeepSinghSodhi/gemma-sfd-agent`)  
**Track:** Google — The Gemma 4 Developer Agent Challenge (Paper Track & Prediction Track)

---

## Corrections & Scientific Integrity Note
> **Notice:** Earlier drafts of this repository and writeup contained preliminary results produced by an analytical simulation (`simulate_benchmark.py`) and a mock smoke-test script (`smoke_test.py`). Those synthetic files have been retracted and quarantined to `_retracted_simulation/`. Every result reported in this repository is computed strictly from real two-phase `swegemma` + `vLLM` execution traces.

---

## Repository Guide & Audit Trail: Two Distinct Research Artifacts

To assist reviewers in verifying our experiments, this repository maintains an explicit distinction between two connected research artifacts:

### Artifact 1: SFD Architecture Paper (Methods Track)
- **Manuscripts:** [`paper.typ`](paper.typ), [`paper.pdf`](paper.pdf), and [`KAGGLE_WRITEUP.md`](KAGGLE_WRITEUP.md).
- **Scope:** 64 total GPU runs across 16 tasks (Cohort 1 Canonical + Cohort 2 Random: 48 paired primary runs in `traces/eval_results/` and `traces/shard2_results/`, plus 16 rerun reproducibility runs in `traces/rerun_results/`).
- **Core Focus:** Evaluates the declarative 3-stage `SequentialAgent` context management mechanism (`include_contents: "none"`).
- **Raw Traces:** Stored in [`traces/eval_results/`](traces/eval_results/), [`traces/shard2_results/`](traces/shard2_results/), and [`traces/rerun_results/`](traces/rerun_results/).
- **Aggregation Pipeline:** Produced by [`scripts/aggregate.py`](scripts/aggregate.py) into [`results/summary.json`](results/summary.json).

### Artifact 2: ATIF-Gemma Diagnostic Corpus (Best New Resource Track)
- **Manuscripts:** [`paper_resource.typ`](paper_resource.typ), [`paper_resource.pdf`](paper_resource.pdf), and [`KAGGLE_WRITEUP_RESOURCE.md`](KAGGLE_WRITEUP_RESOURCE.md).
- **Scope:** **112 total GPU runs across 32 unique benchmark tasks** spanning 5 cohorts on 4x NVIDIA L4 GPUs (1,518 LLM turns, 1,328 tool calls, 11,706,178 logged tokens). Expands Artifact 1's 64 runs by adding Cohort 3 (24 runs in `traces/shard3_results/`) and Cohort 4 (24 runs in `traces/shard4_results/`) across 16 additional tasks (+48 runs = 112 runs total).
- **Core Focus:** An open empirical diagnostic corpus and Phase 2 exit code failure taxonomy for small open-weight developer agents (`gemma-4-e4b-it-qat-w4a16-ct`), accompanied by an Actionable Remediation Playbook and the `atif_gemma` Python toolkit.
- **Dataset Manifest:** [`dataset_resource/corpus_metadata.csv`](dataset_resource/corpus_metadata.csv) (complete master index of all 112 runs: task ID, repo, config, cohort, exit code, tokens, duration).
- **Raw ATIF v1.7 Traces:** Stored in [`dataset_resource/traces/`](dataset_resource/traces/) (all 112 standardized JSON traces, 100% formally schema-validated against the version-pinned Harbor ATIF v1.7 specification).
- **Documentation & Hygiene:** [`dataset_resource/datasheet.md`](dataset_resource/datasheet.md) (Gebru et al. standard), [`dataset_resource/atif_schema_v1_7.json`](dataset_resource/atif_schema_v1_7.json), and [`dataset_resource/checksums.sha256`](dataset_resource/checksums.sha256).
- **Reproduction Pipeline:** Standalone scripts in [`analysis/`](analysis/) generate all tables, metrics, and vector figures:
  - `analysis/reproduce_tables.py` $\to$ Tables 1–3 (`results/table*.csv`, `results/summary_metrics.json`)
  - `analysis/classify_exit2.py` $\to$ Exit Code 2 breakdown (`results/exit2_breakdown.json`)
  - `analysis/subclassify_exit1.py` $\to$ Exit Code 1 assertion failure taxonomy (`results/exit1_breakdown.json`)
  - `analysis/statistical_tests.py` $\to$ Wilson CIs, bootstrap CIs, Wilcoxon & McNemar tests (`results/stats_report.json`)
  - `analysis/claim_audit.py` $\to$ Tool errors & stage prompt reset distributions (`results/tool_errors_breakdown.json`)
  - `analysis/validate_atif_schema.py` $\to$ Formal ATIF v1.7 schema validation (`results/schema_validation_report.json`)
  - `analysis/figures.py` $\to$ Publication vector graphics (`figures/fig*.svg`)
  - `scripts/check_consistency_resource.py` $\to$ 7/7 automated assertion checks pass.
- **Companion Diagnostic Toolkit:** Installable directly via `pip install git+https://github.com/KarandeepSinghSodhi/gemma-sfd-agent.git`. Unit test suite in [`tests/test_taxonomy.py`](tests/test_taxonomy.py) (5/5 passed).

---

## Overview & Key Empirical Findings (`gemma-4-e4b-it-qat-w4a16-ct`)

Autonomous software engineering (SWE) agents built on small open-weight language models (4-bit quantized Gemma 4 E2B and E4B) face tight context and capability constraints when executing multi-turn debugging trajectories. Across all 197 participating teams on the official Small Model Prize leaderboard (`results/small_model_leaderboard_2026_10_24.csv`, updated 2026-10-24 23:58 UTC), public resolution rates range from `0.0%` to `10.0%` (median `5.0%`, with 92.9% of teams scoring $\le 6.0\%$).

**State-Filtered Deliberation (SFD)** is a declarative three-stage `SequentialAgent` architecture built on Google's Agent Development Kit (ADK) and the `swegemma` harness (`TriageAgent` $\to$ `PatchAgent` $\to$ `VerifierAgent`, locked in pre-evaluation commit `af0937d4109f956d7d11aa560809bcb4f6bab471`) that configures `include_contents: "none"` on `PatchAgent` and `VerifierAgent` to slice out intermediate tool observations at stage boundaries while passing structured text state variables (`localization_packet` and `patch_manifest`) through `session.state`. Crucially, SFD deterministically bounds **stage-entry** prompt context and lowers **typical** per-task peak prompt context rather than upper-tail `TriageAgent` peak context (`TriageAgent` itself is not reset).

We evaluated three controlled configurations on `gemma-4-e4b-it-qat-w4a16-ct` on Kaggle's 4x NVIDIA L4 GPU cluster (`NvidiaL4`, 96 GB VRAM, `vLLM`, `tensor_parallel_size=4`, `temperature=0.0`, `seed=42`) across 32 SWE-bench tasks (96 primary paired runs plus 16 rerun reproducibility runs = **112 total 4x L4 GPU runs**, 11,706,178 tokens, 1,328 tool invocations):

| Configuration | Runs | Resolved (95% Wilson CI) | Mean Peak $P_t$ | Mean Cum. Tokens | Mean Duration |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Official Starter (`flat_starter`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 13,359.7 | 105,817.6 | 94.2s |
| **Single-Agent (`flat_controlled`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 13,959.0 | 118,173.0 | 90.8s |
| **State-Filtered Deliberation (`sfd`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 10,907.5 | 80,375.7 | 86.6s |
| **Rerun: `flat_controlled`** | 8 | 1/8 (12.5%) [2.2%, 47.1%] | 12,557.5 | 93,135.6 | 107.4s |
| **Rerun: `sfd`** | 8 | 1/8 (12.5%) [2.2%, 47.1%] | 9,306.4 | 67,710.1 | 96.4s |

- **Measured Stage-Boundary Context Reset & Peak Reduction ($n = 32$):** Across 32 primary `sfd` trajectories, `TriageAgent` reaches a mean peak prompt of **10,473.9 tokens** (median **9,863.0**), which resets at `PatchAgent` entry (`include_contents: "none"`) to a mean of **1,536.9 tokens** (median **1,503.0**). This corresponds to an empirical reset distribution of median **87.43%**, mean **81.95%**, IQR **[75.72%, 89.46%]**, and range **[44.95%, 92.49%]**. SFD achieves a lower per-task peak prompt length than `flat_controlled` on **28/32 tasks (87.5%)** (Wilcoxon $p < 0.0001$, -21.9% peak prompt reduction) and consumes **-32.0% cumulative prompt tokens** (Wilcoxon $p < 0.0001$, lower on 25/32 tasks).
- **Discretionary `AgentTool` Bypass in `flat_starter` ($n = 32$):** Across all 32 tasks (336 tool invocations), `swe_baseline_agent` invoked `code_analyzer` only **7 times (2.1%)**, completely bypassing `code_analyzer` on **29 of 32 tasks (90.6%)**, opting instead to read large files directly into primary context.
- **Statistical Resolution Invariance & Rerun Determinism:** Resolution rate is invariant at **2/32 (6.25%)** across all three architectures (McNemar $p = 1.0000$). Re-running Cohort 1 ($n=8$, 16 paired runs) demonstrated **87.5% bitwise identical patches** (14/16) and **75.0% exit code agreement** (12/16), confirming that single-run resolution differences at small $n$ are within normal execution variance.

---

## Repository Structure

```
.
├── agent_sfd/                  # Declarative Google ADK submission directory (SFD)
│   ├── agent.yaml              # Root SequentialAgent orchestrator
│   ├── eval_config.yaml        # Evaluation budgets & limits
│   ├── configs/
│   │   └── sampling.yaml       # Greedy sampling parameters (temp=0.0, seed=42)
│   ├── prompts/
│   │   ├── triage.md           # Read-only localization instructions
│   │   ├── patcher.md          # Minimal surgical edit instructions
│   │   └── verifier.md         # Targeted test & submit_patch instructions
│   └── sub_agents/
│       ├── triage_agent.yaml   # Stage 1: TriageAgent
│       ├── patch_agent.yaml    # Stage 2: PatchAgent (include_contents: "none")
│       └── verifier_agent.yaml # Stage 3: VerifierAgent (include_contents: "none")
├── traces/                     # Raw execution traces & logs from all 112 4x L4 GPU runs (5 cohorts)
│   ├── eval_results/           # Cohort 1 paired runs (24 runs across 8 canonical tasks)
│   ├── shard2_results/         # Cohort 2 paired runs (24 runs across 8 seeded-random tasks)
│   ├── rerun_results/          # Cohort 1 rerun reproducibility runs (16 runs)
│   ├── shard3_results/         # Cohort 3 paired runs (24 runs across 8 stratified disjoint tasks)
│   └── shard4_results/         # Cohort 4 paired runs (24 runs across 8 stratified disjoint tasks)
├── dataset_resource/           # Unified ATIF-Gemma Resource Directory (112 traces)
│   ├── traces/                 # All 112 standardized ATIF v1.7 JSON traces (100% schema validated)
│   ├── corpus_metadata.csv     # Master index of all 112 runs (task, repo, config, cohort, exit code, tokens)
│   ├── datasheet.md            # Dataset documentation conforming to Gebru et al. (2021)
│   ├── atif_schema_v1_7.json   # Concrete ATIF v1.7 Draft-07 JSON schema (Harbor v1.7 specification)
│   └── checksums.sha256        # SHA-256 verification hashes for all 112 traces
├── analysis/                   # Standalone diagnostic reproduction & statistical scripts
│   ├── reproduce_tables.py     # Re-generates Tables 1–3 from 112 raw traces
│   ├── classify_exit2.py       # Deterministic Exit Code 2 breakdown (agent vs environment)
│   ├── subclassify_exit1.py    # Mutually exclusive Exit Code 1 assertion failure taxonomy
│   ├── statistical_tests.py    # Wilson CIs, bootstrap CIs, Wilcoxon & McNemar tests
│   ├── claim_audit.py          # Tool error taxonomy & stage prompt reset distributions
│   ├── validate_atif_schema.py # Formal ATIF v1.7 schema validation & specification audit
│   └── figures.py              # Generates publication vector figures (figures/fig*.svg)
├── results/
│   ├── summary.json                        # Aggregated metrics for Artifact 1 (64 runs)
│   ├── resource_summary.json               # Aggregated metrics for Artifact 2 (112 runs)
│   ├── summary_metrics.json                # Corpus-level token and turn statistics
│   ├── table1_cohort_summary.csv           # Re-generated Table 1 (5 cohorts)
│   ├── table2_taxonomy.csv                 # Re-generated Table 2 (exit codes)
│   ├── table3_architectures.csv            # Re-generated Table 3 (configurations)
│   ├── exit1_breakdown.json                # Mutually exclusive Exit 1 localization tiers
│   ├── exit2_breakdown.json                # Exit 2 agent vs environment breakdown
│   ├── schema_validation_report.json       # Formal ATIF v1.7 specification validation report
│   ├── stats_report.json                   # Comprehensive statistical tests & CIs
│   ├── tool_errors_breakdown.json          # Tool error frequencies & prompt reset distributions
│   ├── remediation_eval.json               # Post-hoc remediation gate evaluation
│   ├── leaderboard_snapshot_2026_10_26.json # Official main leaderboard & submission #57643078 snapshot
│   └── small_model_leaderboard_2026_10_24.csv # Official Small Model Prize leaderboard snapshot (N=197)
├── scripts/
│   ├── aggregate.py            # Computes results/summary.json from traces/
│   ├── render_paper.py         # Renders paper.typ, paper.tex, KAGGLE_WRITEUP.md, README.md
│   ├── check_consistency.py    # Consistency checks for Artifact 1
│   └── check_consistency_resource.py # Automated 7/7 assertion audit for Artifact 2
├── _retracted_simulation/      # Quarantined earlier synthetic simulation files with README notice
├── kaggle_kernel/              # Reproducible Kaggle 4x L4 GPU evaluation notebook
├── paper.typ                   # Typst source for Artifact 1 paper (Methods Track)
├── paper.pdf                   # Compiled camera-ready PDF (Methods Track)
├── paper_resource.typ          # Typst source for Artifact 2 paper (Resource Track)
├── paper_resource.pdf          # Compiled camera-ready PDF (Resource Track)
├── references_gemma.bib        # Verified BibTeX bibliography
├── KAGGLE_WRITEUP.md           # Kaggle writeup for Artifact 1 (Methods Track)
├── KAGGLE_WRITEUP_RESOURCE.md  # Kaggle writeup for Artifact 2 (Resource Track)
├── experiment_plan.md          # Pre-registered experimental design & failure taxonomy
└── compute_plan.md             # Hardware & runtime budget documentation
```

---

## Reproducibility Pipeline

```bash
# 1. Recompute all aggregate metrics and statistical tests from the 64 real ATIF v1.7 traces:
python scripts/aggregate.py

# 2. Render paper.typ, paper.tex, KAGGLE_WRITEUP.md, and README.md from results/summary.json:
python scripts/render_paper.py

# 3. Verify consistency and confirm zero synthetic/placeholder strings remain:
python scripts/check_consistency.py

# 4. Compile the PDF manuscript (Methods Track):
typst compile paper.typ paper.pdf

# 5. Reproduce all 112-trace ATIF-Gemma tables, figures, schema validation, and consistency checks (Resource Track):
python analysis/reproduce_tables.py
python analysis/classify_exit2.py
python analysis/subclassify_exit1.py
python analysis/statistical_tests.py
python analysis/validate_atif_schema.py
python scripts/check_consistency_resource.py
typst compile paper_resource.typ paper_resource.pdf
```
