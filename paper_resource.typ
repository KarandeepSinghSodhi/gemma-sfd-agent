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
  #text(18pt, weight: "bold")[ATIF-Gemma: Diagnostic Corpus and Failure Taxonomy\ for Small Developer Agents]
  
  #v(0.8cm)
  #text(12pt, weight: "bold")[Karandeep Singh Sodhi] \
  #v(0.15cm)
  #text(10.5pt, style: "italic")[Independent Researcher] \
  #v(0.15cm)
  #text(9.5pt)[karandeep.sodhi2504a\@gmail.com]
  
  #v(0.6cm)
  #text(10pt, fill: luma(100))[October 27, 2026]
  
  #v(0.3cm)
  #text(9pt, weight: "bold", fill: rgb("#1A73E8"))[Kaggle Gemma 4 Developer Agent Paper Competition (Target award: Best New Resource)]
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

  *Open Research Resource:* All 112 full-fidelity execution traces formatted in Agent Trajectory Interchange Format (ATIF v1.7), ground-truth reference specifications, metadata index, diagnostic validation scripts, and the companion `atif_gemma` Python package are openly released on Kaggle and GitHub under the Creative Commons Attribution 4.0 International (CC BY 4.0) license. Embedded third-party repository code and issue descriptions retain their original upstream licenses (MIT, Apache-2.0, and BSD-3-Clause) as specified in the dataset `NOTICE` file. Trajectory traces record agent decisions without disclosing held-out competition test suites (`test_patch` is omitted).

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
  #set text(size: 9.0pt)
  #set par(first-line-indent: 0pt)
  Software engineering (SWE) benchmarks typically report scalar task-resolution rates while discarding multi-turn execution trajectories, obscuring why developer agents fail. For compact 4-bit models (`gemma-4-e4b-it-qat-w4a16-ct`), diagnosing low resolution (median 5.0% across 197 teams on the official Small Model Prize leaderboard; @holbrook2026leaderboard) is hindered by limited public trace data linking small-agent trajectories to systematic failure diagnoses and held-out outcomes. We introduce *ATIF-Gemma*, an open empirical diagnostic corpus of 112 execution traces comprising 1,518 LLM calls, 1,328 tool invocations, and 11,706,178 logged tokens across 32 paired SWE-bench tasks on 4x NVIDIA L4 GPUs using Google ADK and `swegemma`. All evaluated tasks derive from public repositories under permissive open-source licenses (MIT, Apache-2.0, BSD-3-Clause in `NOTICE`; evaluation `test_patch` omitted per data governance rules).
  
  #v(2pt)
  Standardized under ATIF v1.7 (100% schema-validated; @harbor2026atif), ATIF-Gemma cross-references fine-grained actions against held-out outcomes. Across the 26 tasks with valid environments across all configurations, each agent architecture resolved *2/26 tasks (7.69%, 95% Wilson CI [2.14%, 24.14%])*, yielding *6/78 resolved runs overall (7.69%, 95% task-level cluster-bootstrap CI [1.28%, 15.38%])*; across all 96 raw primary runs, resolution is *6/96 (6.25%, 2/32 per configuration, 95% task-level cluster-bootstrap CI [1.04%, 12.50%])*; pooled across 112 runs, resolution is 8/112 (7.14%). We establish a deterministic failure taxonomy: assertion failures (50.0%, 56/112), collection errors (32.1%, 36/112; 55.6% attributed to sandbox defects, flagged `env_suspected`), budget exhaustion (8.0%, 9/112), and verification timeouts (2.7%, 3/112). We release the trace corpus, the `atif_gemma` package, and run-level diagnostic data.
]

#v(0.2cm)
#text(9pt)[*Keywords:* agent trajectory corpus, SWE-bench, Gemma 4, failure taxonomy, ATIF v1.7, open-weight agents, error diagnostics, remediation playbook]

#v(0.4cm)

= 1. Introduction & The Diagnostic Vacuum in SWE Benchmarking

Unlike single-turn code generation benchmarks (HumanEval; @chen2021codex; MBPP; @austin2021mbpp), SWE-bench established repository-level issue resolution for end-to-end coding agents (@jimenez2024swebench). Reported resolution rates depend strongly on benchmark split, model scale, and agent harness. Although agent interfaces and architectures have advanced (@yang2024sweagent; @wang2024openhands; @xia2024agentless), aggregate pass/fail rates alone provide limited insight into multi-turn execution failures.

