#set page(
  paper: "us-letter",
  margin: (top: 1.8cm, bottom: 1.8cm, left: 2.0cm, right: 2.0cm),
  header: align(right)[
    #text(8pt, fill: luma(120))[
      State-Filtered Deliberation: Stage-Isolated Context Management for Small Open-Weight Software Engineering Agents
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
  size: 9.3pt,
  lang: "en"
)

#set par(
  justify: true,
  leading: 0.54em,
  first-line-indent: 1.1em
)

#v(0.1cm)
#align(center)[
  #text(14pt, weight: "bold")[State-Filtered Deliberation: Stage-Isolated Context Management\ for Small Open-Weight Software Engineering Agents]
  
  #v(0.2cm)
  #text(10.2pt, weight: "bold")[Karandeep Singh Sodhi] \
  #text(8.8pt, fill: luma(80))[Independent Researcher (`https://github.com/KarandeepSinghSodhi/gemma-sfd-agent`)] \
  #text(8.3pt, fill: luma(100))[Submitted to the Gemma 4 Developer Agent Challenge (Paper Track) --- October 2026]
]

#v(0.15cm)

#rect(width: 100%, stroke: 0.5pt + luma(180), fill: luma(250), radius: 3pt, inset: 8pt)[
  #text(9.0pt, weight: "bold")[Abstract] \
  #v(1.5pt)
  #set text(size: 8.5pt)
  Autonomous software engineering (SWE) agents built on small open-weight language models (such as 4-bit quantized Gemma 4 E2B and E4B) face tight context and capability constraints when executing multi-turn debugging trajectories. On the official `gemma-4-developer-agent` benchmark (snapshot stored in `results/leaderboard_snapshot_2026_10_26.json`, retrieved 2026-10-26 UTC), while 31B submissions with fine-tuned LoRA adapters reach public resolution rates of 22.0%--24.0%, all 197 participating teams on the official Small Model Prize leaderboard (`results/small_model_leaderboard_2026_10_24.csv`, updated 2026-10-24 23:58 UTC) score between 0.0% and 10.0%, with a median of 5.0% and 92.9% of teams (183/197) scoring $<= 6.0%$.
  
  We study *State-Filtered Deliberation (SFD)*, a declarative three-stage `SequentialAgent` architecture built on Google's Agent Development Kit (ADK) and the `swegemma` harness. SFD partitions the repair workflow into three role-restricted sub-agents---`TriageAgent` (read-only localization), `PatchAgent` (code editing), and `VerifierAgent` (targeted testing and submission)---and configures `include_contents: "none"` on `PatchAgent` and `VerifierAgent` so that intermediate tool calls and observations from preceding stages are sliced out of the prompt context at stage boundaries while passing structured text state variables (`localization_packet` and `patch_manifest`) through `session.state`. Crucially, SFD deterministically bounds *stage-entry* prompt context rather than total or within-stage peak context (`TriageAgent` itself is not reset). Across a paired evaluation on `gemma-4-e4b-it-qat-w4a16-ct` ($n = 16$ tasks across all four competition repositories on 4x NVIDIA L4 GPUs) against both the official competition starter kit (`flat_starter`, using a discretionary `code_analyzer` `AgentTool`) and an unconfounded single-agent baseline (`flat_controlled`, sharing identical tools, prompts, and sampling parameters), SFD resolves 1/16 tasks (6.2%, 95% Wilson CI [1.1%, 28.3%]) compared to 1/16 (6.2%) for `flat_starter` (McNemar $p = 1.0000$) and 0/16 (0.0%) for `flat_controlled` (McNemar $p = 1.0000$). While SFD resets stage-entry prompts from a mean `TriageAgent` peak of 10922.1 tokens down to 1500.9 tokens at `PatchAgent` entry (a -86.3% peak-to-entry reset) and reduces mean single-call peak prompt tokens across tasks (11291.9 vs. 13029.3 and 13550.8), maximum trajectory peak tokens remain comparable (16146 vs. 15281 and 16154), and SFD's single resolved task (`rich_4077`) is attributable to an accurate one-line fix specification produced during the dedicated triage stage rather than relief from context overflow. All execution traces (`ATIF-v1.7`), leaderboard snapshots, and aggregation scripts are publicly available at `https://github.com/KarandeepSinghSodhi/gemma-sfd-agent`.
]

#v(0.12cm)

= 1. Introduction & Motivating Hypotheses

Repository-level software engineering benchmarks such as SWE-bench (@jimenez2024swebench) evaluate whether language model agents can diagnose bug reports, navigate multi-file codebases, synthesize patches, and pass unit test suites. While frontier models and 31B open-weight models achieve strong resolution rates using iterative ReAct loops (@yao2023react; @yang2024sweagent; @wang2024openhands), deploying autonomous coding agents on local developer workstations requires compact, quantized open-weight models such as the Gemma 4 family (E2B, E4B, 12B, 31B) (@gemma2026team).

