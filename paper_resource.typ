#set page(
  paper: "us-letter",
  margin: (top: 2.2cm, bottom: 2.2cm, left: 2.5cm, right: 2.5cm),
  header: context [
    #if counter(page).get().first() > 1 [
      #align(right)[#text(8pt, fill: luma(120))[ATIF-Gemma: Diagnostic Corpus & Failure Taxonomy for Developer Agents]]
    ]
  ],
  footer: context [
    #let page_number = counter(page).get().first()
    #let total_pages = counter(page).final().first()
    #align(center)[#text(9pt, fill: luma(100))[#page_number of #total_pages]]
  ]
)

#set text(
  font: "Arial",
  size: 10pt,
  lang: "en"
)

#set par(
  justify: true,
  leading: 0.65em,
  first-line-indent: 1.2em
)

// ==============================================================================
// TITLE PAGE (APA 7th / IEEE Format)
// ==============================================================================
#v(1.8cm)
#align(center)[
  #text(18pt, weight: "bold")[ATIF-Gemma: An Open Empirical Diagnostic Corpus\ and Failure Taxonomy for Small Open-Weight Developer Agents]
  
  #v(0.8cm)
  #text(12pt, weight: "bold")[Karandeep Singh Sodhi] \
  #v(0.15cm)
  #text(10.5pt, style: "italic")[Independent Researcher] \
  #v(0.15cm)
  #text(9.5pt)[karandeep.sodhi2504a\@gmail.com]
  
  #v(0.6cm)
  #text(10pt, fill: luma(100))[October 27, 2026]
  
  #v(0.3cm)
  #text(9pt, weight: "bold", fill: rgb("#1A73E8"))[Track: Google --- The Gemma 4 Developer Agent Competition (Paper Track: Best New Resource)]
]

#v(2.2cm)
#line(length: 100%, stroke: 0.5pt + luma(180))
#v(0.3cm)
#align(left)[
  #text(10.5pt, weight: "bold")[Author Note & Resource Manifest] \
  #v(0.2cm)
  #set text(size: 9.2pt)
  #set par(first-line-indent: 0pt, leading: 0.6em)
  Karandeep Singh Sodhi is an independent researcher.

  *Open Research Resource:* All 112 full-fidelity execution traces formatted in Agent Trajectory Interchange Format (ATIF v1.7), ground-truth reference specifications, metadata index, diagnostic validation scripts, and the companion `atif_gemma` Python package are openly released on Kaggle and GitHub under the Creative Commons Attribution 4.0 International (CC BY 4.0) license.

  *Kaggle Dataset:* https://www.kaggle.com/datasets/karandeepsinghsodhi/atif-gemma-swe-agent-traces \
  *GitHub Repository:* https://github.com/KarandeepSinghSodhi/gemma-sfd-agent \
  *Interactive Kernel:* https://www.kaggle.com/code/karandeepsinghsodhi/atif-gemma-diagnostic-exploration

  *Disclosures:* The author declares no competing financial or non-financial interests.

  *Correspondence:* Correspondence concerning this article should be addressed to Karandeep Singh Sodhi, Email: karandeep.sodhi2504a\@gmail.com.
]

#pagebreak()

// ==============================================================================
// PAGE 2: ABSTRACT & KEYWORDS
// ==============================================================================
#v(0.3cm)
#rect(width: 100%, stroke: 0.5pt + luma(180), fill: luma(250), radius: 3pt, inset: 12pt)[
  #text(10pt, weight: "bold")[Abstract] \
  #v(3pt)
  #set text(size: 9.2pt)
  #set par(first-line-indent: 0pt)
  Current software engineering (SWE) agent benchmarks report scalar pass/fail resolution rates, obscuring the multi-stage dynamics of agent failure. For small, quantized open-weight models such as Gemma 4 E4B, understanding why agents plateau at low resolution rates (median 5.0% across 197 teams on the official Small Model Prize leaderboard) is hindered by a complete absence of publicly available, fine-grained execution trace data. We introduce *ATIF-Gemma*, an open empirical diagnostic corpus of 112 full-fidelity multi-turn execution traces comprising 1,518 LLM calls, 1,328 tool invocations, and 11,706,178 logged tokens generated across 32 paired SWE-bench tasks on 4x NVIDIA L4 GPUs inside the official Google ADK and `swegemma` execution harness.
  
  #v(3pt)
  Formatted in the Agent Trajectory Interchange Format (ATIF v1.7), ATIF-Gemma cross-references final agent patches and localized file targets against author ground-truth patches and held-out test suites. We establish an empirical 4-way Phase 2 exit code failure taxonomy: while 92.0% of runs (103/112) successfully synthesize a non-empty patch, 32.1% (36/112) exit with collection/import errors (`exit_code = 2`) due to sandbox dependency absences, global virtual environment shadowing, and detached syntax blocks; 50.0% (56/112) exit with test assertion failures (`exit_code = 1`) due to partial localization or imprecise edits; 8.0% (9/112) produce no patch due to budget exhaustion (`exit_code = -1`); 2.7% (3/112) experience verification timeouts (`exit_code = 124`); and 7.1% (8/112) achieve full resolution (`exit_code = 0`). Furthermore, we release an Actionable Remediation Playbook and the pip-installable `atif_gemma` diagnostic Python toolkit, providing the developer agent research community with an empirical foundation to diagnose and eliminate failure modes in small open-weight coding agents.
]