On the competition split, compact edge models (such as 4-bit quantized `gemma-4-e4b-it-qat-w4a16-ct`) plateaued below 10% (median 5.0% across 197 teams on the official Small Model Prize leaderboard; @holbrook2026leaderboard; 183 of 197 teams scoring $<= 6.0%$). Scalar benchmarking reveals this capability cliff without explaining its operational origins.

When an agent fails, developers currently cannot discern whether failure stemmed from:
1. *Upstream Localization Failure*: Did the agent search incorrect directories or inspect irrelevant modules?
2. *Syntax Degradation*: Did the agent generate malformed tool arguments, unindented blocks, or detached edits?
3. *Context Accumulation & Tool Exhaustion*: Did monotonic prompt growth or tool-call budgets exhaust limits before applying a fix?
4. *Environmental & Sandbox Artifacts*: Did the patch fail held-out tests due to missing third-party packages in the offline sandbox, or global virtual environment packages shadowing local repository source files?

To bridge this diagnostic gap, we introduce *ATIF-Gemma*, an open, standardized, full-fidelity diagnostic trajectory corpus and software toolkit for small open-weight developer agents. We provide 112 complete execution traces totaling 11,706,178 tokens, 1,518 LLM turns, and 1,328 tool invocations collected on real 4x NVIDIA L4 GPUs across 32 unique benchmark tasks, structured under the Agent Trajectory Interchange Format (ATIF v1.7).

#v(0.3cm)
= 2. Related Work: Trajectory Corpora & Agent Diagnostics

Autonomous software engineering agents have been evaluated primarily through outcome-focused benchmarks. Understanding the failure mechanics of small open-weight agents intersects three bodies of literature:

== 2.1 Software Engineering Agent Trajectory Datasets
SWE-bench @jimenez2024swebench established the standard benchmark for evaluating language models on real-world repository issue resolution. SWE-agent @yang2024sweagent introduced dedicated Agent-Computer Interfaces (ACIs), demonstrating that specialized shell commands improve model interaction. OpenHands @wang2024openhands provided an extensible multi-agent development environment. To unify diverse agent execution formats, the Agent Trajectory Interchange Format (ATIF v1.7) was developed as a standardized JSON schema capturing multi-turn tool invocations, stdout/stderr observations, and token metrics across disparate agent frameworks @harbor2026atif. Large-scale trajectory datasets on real repository tasks (SWE-Gym; @pan2024swegym) or synthetically synthesized tasks (SWE-smith; @yang2025swesmith), alongside Gemma-specific trajectory collections (@rajak2026tfd), provide valuable execution evidence at scale. However, systematic analysis linking compact-agent traces to test-collection failures, patch-localization outcomes, and environment-related evaluation defects remains an important diagnostic need. ATIF-Gemma complements large unannotated corpora by providing a dense, paired architectural diagnostic sample on compact 4-bit models (Gemma 4 E4B), featuring a deterministic Phase 2 failure taxonomy with explicit agent versus environment attribution, structural file-localization trees, and verified held-out test outcomes.

== 2.2 SWE Agent Failure Analyses & Context Bottlenecks
Prior diagnostic studies on large language model agents have highlighted the fragility of multi-turn deliberation. Xia et al. @xia2024agentless introduced *Agentless*, demonstrating that complex autonomous loops often degrade performance relative to streamlined two-phase localization and repair pipelines. Lindenbauer et al. @lindenbauer2025complexity demonstrated that simple observation masking is as efficient as LLM summarization for managing context in developer agents, avoiding the "complexity trap" of bloated prompts. 

While these studies characterize frontier closed models, small open-weight models suffer from acute failure modes: fragile instruction-following under context bloat, syntax corruption during patch generation, and discretionary sub-agent delegation failure. ATIF-Gemma provides systematic step-level empirical data quantifying these phenomena in small models.

== 2.3 Small Open-Weight Developer Agents
The Gemma 4 family @gemma2026team introduced compact open-weight models optimized for local developer workstations, including 4-bit quantized checkpoints (`gemma-4-e4b-it-qat-w4a16-ct`). While small models demonstrate strong performance on isolated code completion benchmarks such as HumanEval @chen2021codex and MBPP @austin2021mbpp, multi-turn repository repair exposes a severe capability cliff. On the official Gemma 4 Developer Agent challenge @holbrook2026leaderboard, the median resolution rate across 197 participating teams is 5.0%, with 92.9% of teams scoring $<= 6.0%$. Prior to structured diagnostic analysis, researchers lacked the trace data needed to distinguish whether this low resolution ceiling stemmed from model reasoning limitations, context exhaustion, or infrastructure collection failures.

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
  caption: [Summary composition of the ATIF-Gemma diagnostic trace corpus across five cohorts on 4x NVIDIA L4 GPUs. Note: The 40 cohort entries span 32 unique benchmark tasks; Cohort 1 Rerun re-executes the 8 tasks of Cohort 1 for empirical reproducibility verification.]
)

