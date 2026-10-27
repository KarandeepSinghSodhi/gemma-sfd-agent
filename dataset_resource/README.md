# ATIF-Gemma: An Open Empirical Diagnostic Corpus and Failure Taxonomy for Small Open-Weight Developer Agents

## Overview
**ATIF-Gemma** is the first open, full-fidelity diagnostic trajectory corpus specifically recording small open-weight coding agents (`gemma-4-e4b-it-qat-w4a16-ct`) executing multi-turn repository-level software engineering tasks on SWE-bench.

All 64 execution traces were generated on Kaggle's 4x NVIDIA L4 GPU environment inside the official Google ADK / `swegemma` harness, formatted in the standard **Agent Trajectory Interchange Format (ATIF v1.7)**.

---

## Corpus Composition (64 Traces)
- **Primary Paired Evaluation ($n = 48$ runs across 16 unique tasks)**:
  - `flat_starter` (16 runs): Official competition starter kit (`agent_tool` discretionary sub-agent pattern).
  - `flat_controlled` (16 runs): Single `LlmAgent` baseline matching SFD tools, prompts, and sampling parameters.
  - `sfd` (16 runs): State-Filtered Deliberation 3-stage `SequentialAgent` with `include_contents: "none"`.
- **Rerun Reproducibility Study ($n = 16$ runs on Cohort 1)**:
  - `sfd_rerun` (8 runs): Independent run at $T=0.0$, seed=42, tensor parallel=4.
  - `flat_controlled_rerun` (8 runs): Independent run at $T=0.0$, seed=42, tensor parallel=4.

---

## Summary Statistics
- **Total LLM Calls**: 847
- **Total Tool Invocations**: 660 (158 in flat_starter, 168 in flat_controlled, 179 in sfd)
- **Total Logged Tokens**: 6,378,543 (Prompt: 5,984,122; Completion: 394,421)
- **Total 4x L4 GPU Wall-Clock Time**: 6,092.5 seconds (1.69 hours)
- **Phase 2 Exit Code Distribution**:
  - `exit_code -1` (Timeout / 0-byte patch): 4 (6.2%)
  - `exit_code 0` (Resolved / Verification passed): 4 (6.2%)
  - `exit_code 1` (Test assertion failure): 36 (56.2%)
  - `exit_code 2` (Pytest collection / import crash): 20 (31.2%)

---

## Files in this Dataset
- `traces/`: 64 individual ATIF v1.7 JSON trace files detailing every prompt, thought block, tool call, and observation.
- `corpus_metadata.csv`: Structured index of all 64 traces with task IDs, repositories, configs, durations, tokens, and exit codes.
- `tasks_reference.jsonl`: Ground-truth reference patches, problem statements, and test patches for all evaluated SWE-bench instances.

---

## Citation & License
This dataset is released under the Creative Commons Attribution 4.0 International (CC BY 4.0) license.
```bibtex
@misc{sodhi2026atifgemma,
  author = {Sodhi, Karandeep Singh},
  title = {ATIF-Gemma: An Open Empirical Diagnostic Corpus and Failure Taxonomy for Small Open-Weight Developer Agents},
  year = {2026},
  publisher = {Kaggle},
  url = {https://www.kaggle.com/datasets/karandeepsinghsodhi/atif-gemma-swe-agent-traces}
}
```
