"""
Chart generation helpers using matplotlib.
Each function returns a BytesIO PNG buffer for embedding into PDF / Excel.
"""
import io
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Brand palette ──────────────────────────────────────────────────────────
NAVY   = "#1B3A6B"
TEAL   = "#2A7F8F"
GOLD   = "#C8952A"
LIGHT  = "#E8EDF4"
GRAY   = "#6C757D"
GREEN  = "#2E7D4F"
RED    = "#C0392B"

PERF_COLORS = [NAVY, TEAL, GOLD, GREEN, "#7B5EA7"]


def _buf(fig) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf


# ── Enrollment bar chart ───────────────────────────────────────────────────

def enrollment_chart(enrollment_history, capacity_line: bool = True) -> io.BytesIO:
    years  = [e.year for e in enrollment_history]
    totals = [e.total for e in enrollment_history]
    caps   = [e.capacity for e in enrollment_history]

    fig, ax = plt.subplots(figsize=(4.2, 2.6))
    fig.patch.set_facecolor("white")

    bars = ax.bar(years, totals, color=NAVY, width=0.55, zorder=3)
    ax.bar_label(bars, fmt="%d", padding=3, fontsize=7, color=NAVY, fontweight="bold")

    # Capacity line
    if capacity_line and any(c is not None for c in caps):
        cap_vals = [c if c is not None else np.nan for c in caps]
        ax.plot(years, cap_vals, color=GOLD, linewidth=1.8,
                linestyle="--", marker="D", markersize=4, label="Capacity", zorder=4)
        ax.legend(fontsize=7, loc="lower right")

    ax.set_title("Enrollment History", fontsize=9, fontweight="bold", color=NAVY, pad=6)
    ax.set_ylabel("Students", fontsize=7, color=GRAY)
    ax.tick_params(axis="x", labelsize=7, rotation=30)
    ax.tick_params(axis="y", labelsize=7)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.5, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _buf(fig)


# ── Demographics horizontal bar ────────────────────────────────────────────

def demographics_chart(demo) -> io.BytesIO:
    race_labels = ["Black", "Hispanic", "White", "Asian", "Other"]
    race_vals   = [demo.black, demo.hispanic, demo.white, demo.asian, demo.other]
    colors      = [NAVY, TEAL, GOLD, GREEN, GRAY]

    # Filter zeros
    pairs = [(l, v, c) for l, v, c in zip(race_labels, race_vals, colors) if v > 0]
    labels, vals, clrs = zip(*pairs) if pairs else ([], [], [])

    fig, axes = plt.subplots(1, 2, figsize=(4.2, 2.6))
    fig.patch.set_facecolor("white")

    # Left: race/ethnicity pie
    ax1 = axes[0]
    if vals:
        wedges, texts, autotexts = ax1.pie(
            vals, labels=None, colors=clrs,
            autopct=lambda p: f"{p:.0f}%" if p >= 5 else "",
            startangle=90, pctdistance=0.75,
            wedgeprops={"linewidth": 0.5, "edgecolor": "white"}
        )
        for at in autotexts:
            at.set_fontsize(6.5)
        ax1.legend(wedges, labels, fontsize=6, loc="lower center",
                   bbox_to_anchor=(0.5, -0.25), ncol=2, frameon=False)
    ax1.set_title("Race/Ethnicity", fontsize=8, fontweight="bold", color=NAVY, pad=4)

    # Right: service indicators
    ax2 = axes[1]
    indicators = ["FRL", "ELL", "SPED"]
    ind_vals   = [demo.free_reduced_lunch, demo.english_learners, demo.special_education]
    ind_colors = [TEAL, GOLD, NAVY]
    bars = ax2.barh(indicators, ind_vals, color=ind_colors, height=0.5)
    ax2.bar_label(bars, fmt="%.0f%%", padding=3, fontsize=7, color=GRAY)
    ax2.set_xlim(0, max(ind_vals or [100]) * 1.35 + 5)
    ax2.set_title("Service Indicators", fontsize=8, fontweight="bold", color=NAVY, pad=4)
    ax2.tick_params(labelsize=7)
    ax2.spines[["top", "right", "left"]].set_visible(False)
    ax2.xaxis.set_visible(False)
    ax2.set_axisbelow(True)

    fig.tight_layout(pad=0.5)
    return _buf(fig)