The corpus covers 32 unique SWE-bench instances spanning four major Python repositories: `fastapi` (51 runs), `rich` (37 runs), `requests` (19 runs), and `httpx` (5 runs). All experiments were served using vLLM 0.19.1 under tensor parallel 4 (`tp=4`, 96 GB aggregate VRAM) hosting `gemma-4-e4b-it-qat-w4a16-ct` with Google ADK 1.36.1 and `swegemma`.

Each trace conforms strictly to the *ATIF v1.7 JSON Schema*:
- *Metadata Block*: Records `instance_id`, `repo`, `base_commit`, `agent_config_name`, vLLM sampling parameters (`temperature=0.0`, `seed=42`, `max_output_tokens=8192`, `thinking_budget=1536`), and hardware fingerprints.
- *Step Sequence*: Sequential array of interaction turns containing:
  - `metrics`: Exact per-call `prompt_tokens`, `completion_tokens`, and `total_tokens` reported directly by the vLLM engine.
  - `tool_calls`: Function name, input argument JSON dictionary, and stage author tag (`extra.author`).
  - `observation`: Raw tool execution stdout/stderr response, JSON-parsed error status, and error classification types (`FileEditError`, `CommandError`, `FileReadError`, `BudgetExceeded`).
  - `message`: Full model response text containing deliberative reasoning emitted within the thinking budget (tagged in `extra.event_type: "thinking"`).
- *Final Metrics*: Captures cumulative token counts (`total_prompt_tokens`, `total_completion_tokens`, `total_tokens`, `total_steps`), total duration in seconds, agent patch string, and Phase 2 test execution exit codes.

All 112 traces in the corpus (100.0%) pass formal validation against our checked-in, version-pinned ATIF v1.7 JSON schema (`dataset_resource/atif_schema_v1_7.json`), derived from the Harbor specification @harbor2026atif. A portable validation audit (`analysis/validate_atif_schema.py`) performs a structural interoperability check across all 1,942 steps, 1,503 deliberative reasoning turns, and 1,328 tool calls.

== 3.1 Dataset Documentation, Datasheet & Governance (Gebru et al., 2021)
Following the *Datasheets for Datasets* standard (@gebru2021datasheets; full datasheet in `dataset_resource/datasheet.md`):
- *Data Access & Licensing*: Under Official Code Competition Rules (`gemma-4-developer-agent`) Section 1.7 and Section 2.4.a.1 (*Data Access and Use*), participants "may access and use the Competition Data for any purpose, whether commercial or non-commercial, including for participating in the Competition and on Kaggle.com forums, and for academic research and education." All evaluated tasks originate from public open-source projects under MIT, Apache-2.0, and BSD-3-Clause licenses (documented in `NOTICE`).
- *Data Security & Derived Labels (Rule 2.4.b.1)*: Under Rule 2.4.b.1, Competition Data may not be redistributed to non-participants. To maintain strict compliance, ATIF-Gemma distributes only model-generated conversation trajectories, tool arguments, and metadata; proprietary evaluation test patches (`test_patch`) are strictly omitted. On the official forum (Topic 749803), Host Elan Markowitz confirmed: *"Yes, publishing derived labels is okay."* Gold-patch file lists are used solely as internal ground truth to compute derived localization tiers (`analysis/subclassify_exit1.py`) and are not redistributed as competition data. Problem statements in trace step 0 derive from public repository issue descriptions. Traces are licensed under CC BY 4.0; companion code under Apache-2.0.
- *Dual-Submission Allowance (Rule 2.2.b)*: Competition Rule 2.2.b states *"You may select up to two (2) Final Submissions for judging,"* and Host Elan Markowitz explicitly confirmed (Topic 743255): *"A team can submit at most two write-ups. There is only one submission track, and the judges will determine the eligibility for each prize."* ATIF-Gemma serves as the companion empirical resource to our SFD architecture paper (@sodhi2026sfd). While SFD addresses prompt bloat, ATIF-Gemma contributes the diagnostic trace corpus, failure taxonomy, and reproducibility audit.