#v(0.2cm)
#text(9pt)[*Keywords:* agent trajectory corpus, SWE-bench, Gemma 4, failure taxonomy, ATIF v1.7, open-weight agents, error diagnostics, remediation playbook]

#v(0.4cm)

= 1. Introduction & The Diagnostic Vacuum in SWE Benchmarking

Autonomous software engineering agents powered by large language models have achieved notable progress on repository-level repair benchmarks such as SWE-bench @jimenez2024swebench. However, benchmarking in this domain remains almost universally *outcome-centric*: evaluations report a single scalar accuracy metric (the proportion of tasks resolved), discarding the rich, high-dimensional trajectory of decisions, tool calls, token expansions, and environmental interactions that preceded the outcome.

For frontier models (e.g. Claude 3.5 Sonnet, GPT-4o) and large open-weight models (Gemma 4 31B), high resolution rates (22.0%--24.0% on the Google Gemma 4 challenge) allow researchers to treat the agentic loop as an effective black box. In contrast, for compact, 4-bit quantized open-weight models suitable for local developer workstations (such as `gemma-4-e4b-it-qat-w4a16-ct`), scalar benchmarking reveals an acute capability cliff without explaining its origins. Across all $N = 197$ participating teams on the official Small Model Prize leaderboard (ryanholbrook/gemma-4-developer-agent-small-model-leaderboard), public resolution scores range from 0.0% to 10.0%, with a median of exactly 5.0%, a mean of 4.23%, and 183 of 197 teams (92.9%) scoring $<= 6.0%$. 

When an agent fails, developers currently cannot discern whether failure stemmed from:
1. *Upstream Localization Failure*: Did the agent search the wrong directories or read irrelevant modules?
2. *Context Saturation & Syntax Corruption*: Did prompt bloat degrade the model's instruction-following fidelity, causing malformed tool arguments or detached code blocks?
3. *Environmental & Sandbox Artifacts*: Did the patch fail held-out tests due to missing third-party packages in the offline sandbox, or global virtual environment packages shadowing local repository source files?
4. *Tool Exhaustion*: Did the agent exhaust its global turn, time, or tool limits before applying an edit?

To bridge this diagnostic gap, we introduce *ATIF-Gemma*, an open, standardized, full-fidelity diagnostic trajectory corpus and software toolkit for small open-weight developer agents. We provide 112 complete execution traces totaling 11,706,178 tokens, 1,518 LLM turns, and 1,328 tool invocations collected on real 4x NVIDIA L4 GPUs across 32 unique benchmark tasks, structured under the Agent Trajectory Interchange Format (ATIF v1.7).

#v(0.3cm)
= 2. Related Work: Trajectory Corpora & Agent Diagnostics

Autonomous software engineering agents have been evaluated primarily through outcome-focused benchmarks. Understanding the failure mechanics of small open-weight agents intersects three bodies of literature:

== 2.1 Software Engineering Agent Trajectory Datasets
SWE-bench @jimenez2024swebench established the standard benchmark for evaluating language models on real-world repository issue resolution. SWE-agent @yang2024sweagent introduced dedicated Agent-Computer Interfaces (ACIs), demonstrating that specialized shell commands improve model interaction. OpenHands @wang2024openhands provided an extensible multi-agent development environment. To unify diverse agent execution formats, the Agent Trajectory Interchange Format (ATIF v1.7) was developed as a standardized JSON schema capturing multi-turn tool invocations, stdout/stderr observations, and token metrics across disparate agent frameworks. 

