import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
from pathlib import Path

# Dimensions: exactly 560 x 280 px
DPI = 100
WIDTH_IN = 5.6
HEIGHT_IN = 2.8

fig, ax = plt.subplots(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI)
fig.patch.set_facecolor('#070B14')
ax.set_facecolor('#070B14')
ax.set_xlim(0, 560)
ax.set_ylim(0, 280)
ax.axis('off')
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

# Subtle background decorative elements (glows)
glow1 = patches.Circle((480, 220), 140, facecolor='#1E1B4B', alpha=0.35, edgecolor='none')
glow2 = patches.Circle((100, 40), 120, facecolor='#0C4A6E', alpha=0.25, edgecolor='none')
ax.add_patch(glow1)
ax.add_patch(glow2)

# Grid lines background (subtle technical blueprint grid)
for x in range(0, 560, 40):
    ax.axvline(x, color='#1E293B', alpha=0.18, linewidth=0.6)
for y in range(0, 280, 40):
    ax.axhline(y, color='#1E293B', alpha=0.18, linewidth=0.6)

# Outer subtle border
border = patches.Rectangle((2, 2), 556, 276, fill=False, edgecolor='#1E293B', linewidth=1.5, alpha=0.7)
ax.add_patch(border)

# Top Track Pill
pill_box = patches.FancyBboxPatch((28, 238), 240, 24, boxstyle="round,pad=2,rounding_size=6",
                                  facecolor='#0F172A', edgecolor='#0284C7', linewidth=1.2)
ax.add_patch(pill_box)
ax.text(38, 250, "GOOGLE GEMMA 4  •  PAPER TRACK", color='#38BDF8', fontsize=8.2,
        fontweight='bold', va='center', family='sans-serif')

# Main Title (State-Filtered Deliberation)
ax.text(28, 212, "State-Filtered Deliberation", color='#FFFFFF', fontsize=18,
        fontweight='heavy', va='center', family='sans-serif')

# Subtitle / Core Mechanism
ax.text(28, 187, "Stage-Isolated Context Management for Small 4B SWE Agents", color='#94A3B8',
        fontsize=9.2, fontweight='medium', va='center', family='sans-serif')

# Visual Architecture Flow (Triage -> Reset -> Patch -> Verifier)
box_y = 104
box_h = 58
box_w = 118

# Stage 1: TriageAgent
s1 = patches.FancyBboxPatch((28, box_y), box_w, box_h, boxstyle="round,pad=3,rounding_size=6",
                            facecolor='#0B132B', edgecolor='#0284C7', linewidth=1.2)
ax.add_patch(s1)
ax.text(28 + box_w/2, box_y + box_h - 16, "1. TriageAgent", color='#38BDF8', fontsize=8.8,
        fontweight='bold', ha='center', va='center', family='sans-serif')
ax.text(28 + box_w/2, box_y + 24, "Call Graphs + AST\nRead-only Tools", color='#94A3B8',
        fontsize=7.2, ha='center', va='center', family='sans-serif')

# Arrow 1 with Reset Badge
ax.annotate("", xy=(182, box_y + box_h/2), xytext=(150, box_y + box_h/2),
            arrowprops=dict(arrowstyle="->", color='#38BDF8', lw=1.5))
ax.text(166, box_y + box_h/2 + 10, "-86%", color='#34D399', fontsize=7.2, fontweight='bold', ha='center')

# Stage 2: PatchAgent
s2 = patches.FancyBboxPatch((186, box_y), box_w, box_h, boxstyle="round,pad=3,rounding_size=6",
                            facecolor='#1E1B4B', edgecolor='#818CF8', linewidth=1.2)
ax.add_patch(s2)
ax.text(186 + box_w/2, box_y + box_h - 16, "2. PatchAgent", color='#A5B4FC', fontsize=8.8,
        fontweight='bold', ha='center', va='center', family='sans-serif')
ax.text(186 + box_w/2, box_y + 24, "Isolated Context\nSurgical Editing", color='#C7D2FE',
        fontsize=7.2, ha='center', va='center', family='sans-serif')