#v(0.3cm)
= 4. Failure Taxonomy & Phase 2 Outcome Breakdown

*Cross-Paper Taxonomy Concordance & Scope:* While the companion SFD paper (@sodhi2026sfd) evaluated 16 paired tasks (Cohorts 1–2, 48 runs) grouped into three coarse categories, ATIF-Gemma evaluates 32 tasks across 5 cohorts (112 runs) mapped to exact Phase 2 container exit codes:
- `timeout_or_budget_no_patch` (15 runs) = pre-submission turn/tool budget exhaustion (Exit -1, 9 runs) + zero-byte runs where pytest ran without code edits (Exit 1 Tier 1, 6 runs; e.g. `rich_3944` flat_starter).
- `test_verification_failed` (89 runs) = pytest collection crashes (Exit 2, 36 runs: 16 agent syntax vs 20 `env_suspected`) + non-empty assertion failures (Exit 1 Tiers 2–4, 50 runs) + verification timeouts (Exit 124, 3 runs).
- `resolved` (8 runs) = clean execution passing all unit test assertions without regressions (Exit 0; 6 primary runs, 2 reruns). Total: 15 + 89 + 8 = 112 runs.

In SWE-bench, patch verification is executed in an isolated verification sandbox using `pytest`. In ATIF-Gemma, cross-referencing agent traces against Phase 2 test runner outputs reveals that treating unresolved runs as a monolithic failure category conceals fundamentally different failure mechanics. We define four principal failure mechanisms---patch/assertion failure, test-collection failure, pre-submission budget exhaustion, and verification timeout---and report successful resolution as a separate outcome:

