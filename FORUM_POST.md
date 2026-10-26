# Why Small Gemma-4 Agents Choke on SWE-Bench & How Slicing Context Cuts Prompt Bloat by 86% [64 Traces & Code]

Hey everyone! 👋

If you've been working on the **Small Model Prize track** (`gemma-4-e4b-it` / `e2b-it`), you've probably noticed how steep the capability cliff is:
- **31B Models**: 22.0% – 24.0% resolution rate
- **Small Model Leaderboard (197 teams)**: Median is **5.0%** (183/197 teams score $\le 6.0\%$)

We just completed an empirical study across **64 paired runs on 4x NVIDIA L4 GPUs** evaluating why small models fail and how architectural context management can help them. 

Here are the 3 biggest practical takeaways from our traces that might help your own agent design:

---

### 1. The Discretionary Sub-Agent Trap (Bypassed 81% of the time)
The official starter kit wraps `code_analyzer` as a sub-agent tool alongside 9 root tools. Because invoking it is discretionary:
- In our paired sample, the 4B model **bypassed `code_analyzer` on 13 out of 16 tasks (81.2%)**.
- Out of 149 non-submit tool decisions, the root agent only delegated **4 times (2.7%)**.
- Instead of using the analyzer, the 4B model directly dumps huge file slices into its root context until it exhausts its budget.

**Takeaway:** Small models do not reliably delegate on their own. Delegation needs to be structurally mandatory.

---

### 2. The 86% Prompt Reset (`include_contents: "none"`)
To solve prompt bloat, we built **State-Filtered Deliberation (SFD)**: a strict 3-stage `SequentialAgent` in Google ADK (`TriageAgent` $\to$ `PatchAgent` $\to$ `VerifierAgent`).

By configuring `include_contents: "none"` on downstream stages:
- **TriageAgent** peaks at a mean of **10,922 tokens** exploring files and call-graphs.
- At **PatchAgent entry**, ADK slices out prior tool observations and injects only `<triage_packet>`, resetting entry prompt to **1,500 tokens (-86.3% reset)**.
- Across 16 paired tasks, this lowered per-task peak prompt length on **13/16 tasks** (sign test $p = 0.0213$) and cut cumulative token burn by **25.7%** ($88,909$ vs $119,664$ tokens).

---

### 3. The Offline Sandbox Gotchas (Why Pytest Fails with Exit Code 2)
In our failure audit of unresolved tasks, we found subtle environment traps in the sandbox:
1. **Missing test packages**: In some FastAPI tasks (e.g. `fastapi_14361`), `test_patch` imports `inline_snapshot`, which is not installed in the offline sandbox, causing pytest collection to exit with `test_exit_code = 2` across all models.
2. **Global venv shadowing**: In HTTPX tasks (`httpx_3672`), `import httpx` resolves to `/usr/local/lib/python3.12/dist-packages/httpx` rather than `/workspace/src/httpx`.
3. **Syntax errors**: Adding a simple check before `submit_patch` (running `python -m py_compile <file>`) catches broken indentation or detached blocks before submitting!

---

### 🔗 Code, Traces & Paper
Everything we tested is open-source and 100% reproducible:
- 📄 **Camera-Ready Paper**: [Download PDF (508 KB)](https://storage.googleapis.com/kaggle-forum-message-attachments/3544971/53116/paper.pdf)
- 📝 **Competition Writeup**: [State-Filtered Deliberation Writeup](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/writeups/state-filtered-deliberation-stage-isolated-contex)
- 💻 **GitHub Repo (All 64 ATIF v1.7 Traces)**: [gemma-sfd-agent](https://github.com/KarandeepSinghSodhi/gemma-sfd-agent)
- 📓 **Interactive Verification Notebook**: [Kaggle Notebook](https://www.kaggle.com/code/karandeepsinghsodhi/sfd-state-filtered-deliberation-agent-gemma-4)

---

**Discussion Question:**  
Are you finding that your small agents get trapped in circular tool loops or context bloat? Have you found prompting or architectural tricks that keep E4B/E2B inside tight token limits? Would love to hear your thoughts below! 👇
