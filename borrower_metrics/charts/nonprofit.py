"""
Chart functions for generic nonprofit profiles.
"""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .shared import _buf, revenue_mix_stacked_bar, NAVY, TEAL, GOLD, GRAY, GREEN, RED


def revenue_history_chart(revenue_history) -> io.BytesIO:
    """
    Line chart of total revenue vs. total expenses over time.
    Net surplus/deficit area shaded.
    """
    if not revenue_history:
        fig, ax = plt.subplots(figsize=(4.2, 2.6))
        ax.text(0.5, 0.5, "No revenue history", ha="center", va="center",
                transform=ax.transAxes, color=GRAY, fontsize=8)
        ax.axis("off")
        return _buf(fig)

    years    = [r.year for r in revenue_history]
    revenues = [r.total_revenue / 1_000_000 for r in revenue_history]
    expenses = [r.total_expenses / 1_000_000 if r.total_expenses else None
                for r in revenue_history]

    fig, ax = plt.subplots(figsize=(4.2, 2.6))
    fig.patch.set_facecolor("white")

    ax.plot(years, revenues, color=NAVY, linewidth=2, marker="o", markersize=4,
            label="Revenue", zorder=3)

    if any(e is not None for e in expenses):
        safe_exp = [e if e is not None else np.nan for e in expenses]
        ax.plot(years, safe_exp, color=RED, linewidth=2, marker="s", markersize=4,
                linestyle="--", label="Expenses", zorder=3)
        # Shade surplus/deficit
        rev_arr = np.array(revenues)
        exp_arr = np.array([e if e is not None else r
                            for e, r in zip(expenses, revenues)])
        ax.fill_between(years, rev_arr, exp_arr,
                        where=(rev_arr >= exp_arr), alpha=0.15, color=GREEN,
                        label="Surplus")
        ax.fill_between(years, rev_arr, exp_arr,
                        where=(rev_arr < exp_arr), alpha=0.15, color=RED,
                        label="Deficit")

    ax.set_ylabel("$M", fontsize=7, color=GRAY)
    ax.set_title("Revenue & Expense Trend", fontsize=9, fontweight="bold",
                 color=NAVY, pad=6)
    ax.tick_params(axis="x", labelsize=7, rotation=30)
    ax.tick_params(axis="y", labelsize=7)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.5, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=6, loc="upper left", framealpha=0.8)
    fig.tight_layout()
    return _buf(fig)


def revenue_mix_chart(revenue_mix_history) -> io.BytesIO:
    """Stacked bar chart of nonprofit revenue by source."""
    years = [r.year for r in revenue_mix_history]
    series = {
        "Government Grants":    [r.government_grants_pct for r in revenue_mix_history],
        "Foundation Grants":    [r.foundation_grants_pct for r in revenue_mix_history],
        "Corporate":            [r.corporate_contributions_pct for r in revenue_mix_history],
        "Individual":           [r.individual_contributions_pct for r in revenue_mix_history],
        "Earned Revenue":       [r.earned_revenue_pct for r in revenue_mix_history],
        "Other":                [r.other_pct for r in revenue_mix_history],
    }
    return revenue_mix_stacked_bar(years, series, title="Revenue Mix")
