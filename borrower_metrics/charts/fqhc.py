"""
Chart functions for FQHC profiles.
"""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .shared import _buf, revenue_mix_stacked_bar, NAVY, TEAL, GOLD, GRAY, GREEN, RED, PURPLE


def patient_volume_chart(patient_history) -> io.BytesIO:
    """
    Dual-bar chart: unique patients (solid NAVY) and total visits (TEAL outline) per year.
    Visits-per-patient ratio annotated on a secondary axis.
    """
    years    = [p.year for p in patient_history]
    patients = [p.total_patients for p in patient_history]
    visits   = [p.patient_visits for p in patient_history]
    ratios   = [v / p for v, p in zip(visits, patients)]

    x = np.arange(len(years))
    w = 0.35

    fig, ax1 = plt.subplots(figsize=(4.5, 2.6))
    fig.patch.set_facecolor("white")

    b1 = ax1.bar(x - w/2, patients, w, label="Unique Patients", color=NAVY,   zorder=3)
    b2 = ax1.bar(x + w/2, visits,   w, label="Total Visits",    color=TEAL,   zorder=3,
                 edgecolor="white", linewidth=0.5)
    ax1.bar_label(b1, fmt="%,.0f", padding=2, fontsize=5.5, color=NAVY, rotation=90)
    ax1.bar_label(b2, fmt="%,.0f", padding=2, fontsize=5.5, color=TEAL, rotation=90)

    ax2 = ax1.twinx()
    ax2.plot(x, ratios, color=GOLD, linewidth=1.5, marker="o", markersize=4,
             label="Visits / Patient", zorder=4)
    ax2.set_ylabel("Visits / Patient", fontsize=7, color=GOLD)
    ax2.tick_params(axis="y", labelsize=6.5, colors=GOLD)
    ax2.spines["right"].set_color(GOLD)

    ax1.set_xticks(x)
    ax1.set_xticklabels(years, fontsize=7, rotation=30)
    ax1.set_ylabel("Count", fontsize=7, color=GRAY)
    ax1.set_title("Patient Volume", fontsize=9, fontweight="bold", color=NAVY, pad=6)
    ax1.yaxis.grid(True, linestyle=":", linewidth=0.5, alpha=0.7, zorder=0)
    ax1.set_axisbelow(True)
    ax1.spines[["top"]].set_visible(False)
    ax1.tick_params(axis="y", labelsize=7)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=6, loc="upper left",
               framealpha=0.8, ncol=3)
    fig.tight_layout()
    return _buf(fig)


def payer_mix_chart(payer_mix_history) -> io.BytesIO:
    """Stacked horizontal bar chart of payer distribution per year."""
    years = [p.year for p in payer_mix_history]
    series = {
        "Medicaid":           [p.medicaid_pct for p in payer_mix_history],
        "Medicare":           [p.medicare_pct for p in payer_mix_history],
        "Private Insurance":  [p.private_insurance_pct for p in payer_mix_history],
        "Uninsured/Sliding Fee": [p.uninsured_sliding_fee_pct for p in payer_mix_history],
        "Other":              [p.other_pct for p in payer_mix_history],
    }
    return revenue_mix_stacked_bar(years, series, title="Payer Mix")


def quality_measures_chart(quality_measures) -> io.BytesIO:
    """
    Horizontal bar chart of UDS quality measures vs. national benchmarks.
    GREEN if meeting/beating benchmark, RED if below, GOLD if no benchmark.
    """
    if not quality_measures:
        fig, ax = plt.subplots(figsize=(4.5, 2.2))
        ax.text(0.5, 0.5, "No quality measures provided", ha="center",
                va="center", transform=ax.transAxes, color=GRAY, fontsize=8)
        ax.axis("off")
        return _buf(fig)

    names  = [qm.name for qm in quality_measures]
    rates  = [qm.rate for qm in quality_measures]

    def bar_color(qm):
        if qm.national_benchmark is None:
            return GOLD
        if qm.direction == "lower_is_better":
            return GREEN if qm.rate <= qm.national_benchmark else RED
        return GREEN if qm.rate >= qm.national_benchmark else RED

    clrs = [bar_color(qm) for qm in quality_measures]

    fig_h = max(2.2, 0.42 * len(names) + 0.8)
    fig, ax = plt.subplots(figsize=(5.0, fig_h))
    fig.patch.set_facecolor("white")

    y_pos = np.arange(len(names))
    ax.barh(y_pos, rates, color=clrs, height=0.55, zorder=3)
    ax.bar_label(ax.containers[0], fmt="%.1f%%", padding=3,
                 fontsize=6.5, color=GRAY)

    # Benchmark reference line per measure
    for i, qm in enumerate(quality_measures):
        if qm.national_benchmark is not None:
            ax.plot([qm.national_benchmark, qm.national_benchmark],
                    [i - 0.35, i + 0.35], color="black",
                    linewidth=1.5, linestyle="--", zorder=4)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=6.5)
    ax.set_xlabel("Rate (%)", fontsize=7, color=GRAY)
    ax.set_xlim(0, 115)
    ax.set_title("Clinical Quality Measures (UDS)", fontsize=9,
                 fontweight="bold", color=NAVY, pad=6)
    ax.xaxis.grid(True, linestyle=":", linewidth=0.5, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=7)

    # Legend
    import matplotlib.patches as mpatches
    legend_items = [
        mpatches.Patch(color=GREEN, label="Meets/exceeds benchmark"),
        mpatches.Patch(color=RED,   label="Below benchmark"),
        mpatches.Patch(color=GOLD,  label="No benchmark"),
    ]
    ax.legend(handles=legend_items, fontsize=6, loc="lower right", frameon=False)
    fig.tight_layout()
    return _buf(fig)


def revenue_mix_chart(revenue_mix_history) -> io.BytesIO:
    """Stacked bar chart of FQHC revenue sources per year."""
    years = [r.year for r in revenue_mix_history]
    series = {
        "330 Grant":        [r.grant_330_pct for r in revenue_mix_history],
        "Medicaid":         [r.medicaid_pct for r in revenue_mix_history],
        "Medicare":         [r.medicare_pct for r in revenue_mix_history],
        "Private Ins.":     [r.private_insurance_pct for r in revenue_mix_history],
        "Patient Fees":     [r.patient_fees_pct for r in revenue_mix_history],
        "Other":            [r.other_pct for r in revenue_mix_history],
    }
    return revenue_mix_stacked_bar(years, series, title="Revenue Mix")