Empirical data from the Google Gemma 4 Developer Agent Challenge highlights the severity of this capability gap. In our archived leaderboard snapshots (`results/leaderboard_snapshot_2026_10_26.json`, retrieved 2026-10-26 UTC, and `results/small_model_leaderboard_2026_10_24.csv` from `ryanholbrook/gemma-4-developer-agent-small-model-leaderboard`, updated 2026-10-24 23:58 UTC), the official competition starter baseline running on `gemma-4-31b-it-qat-w4a16-ct` with fine-tuned LoRA adapters achieves a 22.0% (`0.22`) public resolution rate and the top 31B submissions reach 24.0% (`0.24`). By contrast, across all $N = 197$ participating teams on the official Small Model Prize leaderboard (restricted to E2B/E4B models), public resolution scores range from 0.0% (`0.00`) to 10.0% (`0.10`), with a median of 5.0% (`0.05`), a mean of 4.23% (`0.0423`), and 183 of 197 teams (92.9%) scoring $<= 6.0%$ (`0.06`). (Our own full-set competition submission, Ref `#57643078` submitted 2026-10-25 21:22:35 UTC, remained in `SubmissionStatus.PENDING` (`public_score: null`) in the asynchronous evaluation queue at the time of snapshot retrieval on 2026-10-26 UTC.)

We investigate how agent workflow structure and stage-boundary context slicing affect `gemma-4-e4b-it-qat-w4a16-ct` under the competition's declarative Google Agent Development Kit (ADK) and `swegemma` harness. We formulate and test three specific hypotheses:
1. *Prompt-Length Error Correlation Hypothesis (Hypothesis 1):* In multi-turn trajectories, as per-call prompt length $P_t$ increases with accumulated tool observations, we hypothesize that tool call errors (malformed `edit_file` search blocks or invalid arguments) and duplicate file reads occur more frequently. We test this observationally by bucketing all recorded LLM calls by prompt token length $P_t$.
2. *Discretionary Sub-Agent Under-Utilization Hypothesis (Hypothesis 2):* The official competition starter kit (`sample_submission/agent.yaml`) already provides a read-only `code_analyzer` sub-agent wrapped as an `AgentTool` (`skip_summarization: true`) alongside all nine built-in `swegemma` tools on the root `swe_baseline_agent`. Because invoking `code_analyzer` is discretionary, we hypothesize that a 4B model rarely delegates to `code_analyzer` and instead executes exploratory file reads directly inside its root context window.
3. *Stage-Entry Context Reset & Role Partitioning Hypothesis (Hypothesis 3):* Replacing discretionary delegation with a mandatory `SequentialAgent` pipeline (`TriageAgent` $->$ `PatchAgent` $->$ `VerifierAgent`) that sets `include_contents: "none"` on `PatchAgent` and `VerifierAgent` deterministically bounds *stage-entry* prompt length (though not `TriageAgent` or within-stage peak prompt length) and separates localization from code editing.

= 2. Context Mechanics in `swegemma` and Google ADK

== 2.1 Prompt Growth and the Token Signal Ratio
Consider an agent trajectory across LLM calls $t in {1, 2, dots, T}$. Let $P_t$ denote the prompt token count and $C_t$ the completion token count on call $t$. In a continuous single-agent session (`include_contents: "default"`), the prompt at call $t$ concatenates the system instruction $s_0$, the initial harness task prompt $u_0$, and all prior assistant turns $a_i$ and tool observations $o_i$:
$ P_t = |s_0| + |u_0| + sum_(i=1)^(t-1) (|a_i| + |o_i|) $
In the `swegemma` harness, even at call $t=1$, $|s_0| + |u_0|$ spans ~1,900--4,800 tokens because `build_agent_prompt()` embeds the problem statement, budget rules, tool schemas, and up to 200 breadth-first directory tree entries under `/workspace`. Furthermore, `swegemma` configures Google ADK's `EventsCompactionConfig` (`compaction_interval=15`, `token_threshold=14336`, `event_retention_size=5`) to compact long histories after 15 turns.

== 2.2 Exact Stage-Boundary Slicing via `include_contents: "none"` in Google ADK
Inspection of `google-adk==1.36.1` (`google/adk/flows/llm_flows/contents.py` and `functions.py`) establishes the exact runtime behavior when `SequentialAgent` transitions between sub-agents:
- When a sub-agent executes a tool call, `functions.py` records both the `function_call` event and the resulting `function_response` event with `event.author = invocation_context.agent.name`.
- When `include_contents: "none"` is configured on `PatchAgent` (or `VerifierAgent`), `_ContentLlmRequestProcessor` calls `_get_current_turn_contents(branch, session.events, agent.name)`. This function scans `session.events` backward from `len(events) - 1` and stops at the first event where `event.author == "user"` or `_is_other_agent_reply(agent.name, event)` is `True`---which is the *immediately preceding sub-agent's final text emission event* $e_k$.
- `_get_current_turn_contents` slices `session.events[k:]`, excluding `events[:k]` (both `events[0]`, the initial 200-entry workspace layout tree, and all intermediate `function_call`, `function_response`, and thought blocks from earlier stages).
- Crucially, within the active sub-agent's own multi-step loop, all new tool calls and responses (`events[k+1:]`) have `event.author == agent.name`, so the backward scan retains the sub-agent's complete within-stage tool history. Thus, `include_contents: "none"` bounds *stage-entry* prompt length by construction, but does *not* bound within-stage prompt growth if a sub-agent makes many tool calls.

= 3. Architecture & Runtime-Enforced vs. Prompt-Requested Rules

All configurations execute inside `swegemma`, which provides nine built-in tools: `run_command`, `read_file`, `edit_file`, `write_file`, `get_status`, `submit_patch`, and the pre-computed NetworkX AST call-graph and `.npz` symbol-embedding tools `search_similar_code`, `get_code_neighbors`, and `get_code_subgraph`. SFD (`sub_sfd`) chains three sub-agents under a root `SequentialAgent`:
1. *`TriageAgent` (`include_contents: "default"`, `output_key: "localization_packet"`):* Restricted in YAML to five read-only tools (`search_similar_code`, `get_code_neighbors`, `get_code_subgraph`, `read_file`, `get_status`).
2. *`PatchAgent` (`include_contents: "none"`, `output_key: "patch_manifest"`):* Restricted in YAML to four workspace tools (`read_file`, `edit_file`, `write_file`, `get_status`). Interpolates `{problem_description?}` and `{localization_packet?}` via `inject_session_state()`.
3. *`VerifierAgent` (`include_contents: "none"`):* Configured with `run_command`, `read_file`, `edit_file`, `get_status`, and `submit_patch`. Interpolates `{problem_description?}`, `{localization_packet?}`, and `{patch_manifest?}`.

