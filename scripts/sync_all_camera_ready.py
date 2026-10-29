from pathlib import Path
import subprocess

ROOT = Path("d:/AI Research/gemma_paper")

def update_writeup():
    p = ROOT / "KAGGLE_WRITEUP_RESOURCE.md"
    text = p.read_text(encoding="utf-8")
    
    # Extra trims to reach ~2,910-2,915 words
    trims = [
        # Sec 2.1
        ("Prior work established repository-level repair benchmarks (SWE-bench; Jimenez et al., 2024), agent interfaces (SWE-agent; Yang et al., 2024; OpenHands; Wang et al., 2024; Agentless; Xia et al., 2024), and training resources on real tasks (SWE-Gym; Pan et al., 2024) or synthetic tasks (SWE-smith; Yang et al., 2025). Public Gemma 4 datasets also offer execution traces (Rajak, 2026). ATIF-Gemma complements these resources with an exit-code-level Phase 2 failure taxonomy, suspected-environment attribution, and a rerun determinism audit for compact Gemma 4 agents under version-pinned ATIF v1.7 (Harbor Framework Contributors, 2026).",
         "Prior work established repair benchmarks (SWE-bench; Jimenez et al., 2024), agent interfaces (SWE-agent; Yang et al., 2024; OpenHands; Wang et al., 2024; Agentless; Xia et al., 2024), and training data on real tasks (SWE-Gym; Pan et al., 2024) or synthetic tasks (SWE-smith; Yang et al., 2025). Public Gemma 4 datasets also provide traces (Rajak, 2026). ATIF-Gemma complements these with an exit-code failure taxonomy, suspected-environment attribution, and a rerun audit for compact Gemma 4 agents under version-pinned ATIF v1.7 (Harbor Framework Contributors, 2026)."),

        # Sec 3
        ("**Schema Conformance, Datasheet & Governance (Gebru et al., 2021):** All 112 traces pass formal validation against our version-pinned ATIF v1.7 schema (`dataset_resource/atif_schema_v1_7.json`; Harbor Framework Contributors, 2026; `analysis/validate_atif_schema.py`). Following Gebru et al. (2021; full sheet in `dataset_resource/datasheet.md`):",
         "**Schema Conformance, Datasheet & Governance (Gebru et al., 2021):** All 112 traces pass formal validation against our version-pinned ATIF v1.7 schema (`dataset_resource/atif_schema_v1_7.json`; Harbor Framework Contributors, 2026; `analysis/validate_atif_schema.py`; full sheet in `dataset_resource/datasheet.md`):"),

        # Sec 4 intro
        ("**Cross-Paper Taxonomy Concordance & Scope:** While our companion SFD paper (Sodhi, 2026) evaluated 16 paired tasks (Cohorts 1–2, 48 runs) grouped into three coarse categories, ATIF-Gemma evaluates 32 tasks across 5 cohorts (112 runs) decomposed into exact Phase 2 container exit codes:",
         "**Cross-Paper Taxonomy Concordance & Scope:** While companion SFD (Sodhi, 2026) evaluated 16 paired tasks (48 runs) across three coarse categories, ATIF-Gemma evaluates 32 tasks across 5 cohorts (112 runs) decomposed into exact container exit codes:"),

        # Sec 4.1
        ("1. **Agent Causes (16/36 = 44.4%)**: Syntax/indentation corruption (13/36 across 7 tasks) and missing modules (3/36 on `rich_3930`).\n2. **Environment Causes (20/36 = 55.6%; `env_suspected=True`)**: Path shadowing (10/36 on `httpx_3672`, `fastapi_15661`) and missing sandbox wheels (`inline_snapshot`, `dirty_equals` across 10 runs on 4 tasks). Gold-patch controls (`analysis/gold_patch_control.py`) require offline containers (future work).",
         "1. **Agent Causes (16/36 = 44.4%)**: Syntax corruption (13/36 across 7 tasks) and missing modules (3/36 on `rich_3930`).\n2. **Environment Causes (20/36 = 55.6%; `env_suspected=True`)**: Path shadowing (10/36 on `httpx_3672`, `fastapi_15661`) and missing wheels (`inline_snapshot`, `dirty_equals` on 10 runs across 4 tasks). Gold-patch controls (`analysis/gold_patch_control.py`) require offline containers (future work)."),

        # Sec 5.3
        ("In `flat_starter`, the root agent wraps `code_analyzer` as an `AgentTool`. Across 32 traces:\n- Out of 336 tool calls, the model delegated to `code_analyzer` only **7 times (2.1%)**.\n- The model **bypassed `code_analyzer` on 26 of 32 tasks (81.2%)**, reading files directly into root context (6/32 delegated).",
         "In `flat_starter`, root wraps `code_analyzer` as an `AgentTool`. Across 32 traces:\n- Out of 336 tool calls, the model delegated to `code_analyzer` only **7 times (2.1%)**.\n- The model **bypassed `code_analyzer` on 26 of 32 tasks (81.2%)**, reading files directly into root context (6/32 delegated)."),

        # Sec 5.4
        ("In `sfd`, `include_contents: \"none\"` resets entry prompts from a mean TriageAgent peak of 10,473.9 tokens (median 9,863.0) to 1,536.9 tokens (median 1,503.0) at PatchAgent entry. Across 32 primary runs, this yields an 81.95% mean prompt reset (median 87.43%, IQR [75.72%, 89.46%]), driving the 32.0% prompt reduction over flat baselines ($p < 0.0001$).",
         "In `sfd`, `include_contents: \"none\"` resets entry prompts from a mean TriageAgent peak of 10,473.9 tokens (median 9,863.0) to 1,536.9 tokens (median 1,503.0) at PatchAgent entry. Across 32 primary runs, this yields an 81.95% mean prompt reset (median 87.43%, IQR [75.72%, 89.46%]), driving 32.0% prompt reduction over flat baselines ($p < 0.0001$)."),

        # Table 5
        ("Two-way symbol verification loop (untested) before editing.",
         "Two-way symbol verification loop (untested) prior to edit."),
        ("Stage context pruning (`include_contents: \"none\"`), resetting context 81.9% mean (reduces tokens; no resolution gain observed).",
         "Stage context pruning (`include_contents: \"none\"`), resetting context 81.9% mean (reduces tokens; no resolution gain)."),

        # Sec 8
        ("1. **Task Sample ($n = 32$)**: Covers ~25% of the benchmark (full evaluation requires >500 L4 GPU hours).\n2. **Model & Quantization**: Specific to `gemma-4-e4b-it-qat-w4a16-ct` (INT4); larger checkpoints may differ.\n3. **Repository Scope**: Evaluates 4 Python libraries; runs sharing tasks are paired and clustered.\n4. **Non-Determinism**: Under $T=0.0$, 12/16 exit codes matched on rerun, but edit hashes diverged (drift: 18,571 tokens).\n5. **Structural Proxy**: File overlap ($F_\\text{agent} \\cap F_\\text{gold}$) is an automated proxy; valid alternative patches exist.\n6. **Sandbox Defects (`env_suspected=True`)**: 20 runs failed from container constraints (missing wheels, path shadowing).",
         "1. **Task Sample ($n = 32$)**: Covers ~25% of benchmark (full evaluation requires >500 L4 GPU hours).\n2. **Model & Quantization**: Specific to `gemma-4-e4b-it-qat-w4a16-ct` (INT4); larger models may differ.\n3. **Repository Scope**: Evaluates 4 Python repos; runs sharing tasks are paired and clustered.\n4. **Non-Determinism**: Under $T=0.0$, 12/16 exit codes matched on rerun, but edit hashes diverged (mean drift: 18,571 tokens).\n5. **Structural Proxy**: File overlap ($F_\\text{agent} \\cap F_\\text{gold}$) is an automated proxy; valid alternative patches exist.\n6. **Sandbox Defects (`env_suspected=True`)**: 20 runs failed from container constraints (missing wheels, path shadowing).")
    ]
    
    for old, new in trims:
        if old in text:
            text = text.replace(old, new)
        else:
            print(f"Writeup trim not found: {old[:40]}")
            
    p.write_text(text, encoding="utf-8")
    words = text.split()
    print(f"Updated KAGGLE_WRITEUP_RESOURCE.md: {len(words)} words")