However, existing public trajectory corpora focus almost exclusively on proprietary frontier models (e.g. Claude 3.5 Sonnet, GPT-4o) running in unconstrained environments with massive 128k--200k context windows [CITATION NEEDED]. These traces do not reflect the acute context constraints, quantization noise, or local offline sandbox execution characteristics of edge developer setups. To our knowledge, *ATIF-Gemma is the first open empirical trajectory corpus specifically documenting small, 4-bit quantized open-weight agents (`gemma-4-e4b-it-qat-w4a16-ct`) operating within the official Google ADK and `swegemma` execution harness.*

== 2.2 SWE Agent Failure Analyses & Context Bottlenecks
Prior diagnostic studies on large language model agents have highlighted the fragility of multi-turn deliberation. Xia et al. @xia2024agentless introduced *Agentless*, demonstrating that complex autonomous loops often degrade performance relative to streamlined two-phase localization and repair pipelines. Lindenbauer et al. @lindenbauer2025complexity demonstrated the "complexity trap" in agent context management: accumulating unpruned tool observations rapidly bloats prompt context, degrading reasoning fidelity. 

While these studies characterize frontier closed models, small open-weight models suffer from acute failure modes: fragile instruction-following under context bloat, syntax corruption during patch generation, and discretionary sub-agent delegation failure. ATIF-Gemma provides the first step-level empirical data quantifying these phenomena in small models.

== 2.3 Small Open-Weight Developer Agents
The Gemma 4 family @gemma2026team introduced compact open-weight models optimized for local developer workstations, including 4-bit quantized checkpoints (`gemma-4-e4b-it-qat-w4a16-ct`). While small models demonstrate strong performance on isolated code completion benchmarks [CITATION NEEDED], multi-turn repository repair exposes a severe capability cliff. On the official Gemma 4 Developer Agent challenge (ryanholbrook/gemma-4-developer-agent-small-model-leaderboard), the median resolution rate across 197 participating teams is 5.0%, with 92.9% of teams scoring $<= 6.0%$. Prior to ATIF-Gemma, researchers lacked the trajectory data needed to distinguish whether this low resolution ceiling stemmed from model reasoning limitations, context exhaustion, or infrastructure collection failures.

#v(0.3cm)
= 3. Corpus Architecture & ATIF v1.7 Schema Specifications