Table 1 separates constraints enforced in code/YAML from behaviors requested only via prompts. Importantly, we did *not* tune or alter the SFD code/YAML design after inspecting evaluation traces.

#figure(
  table(
    columns: (1.5fr, 1.8fr, 1.8fr),
    inset: 4.5pt,
    align: (left, left, left),
    stroke: 0.5pt + luma(180),
    [*Mechanism / Rule*], [*Enforced in Code / YAML Config*], [*Prompt-Requested Only (Unenforced)*],
    [Stage execution & tool separation], [`SequentialAgent` order; per-stage `tools:` lists in `sub_agents/*.yaml`], [Stopping after $<= 3$ tool calls in `TriageAgent` / `PatchAgent`],
    [Cross-stage context reset], [`include_contents: "none"` slices `events[k:]` at stage entry], [Within-stage prompt growth & per-stage tool call count],
    [State packet handoff], [`output_key` writes final text to `session.state`; `{var?}` interpolation], [Formatting text inside `<localization_packet>` / `<patch_manifest>` tags],
    [Observation size caps], [`read_file` $<= 150$ lines / 10k chars; `run_command` stdout $<= 5$k chars], [Reading narrow `start_line`..`end_line` slices],
    [Test & workspace hygiene], [`strip_protected_files_from_patch` strips edits to `tests/*`, `pytest.ini`, `conftest.py`], [Running targeted `pytest` (not bare `pytest`); putting scratch scripts in `/tmp/`],
    [Task session budgets], [Global session caps: `max_tool_calls=15`, `max_turns=20`, `max_time_minutes=2.5`], [Calling `submit_patch` before global budget exhaustion],
  ),
  caption: [Separation between runtime-enforced constraints (`swegemma` / `google-adk`) and prompt-level directives.]
)

= 4. Experimental Setup & Paired Evaluation Results

== 4.1 Hardware, Sampling Design, and Unconfounded Baselines
All experiments were executed on Kaggle's 4x NVIDIA L4 GPU environment (`machine_shape: "NvidiaL4"`, 96 GB total VRAM, `tensor_parallel_size=4`, `vLLM` serving `gemma-4-e4b-it-qat-w4a16-ct` with `max_model_len=32768`, `tool_call_parser="gemma4"`, `reasoning_parser="gemma4"`). Every configuration shares identical generation parameters (`temperature: 0.0`, `seed: 42`, `max_output_tokens: 8192`, `thinking_budget: 1536`, `include_thoughts: true`) and global task budgets (`max_tool_calls: 15`, `max_turns: 20`, `max_time_minutes: 2.5`, `timeout_seconds: 60`, `verification_timeout_seconds: 120`).
The evaluated dataset ($n = 16$ unique tasks, 48 primary paired runs plus 16 rerun reproducibility runs = 64 total `swegemma` runs on 4x L4 GPUs) comprises two disjoint 8-task cohorts stratified across `fastapi/fastapi`, `Textualize/rich`, `psf/requests`, and `encode/httpx`: *Cohort 1* (first $k_r$ tasks per repo in canonical `tasks.jsonl` order, $n = 8$) yielded 1/8 (12.5%) for `sfd` (`rich_4077`), 0/8 (0.0%) for `flat_starter`, and 0/8 (0.0%) for `flat_controlled`; *Cohort 2* (disjoint seeded-random stratified sample using `random.Random(42)`, $n = 8$) yielded 0/8 (0.0%) for `sfd`, 1/8 (12.5%) for `flat_starter` (`fastapi_9753`), and 0/8 (0.0%) for `flat_controlled`.

On each task, we evaluate three configurations back-to-back:
- *`flat_starter`*: Official competition starter kit (`sample_submission/agent.yaml` with `code_analyzer` `AgentTool` and `prompts/system.md`, adapted to `gemma-4-e4b-it-qat-w4a16-ct`).
- *`flat_controlled`*: Single `LlmAgent` with the exact same 9 tools and combined 3-phase prompt instructions as `sfd`, isolating the effect of `SequentialAgent` + `include_contents: "none"` + stage tool partitioning.
- *`sfd`*: Our 3-stage `SequentialAgent` pipeline.

== 4.2 Aggregate Resolution, Patch Failure Split, and Context Metrics
Table 2 reports the aggregate metrics computed by `scripts/aggregate.py` from the ATIF v1.7 traces (`traces/`). To separate budget exhaustion from incorrect code edits, the *Fail: No Patch / Wrong Patch* column explicitly splits unresolved tasks into those that produced no patch due to time/tool budget exhaustion (`timeout_or_budget_no_patch`) versus those that generated a non-empty patch that failed Phase 2 `pytest` verification (`test_verification_failed`). *Mean Peak $P_t$* is the mean across tasks of each task's maximum single-call `prompt_tokens` ($max_t P_t$), while *Max Peak $P_t$* is the maximum single-call `prompt_tokens` across all calls and tasks.