# ── Academic performance grouped bar ───────────────────────────────────────

def academic_chart(academic_history, state_ela: Optional[float] = None,
                   state_math: Optional[float] = None) -> io.BytesIO:
    years      = [a.year for a in academic_history]
    ela_vals   = [a.ela_proficiency for a in academic_history]
    math_vals  = [a.math_proficiency for a in academic_history]

    x    = np.arange(len(years))
    w    = 0.35

    fig, ax = plt.subplots(figsize=(4.8, 2.6))
    fig.patch.set_facecolor("white")

    def safe(vals):
        return [v if v is not None else 0 for v in vals]

    b1 = ax.bar(x - w/2, safe(ela_vals),  w, label="ELA",  color=NAVY,  zorder=3)
    b2 = ax.bar(x + w/2, safe(math_vals), w, label="Math", color=TEAL,  zorder=3)
    ax.bar_label(b1, fmt="%.0f%%", padding=2, fontsize=6.5, color=NAVY)
    ax.bar_label(b2, fmt="%.0f%%", padding=2, fontsize=6.5, color=TEAL)

    # State benchmarks
    if state_ela is not None:
        ax.axhline(state_ela,  color=NAVY, linewidth=1, linestyle=":", alpha=0.6,
                   label=f"State ELA {state_ela:.0f}%")
    if state_math is not None:
        ax.axhline(state_math, color=TEAL, linewidth=1, linestyle=":", alpha=0.6,
                   label=f"State Math {state_math:.0f}%")

    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=7, rotation=30)
    ax.set_ylabel("% Proficient", fontsize=7, color=GRAY)
    ax.set_ylim(0, 110)
    ax.set_title("Academic Proficiency", fontsize=9, fontweight="bold", color=NAVY, pad=6)
    ax.legend(fontsize=6.5, ncol=2, loc="upper left", framealpha=0.8)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.5, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    return _buf(fig)


# ── Charter timeline ───────────────────────────────────────────────────────

EVENT_COLOR = {
    "original":     NAVY,
    "renewal":      GREEN,
    "modification": GOLD,
    "probation":    RED,
    "revocation":   "#8B0000",
}

def charter_timeline_chart(charter_events) -> io.BytesIO:
    events = sorted(charter_events, key=lambda e: e.year)
    years  = [e.year for e in events]
    colors = [EVENT_COLOR.get(e.event_type, GRAY) for e in events]
    labels = [f"{e.event_type.title()}\n{e.year}" for e in events]

    fig, ax = plt.subplots(figsize=(6.5, 1.4))
    fig.patch.set_facecolor("white")

    ax.hlines(0, min(years) - 1, max(years) + 1, color=LIGHT, linewidth=3, zorder=1)
    ax.scatter(years, [0]*len(years), c=colors, s=120, zorder=3)

    for i, (yr, lbl, col) in enumerate(zip(years, labels, colors)):
        offset = 0.35 if i % 2 == 0 else -0.45
        ax.annotate(lbl, (yr, 0), textcoords="offset points",
                    xytext=(0, offset * 80),
                    ha="center", va="center", fontsize=6.5, color=col, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=col, lw=0.8))

    legend_patches = [mpatches.Patch(color=c, label=k.title())
                      for k, c in EVENT_COLOR.items()
                      if any(e.event_type == k for e in events)]
    ax.legend(handles=legend_patches, fontsize=6, loc="upper right",
              bbox_to_anchor=(1, 1.5), ncol=len(legend_patches), frameon=False)

    ax.set_xlim(min(years) - 1.5, max(years) + 1.5)
    ax.set_ylim(-1, 1)
    ax.axis("off")
    ax.set_title("Charter History", fontsize=9, fontweight="bold", color=NAVY, pad=2)
    fig.tight_layout()
    return _buf(fig)
