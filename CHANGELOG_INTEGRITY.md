# Integrity Changelog & Audit Trail

**Date:** October 26, 2026  
**Author:** Karandeep Singh Sodhi  
**Project:** State-Filtered Deliberation (SFD) for Google Gemma 4 Developer Agent Challenge  

---

## 1. Items Retracted and Quarantined

In accordance with strict scientific integrity standards, all synthetic and simulated artifacts from earlier drafts have been quarantined to `_retracted_simulation/` and marked with an explicit non-empirical disclaimer:
- `simulate_benchmark.py`: Quarantined. Generated synthetic benchmark results using an analytical model.
- `benchmark_results.csv`: Quarantined. Contained simulated task resolution rates (1.5%, 1.6%, 12.4%, 28.7%, 43.4%, 48.8%) and token metrics.
- `generate_paper_figures.py`: Quarantined. Plotted synthetic context trajectories and ablation bar charts.
- `PEER_REVIEW_AUDIT.md`: Quarantined. Self-generated review document containing unverified scores.
- `figures/fig1_context_trajectory.*` and `figures/fig2_resolution_ablation.*`: Quarantined. Rendered from simulated data.

---

## 2. Textual Corrections Across Manuscript & Writeup

All simulated numbers and ungrounded claims were completely removed from `paper.typ`, `paper.tex`, `KAGGLE_WRITEUP.md`, `README.md`, and `kaggle_kernel/`:
- **Results Table Removed:** Replaced with system implementation and evaluation protocol.
- **Hypothetical Ablations & P-Values Removed:** All claims of $p=0.38$, $p=0.85$, $p<0.05$ derived from simulated runs were struck.
- **Synthetic Failure Taxonomy Removed:** The synthetic 41/34/17 breakdown was removed; replaced with pre-registered rule-based classification criteria.
- **Inflated Claims Removed:** Stripped all occurrences of "proves", "unprecedented", "first to demonstrate", "mathematically principled", and competition prize amounts.
- **Corrections Notice Added:** A permanent notice was added to `README.md` disclosing the retraction of earlier synthetic drafts.

---

## 3. Real Instrumentation & Grounded Infrastructure Added

- `compute_plan.md`: Formulated hardware audit (local Windows CPU vs Kaggle Cloud GPUs) and timing budget.
- `experiment_plan.md`: Pre-registered experiment protocol featuring:
  - Fair controlled baseline isolating context reset from code-graph tooling.
  - Stratified pilot sample of 45 tasks (`SEED = 20261026`).
  - Pre-registered paired McNemar tests and exact metric definitions.
- `scripts/tracer.py`: Real-time trace recorder with hard caps enforced in code (`max_observation_tokens = 1200`, `max_test_output_tokens = 1500`, stage turn caps) and exact token counting via `tiktoken`.
- `scripts/aggregate.py`: The sole quantitative aggregation engine reading raw JSON traces from `traces/` and computing exact Wilson CIs, peak tokens, and McNemar discordance.
- `traces/`: Directory containing verifiable raw execution JSON traces.
- `results/`: Aggregated output tables (`summary.json`, `summary.csv`).

---

## 4. Hardware Verification & Disclosure

- Local Machine: Windows 11, 16 logical cores, 15.68 GB RAM, CUDA is NOT available (`torch.cuda.is_available() == False`).
- Official Competition Submission: Submission Ref # 57643078 deployed to Kaggle's 4x NVIDIA L4 GPU cluster.
