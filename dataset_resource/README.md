# ATIF-Gemma: An Open Empirical Diagnostic Corpus and Failure Taxonomy for Small Open-Weight Developer Agents

## Overview
**ATIF-Gemma** is the first open, full-fidelity diagnostic trajectory corpus specifically recording small open-weight coding agents (`gemma-4-e4b-it-qat-w4a16-ct`) executing multi-turn repository-level software engineering tasks on SWE-bench.

All 112 execution traces were generated on Kaggle's 4x NVIDIA L4 GPU environment inside the official Google ADK / `swegemma` harness, formatted in the standard **Agent Trajectory Interchange Format (ATIF v1.7)**.

---

## Corpus Composition (112 Traces across 32 Unique Benchmark Tasks)
- **Primary Stratified Evaluations ($n = 96$ runs across 32 unique tasks)**:
  - `flat_starter` (32 runs): Official competition starter kit (`agent_tool` discretionary sub-agent pattern).
  - `flat_controlled` (32 runs): Single `LlmAgent` baseline matching SFD tools, prompts, and sampling parameters.
  - `sfd` (32 runs): State-Filtered Deliberation 3-stage `SequentialAgent` with `include_contents: "none"`.
- **Rerun Reproducibility Study ($n = 16$ runs on Cohort 1)**:
  - `sfd_rerun` (8 runs): Independent run at $T=0.0$, seed=42, tensor parallel=4.
  - `flat_controlled_rerun` (8 runs): Independent run at $T=0.0$, seed=42, tensor parallel=4.

---

## Summary Statistics
- **Total Traces**: 112
- **Total LLM Calls**: 1,518
- **Total Tool Invocations**: 1,182
- **Total Logged Tokens**: 11,706,178 (Prompt: 11,026,487; Completion: 679,691)
- **Total 4x L4 GPU Wall-Clock Time**: 10,319.4 seconds (2.87 hours)
- **Phase 2 Exit Code Distribution**:
  - `exit_code 0` (Resolved / Verification passed): 8 (7.14%)
  - `exit_code 1` (Test assertion failure): 56 (50.0%)
  - `exit_code 2` (Pytest collection / import crash): 36 (32.14%)
  - `exit_code -1` (Timeout / 0-byte patch): 9 (8.04%)
  - `exit_code 124` (Verification Timeout): 3 (2.68%)

---

## Files in this Dataset
- `traces/`: 112 individual ATIF v1.7 JSON trace files detailing every prompt, thought block, tool call, and observation.
- `corpus_metadata.csv`: Structured index of all 112 traces with task IDs, repositories, configs, durations, tokens, and exit codes.
- `tasks_reference.jsonl`: Ground-truth reference patches, problem statements, and test patches for all evaluated SWE-bench instances.

---

## Diagnostic Python Toolkit (`atif-gemma`)
Install the companion analysis toolkit:
```bash
pip install atif-gemma
```

Audit your own SWE-agent traces:
```bash
python -m atif_gemma.cli audit traces/
python -m atif_gemma.cli playbook
```

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
