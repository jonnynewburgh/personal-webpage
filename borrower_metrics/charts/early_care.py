"""
Chart functions for early care & education profiles.
"""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .shared import _buf, revenue_mix_stacked_bar, NAVY, TEAL, GOLD, GRAY, GREEN, RED, PURPLE


def age_group_enrollment_chart(age_group_history) -> io.BytesIO:
    """
    Grouped bar chart of enrollment by age group and year.
    """
    if not age_group_history:
        fig, ax = plt.subplots(figsize=(4.2, 2.6))
        ax.text(0.5, 0.5, "No enrollment data", ha="center", va="center",
                transform=ax.transAxes, color=GRAY, fontsize=8)
        ax.axis("off")
        return _buf(fig)

    # Collect unique years and age groups
    years      = sorted(set(e.year for e in age_group_history))
    age_groups = list(dict.fromkeys(e.age_group for e in age_group_history))  # preserve order
    colors     = [NAVY, TEAL, GOLD, GREEN][:len(age_groups)]

    # Build matrix: rows = years, cols = age groups
    data = {}
    for e in age_group_history:
        data[(e.year, e.age_group)] = e.enrolled

    x = np.arange(len(years))
    n = len(age_groups)
    w = 0.7 / n

    fig, ax = plt.subplots(figsize=(4.5, 2.6))
    fig.patch.set_facecolor("white")

    for i, (ag, color) in enumerate(zip(age_groups, colors)):
        vals = [data.get((yr, ag), 0) for yr in years]
        offset = (i - (n - 1) / 2) * w
        bars = ax.bar(x + offset, vals, w * 0.9, label=ag, color=color, zorder=3)
        ax.bar_label(bars, fmt="%d", padding=2, fontsize=5.5, color=color)

    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=7, rotation=30)
    ax.set_ylabel("Children", fontsize=7, color=GRAY)
    ax.set_title("Enrollment by Age Group", fontsize=9, fontweight="bold", color=NAVY, pad=6)
    ax.legend(fontsize=6, loc="upper left", framealpha=0.8)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.5, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    return _buf(fig)


def revenue_mix_chart(revenue_mix_history) -> io.BytesIO:
    """Stacked bar or pie chart of ECE revenue/subsidy sources."""
    years = [r.year for r in revenue_mix_history]
    series = {
        "CCDF":            [r.ccdf_pct for r in revenue_mix_history],
        "Head Start":      [r.head_start_pct for r in revenue_mix_history],
        "State Pre-K":     [r.state_prek_pct for r in revenue_mix_history],
        "Private Tuition": [r.private_tuition_pct for r in revenue_mix_history],
        "Other Grants":    [r.other_grants_pct for r in revenue_mix_history],
        "Other":           [r.other_pct for r in revenue_mix_history],
    }
    return revenue_mix_stacked_bar(years, series, title="Revenue / Subsidy Mix")


def school_readiness_chart(outcomes) -> io.BytesIO:
    """
    Horizontal grouped bar chart: borrower rate vs. benchmark per domain.
    """
    if not outcomes:
        fig, ax = plt.subplots(figsize=(4.5, 2.2))
        ax.text(0.5, 0.5, "No school readiness data", ha="center", va="center",
                transform=ax.transAxes, color=GRAY, fontsize=8)
        ax.axis("off")
        return _buf(fig)

    # Group by domain, show most recent year
    by_domain = {}
    for o in outcomes:
        by_domain[o.domain] = o  # last one wins (chronological order assumed)

    domains    = list(by_domain.keys())
    rates      = [by_domain[d].pct_on_track or 0 for d in domains]
    benchmarks = [by_domain[d].benchmark_pct for d in domains]
    tool       = outcomes[-1].assessment_tool if outcomes else ""

    y_pos = np.arange(len(domains))
    fig_h = max(2.2, 0.45 * len(domains) + 0.8)
    fig, ax = plt.subplots(figsize=(4.5, fig_h))
    fig.patch.set_facecolor("white")

    def bar_color(rate, bench):
        if bench is None:
            return GOLD
        return GREEN if rate >= bench else RED

    clrs = [bar_color(r, b) for r, b in zip(rates, benchmarks)]
    bars = ax.barh(y_pos, rates, color=clrs, height=0.45, zorder=3, label="Program Rate")
    ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=6.5, color=GRAY)

    for i, bm in enumerate(benchmarks):
        if bm is not None:
            ax.plot([bm, bm], [i - 0.3, i + 0.3], color="black",
                    linewidth=1.5, linestyle="--", zorder=4)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(domains, fontsize=7)
    ax.set_xlabel("% On Track", fontsize=7, color=GRAY)
    ax.set_xlim(0, 115)
    title = f"School Readiness ({tool})" if tool else "School Readiness Outcomes"
    ax.set_title(title, fontsize=9, fontweight="bold", color=NAVY, pad=6)
    ax.xaxis.grid(True, linestyle=":", linewidth=0.5, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=7)

    import matplotlib.patches as mpatches
    ax.legend(handles=[
        mpatches.Patch(color=GREEN, label="At/above benchmark"),
        mpatches.Patch(color=RED,   label="Below benchmark"),
    ], fontsize=6, loc="lower right", frameon=False)
    fig.tight_layout()
    return _buf(fig)


def staff_qualifications_chart(qualifications) -> io.BytesIO:
    """
    Line chart: BA+ % (NAVY), CDA % (TEAL), turnover rate % (RED dashed).
    """
    if not qualifications:
        fig, ax = plt.subplots(figsize=(3.5, 2.2))
        ax.text(0.5, 0.5, "No staff data", ha="center", va="center",
                transform=ax.transAxes, color=GRAY, fontsize=8)
        ax.axis("off")
        return _buf(fig)

    years    = [q.year for q in qualifications]
    ba_plus  = [q.bachelors_or_higher_pct for q in qualifications]
    cda      = [q.cda_pct for q in qualifications]
    turnover = [q.annual_turnover_rate for q in qualifications]

    fig, ax = plt.subplots(figsize=(3.5, 2.2))
    fig.patch.set_facecolor("white")

    ax.plot(years, ba_plus, color=NAVY, linewidth=1.8, marker="o", markersize=4,
            label="BA+ %")
    ax.plot(years, cda,     color=TEAL, linewidth=1.8, marker="s", markersize=4,
            label="CDA %")
    if any(t is not None for t in turnover):
        safe_to = [t if t is not None else np.nan for t in turnover]
        ax.plot(years, safe_to, color=RED, linewidth=1.5, marker="^", markersize=4,
                linestyle="--", label="Turnover %")

    ax.set_ylabel("%", fontsize=7, color=GRAY)
    ax.set_ylim(0, 110)
    ax.set_title("Staff Qualifications", fontsize=9, fontweight="bold", color=NAVY, pad=6)
    ax.tick_params(labelsize=7, axis="x", rotation=30)
    ax.tick_params(axis="y", labelsize=7)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.5, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=6, loc="lower right", framealpha=0.8)
    fig.tight_layout()
    return _buf(fig)