#figure(
  table(
    columns: (2.2fr, 1.1fr, 1.1fr, 1.2fr, 1.2fr, 1.5fr),
    align: (left, center, center, center, center, center),
    stroke: 0.5pt + luma(180),
    fill: (col, row) => if row == 0 { luma(230) } else { none },
    [#strong[Corpus Partition]], [#strong[Traces]], [#strong[Tasks]], [#strong[LLM Calls]], [#strong[Tool Calls]], [#strong[Total Tokens]],
    [Cohort 1 (Canonical Paired)], [24], [8], [304], [265], [2,270,463],
    [Cohort 2 (Stratified Random)], [24], [8], [339], [298], [2,720,322],
    [Cohort 1 Rerun (Reproducibility)], [16], [8], [204], [172], [1,387,758],
    [Cohort 3 (Stratified Disjoint)], [24], [8], [349], [309], [2,771,960],
    [Cohort 4 (Stratified Disjoint)], [24], [8], [322], [284], [2,555,675],
    [#strong[Total ATIF-Gemma Corpus]], [#strong[112]], [#strong[32]], [#strong[1,518]], [#strong[1,328]], [#strong[11,706,178]]
  ),
  caption: [Summary composition of the ATIF-Gemma diagnostic trace corpus across five cohorts on 4x NVIDIA L4 GPUs.]
)

The corpus covers 32 unique SWE-bench instances spanning four major Python repositories: `fastapi` (51 runs), `rich` (37 runs), `requests` (19 runs), and `httpx` (5 runs). All experiments were served using vLLM 0.19.1 under tensor parallel 4 (`tp=4`, 96 GB aggregate VRAM) hosting `gemma-4-e4b-it-qat-w4a16-ct` with Google ADK 1.36.1 and `swegemma`.

Each trace conforms strictly to the *ATIF v1.7 JSON Schema*:
- *Metadata Block*: Records `instance_id`, `repo`, `base_commit`, `agent_config_name`, vLLM sampling parameters (`temperature=0.0`, `seed=42`, `max_output_tokens=8192`, `thinking_budget=1536`), and hardware fingerprints.
- *Step Sequence*: Sequential array of interaction turns containing:
  - `metrics`: Exact per-call `prompt_tokens`, `completion_tokens`, and `total_tokens` reported directly by the vLLM engine.
  - `tool_calls`: Function name, input argument JSON dictionary, and stage author tag (`extra.author`).
  - `observation`: Raw tool execution stdout/stderr response, JSON-parsed error status, and error classification types (`FileEditError`, `CommandError`, `FileReadError`, `BudgetExceeded`).
  - `thought`: Full model reasoning trace emitted within the thinking budget.
- *Final Metrics*: Captures cumulative token counts, total duration in seconds, agent patch string, and Phase 2 test execution exit codes.

#v(0.3cm)
= 4. The 4-Way Phase 2 Exit Code Failure Taxonomy

In SWE-bench, patch verification is executed in an isolated verification sandbox using `pytest`. In ATIF-Gemma, cross-referencing agent traces against Phase 2 test runner outputs reveals that treating unresolved runs as a monolithic failure category conceals fundamentally different failure mechanics. We define an empirical 4-way taxonomy:

#figure(
  table(
    columns: (1.5fr, 1.2fr, 1.2fr, 3.5fr),
    align: (left, center, center, left),
    stroke: 0.5pt + luma(180),
    fill: (col, row) => if row == 0 { luma(230) } else { none },
    [#strong[Category]], [#strong[Exit Code]], [#strong[Count (%)]], [#strong[Empirical Mechanism & Observable Symptoms]],
    [Resolved], [0], [8 (7.1%)], [Patch passes all Phase 2 held-out unit tests with zero regressions.],
    [Assertion Failure], [1], [56 (50.0%)], [Patch syntactically valid and executes under pytest, but fails assertions due to wrong logic or incomplete multi-file edits.],
    [Collection Error], [2], [36 (32.1%)], [Pytest crashes during test collection prior to assertion evaluation (ModuleNotFoundError, SyntaxError, venv shadowing).],
    [Budget / Timeout], [-1], [9 (8.0%)], [Agent exhausted 15 tool calls or 2.5 min wall time; 0 patch characters submitted.],
    [Verification Timeout], [124], [3 (2.7%)], [Verification harness timed out (120s limit) due to daemon process or infinite loop in test runner.]
  ),
  caption: [Empirical Phase 2 exit code distribution across all 112 ATIF-Gemma execution traces.]
)

#v(0.2cm)
#figure(
  image("figures/fig1_exit_codes.svg", width: 95%),
  caption: [Distribution of Phase 2 evaluation outcomes across all 112 ATIF-Gemma runs and individual configurations. Colorblind-safe palette (Okabe-Ito): Green = Resolved (Exit 0), Blue = Test Assertion Fail (Exit 1), Vermilion = Collection/Import Crash (Exit 2), Orange = Budget Exhausted (Exit -1), Purple = Timeout (Exit 124).]
)