#figure(
  table(
    columns: (1.5fr, 1.2fr, 1.2fr, 3.5fr),
    align: (left, center, center, left),
    stroke: 0.5pt + luma(180),
    fill: (col, row) => if row == 0 { luma(230) } else { none },
    [#strong[Category]], [#strong[Exit Code]], [#strong[Count (%)]], [#strong[Empirical Mechanism & Observable Symptoms]],
    [Resolved], [0], [8 (7.1%)], [Patch passes all Phase 2 held-out unit tests with zero regressions.],
    [Assertion Failure], [1], [56 (50.0%)], [Patch applied (or empty zero-byte diff); pytest collected test suite, but >= 1 assertion failed.],
    [Collection Error], [2], [36 (32.1%)], [Pytest crashes during test collection prior to assertion evaluation (ModuleNotFoundError, SyntaxError, venv shadowing).],
    [Budget / Timeout], [-1], [9 (8.0%)], [Exhausted tool or time budget (`max_tool_calls=15`, `max_turns=20`, `max_time_minutes=2.5`) without generating unified diff (0 patch characters).],
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
A critical diagnostic finding enabled by ATIF-Gemma is that *nearly one-third of all agent runs (36/112 = 32.1%) failed before unit tests could execute*. Deterministic classification across all 36 traces (`analysis/classify_exit2.py`) separates these failures into agent-attributable versus environment-attributable causes:

1. *Agent-Attributable Collection Failures (16/36 = 44.4%)*:
   - *Syntactic & Indentation Corruption (13/36 = 36.1%)*: Across 7 tasks (e.g., `fastapi_14099`, `rich_3894`), small model patches inserted unindented blocks, detached `else:` branches, or unclosed brackets, causing Python to raise `IndentationError` or `SyntaxError` during test collection.
   - *Missing New Source Module (3/36 = 8.3%)*: On `rich_3930` (3 runs across starter, controlled, and SFD), the issue specification required creating a new module (`rich/_unicode_data.py`). Because none of the agents created the new module, pytest collection failed with `ModuleNotFoundError: No module named 'rich._unicode_data'`.

2. *Environment-Attributable Collection Failures (20/36 = 55.6%; flagged `env_suspected=True`)*:
   - *Virtual Environment & Path Shadowing (10/36 = 27.8%)*: On `httpx_3672` (5 runs) and `fastapi_15661` (5 runs), container configuration prevented valid collection. In `httpx_3672`, system packages at `/usr/local/lib/python3.12/dist-packages/httpx` shadowed `/workspace/src/httpx`. In `fastapi_15661`, the test patch imported from `scripts.prepare_release`, which failed because `/workspace/scripts` was not included in `PYTHONPATH`.
   - *Missing Sandbox Dependencies (10/36 = 27.8%)*: On 4 tasks (`fastapi_14361`, `fastapi_14371`, `fastapi_14455`, `fastapi_14459`), held-out test patches imported external testing libraries (`inline_snapshot`, `dirty_equals`) absent from the offline wheelhouse, triggering `ModuleNotFoundError` across every evaluated architecture.

These collection failures suggest environment defects in these instances. We could not run a gold-patch control because the offline Phase 2 evaluation container was not available locally; executing this oracle control (`analysis/gold_patch_control.py`) remains future work.

Excluding the 20 suspected sandbox defects leaves 92 valid runs: 80 primary runs and 12 reruns. Excluded runs comprise 16 primary runs (lat_starter: 5, lat_controlled: 5, sfd: 6 across Cohorts 1--4) and 4 reruns (lat_controlled_rerun: 2, sfd_rerun: 2 in Cohort 1 Rerun). Among primary runs, 26 tasks have valid outcomes across all three configurations, yielding a complete-case subset of 78 runs. In this paired complete-case subset, each configuration resolved 2/26 tasks (7.69%, 95% Wilson CI [2.14%, 24.14%]), yielding 6/78 resolved runs overall (7.69%, 95% task-level cluster-bootstrap CI [1.28%, 15.38%]). No statistically significant resolution difference was detected by the exact McNemar tests ($p=1.000$). Given the small number of tasks and low resolution counts, this should not be interpreted as statistical equivalence between architectures. Across all 80 primary valid runs, resolution is *6/80 (7.50%, unadjusted run-level 95% CI [3.48%, 15.41%])* (`flat_starter` 2/27, `flat_controlled` 2/27, `sfd` 2/26); pooled across all 92 valid runs, it is *8/92 (8.70%, unadjusted run-level 95% CI [4.47%, 16.23%])*.

== 4.2 Deterministic Sub-Classification of Assertion Failures (Exit Code 1: 56 Runs)
Representing half of the entire corpus (56/112 = 50.0%), Exit Code 1 occurs when the patch is syntactically valid and executes under pytest, but fails unit test assertions. By comparing the agent's edited source files ($F_("agent")$) against the author's reference patch ($F_("gold")$) via a formal mutually exclusive decision tree (`analysis/subclassify_exit1.py`), we assign every run to exactly one tier. Per-run classifications, instance IDs, and `env_suspected` flags are published in `dataset_resource/failure_taxonomy_runs.csv`:

1. *Empty / Zero-Byte Patch (6/56 = 10.7%)*: Evaluated first: $|F_("agent")| = 0$ (`patch_chars = 0`). Zero-byte diffs where pytest executed without edits from tool errors (`rich_3043` sfd, `rich_3944` flat_starter, `requests_7502` sfd_rerun), budget limits (`fastapi_14372` flat_starter, `requests_7315` flat_controlled), or unattempted edits (`fastapi_5624` flat_controlled). Unpatched execution failed assertions (Exit Code 1), differing from Exit Code -1 (where budget exhaustion halted execution before calling `submit_patch`, skipping Phase 2 verification entirely).
2. *Wrong-File Localization (15/56 = 26.8%)*: Evaluated second: $F_("agent") sect F_("gold") = emptyset$ with non-empty diff. The agent modified completely unrelated repository modules (e.g., in `fastapi_15589`).
3. *Partial Multi-File Localization (14/56 = 25.0%)*: Evaluated third: $|F_("gold")| > 1$ and $F_("agent") subset.neq F_("gold")$. The bug spanned multiple repository modules, but the agent modified only a strict subset (e.g., in `requests_7505`, modifying `models.py` but omitting `src/requests/_types.py`).
4. *Right-File, Wrong-Logic (21/56 = 37.5%)*: Evaluated fourth for remaining runs where $F_("agent") sect F_("gold") != emptyset$ with non-empty diff successfully applied. The agent localized the exact target file(s), but the synthesized logic failed semantic unit test assertions (e.g., in `rich_3471`, `requests_7427`).

*Caveat:* Gold-patch file overlap serves as an automated structural proxy; valid alternative engineering implementations may modify different helper abstractions to resolve an issue.

== 4.3 Ground-Truth Resolved Runs & Task-Level Clustering
Across the 112 runs, 8 runs successfully resolved held-out tests across 4 distinct tasks: `rich_4077` (3 runs), `fastapi_9753` (1 run), `fastapi_14077` (2 runs), and `rich_3894` (2 runs). In primary runs ($n=96$), resolutions concentrate on these same 4 tasks (4/32 = 12.5% of tasks resolved at least once; 0/32 tasks resolved across all 3 configurations). Runs sharing tasks are paired and clustered, not independent i.i.d. draws.

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
  caption: [Architectural comparison across all 112 ATIF-Gemma runs. Primary-run resolution rates reflect unadjusted raw outcomes across all 32 tasks, including suspected sandbox defects; complete-case sensitivity analysis on valid runs (2/26 per config, 6/78 overall) is reported in Section 4.1. *Mean Peak $P_t$*: maximum prompt length reaching context across turns $t$. *Mean Prompt*: sum of input prompt tokens across LLM calls.]
)

== 5.1 Statistical Tests & Resolution Invariance
Across all 32 primary tasks, resolution rates show identical marginal counts at 2/32 (6.25%, 95% Wilson CI [1.73%, 20.15%]) across `flat_starter`, `flat_controlled`, and `sfd` (McNemar's exact two-sided test $p = 1.0000$ for all pairs), though the specific tasks resolved differ between architectures. *No statistically significant resolution difference between agent architectures was detected* (McNemar's exact two-sided test $p = 1.0000$ across all paired comparisons). Given the small sample of tasks and low resolution counts, this indicates lack of statistical power rather than equivalence. All secondary Wilcoxon comparisons across token metrics reported below are exploratory without multiple-testing adjustment.

In contrast, the token reduction achieved by SFD's stage isolation is highly statistically significant:
- *Cumulative Prompt Tokens*: SFD consumes 37,797.4 fewer prompt tokens per task than `flat_controlled` (-32.0%, 95% paired bootstrap CI: `[-52,214.6, -23,755.2]`, Wilcoxon signed-rank $p < 0.0001$; lower on 25/32 tasks) and 25,441.9 fewer than `flat_starter` (-24.0%, 95% bootstrap CI: `[-42,485.1, -9,031.4]`, $p = 0.0061$; lower on 24/32 tasks).
- *Peak Prompt Tokens ($P_t$)*: SFD lowers peak prompt size by 3,051.6 tokens vs `flat_controlled` (-21.9%, 95% bootstrap CI: `[-4,142.9, -1,968.2]`, $p < 0.0001$; lower on 28/32 tasks) and by 2,452.2 tokens vs `flat_starter` (-18.4%, 95% bootstrap CI: `[-3,795.9, -1,111.8]`, $p = 0.0008$; lower on 26/32 tasks).
- *Execution Speed*: Mean wall-clock duration differences (-4.2s vs controlled, -7.7s vs starter) are not statistically significant ($p = 0.4540, 0.4429$).

== 5.2 Rerun Reproducibility & Determinism Audit
Cohort 1 was re-executed independently across 8 tasks x 2 configurations (16 paired runs; `analysis/statistical_tests.py`):
- *Exit Code Agreement*: 12 of 16 runs (75.0%) matched exact Phase 2 exit codes.
- *Patch Presence Agreement*: 14 of 16 runs (87.5%) agreed on patch generation presence (8/8 in `flat_controlled`, 6/8 in `sfd`). Discordances: `fastapi_15589` (sfd: timeout vs 590-char patch) and `requests_7502` (sfd: 581 chars vs 0 bytes from edit-tool exceptions).
- *Normalized Edit-Operation Hash Agreement*: Normalized hashes of recorded edit-operation and patch-submission payloads matched in 0 of 16 rerun pairs (0.0%), indicating substantial run-to-run divergence in recorded edit operations despite greedy decoding ($T=0.0$).
- *Semantic Concordance Across Reruns*:
  - *Successful Resolution Convergence (`rich_4077`)*: All three resolved runs across both configurations (`flat_controlled_rerun`, `sfd_orig`, and `sfd_rerun`) converged to the identical 3-line method logic (`def isatty(self) -> bool: return self.__file.isatty()`), differing only by insertion anchor (after line 18 `fileno()` in `flat_controlled_rerun` and `sfd_orig`; before line 23 `write()` in `sfd_rerun`; full diffs documented in `results/rich_4077_diffs.md`).
  - *Unresolved Edit Concordance (`requests_7505`)*: Across both `flat_controlled` runs on `requests_7505`, original and rerun applied the identical single-line guard (`elif isinstance(fp, _SupportsRead): fdata = fp.read()`), differing only because the rerun matched two preceding comment lines in its tool arguments. Both failed unit tests (Exit Code 1, Tier 3) because the task required modifying `src/requests/_types.py` (defining `has_read()`) and multiple call sites in `models.py`.
  - *Cohort-Wide Concordance*: Across all 16 rerun pairs, 10 pairs (62.5%) touched the identical set of source files; 1 pair (`requests_7505` `flat_controlled`) matched 100% on normalized replacement code; and recorded edit sequences diverged in all 16 pairs due to context lines and anchor positions.
- *Exit-Code Flips*: The 4 discordant pairs: (1) `rich_4077` (ctrl: 1->0 resolved); (2) `fastapi_15588` (sfd: 1->2); (3) `fastapi_15589` (ctrl: 1->2); (4) `fastapi_15589` (sfd: -1->1).
- *Token Drift*: Mean absolute token difference was 18,571.0 cumulative total tokens between paired runs ($|"tokens"_("rerun") - "tokens"_("orig")|$ across the 16 pairs), quantifying multi-turn trajectory divergence.

== 5.3 Sub-Agent Bypassing in the Starter Kit
ATIF-Gemma provides empirical trace evidence of how small models handle discretionary sub-agents. The official starter kit wraps `code_analyzer` as an `AgentTool`. Across all 32 `flat_starter` traces:
- Out of 336 tool invocations, the root agent delegated to `code_analyzer` only *7 times (2.1%)*.
- The model *bypassed `code_analyzer` on 26 of 32 tasks (81.2%)*, with only 6 of 32 tasks invoking delegation.

#v(0.2cm)
#figure(
  image("figures/fig3_delegation_funnel.svg", width: 95%),
  caption: [Sub-agent discretionary delegation breakdown in the official starter kit (`flat_starter`). Small models bypassed `code_analyzer` on 26 of 32 tasks (81.2%), with only 7 delegations out of 336 total tool calls (2.1%).]
)

