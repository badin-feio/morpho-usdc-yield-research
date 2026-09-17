"""Figures for the results section (PDF for the note, PNG for the thread).

required yield = risk-free rate + credit loss + operational loss
                 (11.5 bps, the geometric mean of 2.1 and 62), liquidity = 0
buffer         = realized vault yield - required yield
The risk-free rate is a neutral grey baseline shared by every bar.
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
    "font.size": 9,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": INK2,
    "xtick.color": INK2,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "savefig.facecolor": SURFACE,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "pdf.fonttype": 42,
})


def style_axis(ax):
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0)


def save(fig, stem):
    fig.savefig(f"{OUT}/{stem}.pdf", bbox_inches="tight")
    fig.savefig(f"{OUT}/{stem}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Figure 1
# (label, colour, Ethereum, Base, Dunleavy) in % a year, bottom to top
layers = [
    ("Risk-free rate",               GREY,    4.32,  4.24,   4.30),
    ("Credit loss",                  BLUE,    0.071, 0.0065, 1.50),
    ("Operational & other risks",    ORANGE,  0.115, 0.115,  3.50),
    ("Liquidity premium",            AQUA,    0.0,   0.0,    0.50),
    ("Regulatory risk",              YELLOW,  0.0,   0.0,    1.25),
    ("Tail risk / model uncertainty", MAGENTA, 0.0,  0.0,    1.50),
]
realized = {"Ethereum": 5.96, "Base": 4.19}
bars = ["Ethereum", "Base", "Dunleavy"]
x = [0, 1, 2.35]
width = 0.56

fig, ax = plt.subplots(figsize=(6.4, 4.2))
style_axis(ax)
bottoms = [0.0, 0.0, 0.0]
for label, colour, *vals in layers:
    ax.bar(x, vals, width, bottom=bottoms, color=colour, edgecolor=SURFACE, linewidth=1.2, label=label)
    # direct labels inside Dunleavy's bar, where every segment is tall enough
    v = vals[2]
    if label != "Risk-free rate" and v >= 0.5:
        ax.text(x[2] + width / 2 + 0.08, bottoms[2] + v / 2, f"{label}  {v:.2f}%",
                va="center", ha="left", fontsize=7.5, color=INK2)
    bottoms = [b + val for b, val in zip(bottoms, vals)]

ax.text(x[2] + width / 2 + 0.08, 4.30 / 2, "Risk-free rate (10-year)  4.30%",
        va="center", ha="left", fontsize=7.5, color=INK2)

# totals above bars
for xi, total in zip(x, bottoms):
    ax.text(xi, total + 0.18, f"{total:.2f}%", ha="center", va="bottom", fontsize=9, color=INK, fontweight="bold")

# realized vault yield markers (Ethereum above its bar, Base below its bar top)
for i, name in enumerate(["Ethereum", "Base"]):
    y = realized[name]
    ax.plot([x[i] - width / 2 - 0.02, x[i] + width / 2 + 0.02], [y, y], color=INK, linewidth=2)
    ax.plot(x[i], y, marker="o", markersize=7, color=INK, markeredgecolor=SURFACE, markeredgewidth=1.5)

ax.annotate("realized vault yield 5.96%", xy=(x[0], 5.96), xytext=(x[0] - 0.05, 7.1),
            fontsize=7.5, color=INK2, ha="center",
            arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.6))
ax.annotate("realized 4.19%", xy=(x[1] + width / 2 + 0.02, 4.19), xytext=(x[1] + 0.68, 3.1),
            fontsize=7.5, color=INK2, ha="center",
            arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.6))
for i in (0, 1):
    ax.text(x[i], 2.0, "3-month\nbill", ha="center", va="center", fontsize=7.5, color=INK2)

ax.set_xticks(x)
ax.set_xticklabels(["Ethereum", "Base", "Dunleavy"], color=INK)
ax.set_ylim(0, 14)
ax.set_xlim(-0.5, 4.6)
ax.set_yticks(range(0, 15, 2))
ax.set_yticklabels([f"{t}%" for t in range(0, 15, 2)])
ax.spines["bottom"].set_bounds(-0.4, 2.7)

handles = [Patch(facecolor=c, label=l) for l, c, *_ in layers]
handles.append(Line2D([0], [0], color=INK, marker="o", markersize=6, linewidth=2, label="Realized vault yield"))
ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=7.5, ncol=1, handlelength=1.2)
save(fig, "fig1_required_vs_realized")

# ---------------------------------------------------------------- Figure 2
years = ["2024", "2025", "2026"]
buffer = {"Ethereum": [311, 169, -42], "Base": [-243, 86, 7]}
colours = {"Ethereum": BLUE, "Base": ORANGE}
w = 0.34

fig, ax = plt.subplots(figsize=(6.4, 3.6))
style_axis(ax)
for j, name in enumerate(["Ethereum", "Base"]):
    xs = [i + (j - 0.5) * (w + 0.03) for i in range(len(years))]
    ax.bar(xs, buffer[name], w, color=colours[name], edgecolor=SURFACE, linewidth=1.2, label=name)
    # value on every bar: six bars, all worth labelling
    for xi, v in zip(xs, buffer[name]):
        ax.text(xi, v + (12 if v >= 0 else -12), f"{v:+d}".replace("-", "\u2212"), ha="center",
                va="bottom" if v >= 0 else "top", fontsize=8.5, color=INK, fontweight="bold")

ax.axhline(0, color=INK, linewidth=1.1)
ax.set_xticks(range(len(years)))
ax.set_xticklabels(years, color=INK)
ax.set_ylabel("Buffer (bps a year)")
ax.set_ylim(-300, 380)
ax.spines["bottom"].set_visible(False)
ax.legend(loc="lower right", frameon=False, fontsize=8)

save(fig, "fig2_buffer_by_year")
print("saved:", sorted(os.listdir(OUT)))
