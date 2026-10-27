"""
analysis/figures.py: Generates publication-quality, colorblind-safe vector figures
(SVG, PDF, and high-res PNG) for the ATIF-Gemma paper and writeup:

1. Fig 1: Phase 2 Exit Code Distribution (Overall and by Configuration)
2. Fig 2: Step-Level Prompt Token Trajectories (Mean +/- 95% Bootstrap CI showing SFD resets)
3. Fig 3: Sub-Agent Delegation Funnel in flat_starter (336 tools -> 7 calls -> 90.6% bypass)

Outputs:
- figures/fig1_exit_codes.{svg,pdf,png}
- figures/fig2_prompt_resets.{svg,pdf,png}
- figures/fig3_delegation_funnel.{svg,pdf,png}
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Publication typography & styling
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 12,
    "figure.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# Colorblind-safe palette (Okabe-Ito / Wong 2011)
CB_BLUE = "#0072B2"
CB_VERMILION = "#D55E00"
CB_GREEN = "#009E73"
CB_ORANGE = "#E69F00"
CB_PURPLE = "#CC79A7"
CB_SKY = "#56B4E9"
CB_GRAY = "#7F7F7F"
CB_DARK = "#333333"

ROOT = Path(__file__).resolve().parents[1]
TRACES_DIR = ROOT / "dataset_resource" / "traces"
METADATA_PATH = ROOT / "dataset_resource" / "corpus_metadata.csv"
FIG_DIR = ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def generate_fig1_exit_codes():
    """Fig 1: Exit code distribution overall and broken down by agent configuration."""
    # Data from results/table2_taxonomy.csv and summary_metrics.json
    configs = ["All Runs (112)", "flat_starter (32)", "flat_controlled (32)", "sfd (32)", "Reruns (16)"]
    
    # Categories: Resolved (0), Assertion Fail (1), Collection Crash (2), Budget Exhausted (-1), Timeout (124)
    # Counts:
    # All (112): [8, 56, 36, 9, 3] -> pct: [7.1, 50.0, 32.1, 8.0, 2.7]
    # Starter (32): [2, 18, 9, 2, 1] -> pct: [6.25, 56.25, 28.12, 6.25, 3.12]
    # Controlled (32): [2, 18, 9, 2, 1] -> pct: [6.25, 56.25, 28.12, 6.25, 3.12]
    # SFD (32): [2, 16, 12, 2, 0] -> pct: [6.25, 50.0, 37.5, 6.25, 0.0]
    # Reruns (16): [2, 4, 6, 3, 1] -> pct: [12.5, 25.0, 37.5, 18.75, 6.25]
    
    categories = [
        "Resolved (Exit 0)",
        "Test Assertion Fail (Exit 1)",
        "Collection / Import Crash (Exit 2)",
        "Budget Exhausted (Exit -1)",
        "Timeout (Exit 124)"
    ]
    colors = [CB_GREEN, CB_BLUE, CB_VERMILION, CB_ORANGE, CB_PURPLE]
    
    data = np.array([
        [7.1, 50.0, 32.1, 8.0, 2.7],
        [6.25, 56.25, 28.12, 6.25, 3.12],
        [6.25, 56.25, 28.12, 6.25, 3.12],
        [6.25, 50.0, 37.5, 6.25, 0.0],
        [12.5, 25.0, 37.5, 18.75, 6.25]
    ])
    
    fig, ax = plt.subplots(figsize=(8, 3.8))
    y_pos = np.arange(len(configs))
    left = np.zeros(len(configs))
    
    for cat_idx, (cat_name, col) in enumerate(zip(categories, colors)):
        widths = data[:, cat_idx]
        bars = ax.barh(y_pos, widths, left=left, color=col, edgecolor="white", height=0.55, label=cat_name)
        # Add labels inside wide segments
        for i, (w, l) in enumerate(zip(widths, left)):
            if w >= 7.0:
                ax.text(l + w / 2, i, f"{w:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=8)
        left += widths
        
    ax.set_yticks(y_pos)
    ax.set_yticklabels(configs, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel("Percentage of Cohort Runs (%)", fontweight="bold")
    ax.set_xlim(0, 100)
    ax.xaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_title("Figure 1: Phase 2 Evaluation Outcome Distribution in ATIF-Gemma", fontweight="bold", pad=12)
    
    # Legend below plot
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3, frameon=False)
    
    for ext in ["svg", "pdf", "png"]:
        fig.savefig(FIG_DIR / f"fig1_exit_codes.{ext}")
    plt.close(fig)
    print("Generated Fig 1 (exit codes).")


def generate_fig2_prompt_resets():
    """Fig 2: Step-by-step prompt token trajectories showing SFD resets vs flat accumulation."""
    df = pd.read_csv(METADATA_PATH)
    
    configs = ["flat_starter", "flat_controlled", "sfd"]
    cfg_labels = {
        "flat_starter": "Official Starter (flat_starter)",
        "flat_controlled": "Monolithic Single-Agent (flat_controlled)",
        "sfd": "State-Filtered Deliberation (SFD, 3 stages)"
    }
    cfg_colors = {
        "flat_starter": CB_ORANGE,
        "flat_controlled": CB_BLUE,
        "sfd": CB_VERMILION
    }
    
    # Collect step prompt tokens per config across primary runs
    max_steps = 15
    config_step_tokens = {c: [[] for _ in range(max_steps)] for c in configs}
    
    for idx, row in df[df["config"].isin(configs)].iterrows():
        tpath = TRACES_DIR / row["dataset_trace_file"]
        if not tpath.is_file():
            continue
        data = json.loads(tpath.read_text(encoding="utf-8"))
        cfg = row["config"]
        steps = data.get("steps", [])
        
        for s_idx, s in enumerate(steps[:max_steps]):
            m = s.get("metrics")
            if isinstance(m, dict) and "prompt_tokens" in m:
                pt = int(m.get("prompt_tokens", 0))
                if pt > 0:
                    config_step_tokens[cfg][s_idx].append(pt)
                    
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    
    steps_x = np.arange(1, max_steps + 1)
    
    for cfg in configs:
        means = []
        cis_low = []
        cis_high = []
        for s_idx in range(max_steps):
            vals = config_step_tokens[cfg][s_idx]
            if len(vals) >= 3:
                m = np.mean(vals)
                # 95% bootstrap CI
                boot = [np.mean(np.random.choice(vals, size=len(vals), replace=True)) for _ in range(500)]
                ci_l = np.percentile(boot, 2.5)
                ci_h = np.percentile(boot, 97.5)
            elif len(vals) > 0:
                m = np.mean(vals)
                ci_l, ci_h = m, m
            else:
                m, ci_l, ci_h = np.nan, np.nan, np.nan
            means.append(m)
            cis_low.append(ci_l)
            cis_high.append(ci_h)
            
        means = np.array(means)
        cis_low = np.array(cis_low)
        cis_high = np.array(cis_high)
        
        valid = ~np.isnan(means)
        ax.plot(steps_x[valid], means[valid], label=cfg_labels[cfg], color=cfg_colors[cfg], linewidth=2.2, marker="o" if cfg=="sfd" else "s", markersize=4)
        ax.fill_between(steps_x[valid], cis_low[valid], cis_high[valid], color=cfg_colors[cfg], alpha=0.15)
        
    # Annotate the SFD stage reset boundary
    ax.annotate(
        "SFD Stage Transition\n(include_contents: 'none'\nresets context by ~82%)",
        xy=(5, 2100),
        xytext=(6.5, 6000),
        arrowprops=dict(facecolor=CB_VERMILION, shrink=0.08, width=1.2, headwidth=6),
        fontweight="bold",
        fontsize=8.5,
        color=CB_VERMILION,
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=CB_VERMILION, lw=1)
    )
    
    ax.set_xlabel("Trajectory Turn Step ($t$)", fontweight="bold")
    ax.set_ylabel("Prompt Tokens ($P_t$)", fontweight="bold")
    ax.set_title("Figure 2: Prompt Token Expansion & Stage Resets Across Trajectory Steps", fontweight="bold", pad=12)
    ax.set_xlim(1, 14)
    ax.set_ylim(0, 17500)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", frameon=True, framealpha=0.9)
    
    for ext in ["svg", "pdf", "png"]:
        fig.savefig(FIG_DIR / f"fig2_prompt_resets.{ext}")
    plt.close(fig)
    print("Generated Fig 2 (prompt token resets).")


def generate_fig3_delegation_funnel():
    """Fig 3: Discretionary sub-agent delegation funnel in flat_starter."""
    # Data from ATIF-Gemma audit:
    # 32 benchmark tasks
    # 336 total tool invocations in flat_starter
    # 304 non-submit tool calls
    # 7 delegations to code_analyzer (2.1% of tool calls)
    # 3 tasks used code_analyzer (9.4%)
    # 29 tasks completely bypassed code_analyzer (90.6%)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.5), gridspec_kw={"width_ratios": [1.4, 1.0]})
    
    # Left: Tool decision funnel
    stages = ["Total Tool\nInvocations\n(336)", "Root Non-Submit\nDecisions\n(304)", "Delegated to\ncode_analyzer\n(7 calls = 2.1%)"]
    counts = [336, 304, 7]
    y_pos = np.arange(len(stages))
    
    bar_cols = [CB_BLUE, CB_SKY, CB_VERMILION]
    bars = ax1.barh(y_pos, counts, color=bar_cols, height=0.55, edgecolor="white")
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(stages, fontweight="bold")
    ax1.invert_yaxis()
    ax1.set_xlim(0, 380)
    ax1.set_xlabel("Number of Invocations", fontweight="bold")
    ax1.set_title("(a) Tool Invocation Funnel", fontweight="bold", pad=10)
    ax1.xaxis.grid(True, linestyle="--", alpha=0.5)
    
    for b, c in zip(bars, counts):
        ax1.text(b.get_width() + 8, b.get_y() + b.get_height()/2, f"{c}", ha="left", va="center", fontweight="bold", fontsize=9)
        
    # Right: Task-level bypass donut
    tasks_used = 3
    tasks_bypassed = 29
    labels = ["Bypassed (90.6%)\n29 / 32 Tasks", "Delegated (9.4%)\n3 / 32 Tasks"]
    pie_colors = [CB_VERMILION, CB_GREEN]
    wedges, texts, autotexts = ax2.pie(
        [tasks_bypassed, tasks_used],
        labels=labels,
        autopct="",
        colors=pie_colors,
        startangle=120,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2)
    )
    for t in texts:
        t.set_fontsize(8.5)
        t.set_fontweight("bold")
    ax2.set_title("(b) Task Delegation Rate", fontweight="bold", pad=10)
    
    fig.suptitle("Figure 3: Sub-Agent Discretionary Delegation Breakdown in Official Starter Kit", fontweight="bold", y=1.02)
    plt.tight_layout()
    
    for ext in ["svg", "pdf", "png"]:
        fig.savefig(FIG_DIR / f"fig3_delegation_funnel.{ext}")
    plt.close(fig)
    print("Generated Fig 3 (delegation funnel).")


def main():
    print("Generating colorblind-safe vector figures...")
    generate_fig1_exit_codes()
    generate_fig2_prompt_resets()
    generate_fig3_delegation_funnel()
    print("All figures successfully saved to figures/ in SVG, PDF, and PNG formats.")


if __name__ == "__main__":
    main()