== 5.4 Cross-Stage Prompt Resets
In `sfd` traces, configuring `include_contents: "none"` on downstream stages resets entry prompts from a mean TriageAgent peak of 10,473.9 tokens (median 9,863.0) down to a mean of 1,536.9 tokens (median 1,503.0) at PatchAgent entry. Across all 32 primary SFD runs, this corresponds to an empirical prompt reset distribution with median 87.43%, mean 81.95%, IQR [75.72%, 89.46%], and range [44.95%, 92.49%], driving the overall 32.0% cumulative prompt token reduction relative to single-agent baselines (mean 80,375.7 vs 118,173.0 tokens, Wilcoxon $p < 0.0001$).

#v(0.2cm)
#figure(
  image("figures/fig2_prompt_resets.svg", width: 95%),
  caption: [Prompt token trajectories across trajectory steps $t$ (mean with 95% bootstrap confidence bands). Across all 64 flat baseline runs (32 `flat_starter` + 32 `flat_controlled`), prompt context expanded monotonically at every step because Google ADK context compaction was never triggered under the 15-tool-call operational budget. In contrast, SFD's stage boundary (`include_contents: "none"`) resets prompt tokens by an empirical mean of 81.95% (median 87.43%).]
)

#v(0.3cm)
= 6. Candidate Remediations (Untested Unless Stated)

