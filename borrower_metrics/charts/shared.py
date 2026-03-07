"""
Shared chart utilities: palette, buffer helper, race/ethnicity demographics chart,
and reusable stacked-bar revenue mix helper.
"""
import io
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ── Brand palette ───────────────────────────────────────────────────────────
NAVY   = "#1B3A6B"
TEAL   = "#2A7F8F"
GOLD   = "#C8952A"
LIGHT  = "#E8EDF4"
GRAY   = "#6C757D"
GREEN  = "#2E7D4F"
RED    = "#C0392B"
PURPLE = "#7B5EA7"

REVENUE_COLORS = [NAVY, TEAL, GREEN, GOLD, PURPLE, GRAY]


def _buf(fig) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf


def demographics_chart(demo) -> io.BytesIO:
    """Race/ethnicity pie chart only (service indicators are org-type-specific)."""
    race_labels = ["Black", "Hispanic", "White", "Asian", "Other"]
    race_vals   = [demo.black, demo.hispanic, demo.white, demo.asian, demo.other]
    colors      = [NAVY, TEAL, GOLD, GREEN, GRAY]

    pairs = [(l, v, c) for l, v, c in zip(race_labels, race_vals, colors) if v > 0]
    if not pairs:
        fig, ax = plt.subplots(figsize=(3.0, 2.2))
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
        return _buf(fig)

    labels, vals, clrs = zip(*pairs)

    fig, ax = plt.subplots(figsize=(3.0, 2.2))
    fig.patch.set_facecolor("white")

    wedges, texts, autotexts = ax.pie(
        vals, labels=None, colors=clrs,
        autopct=lambda p: f"{p:.0f}%" if p >= 5 else "",
        startangle=90, pctdistance=0.75,
        wedgeprops={"linewidth": 0.5, "edgecolor": "white"}
    )
    for at in autotexts:
        at.set_fontsize(6.5)
    ax.legend(wedges, labels, fontsize=6, loc="lower center",
              bbox_to_anchor=(0.5, -0.20), ncol=3, frameon=False)
    ax.set_title("Race / Ethnicity", fontsize=8, fontweight="bold", color=NAVY, pad=4)
    fig.tight_layout()
    return _buf(fig)


def revenue_mix_stacked_bar(
    years: list[str],
    pct_series: dict[str, list[float]],
    title: str = "Revenue Mix",
    figsize: tuple = (4.5, 2.6),
) -> io.BytesIO:
    """
    Generic stacked horizontal bar chart for revenue/subsidy mix.
    pct_series: {label: [pct_year0, pct_year1, ...]}  (same order as years)
    """
    labels = list(pct_series.keys())
    data   = [pct_series[l] for l in labels]
    n_years = len(years)
    colors = REVENUE_COLORS[:len(labels)]

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("white")

    lefts = [0.0] * n_years
    for i, (label, vals, color) in enumerate(zip(labels, data, colors)):
        bars = ax.barh(years, vals, left=lefts, color=color, label=label,
                       height=0.5, edgecolor="white", linewidth=0.5)
        # Label segments ≥ 10%
        for bar, val in zip(bars, vals):
            if val >= 10:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_y() + bar.get_height() / 2,
                        f"{val:.0f}%", ha="center", va="center",
                        fontsize=6, color="white", fontweight="bold")
        lefts = [l + v for l, v in zip(lefts, vals)]

    ax.set_xlim(0, 110)
    ax.set_xlabel("% of total", fontsize=7, color=GRAY)
    ax.set_title(title, fontsize=9, fontweight="bold", color=NAVY, pad=6)
    ax.tick_params(labelsize=7)
    ax.xaxis.grid(True, linestyle=":", linewidth=0.5, alpha=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=6, loc="lower right", bbox_to_anchor=(1.0, -0.35),
              ncol=3, frameon=False)
    fig.tight_layout()
    return _buf(fig)
