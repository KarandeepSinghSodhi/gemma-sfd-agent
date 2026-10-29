from pathlib import Path

typ_path = Path("d:/AI Research/gemma_paper/paper_resource.typ")
text = typ_path.read_text(encoding="utf-8")

# 1. Abstract
old_abs = """each agent architecture resolved *2/26 tasks (7.69%, 95% Wilson CI [2.13%, 24.13%])*, yielding *6/78 resolved runs overall (7.69%, 95% task-level cluster-bootstrap CI [1.28%, 15.38%])*; across all 96 raw primary runs, resolution is *6/96 (6.25%, 2/32 per configuration)*."""

new_abs = """each agent architecture resolved *2/26 tasks (7.69%, 95% Wilson CI [2.14%, 24.14%])*, yielding *6/78 resolved runs overall (7.69%, 95% task-level cluster-bootstrap CI [1.28%, 15.38%])*; across all 96 raw primary runs, resolution is *6/96 (6.25%, 2/32 per configuration, 95% task-level cluster-bootstrap CI [1.04%, 12.50%])*; pooled across 112 runs, resolution is 8/112 (7.14%)."""

assert old_abs in text, "Could not find old_abs"
text = text.replace(old_abs, new_abs)

# 2. Governance
old_gov = """- *Data Security (Rule 2.4.b.1)*: To comply strictly with non-redistribution requirements for competition assets, ATIF-Gemma distributes only model-generated execution trajectories, tool-call arguments, and metadata; proprietary evaluation test patches (`test_patch`) are strictly omitted. Traces are licensed under CC BY 4.0; companion code under Apache-2.0.
- *Dual-Submission Differentiation (Rule 2.2.b)*: Competition Rule 2.2.b and organizers confirm participants may submit up to two final writeups. ATIF-Gemma serves as the companion empirical resource to our architectural investigation of State-Filtered Deliberation (SFD; @sodhi2026sfd). While SFD addresses the prompt-bloat mechanism, ATIF-Gemma contributes the diagnostic trace corpus, failure taxonomy, and reproducibility audit."""

new_gov = """- *Data Security & Derived Labels (Rule 2.4.b.1)*: Under Rule 2.4.b.1, Competition Data may not be redistributed to non-participants. To maintain strict compliance, ATIF-Gemma distributes only model-generated conversation trajectories, tool arguments, and metadata; proprietary evaluation test patches (`test_patch`) are strictly omitted. On the official forum (Topic 749803), Host Elan Markowitz confirmed: *"Yes, publishing derived labels is okay."* Gold-patch file lists are used solely as internal ground truth to compute derived localization tiers (`analysis/subclassify_exit1.py`) and are not redistributed as competition data. Problem statements in trace step 0 derive from public repository issue descriptions. Traces are licensed under CC BY 4.0; companion code under Apache-2.0.
- *Dual-Submission Allowance (Rule 2.2.b)*: Competition Rule 2.2.b states *"You may select up to two (2) Final Submissions for judging,"* and Host Elan Markowitz explicitly confirmed (Topic 743255): *"A team can submit at most two write-ups. There is only one submission track, and the judges will determine the eligibility for each prize."* ATIF-Gemma serves as the companion empirical resource to our SFD architecture paper (@sodhi2026sfd). While SFD addresses prompt bloat, ATIF-Gemma contributes the diagnostic trace corpus, failure taxonomy, and reproducibility audit."""

assert old_gov in text, "Could not find old_gov"
text = text.replace(old_gov, new_gov)

# 3. Section 4 Concordance
idx_s4 = text.find("*Cross-Paper Taxonomy Concordance:*")
assert idx_s4 != -1
end_s4 = text.find("\n\nIn SWE-bench", idx_s4)
assert end_s4 != -1

