# Verification Checklist: Paper Number Mapping to File Sources

This checklist maps every single quantitative number in the research paper and writeup to its exact file source and script in the repository.

---

## 1. Quantitative Paper Metrics Mapping

| Number in Paper / Writeup | Section | Context / Description | Exact Source File | Generating Script / Source |
| :--- | :--- | :--- | :--- | :--- |
| **129** | Abstract, §1, §4.2 | Total official competition tasks in benchmark | `tasks.jsonl` | Counted directly via `len(open("tasks.jsonl").readlines())` |
| **67** | §4.2 | FastAPI repository task count (51.9%) | `tasks.jsonl` | Filter: `task["repo"] == "fastapi/fastapi"` |
| **48** | §4.2 | Rich repository task count (37.2%) | `tasks.jsonl` | Filter: `task["repo"] == "Textualize/rich"` |
| **13** | §4.2 | Requests repository task count (10.1%) | `tasks.jsonl` | Filter: `task["repo"] == "psf/requests"` |
| **1** | §4.2 | HTTPX repository task count (0.8%) | `tasks.jsonl` | Filter: `task["repo"] == "encode/httpx"` |
| **32,768** | Abstract, §1, §2 | Max model context window capacity on vLLM | `HARNESS_README.md`, `scripts/tracer.py` | Official competition vLLM configuration parameter `max_model_len` |
| **518 ± 176** | §4.1 | Mean problem statement length (tokens) | `tasks.jsonl` | Measured across all 129 tasks using `tiktoken` (`cl100k_base`) |
| **142** | §4.1 | Shortest problem statement length (tokens) | `tasks.jsonl` | Measured via `min(count_tokens(t["problem_statement"]) for t in tasks)` |
| **1,485** | §4.1 | Longest problem statement length (tokens) | `tasks.jsonl` | Measured via `max(count_tokens(t["problem_statement"]) for t in tasks)` |
| **250** | Abstract, §3 | Size of structured YAML `<triage_packet>` | `agent_sfd/prompts/triage.md` | Measured via `count_tokens(state_packet)` |
| **1,200** | §3, §4 | Max observation token cap | `scripts/tracer.py` | Hard cap constant `CAPS["max_observation_tokens"]` in code |
| **1,500** | §3, §4 | Max test output token cap | `scripts/tracer.py` | Hard cap constant `CAPS["max_test_output_tokens"]` in code |
| **57643078** | §4.3 | Kaggle Prediction Track Submission Reference | Kaggle Competition Submissions API | Active submission running on Kaggle evaluation backend |

---

## 2. Integrity Verification
- **Simulated Pass Rates:** 0% simulated pass rates cited in active manuscript.
- **Hypothetical Figures:** 0 synthetic figures embedded.
- **Trace Consistency:** Every empirical trace is stored as raw JSON in `traces/` and summarized via `scripts/aggregate.py`.
- **Validation Script:** Automated test `scripts/check_consistency.py` exits with status `0`.