== 4.1 Deterministic Mechanism Breakdown of Collection Errors (Exit Code 2: 36 Runs)
A critical diagnostic finding enabled by ATIF-Gemma is that *nearly one-third of all agent runs (36/112 = 32.1%) failed before unit tests could execute*. Deterministic classification across all 36 traces (`analysis/classify_exit2.py`) reveals four distinct failure mechanisms:
1. *Syntactic & Indentation Corruption (13/36 = 36.1%)*: Across 7 tasks (`fastapi_14099`, `fastapi_15280`, `fastapi_15785`, `fastapi_15588`, `fastapi_15589`, `fastapi_14077`, and `rich_3894`), small model patches inserted unindented blocks (e.g. `if` statements with zero indent inside class methods), detached `else:` branches, or unclosed brackets, causing Python to raise `IndentationError` or `SyntaxError` during test module import.
2. *Virtual Environment & Path Shadowing (10/36 = 27.8%)*: On `httpx_3672` (5 runs across all configs) and `fastapi_15661` (5 runs across all configs), environment configuration prevented valid collection. In `httpx_3672`, pre-installed system packages at `/usr/local/lib/python3.12/dist-packages/httpx` shadowed `/workspace/src/httpx`. In `fastapi_15661`, the test patch imported from `scripts.prepare_release`, which failed because `/workspace/scripts` was not included in `PYTHONPATH`.
3. *Missing Sandbox Dependencies (10/36 = 27.8%)*: On 4 tasks (`fastapi_14361`, `fastapi_14371`, `fastapi_14455`, `fastapi_14459`), held-out test patches imported external third-party testing libraries (e.g. `inline_snapshot`, `dirty_equals`) absent from the competition offline wheelhouse, triggering `ModuleNotFoundError` across every evaluated architecture.
4. *Missing New Source Module (3/36 = 8.3%)*: On `rich_3930` (3 runs across starter, controlled, and SFD), the issue specification required creating a new module (`rich/_unicode_data.py`). Because none of the agents created the new module, pytest collection failed with `ModuleNotFoundError: No module named 'rich._unicode_data'`.

== 4.2 Deterministic Sub-Classification of Assertion Failures (Exit Code 1: 56 Runs)
Representing half of the entire corpus (56/112 = 50.0%), Exit Code 1 occurs when the patch is syntactically valid and executes under pytest, but fails unit test assertions. By deterministically comparing the agent's edited source files ($F_("agent")$) against the author's reference patch ($F_("gold")$) in `analysis/subclassify_exit1.py`, we categorize all 56 assertion failures into four precise tiers:
1. *Right-File, Wrong-Logic (24/56 = 42.9%)*: The agent localized the exact target file(s) (where $F_("agent") sect F_("gold") != emptyset$), but the synthesized code modification failed semantic assertions or introduced boundary regressions (e.g. `requests_7502`, `rich_3043`, `requests_7427`, `rich_3471`).
2. *Wrong-File Localization (17/56 = 30.4%)*: The agent modified completely unrelated modules (where $F_("agent") sect F_("gold") = emptyset$). For example, in `fastapi_15589`, the gold patch requires editing `fastapi/dependencies/utils.py`, but the agent modified `fastapi/params.py`.
3. *Partial Multi-File Localization (14/56 = 25.0%)*: The bug spanned multiple repository modules (with $|F_("gold")| > 1$), but the agent modified only a strict subset ($F_("agent") subset F_("gold")$). For instance, in `requests_7505`, the fix required changes across both `models.py` and `sessions.py`, but the model modified only `models.py`.
4. *Empty or Unparsed Patch (1/56 = 1.8%)*: On `fastapi_5624`, the agent submitted zero modified source characters prior to turn termination.

== 4.3 Ground-Truth Resolved Runs
Across the 112 runs, 8 runs successfully resolved held-out tests across 4 distinct tasks:
- `rich_4077`: Resolved by `sfd` (5 tools, 40.3s), `sfd_rerun` (6 tools, 41.8s), and `flat_controlled_rerun` (5 tools, 49.2s).
- `fastapi_9753`: Resolved by `flat_starter` (7 tools, 46.1s).
- `fastapi_14077`: Resolved by both `sfd` (6 tools, 43.9s) and `flat_controlled` (12 tools, 67.5s). In this individual $n=1$ comparison, SFD required 50% fewer tool calls (6 vs 12) and 34.9% faster runtime (43.9s vs 67.5s), though across the full 32 tasks, overall duration differences between architectures are not statistically significant (Wilcoxon $p = 0.4540$).
- `rich_3894`: Resolved by `flat_starter` (3 tools, 26.0s) and `flat_controlled` (5 tools, 30.7s).

#v(0.3cm)
= 5. Quantitative Audit Across Agent Architectures

ATIF-Gemma pairs each task across three distinct agent architectures executing on `gemma-4-e4b-it-qat-w4a16-ct`:

