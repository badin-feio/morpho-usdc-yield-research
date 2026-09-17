"""Images for the X article: a 5:2 cover and the credit-loss table.

Same palette and type as make_figures.py; sized for screens rather than print.
"""
import os

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

OUT = "figures"
os.makedirs(OUT, exist_ok=True)

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#ffffff"
GREY = "#b9b8b2"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "savefig.facecolor": SURFACE, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
})

# ---------------------------------------------------------------- cover, 5:2
layers = [
    ("Risk-free rate", GREY, 4.32, 4.24, 4.30),
    ("Credit loss", BLUE, 0.071, 0.0065, 1.50),
    ("Operational & other risks", ORANGE, 0.115, 0.115, 3.50),
    ("Liquidity premium", AQUA, 0.0, 0.0, 0.50),
    ("Regulatory risk", YELLOW, 0.0, 0.0, 1.25),
    ("Tail risk / model uncertainty", MAGENTA, 0.0, 0.0, 1.50),
]
realized = {"Ethereum": 5.96, "Base": 4.19}
x, width = [0, 0.9, 2.1], 0.5

fig, ax = plt.subplots(figsize=(10, 4))          # 5:2
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.tick_params(axis="both", length=0, labelsize=13)

bottoms = [0.0, 0.0, 0.0]
for label, colour, *vals in layers:
    ax.bar(x, vals, width, bottom=bottoms, color=colour, edgecolor=SURFACE,
           linewidth=1.2, label=label)
    bottoms = [b + v for b, v in zip(bottoms, vals)]

# our two bars: label to the left of the bar, clear of the realized marker
for i in (0, 1):
    ax.text(x[i] - width / 2 - 0.08, bottoms[i] - 0.35, f"{bottoms[i]:.2f}%",
            ha="right", va="center", fontsize=14, color=INK, fontweight="bold")
ax.text(x[2], bottoms[2] + 0.2, f"{bottoms[2]:.2f}%", ha="center", va="bottom",
        fontsize=15, color=INK, fontweight="bold")

for i, name in enumerate(["Ethereum", "Base"]):
    y = realized[name]
    ax.plot([x[i] - width / 2 - 0.02, x[i] + width / 2 + 0.02], [y, y], color=INK, linewidth=2.5)
    ax.plot(x[i], y, marker="o", markersize=9, color=INK,
            markeredgecolor=SURFACE, markeredgewidth=1.5)

ax.text(x[0], 6.3, "what depositors\nactually earned", ha="center", va="bottom",
        fontsize=11, color=INK2)
ax.set_xticks(x)
ax.set_xticklabels(["Ethereum", "Base", "Dunleavy"], color=INK, fontsize=14)
ax.set_ylim(0, 14.5)
ax.set_xlim(-0.75, 5.4)
ax.set_yticks(range(0, 15, 2))
ax.set_yticklabels([f"{t}%" for t in range(0, 15, 2)])
ax.spines["bottom"].set_bounds(-0.5, 2.5)

handles = [Patch(facecolor=c, label=l) for l, c, *_ in layers]
handles.append(Line2D([0], [0], color=INK, marker="o", markersize=7, linewidth=2.5,
                      label="Realized vault yield"))
ax.legend(handles=handles, loc="upper right", frameon=False, fontsize=11.5,
          handlelength=1.3, labelspacing=0.55)
fig.subplots_adjust(left=0.08, right=0.99, top=0.97, bottom=0.12)
fig.savefig(f"{OUT}/x_cover_5x2.png", dpi=170)   # exact 5:2, no tight bbox
plt.close(fig)

# ---------------------------------------------------------------- table image
rows = [
    ("Liquidation intensity (per year)", "13.8%", "28.2%"),
    ("P(bad debt | liquidation), by amount", "0.52%", "0.12%"),
    ("P(bad debt | liquidation), by count", "9.2%", "1.6%"),
    ("LGD", "0.998", "0.187"),
    ("Expected credit loss (per year)", "7.1 bps", "0.7 bps"),
]
fig, ax = plt.subplots(figsize=(9, 3.4))
ax.axis("off")
ax.text(0.02, 0.93, "Credit loss in Morpho's USDC markets, Apr 2024 - Sep 2026",
        fontsize=13, color=INK, fontweight="bold", transform=ax.transAxes)
head_y = 0.76
for label, xpos in (("Ethereum", 0.66), ("Base", 0.88)):
    ax.text(xpos, head_y, label, fontsize=12.5, color=INK2, ha="right",
            transform=ax.transAxes)
ax.plot([0.02, 0.98], [head_y - 0.06] * 2, color=AXIS, linewidth=1.1,
        transform=ax.transAxes, clip_on=False)
for i, (label, a, b) in enumerate(rows):
    y = head_y - 0.16 - i * 0.135
    weight = "bold" if "Expected" in label else "normal"
    ax.text(0.02, y, label, fontsize=12.5, color=INK, transform=ax.transAxes, fontweight=weight)
    ax.text(0.66, y, a, fontsize=12.5, color=INK, ha="right", transform=ax.transAxes, fontweight=weight)
    ax.text(0.88, y, b, fontsize=12.5, color=INK, ha="right", transform=ax.transAxes, fontweight=weight)
fig.savefig(f"{OUT}/x_table_credit_loss.png", dpi=170, bbox_inches="tight")
plt.close(fig)
print("saved: x_cover_5x2.png, x_table_credit_loss.png")