#figure(
  table(
    columns: (1.6fr, 0.85fr, 0.95fr, 0.85fr, 0.85fr, 0.75fr, 0.7fr, 0.85fr, 0.6fr, 0.65fr),
    inset: 4pt,
    align: (left, center, center, center, center, center, center, center, center, center),
    stroke: 0.5pt + luma(180),
    [*Configuration*], [*Resolved*], [*95% Wilson CI*], [*Non-Empty Patch*], [*Fail: No / Wrong Patch*], [*Mean Peak $P_t$*], [*Max Peak $P_t$*], [*Mean Cum. Tokens*], [*Mean Tools*], [*Mean Time*],
  [Official Starter Kit (`agent_tool` pattern)], [1/16 (6.2%)], [[1.1%, 28.3%]], [13/16 (81.2%)], [3 / 12], [13029.3], [15281], [103350.1], [9.9], [97.3s],
  [Controlled Single-Agent (`LlmAgent`)], [0/16 (0.0%)], [[0.0%, 19.4%]], [14/16 (87.5%)], [2 / 14], [13550.8], [16154], [119664.4], [10.5], [92.2s],
  [State-Filtered Deliberation (`SequentialAgent`)], [1/16 (6.2%)], [[1.1%, 28.3%]], [14/16 (87.5%)], [2 / 13], [11291.9], [16146], [88909.5], [11.2], [89.4s],
  ),
  caption: [Paired evaluation results on `gemma-4-e4b-it-qat-w4a16-ct` ($n = 16$ tasks on 4x NVIDIA L4 GPUs). *Mean Tools* reports budget-counted tool calls (`session.state["tool_calls_used"]`).]
)

*Statistical Comparison & Power Considerations:*
- *`sfd` vs. `flat_starter`:* Absolute difference $Delta = -0.00%$, 95% paired bootstrap CI $[-18.75%, +18.75%]$, discordant pairs $(b=1, c=1)$, exact two-sided McNemar $p = 1.0000$.
- *`sfd` vs. `flat_controlled`:* Absolute difference $Delta = +6.25%$, 95% paired bootstrap CI $[-0.00%, +18.75%]$, discordant pairs $(b=1, c=0)$, exact two-sided McNemar $p = 1.0000$.
- *Rerun Reproducibility under `vLLM` Tensor Parallelism (`tp=4`, `temperature=0.0`, `seed=42`):* Rerunning `sfd` ($n=8$) and `flat_controlled` ($n=8$) on Cohort 1 (`traces/rerun_results/`) produced 8/8 (100.0%) and 7/8 (87.5%) `resolved` agreement (`6/8` and `8/8` patch-presence agreement), with a mean absolute peak prompt drift of 2427.2 tokens (max 5292) for `sfd` and 1797.4 tokens (max 4457) for `flat_controlled` due to non-associative parallel GPU reductions. Notably, while `sfd_rerun` again resolved `rich_4077` (1/8), `flat_controlled_rerun` also generated `self.__file.isatty()` and resolved `rich_4077` (1/8), demonstrating that the 1-task difference on `rich_4077` in Run 1 lies within `tp=4` floating-point run-to-run variance.

*Stage-Entry Context Reset vs. Trajectory Peak Context:*
The trace data demonstrate an important distinction between *stage-entry* prompt length and *trajectory-peak* prompt length. Across the `sfd` runs ($n = 16$), `TriageAgent` (which has `include_contents: "default"` and is never reset) reaches a mean peak prompt of *10922.1 tokens* and a maximum of *16146 tokens* (hitting `16,146` on `rich_4076`, `15,605` on `fastapi_14459`, `14,528` on `rich_3944`, `14,454` on `fastapi_15589`, and `14,446` on `requests_7502`). When `SequentialAgent` transitions to `PatchAgent` (`include_contents: "none"`), the entry prompt on `PatchAgent`'s first LLM call drops to a mean of *1500.9 tokens* (max *2126 tokens*)---a *-86.3% cross-boundary peak-to-entry reset* that holds by construction because `_get_current_turn_contents()` slices out prior tool history and `events[0]` and injects only the problem statement and `<localization_packet>`. Similarly, `VerifierAgent` entry resets to a mean of *1470.2 tokens* (max *2165 tokens*) after `PatchAgent` reaches a within-stage mean peak of *5355.9 tokens* (max *12680 tokens*). While this lowers mean single-call peak prompt tokens across tasks by 13.3% vs. `flat_starter` (11291.9 vs. 13029.3) and 16.7% vs. `flat_controlled` (11291.9 vs. 13550.8), SFD does *not* bound trajectory peak prompt length: SFD's maximum peak (16146) is virtually identical to `flat_starter` (15281) and `flat_controlled` (16154), and on tasks such as `requests_7502` (`14,446` vs. `10,436` / `11,238`) and `rich_4076` (`16,146` vs. `12,860` / `14,849`), SFD peaked higher than both baselines.

= 5. Per-Task Trace Analysis, Hypothesis Tests & Failure Audit