Converting diagnostic failure classifications into practical engineering patterns provides guidance for compact-agent frameworks:

#figure(
  table(
    columns: (1.8fr, 1.4fr, 3.2fr),
    align: (left, left, left),
    stroke: 0.5pt + luma(180),
    fill: (col, row) => if row == 0 { luma(230) } else { none },
    [#strong[Failure Mode]], [#strong[Prevalence]], [#strong[Candidate Remediation Pattern]],
    [Collection / Path Crash], [36/112 (32.1%)], [Enforce `PYTHONPATH` priority in test execution commands and execute pre-flight dependency imports before running test suites.],
    [Edit-Tool Failures], [100 errors (64 StringNotFound, 36 Malformed)], [Validate edit targets against buffer state and handle failed edits explicitly.],
    [Syntax / Indentation Corruption], [13/112 runs (11.6%)], [Mandate a strict `python -m py_compile <modified_file>` verification check before calling `submit_patch` with autonomous self-repair turns.],
    [Wrong-File Localization], [15/112 runs (13.4% overall; 26.8% of assertion failures)], [Candidate two-way validation loop (untested) where Stage 2 verifies that the localized symbol exists in the problem description before executing an edit.],
    [Unbounded Context Growth], [64/64 flat runs (100% monotonic accumulation)], [Implement stage-isolated context pruning via `include_contents: "none"` in Google ADK, resetting prompt context by 81.9% mean across pipeline boundaries (reduces tokens; no resolution gain observed).]
  ),
  caption: [Candidate developer agent remediation playbook derived from empirical ATIF-Gemma failure traces.]
)

