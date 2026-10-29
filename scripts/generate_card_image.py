import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
from pathlib import Path

def create_sfd_card(scale=1.0, filename="card_thumbnail_560x280.png"):
    dpi = 100 * scale
    
    fig, ax = plt.subplots(figsize=(5.6, 2.8), dpi=dpi)
    fig.patch.set_facecolor('#070B14')
    ax.set_facecolor('#070B14')
    ax.set_xlim(0, 560)
    ax.set_ylim(0, 280)
    ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    # Ambient glows
    glow1 = patches.Circle((480, 220), 140, facecolor='#1E1B4B', alpha=0.35, edgecolor='none')
    glow2 = patches.Circle((100, 40), 120, facecolor='#0C4A6E', alpha=0.25, edgecolor='none')
    ax.add_patch(glow1)
    ax.add_patch(glow2)
    
    # Subtle Technical Grid
    for x in range(0, 560, 40):
        ax.axvline(x, color='#1E293B', alpha=0.18, linewidth=0.6)
    for y in range(0, 280, 40):
        ax.axhline(y, color='#1E293B', alpha=0.18, linewidth=0.6)
        
    # Outer border
    border = patches.Rectangle((2, 2), 556, 276, fill=False, edgecolor='#1E293B', linewidth=1.5, alpha=0.7)
    ax.add_patch(border)
    
    # Top Category Pill
    pill_box = patches.FancyBboxPatch((28, 240), 250, 22, boxstyle="round,pad=2,rounding_size=5",
                                      facecolor='#0F172A', edgecolor='#0284C7', linewidth=1.0)
    ax.add_patch(pill_box)
    ax.text(36, 251, "GOOGLE GEMMA 4  •  PAPER TRACK", color='#38BDF8', fontsize=7.4,
            fontweight='bold', va='center', family='sans-serif')
            
    # Main Title
    ax.text(28, 214, "State-Filtered Deliberation", color='#FFFFFF', fontsize=19,
            fontweight='heavy', va='center', family='sans-serif')
            
    # Subtitle
    ax.text(28, 190, "Stage-Isolated Context Management for Small 4B SWE Agents", color='#94A3B8',
            fontsize=8.6, fontweight='medium', va='center', family='sans-serif')
            
    # Architecture Flow: Triage -> Reset -> Patch -> Reset -> Verifier
    box_y = 100
    box_h = 66
    box_w = 116
    
    # Stage 1: TriageAgent
    s1 = patches.FancyBboxPatch((28, box_y), box_w, box_h, boxstyle="round,pad=3,rounding_size=6",
                                facecolor='#0B132B', edgecolor='#0284C7', linewidth=1.1)
    ax.add_patch(s1)
    ax.text(28 + box_w/2, box_y + box_h - 15, "1. TriageAgent", color='#38BDF8', fontsize=8.6,
            fontweight='bold', ha='center', va='center', family='sans-serif')
    ax.text(28 + box_w/2, box_y + 24, "Call Graphs + AST\nRead-only Tools", color='#94A3B8',
            fontsize=6.8, ha='center', va='center', family='sans-serif')
            
    # Arrow 1 with Reset Badge
    ax.annotate("", xy=(180, box_y + box_h/2), xytext=(148, box_y + box_h/2),
                arrowprops=dict(arrowstyle="->", color='#38BDF8', lw=1.4))
    ax.text(164, box_y + box_h/2 + 9, "-86%", color='#34D399', fontsize=7.0, fontweight='bold', ha='center')
    
    # Stage 2: PatchAgent
    s2 = patches.FancyBboxPatch((184, box_y), box_w, box_h, boxstyle="round,pad=3,rounding_size=6",
                                facecolor='#1E1B4B', edgecolor='#818CF8', linewidth=1.1)
    ax.add_patch(s2)
    ax.text(184 + box_w/2, box_y + box_h - 15, "2. PatchAgent", color='#A5B4FC', fontsize=8.6,
            fontweight='bold', ha='center', va='center', family='sans-serif')
    ax.text(184 + box_w/2, box_y + 24, "Isolated Context\nSurgical Editing", color='#C7D2FE',
            fontsize=6.8, ha='center', va='center', family='sans-serif')
            
    # Arrow 2 with Reset Badge
    ax.annotate("", xy=(336, box_y + box_h/2), xytext=(304, box_y + box_h/2),
                arrowprops=dict(arrowstyle="->", color='#818CF8', lw=1.4))
    ax.text(320, box_y + box_h/2 + 9, "Reset", color='#34D399', fontsize=6.8, fontweight='bold', ha='center')
    
    # Stage 3: VerifierAgent
    s3 = patches.FancyBboxPatch((340, box_y), box_w, box_h, boxstyle="round,pad=3,rounding_size=6",
                                facecolor='#06281E', edgecolor='#10B981', linewidth=1.1)
    ax.add_patch(s3)
    ax.text(340 + box_w/2, box_y + box_h - 15, "3. VerifierAgent", color='#34D399', fontsize=8.6,
            fontweight='bold', ha='center', va='center', family='sans-serif')
    ax.text(340 + box_w/2, box_y + 24, "pytest Execution\nsubmit_patch", color='#A7F3D0',
            fontsize=6.8, ha='center', va='center', family='sans-serif')
            
    # Hardware / Stack Mini Box
    m_box = patches.FancyBboxPatch((468, box_y), 64, box_h, boxstyle="round,pad=3,rounding_size=6",
                                   facecolor='#111827', edgecolor='#374151', linewidth=1.0)
    ax.add_patch(m_box)
    ax.text(500, box_y + box_h - 15, "Gemma 4", color='#F1F5F9', fontsize=7.6, fontweight='bold', ha='center')
    ax.text(500, box_y + box_h - 27, "E4B QAT", color='#38BDF8', fontsize=7.2, fontweight='bold', ha='center')
    ax.text(500, box_y + 16, "4x L4 GPUs\n64 Traces", color='#94A3B8', fontsize=6.6, ha='center')
    
    # Bottom Summary Strip (3 clean non-overlapping zones)
    b_strip = patches.FancyBboxPatch((28, 22), 504, 56, boxstyle="round,pad=2,rounding_size=5",
                                     facecolor='#0F172A', edgecolor='#334155', linewidth=1.0)
    ax.add_patch(b_strip)
    
    # Zone 1: Prompt Reset
    ax.text(112, 53, "-86.3% Prompt Reset", color='#34D399', fontsize=8.2, fontweight='bold', ha='center')
    ax.text(112, 35, "10,922 ➔ 1,501 tokens at entry", color='#94A3B8', fontsize=7.0, ha='center')
    
    # Separator 1
    ax.axvline(196, ymin=0.10, ymax=0.26, color='#334155', linewidth=0.8)
    
    # Zone 2: Total Token Efficiency
    ax.text(280, 53, "-25.7% Total Tokens", color='#60A5FA', fontsize=8.2, fontweight='bold', ha='center')
    ax.text(280, 35, "Lower on 13/16 tasks (p = 0.021)", color='#94A3B8', fontsize=7.0, ha='center')
    
    # Separator 2
    ax.axvline(364, ymin=0.10, ymax=0.26, color='#334155', linewidth=0.8)
    
    # Zone 3: Empirical Rigor
    ax.text(448, 53, "100% Trace-Backed", color='#A5B4FC', fontsize=8.2, fontweight='bold', ha='center')
    ax.text(448, 35, "ATIF v1.7 • Zero Simulated Data", color='#94A3B8', fontsize=7.0, ha='center')
    
    out_path = Path("d:/AI Research/gemma_paper") / filename
    plt.savefig(out_path, dpi=dpi, facecolor=fig.get_facecolor(), edgecolor='none', pad_inches=0)
    plt.close()
    
    im = Image.open(out_path)
    print(f"Generated {filename}: {im.size} (Width: {im.width}, Height: {im.height})")

if __name__ == "__main__":
    create_sfd_card(1.0, "card_thumbnail_560x280.png")
    create_sfd_card(2.0, "card_thumbnail_1120x560.png")