#figure(
  table(
    columns: (1.1fr, 1.0fr, 1.5fr, 1.5fr, 1.5fr),
    inset: 4.2pt,
    align: (left, left, left, left, left),
    stroke: 0.5pt + luma(180),
    [*Task ID*], [*Repository*], [*`flat_starter` (Peak $P_t$)*], [*`flat_controlled` (Peak $P_t$)*], [*`sfd` (Peak $P_t$)*],
  [`fastapi\_14099`], [`fastapi/fastapi`], [Fail (test verification failed) (15281)], [Fail (timeout or budget no patch) (13933)], [Fail (test verification failed) (15961)],
  [`fastapi\_14361`], [`fastapi/fastapi`], [Fail (test verification failed) (10191)], [Fail (test verification failed) (15010)], [Fail (test verification failed) (9831)],
  [`fastapi\_14459`], [`fastapi/fastapi`], [Fail (test verification failed) (14820)], [Fail (timeout or budget no patch) (16154)], [Fail (test verification failed) (15605)],
  [`fastapi\_15588`], [`fastapi/fastapi`], [Fail (test verification failed) (13083)], [Fail (test verification failed) (10785)], [Fail (test verification failed) (7291)],
  [`fastapi\_15589`], [`fastapi/fastapi`], [Fail (test verification failed) (14711)], [Fail (test verification failed) (14912)], [Fail (timeout or budget no patch) (14454)],
  [`fastapi\_15661`], [`fastapi/fastapi`], [Fail (test verification failed) (11099)], [Fail (test verification failed) (14445)], [Fail (test verification failed) (7180)],
  [`fastapi\_9753`], [`fastapi/fastapi`], [Pass (11047)], [Fail (test verification failed) (11743)], [Fail (test verification failed) (6469)],
  [`httpx\_3672`], [`encode/httpx`], [Fail (test verification failed) (14736)], [Fail (test verification failed) (13010)], [Fail (test verification failed) (8140)],
  [`requests\_7427`], [`psf/requests`], [Fail (test verification failed) (9747)], [Fail (test verification failed) (15387)], [Fail (test verification failed) (13362)],
  [`requests\_7502`], [`psf/requests`], [Fail (test verification failed) (10436)], [Fail (test verification failed) (11238)], [Fail (test verification failed) (14446)],
  [`requests\_7505`], [`psf/requests`], [Fail (test verification failed) (10800)], [Fail (test verification failed) (12318)], [Fail (test verification failed) (10659)],
  [`rich\_3043`], [`Textualize/rich`], [Fail (test verification failed) (14789)], [Fail (test verification failed) (14820)], [Fail (timeout or budget no patch) (14384)],
  [`rich\_3944`], [`Textualize/rich`], [Fail (timeout or budget no patch) (15175)], [Fail (test verification failed) (15031)], [Fail (test verification failed) (14528)],
  [`rich\_4070`], [`Textualize/rich`], [Fail (timeout or budget no patch) (13298)], [Fail (test verification failed) (14826)], [Fail (test verification failed) (8499)],
  [`rich\_4076`], [`Textualize/rich`], [Fail (test verification failed) (14577)], [Fail (test verification failed) (15083)], [Fail (test verification failed) (16146)],
  [`rich\_4077`], [`Textualize/rich`], [Fail (timeout or budget no patch) (14679)], [Fail (test verification failed) (8117)], [Pass (3716)],
  ),
  caption: [Task-by-task paired outcomes and single-call peak prompt tokens ($max_t P_t$) on `gemma-4-e4b-it-qat-w4a16-ct`.]
)

#figure(
  table(
    columns: (1.1fr, 0.9fr, 0.9fr, 1.25fr, 0.9fr, 0.9fr, 0.9fr),
    inset: 4.2pt,
    align: (left, center, center, center, center, center, center),
    stroke: 0.5pt + luma(180),
    [*Task ID*], [*Triage Entry*], [*Triage Peak*], [*Patch Entry (Reset vs. Peak)*], [*Patch Peak*], [*Verifier Entry*], [*Verifier Peak*],
  [`fastapi\_14099`], [2634], [15961], [1746 (-89.1%)], [4145], [1420], [6860],
  [`fastapi\_14361`], [2477], [9831], [1192 (-87.9%)], [6365], [1260], [2117],
  [`fastapi\_14459`], [2773], [15605], [1804 (-88.4%)], [3633], [1562], [2496],
  [`fastapi\_15588`], [3373], [4979], [1877 (-62.3%)], [7291], [1818], [2333],
  [`fastapi\_15589`], [3083], [14454], [1534 (-89.4%)], [12680], [1588], [1588],
  [`fastapi\_15661`], [2993], [3873], [1505 (-61.1%)], [7180], [1557], [4875],
  [`fastapi\_9753`], [2763], [6469], [1881 (-70.9%)], [3030], [1652], [4976],
  [`httpx\_3672`], [2116], [7842], [1261 (-83.9%)], [5007], [1304], [8140],
  [`requests\_7427`], [2072], [13362], [1326 (-90.1%)], [5891], [1347], [1850],
  [`requests\_7502`], [1914], [14446], [1480 (-89.8%)], [2714], [1427], [3042],
  [`requests\_7505`], [2102], [10659], [1293 (-87.9%)], [2784], [1362], [1812],
  [`rich\_3043`], [2618], [14384], [1388 (-90.4%)], [7650], [1285], [2014],
  [`rich\_3944`], [2892], [14528], [1187 (-91.8%)], [4323], [1255], [2141],
  [`rich\_4070`], [4829], [8499], [2126 (-75.0%)], [5380], [2165], [7542],
  [`rich\_4076`], [2901], [16146], [1212 (-92.5%)], [4816], [1268], [1887],
  [`rich\_4077`], [2903], [3716], [1203 (-67.6%)], [2805], [1254], [1970],
  ),
  caption: [Measured prompt token counts ($P_t$) at stage entry and stage peak across `sfd` runs (`traces/`). Note that *Patch Entry (Reset vs. Peak)* compares `PatchAgent`'s first call against `TriageAgent`'s peak call.]
)

