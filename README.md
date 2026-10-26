# State-Filtered Deliberation (SFD): Stage-Isolated Context Management for Small Open-Weight Software Engineering Agents

[![Paper](https://img.shields.io/badge/Paper-PDF-red.svg)](paper.pdf)
[![Kaggle Competition](https://img.shields.io/badge/Kaggle-Gemma--4--Developer--Agent-blue.svg)](https://www.kaggle.com/competitions/gemma-4-developer-agent)
[![Kaggle Paper Track](https://img.shields.io/badge/Kaggle-Paper--Track-orange.svg)](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper)
[![Kaggle Kernel](https://img.shields.io/badge/Kaggle-Live_Notebook-20BEFF.svg)](https://www.kaggle.com/code/karandeepsinghsodhi/sfd-state-filtered-deliberation-agent-gemma-4)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)

**Author:** Karandeep Singh Sodhi (`karandeep.sodhi2504a@gmail.com`)  
**Track:** Google — The Gemma 4 Developer Agent Challenge (Paper Track & Prediction Track)

---

## Corrections & Scientific Integrity Note
> **Notice:** Earlier drafts of this repository and writeup contained preliminary results produced by an analytical simulation (`simulate_benchmark.py`) and a mock smoke-test script (`smoke_test.py`). Those synthetic files have been retracted and quarantined to `_retracted_simulation/`. Every result reported in `paper.typ`, `paper.pdf`, `paper.tex`, `KAGGLE_WRITEUP.md`, and `results/summary.json` is computed by `scripts/aggregate.py` directly from real two-phase `swegemma` + `vLLM` execution traces (`traces/eval_results/`).

---

## Overview & Key Empirical Findings (`gemma-4-e4b-it-qat-w4a16-ct`)

Autonomous software engineering (SWE) agents built on small open-weight language models (4-bit quantized Gemma 4 E2B and E4B) face severe operational constraints when executing multi-turn debugging trajectories. Across all 24 participating teams on the official Small Model Prize leaderboard (E2B/E4B), resolution rates range from `0.0%` to `6.0%` (median `3.0%`).

**State-Filtered Deliberation (SFD)** is a declarative three-stage `SequentialAgent` architecture built on Google's Agent Development Kit (ADK) and the `swegemma` harness (`TriageAgent` $\to$ `PatchAgent` $\to$ `VerifierAgent`) that configures `include_contents: "none"` on `PatchAgent` and `VerifierAgent` to slice out intermediate tool observations at stage boundaries while passing structured text state variables (`localization_packet` and `patch_manifest`) through `session.state`.

We evaluated three controlled configurations on `gemma-4-e4b-it-qat-w4a16-ct` on Kaggle's 4x NVIDIA L4 GPU cluster (`NvidiaL4`, 96 GB VRAM, `vLLM`, `temperature=0.0`, `seed=42`) across a deterministic stratified subset of $n = 8$ tasks spanning all four competition repositories (24 complete two-phase runs):

| Configuration | Resolved ($k/n$) | 95% Wilson CI | Non-Empty Patch | Mean Peak $P_t$ | Max Peak $P_t$ | Mean Cum. Tokens | Mean Tools | Mean Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Official Starter Kit (`agent_tool` pattern) | 0/8 (0.0%) | [0.0%, 32.4%] | 6/8 (75.0%) | 12855.2 | 14736 | 93509.9 | 8.9 | 103.2s |
| Controlled Single-Agent (`LlmAgent`) | 0/8 (0.0%) | [0.0%, 32.4%] | 8/8 (100.0%) | 12456.4 | 14912 | 109507.1 | 9.8 | 88.9s |
| State-Filtered Deliberation (`SequentialAgent`) | 1/8 (12.5%) | [2.2%, 47.1%] | 7/8 (87.5%) | 9298.1 | 14454 | 80790.9 | 10.9 | 92.7s |

- **Measured Stage-Boundary Context Reset:** Across the 8 `sfd` trajectories, `TriageAgent` reaches a mean peak prompt of **8558.5 tokens** (max 14454), which resets at `PatchAgent` entry (`include_contents: "none"`) to a mean of **1534.9 tokens** (max 2126, a **-82.1%** reduction) and at `VerifierAgent` entry (`include_contents: "none"`) to a mean of **1559.4 tokens** (max 2165).
- **Discretionary `AgentTool` Bypass in `flat_starter`:** Across 8 tasks and 79 recorded tool invocations in `flat_starter`, `code_analyzer_agent` was invoked only **2 times (2.5% of tool calls)**, while **6/8 tasks (75.0%)** bypassed `code_analyzer_agent` completely.
- **Statistical Significance:** At $n = 8$, the resolution difference of `1/8` (`12.5%`, resolving `rich_4077`) vs. `0/8` (`0.0%`) has a 95% paired bootstrap CI of `[+0.00%, +37.50%]` and exact two-sided McNemar $p = 1.0000$ (not statistically significant at $n = 8$).

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
├── traces/eval_results/        # Real ATIF v1.7 traces & logs from 4x L4 GPU evaluation
│   ├── paired_progress.jsonl   # Task-level execution summary across 24 runs
│   ├── flat_starter/           # Official starter kit traces (8 JSON traces + 8 logs)
│   ├── flat_controlled/        # Unconfounded single-agent traces (8 JSON traces + 8 logs)
│   └── sfd/                    # State-Filtered Deliberation traces (8 JSON traces + 8 logs)
├── results/
│   ├── summary.json            # Aggregated metrics, Wilson CIs, McNemar & bootstrap tests
│   └── summary_table.csv       # Tabular summary generated by scripts/aggregate.py
├── scripts/
│   ├── aggregate.py            # Computes results/summary.json from traces/eval_results/
│   ├── render_paper.py         # Renders paper.typ, paper.tex, KAGGLE_WRITEUP.md from summary.json
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
# 1. Recompute all aggregate metrics and statistical tests from the 24 real ATIF v1.7 traces:
python scripts/aggregate.py

# 2. Render paper.typ, paper.tex, and KAGGLE_WRITEUP.md directly from results/summary.json:
python scripts/render_paper.py

# 3. Verify consistency and confirm zero synthetic/placeholder strings remain:
python scripts/check_consistency.py

# 4. Compile the PDF manuscript:
typst compile paper.typ paper.pdf
```