== 6.1 Post-Hoc Diagnostic Re-Evaluation (Non-Official Harness)
We conducted an offline diagnostic assessment of stored patches (`analysis/remediation_eval.py`, `results/remediation_eval.json`). *These offline diagnostic checks do not alter the official competition evaluation benchmarks reported in Section 4 and Tables 1–3.*

1. *Pre-Submission `py_compile` Gate*: We tested an automated syntax validation gate against all 13 Exit Code 2 runs exhibiting syntactic corruption. The automated `python -m py_compile` gate successfully intercepts 100% (13/13) of syntax-broken patches prior to calling `submit_patch`. This serves as a static sanity check confirming the parser catches syntax errors by construction; it does *not* prove autonomous model recovery without self-repair turns (resolution remains 0/13 without re-prompting).
2. *`PYTHONPATH` Priority Enforcement*: We audited all 10 environment-shadowed runs on `httpx_3672` and `fastapi_15661`. Prepending repository source paths (`PYTHONPATH=/workspace/src:/workspace`) is predicted to avoid path-shadowing collection failures across all 10 runs (`httpx_3672`, `fastapi_15661`). Full semantic evaluation of the resulting tests requires execution within the offline Linux container; thus, no speculative resolution gains are claimed.

#v(0.3cm)
= 7. The `atif_gemma` Python Package & CLI

Along with the dataset, we release a standalone Python package (`atif-gemma`) installable directly from GitHub or source:

```bash
# Direct installation via pip from GitHub
pip install git+https://github.com/KarandeepSinghSodhi/gemma-sfd-agent.git

# Or local editable install from a cloned repository
git clone https://github.com/KarandeepSinghSodhi/gemma-sfd-agent.git
cd gemma-sfd-agent
pip install -e .
```

The package provides automated diagnostic modules:
- `atif_gemma.audit`: Parses any ATIF v1.7 trajectory directory, extracting token trajectories, tool error frequencies, and exit-code failure buckets.
- `atif_gemma.taxonomy`: Deterministic classifier for Phase 2 test runner exit codes and localization tiers.
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
3. *Repository Diversity & Clustered Runs*: The corpus is concentrated across four Python libraries (`fastapi`, `rich`, `requests`, `httpx`). Runs across configurations on the same task are paired and clustered, not independent samples.
4. *Trajectory Non-Determinism & Token Drift*: Under greedy decoding ($T=0.0$, `seed=42`), 12/16 exit codes matched on rerun, but no paired workspace edit sequences were byte-identical across the 16 pairs (mean absolute token difference: 18,571.0 cumulative total tokens), reflecting serving-level trajectory divergence.
5. *File-Level Structural Proxy*: Evaluates file overlap ($F_("agent") sect F_("gold")$); valid alternative patches modifying different helper abstractions remain possible.
6. *Harness Environment Failures (`env_suspected=True`)*: 20 runs failed due to offline container constraints (missing wheels and site-package shadowing), demonstrating real-world benchmark friction.

#v(0.3cm)
= 9. Conclusion & Resource Availability

ATIF-Gemma establishes an open, reproducible, full-fidelity diagnostic foundation for the small-model coding agent community. By moving beyond scalar pass/fail metrics to an open 112-trace ATIF v1.7 corpus, a structured failure taxonomy, an Actionable Remediation Playbook, and open diagnostic Python tooling, this resource enables researchers to target the true bottlenecks of small developer agents: sandbox collection errors, context bloat, and localization drift.

*Dataset URL:* https://www.kaggle.com/datasets/karandeepsinghsodhi/atif-gemma-swe-agent-traces \
*Code Repository:* https://github.com/KarandeepSinghSodhi/gemma-sfd-agent \
*Interactive Exploration Kernel:* https://www.kaggle.com/code/karandeepsinghsodhi/atif-gemma-diagnostic-exploration \
*Manuscript PDF:* https://raw.githubusercontent.com/KarandeepSinghSodhi/gemma-sfd-agent/v1.0.0-camera-ready/paper_resource.pdf

#v(0.3cm)
#bibliography("references_gemma.bib", style: "ieee", title: "References")