# Arrow 2 with Reset Badge
ax.annotate("", xy=(340, box_y + box_h/2), xytext=(308, box_y + box_h/2),
            arrowprops=dict(arrowstyle="->", color='#818CF8', lw=1.5))
ax.text(324, box_y + box_h/2 + 10, "Reset", color='#34D399', fontsize=7.0, fontweight='bold', ha='center')

# Stage 3: VerifierAgent
s3 = patches.FancyBboxPatch((344, box_y), box_w, box_h, boxstyle="round,pad=3,rounding_size=6",
                            facecolor='#06281E', edgecolor='#10B981', linewidth=1.2)
ax.add_patch(s3)
ax.text(344 + box_w/2, box_y + box_h - 16, "3. VerifierAgent", color='#34D399', fontsize=8.8,
        fontweight='bold', ha='center', va='center', family='sans-serif')
ax.text(344 + box_w/2, box_y + 24, "pytest Execution\nsubmit_patch", color='#A7F3D0',
        fontsize=7.2, ha='center', va='center', family='sans-serif')

# Right Side Metrics Summary Box
m_box = patches.FancyBboxPatch((474, box_y), 62, box_h, boxstyle="round,pad=3,rounding_size=6",
                               facecolor='#111827', edgecolor='#374151', linewidth=1.0)
ax.add_patch(m_box)
ax.text(505, box_y + box_h - 14, "Gemma 4", color='#F1F5F9', fontsize=7.6, fontweight='bold', ha='center')
ax.text(505, box_y + box_h - 26, "E4B QAT", color='#38BDF8', fontsize=7.2, fontweight='bold', ha='center')
ax.text(505, box_y + 14, "4x L4 GPUs\n64 Traces", color='#94A3B8', fontsize=6.8, ha='center')

# Bottom Empirical Badges (Three Key Highlights)
b1 = patches.FancyBboxPatch((28, 28), 158, 44, boxstyle="round,pad=2,rounding_size=5",
                            facecolor='#06251E', edgecolor='#059669', linewidth=1.0)
ax.add_patch(b1)
ax.text(38, 56, "-86.3% Prompt Reset", color='#34D399', fontsize=8.5, fontweight='bold', family='sans-serif')
ax.text(38, 40, "10,922 ➔ 1,501 tokens at stage entry", color='#A7F3D0', fontsize=7.0, family='sans-serif')

b2 = patches.FancyBboxPatch((198, 28), 164, 44, boxstyle="round,pad=2,rounding_size=5",
                            facecolor='#0F2042', edgecolor='#2563EB', linewidth=1.0)
ax.add_patch(b2)
ax.text(208, 56, "-25.7% Total Tokens", color='#60A5FA', fontsize=8.5, fontweight='bold', family='sans-serif')
ax.text(208, 40, "Lower on 13/16 tasks (p = 0.0213)", color='#BFDBFE', fontsize=7.0, family='sans-serif')

b3 = patches.FancyBboxPatch((374, 28), 162, 44, boxstyle="round,pad=2,rounding_size=5",
                            facecolor='#1E1E2E', edgecolor='#6366F1', linewidth=1.0)
ax.add_patch(b3)
ax.text(384, 56, "100% Trace-Backed", color='#C7D2FE', fontsize=8.5, fontweight='bold', family='sans-serif')
ax.text(384, 40, "ATIF v1.7 • Zero Simulated Data", color='#E0E7FF', fontsize=7.0, family='sans-serif')

# Save exactly at 560 x 280
out_img = Path(r"d:\AI Research\gemma_paper\card_thumbnail_560x280.png")
plt.savefig(out_img, dpi=DPI, facecolor=fig.get_facecolor(), edgecolor='none', pad_inches=0)
plt.close()

# Verify dimensions with PIL
im = Image.open(out_img)
print(f"Generated card image: {out_img} with exact dimensions {im.size} (Width: {im.width}, Height: {im.height})")
