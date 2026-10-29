import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
from pathlib import Path

def create_resource_card(scale=1.0, filename="card_resource_560x280.png"):
    dpi = 100 * scale
    
    fig, ax = plt.subplots(figsize=(5.6, 2.8), dpi=dpi)
    fig.patch.set_facecolor('#070B14')
    ax.set_facecolor('#070B14')
    ax.set_xlim(0, 560)
    ax.set_ylim(0, 280)
    ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    # Ambient glows
    glow1 = patches.Circle((480, 230), 140, facecolor='#1E1B4B', alpha=0.35, edgecolor='none')
    glow2 = patches.Circle((70, 40), 120, facecolor='#0C4A6E', alpha=0.25, edgecolor='none')
    ax.add_patch(glow1)
    ax.add_patch(glow2)
    
    # Technical Grid Background
    for x in range(0, 560, 40):
        ax.axvline(x, color='#1E293B', alpha=0.18, linewidth=0.6)
    for y in range(0, 280, 40):
        ax.axhline(y, color='#1E293B', alpha=0.18, linewidth=0.6)
        
    # Outer subtle border
    border = patches.Rectangle((2, 2), 556, 276, fill=False, edgecolor='#1E293B', linewidth=1.5, alpha=0.7)
    ax.add_patch(border)
    
    # Top Category Pill
    pill_box = patches.FancyBboxPatch((28, 240), 285, 22, boxstyle="round,pad=2,rounding_size=5",
                                      facecolor='#0F172A', edgecolor='#0284C7', linewidth=1.0)
    ax.add_patch(pill_box)
    ax.text(36, 251, "GOOGLE GEMMA 4  •  BEST NEW RESOURCE TRACK", color='#38BDF8', fontsize=7.4,
            fontweight='bold', va='center', family='sans-serif')
            
    # Main Title
    ax.text(28, 214, "ATIF-Gemma", color='#FFFFFF', fontsize=21,
            fontweight='heavy', va='center', family='sans-serif')
            
    # Subtitle
    ax.text(28, 190, "Diagnostic Corpus & Failure Taxonomy for Small Developer Agents", color='#94A3B8',
            fontsize=8.6, fontweight='medium', va='center', family='sans-serif')
            
    # 3 Middle Diagnostic Pillars
    box_y = 100
    box_h = 66
    box_w = 156
    
    # Pillar 1: Empirical Corpus
    p1 = patches.FancyBboxPatch((28, box_y), box_w, box_h, boxstyle="round,pad=3,rounding_size=6",
                                facecolor='#0B132B', edgecolor='#0284C7', linewidth=1.1)
    ax.add_patch(p1)
    ax.text(28 + box_w/2, box_y + box_h - 15, "112 Execution Traces", color='#38BDF8', fontsize=8.6,
            fontweight='bold', ha='center', va='center', family='sans-serif')
    ax.text(28 + box_w/2, box_y + 24, "32 SWE-bench Tasks\n4x NVIDIA L4 GPUs (vLLM)\n11.7M Total Tokens", color='#94A3B8',
            fontsize=6.8, ha='center', va='center', family='sans-serif')
            
    # Pillar 2: Failure Taxonomy
    p2 = patches.FancyBboxPatch((202, box_y), box_w, box_h, boxstyle="round,pad=3,rounding_size=6",
                                facecolor='#1E1B4B', edgecolor='#818CF8', linewidth=1.1)
    ax.add_patch(p2)
    ax.text(202 + box_w/2, box_y + box_h - 15, "Deterministic Taxonomy", color='#A5B4FC', fontsize=8.6,
            fontweight='bold', ha='center', va='center', family='sans-serif')
    ax.text(202 + box_w/2, box_y + 24, "50.0% Assertion Failures\n32.1% Collection Crashes\nExit-Code Grounding", color='#C7D2FE',
            fontsize=6.8, ha='center', va='center', family='sans-serif')
            
    # Pillar 3: Open Resource & Tooling
    p3 = patches.FancyBboxPatch((376, box_y), box_w, box_h, boxstyle="round,pad=3,rounding_size=6",
                                facecolor='#06281E', edgecolor='#10B981', linewidth=1.1)
    ax.add_patch(p3)
    ax.text(376 + box_w/2, box_y + box_h - 15, "ATIF v1.7 & Toolkit", color='#34D399', fontsize=8.6,
            fontweight='bold', ha='center', va='center', family='sans-serif')
    ax.text(376 + box_w/2, box_y + 24, "100% Schema Validated\n`atif-gemma` Python Package\nDatasheet & Full Audit", color='#A7F3D0',
            fontsize=6.8, ha='center', va='center', family='sans-serif')
            
    # Bottom Summary Strip
    b_strip = patches.FancyBboxPatch((28, 22), 504, 56, boxstyle="round,pad=2,rounding_size=5",
                                     facecolor='#0F172A', edgecolor='#334155', linewidth=1.0)
    ax.add_patch(b_strip)
    
    # Zone 1: LLM & Tool Calls
    ax.text(112, 53, "1,518 LLM Calls", color='#F1F5F9', fontsize=8.2, fontweight='bold', ha='center')
    ax.text(112, 35, "1,328 Tool Invocations", color='#94A3B8', fontsize=7.0, ha='center')
    
    # Separator 1
    ax.axvline(196, ymin=0.10, ymax=0.26, color='#334155', linewidth=0.8)
    
    # Zone 2: Reproducibility & Concordance
    ax.text(280, 53, "16 Rerun Audit Pairs", color='#60A5FA', fontsize=8.2, fontweight='bold', ha='center')
    ax.text(280, 35, "75% Exit Code Agreement", color='#94A3B8', fontsize=7.0, ha='center')
    
    # Separator 2
    ax.axvline(364, ymin=0.10, ymax=0.26, color='#334155', linewidth=0.8)
    
    # Zone 3: Governance & License
    ax.text(448, 53, "Apache-2.0 & CC BY 4.0", color='#34D399', fontsize=8.2, fontweight='bold', ha='center')
    ax.text(448, 35, "Full Data Governance", color='#94A3B8', fontsize=7.0, ha='center')
    
    out_path = Path("d:/AI Research/gemma_paper") / filename
    plt.savefig(out_path, dpi=dpi, facecolor=fig.get_facecolor(), edgecolor='none', pad_inches=0)
    plt.close()
    
    im = Image.open(out_path)
    print(f"Generated {filename}: {im.size} (Width: {im.width}, Height: {im.height})")

if __name__ == "__main__":
    create_resource_card(1.0, "card_resource_560x280.png")
    create_resource_card(2.0, "card_resource_1120x560.png")