== 5.1 Testing Hypothesis 1: Observational Error Rates by Prompt-Length Bucket
To test whether longer prompts correlate with higher tool error rates in our recorded trajectories, Table 5 groups all LLM calls and tool invocations across the primary configurations (`flat_starter`, `flat_controlled`, `sfd`, 48 runs across $n = 16$ tasks) into four prompt-length buckets ($P_t < 4,000$; $4,000$--$7,999$; $8,000$--$11,999$; and $>= 12,000$ tokens) and reports: (a) overall tool execution error rate (`status == "error"` in the tool observation), (b) `edit_file` failure rate (`FileEditError` or `BudgetExceeded`), and (c) duplicate `read_file` rate (re-reading an identical `(filepath, start_line, end_line)` slice within the same task trajectory).

#figure(
  table(
    columns: (1.2fr, 0.8fr, 0.8fr, 1.2fr, 1.2fr, 1.2fr),
    inset: 4.2pt,
    align: (left, center, center, center, center, center),
    stroke: 0.5pt + luma(180),
    [*Prompt Length Bucket ($P_t$)*], [*LLM Calls*], [*Tool Calls*], [*All Tool Errors*], [*`edit_file` Errors*], [*Duplicate `read_file`*],
  [$<$ 4,000], [155], [138], [19/138 (13.8%)], [4/20 (20.0%)], [6/50 (12.0%)],
  [4,000 - 7,999], [220], [193], [33/193 (17.1%)], [13/38 (34.2%)], [3/102 (2.9%)],
  [8,000 - 11,999], [183], [160], [26/160 (16.2%)], [13/30 (43.3%)], [6/54 (11.1%)],
  [$>=$ 12,000], [85], [72], [14/72 (19.4%)], [7/17 (41.2%)], [5/25 (20.0%)],
  ),
  caption: [Observational tool error, `edit_file` error, and duplicate `read_file` rates across per-call prompt-length buckets ($P_t$).]
)

While `edit_file` failure rates increase from 20.0% (4/20) at $P_t < 4,000$ to 34.2% (13/38) at $4,000$--$7,999$, 43.3% (13/30) at $8,000$--$11,999$, and 41.2% (7/17) at $P_t >= 12,000$ (and all-tool error rates rise from 13.8% at $P_t < 4,000$ to 19.4% at $P_t >= 12,000$), sample sizes in the upper buckets remain modest and higher prompt lengths occur on later trajectory steps where the agent is already struggling with harder tasks or approaching the 15-call budget limit. Thus, while directionally consistent, this observational breakdown is confounded by step index and task difficulty and does not prove a causal context-dilution effect.

== 5.2 Testing Hypothesis 2: Exact Reconciliation of `code_analyzer_agent` Calls in `flat_starter`
Inspection of the `flat_starter` ATIF v1.7 traces confirms Hypothesis 2 and reconciles the budget-counted tool metric in Table 2 with the raw ATIF trace event count:
- In `swegemma`, `session.state["tool_calls_used"]` (reported in Table 2 as *Mean Tools* = 9.9, or *158 budget-counted calls* across 16 tasks, $158 / 16 = 9.875$) increments on workspace, graph, and shell tools (`read_file`, `edit_file`, `write_file`, `run_command`, `search_similar_code`, `get_code_neighbors`, `get_code_subgraph`), including those executed inside the child `code_analyzer_agent`, but does *not* increment on free `submit_patch` calls (`13` calls) or on the parent `AgentTool` wrapper call `code_analyzer_agent(request=...)` itself (`4` calls).
- Specifically, the *176 total ATIF trace `tool_calls` events* in `flat_starter` decompose into: *145 root-agent workspace/graph/shell calls* + *14 child `code_analyzer_agent` calls* (`4` on `requests_7505`, `3` on `rich_4077`, `7` on `requests_7427`, totaling 159 attempted budget-applicable calls, of which *158* incremented `tool_calls_used` and 1 call on `fastapi_14099` was rejected after hitting the `max_tool_calls=15` cap), plus *13 free `submit_patch` calls* + *4 root `code_analyzer_agent` delegation calls* = *176 total trace tool events*.
- Out of `149` non-`submit_patch` tool decisions made by the root `swe_baseline_agent` (`145` direct workspace/graph/shell calls vs. `4` `code_analyzer_agent` delegations), `swe_baseline_agent` delegated to `code_analyzer_agent` only *4/149 times (2.7%)* (`4/176 = 2.3%` of all trace tool events), bypassing `code_analyzer_agent` completely on *13/16 tasks (81.2%)*.

