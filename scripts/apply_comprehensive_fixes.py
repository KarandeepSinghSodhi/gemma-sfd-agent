from pathlib import Path

ROOT = Path("d:/AI Research/gemma_paper")
p = ROOT / "KAGGLE_WRITEUP_RESOURCE.md"
text = p.read_text(encoding="utf-8")

# 1. Section 3.1 Datasheet & Governance: Exact quotes and links
pos_ds = text.find("**Schema Conformance, Datasheet & Governance")
pos_ds_end = text.find("---", pos_ds)
assert pos_ds != -1 and pos_ds_end != -1

new_ds = """**Schema Conformance, Datasheet & Governance (Gebru et al., 2021):** All 112 traces pass formal validation against our version-pinned ATIF v1.7 schema (`dataset_resource/atif_schema_v1_7.json`; Harbor Framework Contributors, 2026; `analysis/validate_atif_schema.py`). Following Gebru et al. (2021; full sheet in `dataset_resource/datasheet.md`):
- *Data Access & Licensing*: Under [Official Competition Rules](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/rules) Sections 1.7 & 2.4.a.1, participants *"may access and use the Competition Data for any purpose, whether commercial or non-commercial, including for participating in the Competition and on Kaggle.com forums, and for academic research and education."* All evaluated repository tasks originate from public open-source projects under MIT, Apache-2.0, and BSD-3-Clause licenses (documented in `NOTICE`).
- *Data Security & Derived Labels (Rule 2.4.b.1)*: Under Rule 2.4.b.1, Competition Data may not be redistributed to non-participants. To maintain strict compliance, ATIF-Gemma distributes only model-generated conversation trajectories, tool arguments, and metadata; proprietary evaluation test patches (`test_patch`) are strictly omitted. On the official forum ([Topic 749803](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/749803)), Host Elan Markowitz confirmed: *"Yes, publishing derived labels is okay."* Gold-patch file lists are used solely as internal ground truth to compute derived localization tiers (`analysis/subclassify_exit1.py`) and are not redistributed as competition data. Problem statements in trace step 0 derive from public repository issue descriptions. Traces are licensed under CC BY 4.0; companion code under Apache-2.0.
- *Dual-Submission Allowance (Rule 2.2.b)*: Competition Rule 2.2.b states *"You may select up to two (2) Final Submissions for judging,"* and Host Elan Markowitz explicitly confirmed ([Topic 743255](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/743255)): *"A team can submit at most two write-ups. There is only one submission track, and the judges will determine the eligibility for each prize."* ATIF-Gemma serves as the companion empirical resource to our SFD architecture paper (Sodhi, 2026). While SFD addresses prompt bloat, ATIF-Gemma contributes the diagnostic trace corpus, failure taxonomy, and reproducibility audit.

"""
text = text[:pos_ds] + new_ds + text[pos_ds_end:]

# 2. Section 4: Concordance Note matching exact SFD labels (test_verification_failed) and sample size (n=16 vs n=32)
pos_s4 = text.find("## 4. Failure Taxonomy & Phase 2 Outcome Breakdown")
pos_s4_next = text.find("### Table 2:", pos_s4)
assert pos_s4 != -1 and pos_s4_next != -1

new_s4_intro = """## 4. Failure Taxonomy & Phase 2 Outcome Breakdown

**Cross-Paper Taxonomy Concordance & Scope:** The companion SFD paper (Sodhi, 2026) evaluated the first 16 paired tasks (Cohorts 1–2, 48 runs) focusing on prompt-bloat dynamics, grouping outcomes into three coarse categories (`resolved`, `test_verification_failed`, and `timeout_or_budget_no_patch`). ATIF-Gemma expands coverage to 32 tasks across 5 cohorts (112 runs) and decomposes these coarse categories into exact Phase 2 container exit codes:
1. `resolved` maps to Phase 2 Exit Code 0 (8 runs pooled; 6 in primary 96 runs).
2. `timeout_or_budget_no_patch` maps to turn-budget exhaustion before patch creation (Exit Code -1, 9 runs; 0 patch characters submitted).
3. `test_verification_failed` maps to all failure modes where a patch was tested in the harness: pytest collection crashes (Exit Code 2, 36 runs; partitioned into 16 agent syntax errors vs 20 suspected sandbox defects `env_suspected`), unit test assertion failures (Exit Code 1, 56 runs; partitioned into Tiers 1–4, including 6 zero-byte patches that ran under pytest without edits, such as `rich_3944` flat_starter), and test harness verification timeouts where tests exceeded 120s (Exit Code 124, 3 runs).

In SWE-bench, patch verification runs in an isolated Linux container. The evaluation script returns a discrete exit code summarizing execution:

"""
text = text[:pos_s4] + new_s4_intro + text[pos_s4_next:]

