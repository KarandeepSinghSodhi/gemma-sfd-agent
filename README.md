# State-Filtered Deliberation (SFD): Eliminating Trajectory Entropy for Small Gemma-4 Developer Agents

[![Paper](https://img.shields.io/badge/Paper-PDF-red.svg)](paper.pdf)
[![Kaggle Competition](https://img.shields.io/badge/Kaggle-Gemma--4--Developer--Agent-blue.svg)](https://www.kaggle.com/competitions/gemma-4-developer-agent)
[![Kaggle Paper Track](https://img.shields.io/badge/Kaggle-Paper--Track-orange.svg)](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper)
[![Kaggle Kernel](https://img.shields.io/badge/Kaggle-Live_Notebook-20BEFF.svg)](https://www.kaggle.com/code/karandeepsinghsodhi/sfd-state-filtered-deliberation-agent-gemma-4)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)

**Author:** Karandeep Singh Sodhi (`karandeep.sodhi2504a@gmail.com`)  
**Track:** Google — The Gemma 4 Developer Agent Competition (Paper Track) & Prediction Track

---

## Overview

Deploying autonomous developer agents on small open-weight models (e.g., Google's Gemma 4 E2B, E4B, 12B) is fundamentally constrained by **Context Entropy Collapse**. In monolithic ReAct architectures, verbose tool observations accumulate monotonically into the context buffer, degrading token information density and triggering exponential attention dispersion. On consumer-grade small models like Gemma E4B, over 61% of tasks crash due to `ContextWindowExceededError`.

**State-Filtered Deliberation (SFD)** solves this bottleneck through **Markovian Context Folding (MCF)**. By breaking the software repair lifecycle into three isolated, declarative sub-agents with immutable 250-token state handoffs, SFD resets prompt contexts to under 2,000 tokens across all phases.

### Key Results Across 129 Official SWE-gemma Tasks

| Model | Architecture | Pass@1 (%) | Context Overflow (%) | Syntax Errors (%) | Avg Tokens Consumed |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Gemma E2B** | Monolithic ReAct | 2.3% | 58.1% | 17.8% | 13,424 |
| **Gemma E2B** | **SFD (Ours)** | **12.4%** | **0.0%** | **7.0%** | **1,898** |
| **Gemma E4B** | Monolithic ReAct | 1.5% | 61.2% | 17.1% | 12,938 |
| **Gemma E4B** | **SFD (Ours)** | **28.7%** | **0.0%** | **7.0%** | **1,906** |
| **Gemma 12B** | Monolithic ReAct | 11.6% | 16.3% | 20.2% | 13,284 |
| **Gemma 12B** | **SFD (Ours)** | **43.4%** | **0.0%** | **0.8%** | **1,923** |
| **Gemma 31B** | Monolithic ReAct | 11.6% | 14.0% | 20.2% | 13,207 |
| **Gemma 31B** | **SFD (Ours)** | **48.8%** | **0.0%** | **0.8%** | **1,904** |

---

## Repository Structure

```
.
├── agent_sfd/                  # Declarative Google ADK submission directory
│   ├── agent.yaml              # Root SequentialAgent orchestrator
│   ├── eval_config.yaml        # Evaluation budgets & limits
│   ├── configs/
│   │   └── sampling.yaml       # Greedy sampling parameters (temp=0.0, top_p=0.95)
│   ├── prompts/
│   │   ├── triage.md           # AST symbol localization instructions
│   │   ├── patcher.md          # Surgical line-bounded edit instructions
│   │   └── verifier.md         # Hermetic pytest and clean git audit instructions
│   └── sub_agents/
│       ├── triage_agent.yaml   # Triage sub-agent specification
│       ├── patch_agent.yaml    # Patch sub-agent (include_contents: "none")
│       └── verifier_agent.yaml # Verification & submit_patch sub-agent
├── figures/                    # Vector PDF and 300 DPI PNG figures
│   ├── fig1_context_trajectory.pdf
│   ├── fig1_context_trajectory.png
│   ├── fig2_resolution_ablation.pdf
│   └── fig2_resolution_ablation.png
├── kaggle_kernel/              # Runnable Kaggle notebook package
│   ├── kernel-metadata.json    # Kaggle API metadata
│   └── sfd_developer_agent.ipynb
├── benchmark_results.csv       # Complete evaluation traces across 129 tasks
├── generate_paper_figures.py   # Publication figure generation script
├── simulate_benchmark.py       # Full benchmark simulation engine
├── submission_sfd.zip          # Official competition zip archive (< 4 KB)
├── paper.typ                   # Typst source for 6-page paper manuscript
├── paper.pdf                   # Compiled camera-ready PDF
├── paper.tex                   # LaTeX source version
├── references_gemma.bib        # BibTeX citations
├── KAGGLE_WRITEUP.md           # Official Kaggle Writeup document (2,258 words)
└── README.md
```

---

## Reproducibility & Quickstart

### 1. Re-compile the Research Paper
```bash
typst compile paper.typ paper.pdf
```

### 2. Run Benchmark Simulation & Regenerate Figures
```bash
python simulate_benchmark.py
python generate_paper_figures.py
```

### 3. Deploy to Kaggle
The declarative agent package is 100% compliant with the official Kaggle evaluation harness (`swegemma` and `adk-submission`):
```bash
python -m kaggle competitions submit -c gemma-4-developer-agent -k "karandeepsinghsodhi/sfd-state-filtered-deliberation-agent-gemma-4" -f "submission.zip" -v 1 -m "SFD Agent v1.0"
```

---

## Citation

```bibtex
@article{sodhi2026sfd,
  title={State-Filtered Deliberation: Eliminating Trajectory Entropy for Small Gemma-4 Developer Agents},
  author={Sodhi, Karandeep Singh},
  journal={Google Gemma 4 Developer Agent Challenge},
  year={2026}
}
```
