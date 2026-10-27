import re
from pathlib import Path

p = Path("README.md")
text = p.read_text(encoding="utf-8")

old_table_pat = re.compile(r"\| Configuration \| Resolved \(\$k/n\$\).*?State-Filtered Deliberation.*?89\.4s \|\n", re.DOTALL)
new_table = """| Configuration | Runs | Resolved (95% Wilson CI) | Mean Peak $P_t$ | Mean Cum. Tokens | Mean Duration |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Official Starter (`flat_starter`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 13,359.7 | 105,817.6 | 94.2s |
| **Single-Agent (`flat_controlled`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 13,959.0 | 118,173.0 | 90.8s |
| **State-Filtered Deliberation (`sfd`)** | 32 | 2/32 (6.2%) [1.7%, 20.2%] | 10,907.5 | 80,375.7 | 86.6s |
| **Rerun: `flat_controlled`** | 8 | 1/8 (12.5%) [2.2%, 47.1%] | 12,557.5 | 93,135.6 | 107.4s |
| **Rerun: `sfd`** | 8 | 1/8 (12.5%) [2.2%, 47.1%] | 9,306.4 | 67,710.1 | 96.4s |
"""

old_bullets_pat = re.compile(r"- \*\*Measured Stage-Boundary Context Reset & Paired Peak Reduction.*?execution variance\.\n", re.DOTALL)
new_bullets = """- **Measured Stage-Boundary Context Reset & Peak Reduction ($n = 32$):** Across 32 primary `sfd` trajectories, `TriageAgent` reaches a mean peak prompt of **10,473.9 tokens** (median **9,863.0**), which resets at `PatchAgent` entry (`include_contents: "none"`) to a mean of **1,536.9 tokens** (median **1,503.0**). This corresponds to an empirical reset distribution of median **87.43%**, mean **81.95%**, IQR **[75.72%, 89.46%]**, and range **[44.95%, 92.49%]**. SFD achieves a lower per-task peak prompt length than `flat_controlled` on **28/32 tasks (87.5%)** (Wilcoxon $p < 0.0001$, -21.9% peak prompt reduction) and consumes **-32.0% cumulative prompt tokens** (Wilcoxon $p < 0.0001$, lower on 25/32 tasks).
- **Discretionary `AgentTool` Bypass in `flat_starter` ($n = 32$):** Across all 32 tasks (336 tool invocations), `swe_baseline_agent` invoked `code_analyzer` only **7 times (2.1%)**, completely bypassing `code_analyzer` on **29 of 32 tasks (90.6%)**, opting instead to read large files directly into primary context.
- **Statistical Resolution Invariance & Rerun Determinism:** Resolution rate is invariant at **2/32 (6.25%)** across all three architectures (McNemar $p = 1.0000$). Re-running Cohort 1 ($n=8$, 16 paired runs) demonstrated **87.5% bitwise identical patches** (14/16) and **75.0% exit code agreement** (12/16), confirming that single-run resolution differences at small $n$ are within normal execution variance.
"""

new_text, n_tbl = old_table_pat.subn(new_table, text)
print(f"Table replaced: {n_tbl}")
new_text, n_blt = old_bullets_pat.subn(new_bullets, new_text)
print(f"Bullets replaced: {n_blt}")

p.write_text(new_text, encoding="utf-8")
print("README.md updated successfully.")