== 5.3 Testing Hypothesis 3: Case Studies (`rich_4077` & `fastapi_9753`) and Audit of Unresolved SFD Tasks
*Why `sfd` resolved `rich_4077` while `flat_starter` and `flat_controlled` (Run 1) failed, and why `flat_starter` resolved `fastapi_9753`:*
- On `rich_4077` (Cohort 1, adding `isatty()` to `FileProxy` in `rich/file_proxy.py`): `flat_starter` spent all 15 budget-counted tool calls running commands and reading files (`14,679` peak prompt tokens) without ever calling `edit_file` (`0` patch chars). `flat_controlled` (Run 1) localized `rich/file_proxy.py` in 6 calls at its lowest peak prompt (`8,117` tokens), but wrote `import os` and `return os.isatty(self.__file.fileno())`, which fails Phase 2 `pytest` verification when the wrapped file object does not expose an integer file descriptor. In `sfd`, `TriageAgent` read `rich/file_proxy.py` (`3,716` peak prompt tokens) and wrote `<localization_packet>` explicitly specifying `def isatty(self) -> bool: return self.__file.isatty()`; `PatchAgent` entered at `1,203` tokens and applied that exact 3-line method (`resolved=True`). Moreover, in our rerun reproducibility study (`traces/rerun_results/`), both `sfd_rerun` (`resolved=True`) and `flat_controlled_rerun` (`resolved=True`) generated `self.__file.isatty()`, confirming that `rich_4077` does not fail due to context overflow in single-agent mode.
- On `fastapi_9753` (Cohort 2, supporting `functools.partial` in FastAPI dependencies): `flat_starter` read `fastapi/dependencies/models.py` directly (`9,595` peak prompt tokens) and edited `Dependant._unwrapped_call` to unwrap `isinstance(self.call, functools.partial)` via `return self.call.func` (`resolved=True`). By contrast, `sfd`'s `TriageAgent` (`6,469` peak prompt tokens) localized `fastapi/dependencies/utils.py` instead of `models.py`, and `PatchAgent` merely added an unused `from functools import partial` import (`test_verification_failed`). This illustrates a key trade-off of strict stage isolation: when `TriageAgent` localizes the wrong file (`utils.py` vs. `models.py`), `PatchAgent` (`include_contents: "none"`) starts with only `<localization_packet>` and does not re-explore neighboring modules.

#figure(
  table(
    columns: (0.95fr, 1.35fr, 1.15fr, 2.55fr),
    inset: 4.2pt,
    align: (left, left, left, left),
    stroke: 0.5pt + luma(180),
    [*Task ID*], [*Submitted SFD Patch*], [*Failure Bucket*], [*Trace-Verified Failure Mechanism (`traces/`)*],
  [`fastapi\_14099`], [`fastapi/routing.py` (588 chars)], [`test\_verification\_failed`], [Localized `get_request_handler` in `fastapi/routing.py` (`P_t` peaked at 15,961 during `VerifierAgent`), but inserted an `AsyncExitStack` dependency callback block that broke indentation/control flow and failed generator cleanup tests.],
  [`fastapi\_14361`], [`fastapi/openapi/models.py` (383 chars)], [`test\_verification\_failed`], [Changed `ref: str = Field(alias='$ref')` to `Optional[str] = Field(default=None, alias='$ref')` on `Reference` in `fastapi/openapi/models.py`, but missed updating `$ref` dictionary lookup in `fastapi/openapi/utils.py`.],
  [`fastapi\_14459`], [`fastapi/dependencies/models.py` (783 chars)], [`test\_verification\_failed`], [Replaced list iteration in `Dependant.oauth_scopes` with `set(self.parent_oauth_scopes) | set(self.own_oauth_scopes)`, losing deterministic scope ordering and missing sub-dependency scope propagation in `fastapi/dependencies/utils.py`.],
  [`fastapi\_15588`], [`fastapi/sse.py` (1008 chars)], [`test\_verification\_failed`], [Replaced `_check_id_no_null` with `_check_sse_string` (`\0`, `\n`, `\r`) on `id` and `event`, but omitted `retry` field validation and mismatched exact expected `ValueError` messages.],
  [`fastapi\_15589`], [None (0 chars)], [`timeout\_or\_budget\_no\_patch`], [`TriageAgent` ignored the prompt's $<=$3-call directive and made 10 read-only calls (`P_t` peaked at 14454); `PatchAgent` entered at 1534 tokens, read 6 slices, and hit the global 15-call cap on `edit_file`.],
  [`fastapi\_15661`], [`scripts/add\_latest\_release\_date.py` (660 chars)], [`test\_verification\_failed`], [Rewrote `RELEASE_HEADER_PATTERN` with mandatory escaped parentheses `\\((.*)\\)`, causing `RELEASE_HEADER_PATTERN.match()` to fail (`exit_code=1`, `No release header found`) on undated headers.],
  [`fastapi\_9753`], [`fastapi/dependencies/utils.py` (349 chars)], [`test\_verification\_failed`], [`PatchAgent` only added `from functools import partial` to `fastapi/dependencies/utils.py` without unwrapping `functools.partial` in `Dependant._unwrapped_call` in `fastapi/dependencies/models.py` (whereas `flat_starter` unwrapped `self.call.func` in `models.py` and resolved the task).],
  [`httpx\_3672`], [`src/httpx/\_server.py` (630 chars)], [`test\_verification\_failed`], [Added `self._parser.complete()` and `self._parser.reset()` in `_server.py` and caught `KeyboardInterrupt`, but missed implementing `HTTPParser.keep_alive` and `reset()` in `src/httpx/_parsers.py`.],
  [`requests\_7427`], [`src/requests/utils.py` (471 chars)], [`test\_verification\_failed`], [Modified `proxy_bypass` in `src/requests/utils.py` to strip URL scheme/path via `urlparse`, but missed fixing leading-dot domain boundary matching inside `proxy_bypass_environment`.],
  [`requests\_7502`], [`src/requests/models.py` (581 chars)], [`test\_verification\_failed`], [Replaced `elif isinstance(fp, _SupportsRead):` with `elif hasattr(fp, 'read'):` at line 236 of `models.py`, but missed companion stream-wrapper length/redirect checks in `src/requests/utils.py`.],
  [`requests\_7505`], [`src/requests/models.py` (978 chars)], [`test\_verification\_failed`], [Replaced two `isinstance(data, _SupportsRead)` checks in `models.py` with `hasattr(data, 'read')`, but missed remaining `_SupportsRead` protocol checks in `src/requests/utils.py` and `sessions.py`.],
  [`rich\_3043`], [None (0 chars)], [`timeout\_or\_budget\_no\_patch`], [`TriageAgent` localized `CONSOLE_HTML_FORMAT` in `rich/_export_format.py`, but `PatchAgent` failed 4 consecutive `edit_file` calls (`old_string not found` on triple-quoted HTML template) and `VerifierAgent` submitted a 0-byte diff.],
  [`rich\_3944`], [`rich/\_win32\_console.py` (474 chars)], [`test\_verification\_failed`], [Changed `ctypes.c_char(char.encode())` to `ctypes.c_wchar(char)` in `rich/_win32_console.py`, whereas the bug required fixing style/color handling in `rich/console.py` and `rich/style.py`.],
  [`rich\_4070`], [`rich/logging.py` (967 chars)], [`test\_verification\_failed`], [Deferred `from .traceback import Traceback` inside `RichHandler.emit` in `rich/logging.py`, but `TriageAgent` never localized `rich/console.py`, leaving `from rich.console import Console` import time unreduced.],
  [`rich\_4076`], [`rich/text.py` (467 chars)], [`test\_verification\_failed`], [Removed `strip_control_codes(text)` in `Text.__init__` in `rich/text.py` (`P_t` peaked at 16,146 in `TriageAgent`), breaking control-code stripping tests instead of fixing trailing `end` newline handling.],
  ),
  caption: [Complete task-by-task trace audit of every unresolved `sfd` run ($15/16$ tasks).]
)