#figure(
  table(
    columns: (2.2fr, 0.8fr, 1.8fr, 1.4fr, 1.5fr, 1.3fr),
    align: (left, center, center, center, center, center),
    stroke: 0.5pt + luma(180),
    fill: (col, row) => if row == 0 { luma(230) } else { none },
    [#strong[Configuration]], [#strong[Runs]], [#strong[Resolved (95% Wilson CI)]], [#strong[Mean Peak $P_t$]], [#strong[Mean Prompt]], [#strong[Mean Duration]],
    [Official Starter (flat_starter)], [32], [2/32 (6.2%) [1.7%, 20.2%]], [13,359.7], [105,817.6], [94.2s],
    [Single-Agent (flat_controlled)], [32], [2/32 (6.2%) [1.7%, 20.2%]], [13,959.0], [118,173.0], [90.8s],
    [State-Filtered Deliberation (sfd)], [32], [2/32 (6.2%) [1.7%, 20.2%]], [10,907.5], [80,375.7], [86.6s],
    [Rerun: flat_controlled], [8], [1/8 (12.5%) [2.2%, 47.1%]], [12,557.5], [93,135.6], [107.4s],
    [Rerun: sfd], [8], [1/8 (12.5%) [2.2%, 47.1%]], [9,306.4], [67,710.1], [96.4s]
  ),
  caption: [Architectural comparison of token consumption, peak prompt lengths, and execution speed across all 112 ATIF-Gemma runs. We define *Mean Peak $P_t$* as $1/N sum_(i=1)^N max_t P_(i,t)$, representing the per-run maximum prompt token length reaching the model context window across turn steps $t$, averaged over all $N$ benchmark runs in the configuration.]
)

== 5.1 Statistical Tests & Resolution Invariance
Across all 32 benchmark tasks, resolution rates are identical (2/32 = 6.25%, 95% Wilson CI [1.73%, 20.15%]) across `flat_starter`, `flat_controlled`, and `sfd`. McNemar's exact two-sided test yields $p = 1.0000$ for all pairwise comparisons ($b = 1, c = 1$ for SFD vs controlled and controlled vs starter; $b = 2, c = 2$ for SFD vs starter). *There is no statistically significant resolution rate advantage for any architecture on this small open-weight model.*

In contrast, the token reduction achieved by SFD's stage isolation is highly statistically significant:
- *Cumulative Prompt Tokens*: SFD consumes 37,797.4 fewer prompt tokens per task than `flat_controlled` (-32.0%, 95% paired bootstrap CI: `[-52,214.6, -23,755.2]`, Wilcoxon signed-rank $p < 0.0001$), with SFD lower on 25 of 32 tasks (78.1%). Compared to `flat_starter`, SFD consumes 25,441.9 fewer prompt tokens (-24.0%, 95% bootstrap CI: `[-42,485.1, -9,031.4]`, Wilcoxon $p = 0.0061$, lower on 24/32 tasks).
- *Peak Prompt Tokens ($P_t$)*: SFD lowers peak prompt size by 3,051.6 tokens (-21.9%, 95% bootstrap CI: `[-4,142.9, -1,968.2]`, Wilcoxon $p < 0.0001$), with SFD lower on 28 of 32 tasks (87.5%).
- *Execution Speed*: Mean wall-clock duration differences (-4.2s vs controlled, -7.7s vs starter) are not statistically significant (Wilcoxon $p = 0.4540$ and $p = 0.4429$).

== 5.2 Rerun Reproducibility & Determinism Audit
To evaluate run-to-run stability under $T=0.0$, Cohort 1 was re-executed independently across 8 tasks x 2 configurations (16 paired runs). Rerun analysis (`analysis/statistical_tests.py`) confirms:
- *Patch Identity*: 14 of 16 runs (87.5%) produced bitwise identical patches (identical SHA-256 patch hashes).
- *Exit Code Agreement*: 12 of 16 runs (75.0%) matched exact Phase 2 exit codes.
- *Token Stability*: Mean absolute token difference across runs was 18,571 tokens, attributable to subtle asynchronous vLLM tensor-parallel micro-batching variations on 4x L4 GPUs.

== 5.3 Sub-Agent Bypassing in the Starter Kit
ATIF-Gemma provides empirical trace evidence of how small models handle discretionary sub-agents. The official starter kit wraps `code_analyzer` as an `AgentTool`. Across all 32 `flat_starter` traces:
- Out of 336 tool invocations, the root agent delegated to `code_analyzer` only *7 times (2.1%)*.
- The model *bypassed `code_analyzer` on 29 of 32 tasks (90.6%)*, opting instead to read large files directly into its primary context.

