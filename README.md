# State-Filtered Deliberation (SFD): Mitigating Context Bloat for Small Open-Weight Developer Agents

[![Paper](https://img.shields.io/badge/Paper-PDF-red.svg)](paper.pdf)
[![Kaggle Competition](https://img.shields.io/badge/Kaggle-Gemma--4--Developer--Agent-blue.svg)](https://www.kaggle.com/competitions/gemma-4-developer-agent)
[![Kaggle Paper Track](https://img.shields.io/badge/Kaggle-Paper--Track-orange.svg)](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper)
[![Kaggle Kernel](https://img.shields.io/badge/Kaggle-Live_Notebook-20BEFF.svg)](https://www.kaggle.com/code/karandeepsinghsodhi/sfd-state-filtered-deliberation-agent-gemma-4)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)

**Author:** Karandeep Singh Sodhi (`karandeep.sodhi2504a@gmail.com`)  
**Track:** Google — The Gemma 4 Developer Agent Challenge (Paper Track & Prediction Track)

---

## Corrections & Scientific Integrity Note
> **Notice:** Earlier drafts of this repository and writeup contained preliminary results produced by an analytical simulation (`simulate_benchmark.py`). Those synthetic numbers and figures have been retracted and quarantined to `_retracted_simulation/`. The paper now reports only verified system designs and real containerized measurements.

---

## Overview

Deploying autonomous developer agents on small open-weight language models (e.g., Google's Gemma 4 E2B, E4B, 12B) is constrained by context accumulation. In standard monolithic ReAct loops, verbose tool observations accumulate monotonically into the context buffer, diluting token signal density and causing premature context exhaustion.

**State-Filtered Deliberation (SFD)** addresses this bottleneck through modular sequential sub-agents. By decomposing the software repair lifecycle into three isolated sub-agents with immutable ~250-token state handoffs, SFD resets prompt contexts to under 1,500 tokens at each stage boundary.

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
├── _retracted_simulation/      # Quarantined synthetic simulation scripts and data
│   ├── README.md               # Retraction notice
│   ├── simulate_benchmark.py
│   ├── benchmark_results.csv
│   ├── generate_paper_figures.py
│   └── PEER_REVIEW_AUDIT.md
├── kaggle_kernel/              # Runnable Kaggle notebook package
│   ├── kernel-metadata.json    # Kaggle API metadata
│   └── sfd_developer_agent.ipynb
├── submission_sfd.zip          # Official competition zip archive (< 4 KB)
├── paper.typ                   # Typst source for paper manuscript
├── paper.pdf                   # Compiled camera-ready PDF
├── paper.tex                   # LaTeX source version
├── references_gemma.bib        # BibTeX citations
├── KAGGLE_WRITEUP.md           # Official Kaggle Writeup document
└── README.md
```

---

## Reproducibility & Quickstart

### 1. Compile the Research Paper
```bash
typst compile paper.typ paper.pdf
```

### 2. Declarative ADK Package
The agent package in `agent_sfd/` adheres strictly to the official competition schema (`swegemma` and `adk-submission`). It can be validated and evaluated within the competition harness container.

---

## Citation

```bibtex
@article{sodhi2026sfd,
  title={State-Filtered Deliberation: Mitigating Context Bloat for Small Open-Weight Developer Agents},
  author={Sodhi, Karandeep Singh},
  journal={Google Gemma 4 Developer Agent Challenge},
  year={2026}
}
```