= 6. Related Work

*Staged vs. Monolithic SWE Agents.* SWE-agent (@yang2024sweagent) and OpenHands (@wang2024openhands) equip an LLM with an interactive bash/file environment inside a continuous trajectory, whereas Agentless (@xia2024agentless) uses a fixed pipeline of localization and repair without autonomous tool loops. SFD combines tool-using ADK sub-agents with stage-boundary context slicing.

*Observation Masking vs. LLM Summarization.* Lindenbauer et al. (@lindenbauer2025complexity) (*"The Complexity Trap"*, JetBrains Research & TU Munich) show that simple observation masking of older tool outputs halves token costs while matching or outperforming LLM-based trajectory summarization on SWE-bench Verified. SFD's `include_contents: "none"` transition acts as a coarse stage-boundary observation mask.

= 7. Limitations & Threats to Validity

1. *Sample Size and Statistical Power:* At $n = 16$, `sfd` (1/16 = 6.2%) and `flat_starter` (1/16 = 6.2%) tie in resolution rate (McNemar $p = 1.0000$), and the 1-task difference over `flat_controlled` (0/16 = 0.0%) also yields McNemar $p = 1.0000$. Detecting a 10 percentage point paired difference (e.g., 15% vs. 5% with 12% discordant pairs) at 80% power ($alpha = 0.05$, two-sided McNemar test) requires $N approx 115$--$130$ paired tasks (essentially the entire 129-task benchmark).
2. *Confounding of Budget Limits (`max_tool_calls=15`, `max_time_minutes=2.5`) with Context Effects:* As shown in Table 2 and Table 6, 3/16 `flat_starter` runs (`rich_3944`, `rich_4070`, `rich_4077`), 2/16 `flat_controlled` runs (`fastapi_14099`, `fastapi_14459`), and 2/16 `sfd` runs (`fastapi_15589`, `rich_3043`) failed to produce a patch (`timeout_or_budget_no_patch`). Without per-stage code caps on tool calls, global budget exhaustion confounds purely architectural comparisons.
3. *Propagation of Triage Localization Errors Across Isolated Stages:* As demonstrated by `fastapi_9753` (`flat_starter` resolved by editing `models.py`, whereas `sfd` localized `utils.py`) and `rich_4070`, when `TriageAgent` misidentifies the target file or omits a companion module in a multi-file bug, `PatchAgent` receives only `<localization_packet>` and cannot recover from the upstream localization error.

= 8. Conclusion & Reproducibility

We presented and empirically audited State-Filtered Deliberation (SFD) on `gemma-4-e4b-it-qat-w4a16-ct` across 64 real `swegemma` + `vLLM` execution runs ($n = 16$ paired tasks across 3 configurations = 48 primary runs, plus 16 rerun reproducibility runs) on 4x NVIDIA L4 GPUs. Our traces establish three findings: (1) in the official starter kit (`flat_starter`), the 4B model bypassed the discretionary `code_analyzer_agent` on 13/16 tasks (81.2%), invoking it on only 4/149 (2.7%) of root non-`submit_patch` tool decisions; (2) configuring `include_contents: "none"` in a 3-stage `SequentialAgent` deterministically resets *stage-entry* prompt length (`PatchAgent` entry mean 1500.9 tokens vs. `TriageAgent` peak mean 10922.1 tokens, a -86.3% reset) and reduces mean single-call peak prompt tokens by 13.3% vs. `flat_starter` and 16.7% vs. `flat_controlled`, but does *not* bound `TriageAgent` or overall trajectory peak tokens (max 16146 tokens); and (3) end-to-end task resolution on 4-bit quantized E4B (1/16 = 6.2% for `sfd` and `flat_starter` vs. 0/16 = 0.0% for `flat_controlled`, McNemar $p = 1.0000$) shows a null overall resolution difference, remaining bottlenecked by multi-file localization and patch semantics. All 64 execution traces (`traces/`), leaderboard snapshots (`results/`), and scripts (`scripts/`) are publicly available at `https://github.com/KarandeepSinghSodhi/gemma-sfd-agent`.

#v(0.1cm)
#bibliography("references_gemma.bib", style: "apa", title: "References")