#v(0.2cm)
#figure(
  image("figures/fig3_delegation_funnel.svg", width: 95%),
  caption: [Sub-agent discretionary delegation breakdown in the official starter kit (`flat_starter`). Small models bypassed `code_analyzer` on 29 of 32 tasks (90.6%), with only 7 delegations out of 336 total tool calls (2.1%).]
)

== 5.4 Cross-Stage Prompt Resets
In `sfd` traces, configuring `include_contents: "none"` on downstream stages resets entry prompts from a mean TriageAgent peak of 10,473.9 tokens (median 9,863.0) down to a mean of 1,536.9 tokens (median 1,503.0) at PatchAgent entry. Across all 32 primary SFD runs, this corresponds to an empirical prompt reset distribution with median 87.43%, mean 81.95%, IQR [75.72%, 89.46%], and range [44.95%, 92.49%], driving the overall 32.0% cumulative prompt token reduction relative to single-agent baselines (mean 80,375.7 vs 118,173.0 tokens, Wilcoxon $p < 0.0001$).

#v(0.2cm)
#figure(
  image("figures/fig2_prompt_resets.svg", width: 95%),
  caption: [Prompt token trajectories across trajectory steps $t$ (mean with 95% bootstrap confidence bands). While monolithic architectures expand prompt context monotonically toward saturation, SFD's stage boundary (`include_contents: "none"`) resets prompt tokens by an empirical mean of 81.95% (median 87.43%).]
)

#v(0.3cm)
= 6. Actionable Remediation Playbook for Developer Agents

A primary contribution of the ATIF-Gemma corpus is converting diagnostic failure classifications into an actionable, production-ready engineering playbook for developers building small coding agents:

#figure(
  table(
    columns: (1.8fr, 1.4fr, 3.2fr),
    align: (left, left, left),
    stroke: 0.5pt + luma(180),
    fill: (col, row) => if row == 0 { luma(230) } else { none },
    [#strong[Failure Mode]], [#strong[Prevalence]], [#strong[Recommended Production Remediation Pattern]],
    [Collection / Import Crash], [36/112 (32.1%)], [Enforce `PYTHONPATH=/workspace/src:/workspace` priority in test execution commands and execute pre-flight dependency imports with `python -c` before running test suites.],
    [Syntax / Diff Corruption], [100 FileEditErrors (64 StringNotFound, 36 Malformed; mean 0.89/run)], [Mandate a strict `python -m py_compile <modified_file>` verification check before calling `submit_patch` to prevent broken indentation or detached blocks.],
    [Wrong-File Localization], [17/112 runs (15.2% overall; 30.4% of Exit 1)], [Introduce a two-way validation loop where Stage 2 verifies that the localized symbol exists in the problem description before executing an edit.],
    [Prompt Bloat / Memory Leak], [32/32 flat runs (100% monotonic accumulation; SFD lowers peak on 28/32 tasks)], [Implement stage-isolated context pruning via `include_contents: "none"` in Google ADK, resetting prompt context by 81.9% mean (87.4% median) across pipeline boundaries.]
  ),
  caption: [Actionable developer agent remediation playbook derived from empirical ATIF-Gemma failure traces.]
)

== 6.1 Post-Hoc Diagnostic Re-Evaluation (Non-Official Harness)
To evaluate the practical efficacy of the proposed remediations, we conducted an offline post-hoc re-evaluation of stored patches (`analysis/remediation_eval.py`, `results/remediation_eval.json`). *Crucially, these results are an offline diagnostic assessment and do not alter the official Phase 2 competition evaluation benchmarks reported in Section 4 and Tables 1–3.*

1. *Pre-Submission `py_compile` Gate*: We tested an automated syntax validation gate against all 13 Exit Code 2 runs exhibiting syntactic corruption (including `fastapi_14099` and `rich_3894`). Across all 13 runs, exactly 0% of the baseline agents executed pre-submission syntax checks. The automated `python -m py_compile` gate successfully intercepts 100% (13/13) of syntax-broken patches prior to calling `submit_patch`. Reporting honestly: intercepting a malformed patch prevents a blind collection crash (Exit Code 2), but does *not* resolve the underlying task without additional agent self-repair turns (resolution remains 0/13 without re-prompting).
2. *`PYTHONPATH` Priority Enforcement*: We audited all 10 environment-shadowed runs on `httpx_3672` and `fastapi_15661`. Prepending repository source paths (`PYTHONPATH=/workspace/src:/workspace`) eliminates the collection import crash caused by site-package shadowing. Full semantic evaluation of the resulting tests requires execution within the offline Linux `swegemma` container; thus, no speculative resolution gains are claimed.