# 3. Section 4.1: MDE derivation
old_s41_text = """No resolution difference is detectable at this sample size (McNemar exact $p=1.000$; MDE $\\approx 15\\text{--}20$ percentage points at $80\\%$ power). Across all 80 valid primary runs, resolution is **6/80 (7.50%, unadjusted 95% CI [3.48%, 15.41%])** (`flat_starter` 2/27, `flat_controlled` 2/27, `sfd` 2/26); pooled across 92 valid runs, resolution is **8/92 (8.70%, unadjusted 95% CI [4.47%, 16.23%])**."""

new_s41_text = """No resolution difference is detectable at this sample size (McNemar exact two-sided $p=1.000$; minimum detectable effect size $\\text{MDE} \\approx 15\\text{--}20$ percentage points at $80\\%$ power, $\\alpha=0.05$, requiring $\\ge 4$ net discordant tasks for detection on $N=26$ complete cases). Across all 80 valid primary runs, resolution is **6/80 (7.50%, unadjusted 95% CI [3.48%, 15.41%])** (`flat_starter` 2/27, `flat_controlled` 2/27, `sfd` 2/26); pooled across 92 valid runs, resolution is **8/92 (8.70%, unadjusted 95% CI [4.47%, 16.23%])**."""

if old_s41_text in text:
    text = text.replace(old_s41_text, new_s41_text, 1)

# 4. Section 5.2: Separate rich_4077 and requests_7505, cite rich_4077_diffs.md, report 10/16 files, 1/16 norm match
pos_52 = text.find("### 5.2 Rerun Reproducibility & Determinism Audit")
pos_53 = text.find("### 5.3 Sub-Agent Bypassing", pos_52)
assert pos_52 != -1 and pos_53 != -1

new_52 = """### 5.2 Rerun Reproducibility & Determinism Audit
Cohort 1 was re-executed across 8 tasks $\\times$ 2 configs (16 paired runs; `analysis/statistical_tests.py`):
- **Exit Code Agreement**: 12/16 runs (75.0%) matched exact Phase 2 exit codes.
- **Patch Presence Agreement**: 14/16 runs (87.5%) agreed on patch generation presence (8/8 in `flat_controlled`, 6/8 in `sfd`). Discordances occurred on `fastapi_15589` (sfd: timeout vs 590-char patch) and `requests_7502` (sfd: 581 chars vs 0 bytes due to edit errors).
- **Normalized Edit-Operation Hash Agreement**: Normalized hashes of recorded edit-operation payloads matched in 0 of 16 rerun pairs (0.0%), indicating substantial run-to-run divergence in recorded edit operations despite greedy decoding ($T=0.0$).
- **Semantic Concordance Across Reruns**:
  - *Successful Resolution Convergence (`rich_4077`)*: All three resolved runs across both configurations (`flat_controlled_rerun`, `sfd_orig`, and `sfd_rerun`) converged to the identical 3-line method logic (`def isatty(self) -> bool: return self.__file.isatty()`), differing only by insertion anchor (after line 18 `fileno()` in `flat_controlled_rerun` and `sfd_orig`; before line 23 `write()` in `sfd_rerun`; full diffs documented in `results/rich_4077_diffs.md`).
  - *Unresolved Edit Concordance (`requests_7505`)*: Across the two `flat_controlled` runs on `requests_7505`, both original and rerun applied the identical single-line guard (`elif isinstance(fp, _SupportsRead): fdata = fp.read()`), differing only because the rerun matched two preceding comment lines in its tool arguments. Both runs failed unit tests (Exit Code 1, Tier 3) because the task required an unattempted edit in `adapters.py`.
  - *Cohort-Wide Concordance*: Across all 16 rerun pairs, 10 pairs (62.5%) touched the identical set of source files; 1 pair (`requests_7505` `flat_controlled`) matched 100% on normalized replacement code; and 0 pairs produced bitwise-identical final patches due to context lines and anchor positions.
- **Exit-Code Flips (4 pairs)**: `rich_4077` (ctrl: 1->0 resolved); `fastapi_15588` (sfd: 1->2); `fastapi_15589` (ctrl: 1->2); `fastapi_15589` (sfd: -1->1).
- **Token Drift**: Mean absolute token difference was **18,571.0 total tokens** between original and rerun pairs.

"""
text = text[:pos_52] + new_52 + text[pos_53:]