def update_typst():
    p = ROOT / "paper_resource.typ"
    text = p.read_text(encoding="utf-8")

    # 1. Title and header track
    old_title = '#text(18pt, weight: "bold")[ATIF-Gemma: An Open Empirical Diagnostic Corpus\\\n and Failure Taxonomy for Small Open-Weight Developer Agents]'
    new_title = '#text(18pt, weight: "bold")[ATIF-Gemma: Diagnostic Corpus and Failure Taxonomy\\\n for Small Developer Agents]'
    if old_title in text:
        text = text.replace(old_title, new_title)
    else:
        print("old_title not found")

    old_track = '#text(9pt, weight: "bold", fill: rgb("#1A73E8"))[Track: Google --- The Gemma 4 Developer Agent Competition (Paper Track: Best New Resource)]'
    new_track = '#text(9pt, weight: "bold", fill: rgb("#1A73E8"))[Kaggle Gemma 4 Developer Agent Paper Competition (Target award: Best New Resource)]'
    if old_track in text:
        text = text.replace(old_track, new_track)
    else:
        print("old_track not found")

    # 2. Section 1 Introduction: Re-anchor opening
    old_intro = """Autonomous software engineering agents powered by large language models have advanced rapidly on repository-level repair benchmarks such as SWE-bench @jimenez2024swebench. However, evaluation in this domain remains almost universally *outcome-centric*: benchmarks report a single scalar accuracy metric (the proportion of tasks resolved), discarding the rich, high-dimensional trajectory of decisions, tool calls, token expansions, and environmental interactions that preceded the outcome.

For large frontier models and massive open-weight models, high resolution rates allow researchers to treat the agentic loop as an effective black box. In contrast, for compact, 4-bit quantized open-weight models suitable for local developer workstations (such as `gemma-4-e4b-it-qat-w4a16-ct`), scalar benchmarking reveals an acute capability cliff without explaining its origins. Across all $N = 197$ participating teams on the official Small Model Prize leaderboard @holbrook2026leaderboard, public resolution scores range from 0.0% to 10.0%, with a median of 5.0%, a mean of 4.23%, and 183 of 197 teams (92.9%) scoring $<= 6.0%$. """

    new_intro = """Unlike single-turn code generation benchmarks (HumanEval; @chen2021codex; MBPP; @austin2021mbpp), SWE-bench established repository-level issue resolution for end-to-end coding agents (@jimenez2024swebench). Reported resolution rates depend strongly on benchmark split, model scale, and agent harness. Although agent interfaces and architectures have advanced (@yang2024sweagent; @wang2024openhands; @xia2024agentless), aggregate pass/fail rates alone provide limited insight into multi-turn execution failures.

On the competition split, compact edge models (such as 4-bit quantized `gemma-4-e4b-it-qat-w4a16-ct`) plateaued below 10% (median 5.0% across 197 teams on the official Small Model Prize leaderboard; @holbrook2026leaderboard; 183 of 197 teams scoring $<= 6.0%$). Scalar benchmarking reveals this capability cliff without explaining its operational origins."""

    if old_intro in text:
        text = text.replace(old_intro, new_intro)
    else:
        print("old_intro not found")

    # 3. Section 2.1 & 2.2: SWE-Gym real vs SWE-smith synthetic, Rajak softened, Lindenbauer
    old_rw1 = """Large-scale trajectory datasets (such as Nebius SWE-agent traces, SWE-Gym @pan2024swegym, and SWE-smith @yang2025swesmith) and Gemma-specific collections (50 multi-turn trajectories; @rajak2026tfd) provide valuable execution evidence at scale."""
    new_rw1 = """Large-scale trajectory datasets on real repository tasks (SWE-Gym; @pan2024swegym) or synthetically synthesized tasks (SWE-smith; @yang2025swesmith), alongside Gemma-specific trajectory collections (@rajak2026tfd), provide valuable execution evidence at scale."""
    if old_rw1 in text:
        text = text.replace(old_rw1, new_rw1)
    else:
        print("old_rw1 not found")

    old_rw2 = """Lindenbauer et al. @lindenbauer2025complexity demonstrated the "complexity trap" in agent context management: accumulating unpruned tool observations rapidly bloats prompt context, degrading reasoning fidelity. """
    new_rw2 = """Lindenbauer et al. @lindenbauer2025complexity demonstrated that simple observation masking is as efficient as LLM summarization for managing context in developer agents, avoiding the "complexity trap" of bloated prompts. """
    if old_rw2 in text:
        text = text.replace(old_rw2, new_rw2)
    else:
        print("old_rw2 not found")

    # 4. Section 3.1: Rule segregation
    old_rule = """- *Data Access & Licensing*: Under Official Competition Rules Section 1.7 and Section 2.4.a.1 (*Data Access and Use*), participants "may access and use the Competition Data for any purpose, whether commercial or non-commercial, including for participating in the Competition and on Kaggle.com forums, and for academic research and education." All evaluated tasks originate from public open-source projects under MIT, Apache-2.0, and BSD-3-Clause licenses (documented in `NOTICE`)."""
    new_rule = """- *Data Access & Licensing*: Under Official Code Competition Rules (`gemma-4-developer-agent`) Section 1.7 and Section 2.4.a.1 (*Data Access and Use*), participants "may access and use the Competition Data for any purpose, whether commercial or non-commercial, including for participating in the Competition and on Kaggle.com forums, and for academic research and education." All evaluated tasks originate from public open-source projects under MIT, Apache-2.0, and BSD-3-Clause licenses (documented in `NOTICE`)."""
    if old_rule in text:
        text = text.replace(old_rule, new_rule)
    else:
        print("old_rule not found")

    # 5. Section 4 Concordance: Strict mapping
    old_conc = """*Cross-Paper Taxonomy Concordance & Scope:* While the companion SFD paper (@sodhi2026sfd) evaluated 16 paired tasks (Cohorts 1–2, 48 runs) grouped into three coarse categories (`resolved`, `test_verification_failed`, `timeout_or_budget_no_patch`), ATIF-Gemma evaluates 32 tasks across 5 cohorts (112 runs) mapped to exact Phase 2 container exit codes: (1) `resolved` maps to Exit 0 (8 pooled, 6 primary); (2) `timeout_or_budget_no_patch` maps to turn-budget exhaustion without patch generation (Exit -1, 9 runs); and (3) `test_verification_failed` maps to pytest collection crashes (Exit 2, 36 runs: 16 agent syntax vs 20 `env_suspected`), assertion failures (Exit 1, 56 runs: Tiers 1–4, including 6 zero-byte runs like `rich_3944` flat_starter), and verification timeouts (Exit 124, 3 runs)."""

    new_conc = """*Cross-Paper Taxonomy Concordance & Scope:* While the companion SFD paper (@sodhi2026sfd) evaluated 16 paired tasks (Cohorts 1–2, 48 runs) grouped into three coarse categories, ATIF-Gemma evaluates 32 tasks across 5 cohorts (112 runs) mapped to exact Phase 2 container exit codes:
- `timeout_or_budget_no_patch` (15 runs) = pre-submission turn/tool budget exhaustion (Exit -1, 9 runs) + zero-byte runs where pytest ran without code edits (Exit 1 Tier 1, 6 runs; e.g. `rich_3944` flat_starter).
- `test_verification_failed` (89 runs) = pytest collection crashes (Exit 2, 36 runs: 16 agent syntax vs 20 `env_suspected`) + non-empty assertion failures (Exit 1 Tiers 2–4, 50 runs) + verification timeouts (Exit 124, 3 runs).
- `resolved` (8 runs) = clean execution passing all unit test assertions without regressions (Exit 0; 6 primary runs, 2 reruns). Total: 15 + 89 + 8 = 112 runs."""

    if old_conc in text:
        text = text.replace(old_conc, new_conc)
    else:
        print("old_conc not found")

    # Table 2: Exit 1 & Exit -1 descriptions
    old_t2_e1 = "[Assertion Failure], [1], [56 (50.0%)], [Patch syntactically valid and executes under pytest, but fails assertions due to wrong logic or incomplete multi-file edits.],"
    new_t2_e1 = "[Assertion Failure], [1], [56 (50.0%)], [Patch applied (or empty zero-byte diff); pytest collected test suite, but >= 1 assertion failed.],"
    if old_t2_e1 in text:
        text = text.replace(old_t2_e1, new_t2_e1)
    else:
        print("old_t2_e1 not found")

    old_t2_em1 = "[Budget / Timeout], [-1], [9 (8.0%)], [Agent exhausted 15 tool calls or 2.5 min wall time; 0 patch characters submitted.],"
    new_t2_em1 = "[Budget / Timeout], [-1], [9 (8.0%)], [Exhausted tool or time budget (`max_tool_calls=15`, `max_turns=20`, `max_time_minutes=2.5`) without generating unified diff (0 patch characters).],"
    if old_t2_em1 in text:
        text = text.replace(old_t2_em1, new_t2_em1)
    else:
        print("old_t2_em1 not found")

    # 6. Section 4.1 MDE: Defensible statement
    old_mde_41 = """While specific resolved tasks differ between configurations, no statistically significant resolution difference is detectable at this sample size (McNemar exact two-sided $p=1.000$; minimum detectable effect size MDE $approx 15-20$ percentage points at $80%$ power, $alpha=0.05$, requiring $>= 4$ net discordant tasks for detection on $N=26$ complete cases)."""
    new_mde_41 = """No statistically significant resolution difference was detected by the exact McNemar tests ($p=1.000$). Given the small number of tasks and low resolution counts, this should not be interpreted as statistical equivalence between architectures."""
    if old_mde_41 in text:
        text = text.replace(old_mde_41, new_mde_41)
    else:
        print("old_mde_41 not found")

    # Section 5.1 MDE
    old_mde_51 = """*No statistically significant resolution difference between agent architectures is detectable at this sample size* (McNemar's exact two-sided test $p = 1.0000$ across all paired comparisons; minimum detectable effect size MDE $approx 15-20$ percentage points at $80%$ power, $alpha = 0.05$). All secondary Wilcoxon comparisons across token metrics reported below are exploratory without multiple-testing adjustment."""
    new_mde_51 = """*No statistically significant resolution difference between agent architectures was detected* (McNemar's exact two-sided test $p = 1.0000$ across all paired comparisons). Given the small sample of tasks and low resolution counts, this indicates lack of statistical power rather than equivalence. All secondary Wilcoxon comparisons across token metrics reported below are exploratory without multiple-testing adjustment."""
    if old_mde_51 in text:
        text = text.replace(old_mde_51, new_mde_51)
    else:
        print("old_mde_51 not found")

    # 7. Section 4.2: List 6 zero-byte runs
    old_zb = """1. *Empty / Zero-Byte Patch (6/56 = 10.7%)*: Evaluated first: $|F_("agent")| = 0$ (`patch_chars = 0`). The agent submitted a 0-byte diff because it either attempted zero source edits (`fastapi_5624`) or edit attempts failed due to `FileEditError` exceptions (`rich_3043`, `rich_3944`, `requests_7502`) or `BudgetExceeded` before edits (`fastapi_14372`, `requests_7315`). Unpatched execution failed assertions (Exit Code 1), differing from Exit Code -1 (where budget exhaustion halted execution before calling `submit_patch`, skipping Phase 2 verification entirely)."""
    new_zb = """1. *Empty / Zero-Byte Patch (6/56 = 10.7%)*: Evaluated first: $|F_("agent")| = 0$ (`patch_chars = 0`). Zero-byte diffs where pytest executed without edits from tool errors (`rich_3043` sfd, `rich_3944` flat_starter, `requests_7502` sfd_rerun), budget limits (`fastapi_14372` flat_starter, `requests_7315` flat_controlled), or unattempted edits (`fastapi_5624` flat_controlled). Unpatched execution failed assertions (Exit Code 1), differing from Exit Code -1 (where budget exhaustion halted execution before calling `submit_patch`, skipping Phase 2 verification entirely)."""
    if old_zb in text:
        text = text.replace(old_zb, new_zb)
    else:
        print("old_zb not found")

    # 8. Section 4.2 tier 3 & Section 5.2 requests_7505
    old_p_mf = """(e.g., in `requests_7505`, modifying `models.py` but omitting `sessions.py`)."""
    new_p_mf = """(e.g., in `requests_7505`, modifying `models.py` but omitting `src/requests/_types.py`)."""
    if old_p_mf in text:
        text = text.replace(old_p_mf, new_p_mf)
    else:
        print("old_p_mf not found")

    old_s52_req = """Both failed unit tests (Exit Code 1, Tier 3) because the task required an unattempted edit in `adapters.py`."""
    new_s52_req = """Both failed unit tests (Exit Code 1, Tier 3) because the task required modifying `src/requests/_types.py` (defining `has_read()`) and multiple call sites in `models.py`."""
    if old_s52_req in text:
        text = text.replace(old_s52_req, new_s52_req)
    else:
        print("old_s52_req not found")

    old_s52_rec = """0 pairs produced bitwise-identical final patches due to context lines and anchor positions."""
    new_s52_rec = """recorded edit sequences diverged in all 16 pairs due to context lines and anchor positions."""
    if old_s52_rec in text:
        text = text.replace(old_s52_rec, new_s52_rec)
    else:
        print("old_s52_rec not found")

    # 9. Repository pinned tag in URL
    old_pdf_url = """*Manuscript PDF:* https://raw.githubusercontent.com/KarandeepSinghSodhi/gemma-sfd-agent/main/paper_resource.pdf"""
    new_pdf_url = """*Manuscript PDF:* https://raw.githubusercontent.com/KarandeepSinghSodhi/gemma-sfd-agent/v1.0.0-camera-ready/paper_resource.pdf"""
    if old_pdf_url in text:
        text = text.replace(old_pdf_url, new_pdf_url)
    else:
        print("old_pdf_url not found")

    p.write_text(text, encoding="utf-8")
    print("Updated paper_resource.typ successfully")

if __name__ == "__main__":
    update_writeup()
    update_typst()