new_s4 = """*Cross-Paper Taxonomy Concordance & Scope:* While the companion SFD paper (@sodhi2026sfd) evaluated 16 paired tasks (Cohorts 1–2, 48 runs) grouped into three coarse categories (`resolved`, `test_verification_failed`, `timeout_or_budget_no_patch`), ATIF-Gemma evaluates 32 tasks across 5 cohorts (112 runs) mapped to exact Phase 2 container exit codes: (1) `resolved` maps to Exit 0 (8 pooled, 6 primary); (2) `timeout_or_budget_no_patch` maps to turn-budget exhaustion without patch generation (Exit -1, 9 runs); and (3) `test_verification_failed` maps to pytest collection crashes (Exit 2, 36 runs: 16 agent syntax vs 20 `env_suspected`), assertion failures (Exit 1, 56 runs: Tiers 1–4, including 6 zero-byte runs like `rich_3944` flat_starter), and verification timeouts (Exit 124, 3 runs)."""

text = text[:idx_s4] + new_s4 + text[end_s4:]

# 4. Section 4.1 Wilson CI and MDE derivation
old_s41 = """each configuration resolved 2/26 tasks (7.69%, 95% Wilson CI [2.13%, 24.13%]), yielding 6/78 resolved runs overall (7.69%, 95% task-level cluster-bootstrap CI [1.28%, 15.38%]). While specific resolved tasks differ between configurations, no statistically significant resolution difference is detectable at this sample size (McNemar exact two-sided $p=1.000$; minimum detectable effect size MDE $approx 15-20$ percentage points at $80%$ power)."""

new_s41 = """each configuration resolved 2/26 tasks (7.69%, 95% Wilson CI [2.14%, 24.14%]), yielding 6/78 resolved runs overall (7.69%, 95% task-level cluster-bootstrap CI [1.28%, 15.38%]). While specific resolved tasks differ between configurations, no statistically significant resolution difference is detectable at this sample size (McNemar exact two-sided $p=1.000$; minimum detectable effect size MDE $approx 15-20$ percentage points at $80%$ power, $alpha=0.05$, requiring $>= 4$ net discordant tasks for detection on $N=26$ complete cases)."""

assert old_s41 in text, "Could not find old_s41"
text = text.replace(old_s41, new_s41)

# 5. Section 5.2 Concrete Concordance
idx_s52 = text.find("- *Semantic Normalization & Concrete Diff Concordance*:")
assert idx_s52 != -1
end_s52 = text.find("\n- *Exit-Code", idx_s52)
assert end_s52 != -1

new_s52 = """- *Semantic Concordance Across Reruns*:
  - *Successful Resolution Convergence (`rich_4077`)*: All three resolved runs across both configurations (`flat_controlled_rerun`, `sfd_orig`, and `sfd_rerun`) converged to the identical 3-line method logic (`def isatty(self) -> bool: return self.__file.isatty()`), differing only by insertion anchor (after line 18 `fileno()` in `flat_controlled_rerun` and `sfd_orig`; before line 23 `write()` in `sfd_rerun`; full diffs documented in `results/rich_4077_diffs.md`).
  - *Unresolved Edit Concordance (`requests_7505`)*: Across both `flat_controlled` runs on `requests_7505`, original and rerun applied the identical single-line guard (`elif isinstance(fp, _SupportsRead): fdata = fp.read()`), differing only because the rerun matched two preceding comment lines in its tool arguments. Both failed unit tests (Exit Code 1, Tier 3) because the task required an unattempted edit in `adapters.py`.
  - *Cohort-Wide Concordance*: Across all 16 rerun pairs, 10 pairs (62.5%) touched the identical set of source files; 1 pair (`requests_7505` `flat_controlled`) matched 100% on normalized replacement code; and 0 pairs produced bitwise-identical final patches due to context lines and anchor positions."""

text = text[:idx_s52] + new_s52 + text[end_s52:]

typ_path.write_text(text, encoding="utf-8")
print("Successfully updated paper_resource.typ with all r1/r2 revisions")