#v(0.3cm)
= 7. The `atif_gemma` Python Package & CLI

Along with the dataset, we release a standalone, pip-installable Python package (`atif-gemma`):
- `atif_gemma.audit`: Automatically parses any ATIF v1.7 trajectory directory, extracting token trajectories, tool error frequencies, and exit-code failure buckets.
- `atif_gemma.taxonomy`: Deterministic classifier for Phase 2 test runner exit codes.
- `atif_gemma.remediation`: Programmatic interface to the Actionable Remediation Playbook.
- `atif-gemma` CLI: Command-line tool providing instant diagnostics:
  ```bash
  python -m atif_gemma.cli audit traces/
  python -m atif_gemma.cli playbook
  ```

#v(0.3cm)
= 8. Limitations & Threats to Validity

To ensure rigorous interpretation of our empirical findings, we explicitly identify six structural limitations:

1. *Task Sample Size ($n = 32$ tasks)*: While stratified across four major repositories, evaluating 32 unique benchmark instances covers approximately 25% of the 129 SWE-bench instances in the competition split. Evaluating the full 129 instances across three paired configurations would require over 500 NVIDIA L4 GPU hours.
2. *Single Model Architecture & Quantization Level*: All 112 traces were generated exclusively on `gemma-4-e4b-it-qat-w4a16-ct` (4-bit INT4 quantization). Behaviors such as 90.6% discretionary sub-agent bypassing, syntax corruption rates, and context sensitivity are specific to this model capacity. Unquantized checkpoints (FP16/BF16) or larger open-weight models (e.g. Gemma 4 31B) may exhibit different failure dynamics.
3. *Repository & Language Diversity*: The corpus is concentrated across four popular Python libraries (`fastapi` 51 runs, `rich` 37 runs, `requests` 19 runs, `httpx` 5 runs). Codebases in statically typed languages (C++, TypeScript, Rust) or repositories using alternative test runners (e.g. `unittest`, `tox`) may exhibit different collection dynamics.
4. *Greedy Sampling & Single Seed ($T = 0.0$, `seed = 42`)*: All evaluations were performed using greedy decoding ($T = 0.0$) with a fixed seed. While our 16-run rerun audit demonstrated 87.5% bitwise patch determinism, minor token variations persist due to asynchronous tensor-parallel micro-batching in vLLM. We did not evaluate stochastic sampling temperatures ($T > 0$), which might alter exploration diversity.
5. *Exit-Code-Level vs. Intra-Step Semantic Analysis*: Our deterministic taxonomy categorizes outcomes based on Phase 2 test runner exit codes and file-level diff overlap ($F_("agent") sect F_("gold")$). While avoiding subjective LLM judgment, this does not capture intra-file semantic reasoning errors or line-by-line edit fidelity.
6. *Harness & Offline Sandbox Specifics*: Evaluations were executed inside the competition's `swegemma` harness on Kaggle's offline Linux container. Environmental artifacts (e.g., missing `inline_snapshot` wheels, dist-packages shadowing) reflect this specific container setup and may not reproduce in online or differently configured developer environments.

#v(0.3cm)
= 9. Conclusion & Resource Availability

ATIF-Gemma establishes an open, reproducible, full-fidelity diagnostic foundation for the small-model coding agent community. By moving beyond scalar pass/fail metrics to an open 112-trace ATIF v1.7 corpus, a 4-way Phase 2 exit code taxonomy, an Actionable Remediation Playbook, and an open diagnostic Python library, this resource enables researchers to target the real bottlenecks of small developer agents: sandbox collection errors, context bloat, and localization drift.

*Dataset URL:* https://www.kaggle.com/datasets/karandeepsinghsodhi/atif-gemma-swe-agent-traces \
*Code Repository:* https://github.com/KarandeepSinghSodhi/gemma-sfd-agent \
*Interactive Exploration Kernel:* https://www.kaggle.com/code/karandeepsinghsodhi/atif-gemma-diagnostic-exploration

#v(0.3cm)
#bibliography("references_gemma.bib", style: "ieee", title: "References")