# 5. Section 10 References: Full unabbreviated titles with complete links & snapshot
pos_refs = text.find("## 10. References")
assert pos_refs != -1

new_full_refs = """## 10. References

- Austin, J., Odena, A., Nye, M., Bosma, M., Michalewski, H., Dohan, D., ... & Le, Q. (2021). Program Synthesis with Large Language Models. *arXiv:2108.07732*. https://arxiv.org/abs/2108.07732
- Chen, M., Tworek, J., Jun, H., Yuan, Q., Pinto, H. P. D. O., Kaplan, J., ... & Zaremba, W. (2021). Evaluating Large Language Models Trained on Code. *arXiv:2107.03374*. https://arxiv.org/abs/2107.03374
- Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J. W., Wallach, H., Daumé III, H., & Crawford, K. (2021). Datasheets for Datasets. *Communications of the ACM*, 64(12), 86–92.
- Gemma Team. (2026). Gemma 4 Technical Report. *arXiv:2607.02770*. https://arxiv.org/abs/2607.02770
- Harbor Framework Contributors. (2026). Agent Trajectory Interchange Format (ATIF) Specification (v1.7). *GitHub*. https://github.com/laude-institute/harbor
- Holbrook, R. (2026). Google Gemma 4 Developer Agent Competition: Small Model Prize Leaderboard Snapshot. *Kaggle*. https://www.kaggle.com/competitions/gemma-4-developer-agent/leaderboard (Snapshot: `results/small_model_leaderboard_2026_10_24.csv`, accessed October 24, 2026).
- Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., & Narasimhan, K. (2024). SWE-bench: Can Language Models Resolve Real-World GitHub Issues? *ICLR 2024*. https://arxiv.org/abs/2310.06770
- Lindenbauer, T., Slinko, I., Felder, L., Bogomolov, E., & Zharov, Y. (2025). The Complexity Trap: Simple Observation Masking Is as Efficient as LLM Summarization for Agent Context Management. *arXiv:2508.21433*. https://arxiv.org/abs/2508.21433
- Pan, J., Wang, X., Neubig, G., Jaitly, N., Ji, H., Suhr, A., & Zhang, Y. (2024). Training Software Engineering Agents and Verifiers with SWE-Gym. *arXiv:2412.21139*. https://arxiv.org/abs/2412.21139
- Rajak, R. (2026). Gemma 4 TFD Agentic Trajectories & Benchmark: 50 multi-turn SWE-bench trajectories. *Kaggle Datasets*. https://www.kaggle.com/datasets/rajarajak/gemma-4-tfd-agentic-trajectories-benchmark
- Shinn, N., Cassano, F., Berman, E., Gopinath, A., Narasimhan, K., & Yao, S. (2023). Reflexion: Language Agents with Verbal Reinforcement Learning. *NeurIPS 2023*.
- Sodhi, K. S. (2026). State-Filtered Deliberation: Mitigating Multi-Turn Context Bloat in Small Developer Agents. *Kaggle Gemma 4 Developer Agent Paper Competition*. https://github.com/KarandeepSinghSodhi/gemma-sfd-agent/blob/main/KAGGLE_WRITEUP.md (Companion Paper).
- Wang, X., Li, B., Song, Y., Frank, F. F., ... & Neubig, G. (2024). OpenHands: An Open Platform for AI Software Developers as Generalist Agents. *arXiv:2407.16741*. https://arxiv.org/abs/2407.16741
- Xia, C. S., Deng, Y., Dunn, S., & Zhang, L. (2024). Agentless: Demystifying LLM-based Software Engineering Agents. *arXiv:2407.01489*. https://arxiv.org/abs/2407.01489
- Yang, J., Jimenez, C. E., Wettig, A., Lieret, K., Yao, S., Narasimhan, K., & Press, O. (2024). SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering. *NeurIPS 2024*. https://arxiv.org/abs/2405.15793
- Yang, J., Lieret, K., Jimenez, C. E., Pan, J., Wetzel, Q., Chi, J., Yao, S., & Narasimhan, K. (2025). SWE-smith: Scaling Data for Software Engineering Agents. *arXiv:2504.21798*. https://arxiv.org/abs/2504.21798
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. *ICLR 2023*.
"""
text = text[:pos_refs] + new_full_refs

p.write_text(text, encoding="utf-8")
print("Successfully updated KAGGLE_WRITEUP_RESOURCE.md with full references and governance updates")
