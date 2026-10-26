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
> **Notice:** Earlier drafts of this repository and writeup contained preliminary results produced by an analytical simulation (`simulate_benchmark.py`) and a mock smoke-test script (`smoke_test.py`). Those synthetic files have been retracted and quarantined to `_retracted_simulation/`. Every result reported in `paper.typ`, `paper.pdf`, `paper.tex`, `KAGGLE_WRITEUP.md`, and `results/summary.json` is computed by `scripts/aggregate.py` directly from real two-phase `swegemma` + `vLLM` execution traces (`traces/`).

---

## Overview & Key Empirical Findings (`gemma-4-e4b-it-qat-w4a16-ct`)

Autonomous software engineering (SWE) agents built on small open-weight language models (4-bit quantized Gemma 4 E2B and E4B) face tight context and capability constraints when executing multi-turn debugging trajectories. Across all 197 participating teams on the official Small Model Prize leaderboard (`results/small_model_leaderboard_2026_10_24.csv`, updated 2026-10-24 23:58 UTC), public resolution rates range from `0.0%` to `10.0%` (median `5.0%`, with 92.9% of teams scoring $\le 6.0\%$).

**State-Filtered Deliberation (SFD)** is a declarative three-stage `SequentialAgent` architecture built on Google's Agent Development Kit (ADK) and the `swegemma` harness (`TriageAgent` $\to$ `PatchAgent` $\to$ `VerifierAgent`) that configures `include_contents: "none"` on `PatchAgent` and `VerifierAgent` to slice out intermediate tool observations at stage boundaries while passing structured text state variables (`localization_packet` and `patch_manifest`) through `session.state`. Crucially, SFD deterministically bounds **stage-entry** prompt context rather than total or within-stage peak context (`TriageAgent` itself is not reset).

We evaluated three controlled configurations on `gemma-4-e4b-it-qat-w4a16-ct` on Kaggle's 4x NVIDIA L4 GPU cluster (`NvidiaL4`, 96 GB VRAM, `vLLM`, `tensor_parallel_size=4`, `temperature=0.0`, `seed=42`) across $n = 16$ tasks spanning two disjoint 8-task cohorts (48 primary paired two-phase runs plus 16 rerun reproducibility runs = **64 total 4x L4 GPU runs**):

| Configuration | Resolved ($k/n$) | 95% Wilson CI | Non-Empty Patch | Fail: No / Wrong Patch | Mean Peak $P_t$ | Max Peak $P_t$ | Mean Cum. Tokens | Mean Tools | Mean Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Official Starter Kit (`agent_tool` pattern) | 1/16 (6.2%) | [1.1%, 28.3%] | 13/16 (81.2%) | 3 / 12 | 13029.3 | 15281 | 103350.1 | 9.9 | 97.3s |
| Controlled Single-Agent (`LlmAgent`) | 0/16 (0.0%) | [0.0%, 19.4%] | 14/16 (87.5%) | 2 / 14 | 13550.8 | 16154 | 119664.4 | 10.5 | 92.2s |
| State-Filtered Deliberation (`SequentialAgent`) | 1/16 (6.2%) | [1.1%, 28.3%] | 14/16 (87.5%) | 2 / 13 | 11291.9 | 16146 | 88909.5 | 11.2 | 89.4s |

- **Measured Stage-Boundary Context Reset vs. Peak Context ($n = 16$):** Across the 16 `sfd` trajectories, `TriageAgent` reaches a mean peak prompt of **10922.1 tokens** (max **16146**), which resets at `PatchAgent` entry (`include_contents: "none"`) to a mean of **1500.9 tokens** (max **2126**, a **-86.3%** peak-to-entry reset) and at `VerifierAgent` entry (`include_contents: "none"`) to a mean of **1470.2 tokens** (max **2165**). While this lowers mean single-call peak prompt tokens by 13.3% vs. `flat_starter` and 16.7% vs. `flat_controlled`, SFD does **not** bound overall trajectory peak prompt length (max 16146 vs. 15281 and 16154).
- **Discretionary `AgentTool` Bypass in `flat_starter`:** Across 16 tasks (`158` budget-counted tool calls, `176` total trace tool events), `swe_baseline_agent` invoked `code_analyzer_agent` only **4/149 times (2.7% of root non-`submit_patch` tool decisions; 2.3% of all trace tool events)**, bypassing `code_analyzer_agent` completely on **13/16 tasks (81.2%)**.
- **Statistical Comparison & Rerun Reproducibility:** Across $n = 16$ paired tasks, `sfd` (`1/16`) and `flat_starter` (`1/16`) tie in resolution rate (McNemar $p = 1.0000$), and `sfd` vs. `flat_controlled` (`0/16`) yields McNemar $p = 1.0000$. Furthermore, rerunning Cohort 1 ($n=8$) under `tensor_parallel_size=4` (`traces/rerun_results/`) showed `8/8` (`100.0%`) `resolved` agreement for `sfd` and `7/8` (`87.5%`) for `flat_controlled` (where `flat_controlled_rerun` also resolved `rich_4077`).

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
├── traces/                     # All 64 real ATIF v1.7 traces & logs from 4x L4 GPU runs
│   ├── eval_results/           # Cohort 1 paired runs (24 runs across 8 canonical tasks)
│   ├── shard2_results/         # Cohort 2 paired runs (24 runs across 8 seeded-random tasks)
│   └── rerun_results/          # Cohort 1 rerun reproducibility runs (16 runs)
├── results/
│   ├── summary.json                        # Aggregated metrics, Wilson CIs, McNemar & bootstrap tests
│   ├── summary_table.csv                   # Tabular summary generated by scripts/aggregate.py
│   ├── leaderboard_snapshot_2026_10_26.json # Official main leaderboard & submission #57643078 snapshot
│   └── small_model_leaderboard_2026_10_24.csv # Official Small Model Prize leaderboard snapshot (N=197)
├── scripts/
│   ├── aggregate.py            # Computes results/summary.json from all traces in traces/
│   ├── render_paper.py         # Renders paper.typ, paper.tex, KAGGLE_WRITEUP.md, README.md
│   └── check_consistency.py    # Automated verification that zero unmeasured/retracted numbers exist
├── _retracted_simulation/      # Quarantined earlier synthetic simulation files with README notice
├── kaggle_kernel/              # Reproducible Kaggle 4x L4 GPU evaluation notebook
├── paper.typ                   # Typst source for paper manuscript
├── paper.pdf                   # Compiled camera-ready PDF
├── paper.tex                   # LaTeX source version
├── references_gemma.bib        # Verified BibTeX bibliography
├── KAGGLE_WRITEUP.md           # Complete Kaggle Paper Track writeup
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

# 4. Compile the PDF manuscript:
typst compile paper.typ paper.pdf
```
