"""
PDF story builder for NonprofitProfile.
"""
from reportlab.platypus import Paragraph, Table, Spacer

from ..shared import (
    _img_from_buf, _row_style, build_header, build_footer,
    build_accountability_cell, GRAY, NAVY,
)
from borrower_metrics.charts import (
    revenue_history_chart, nonprofit_revenue_mix_chart,
)


def build_story(profile, usable_w, usable_h, S):
    story = []

    # ── Header extra lines ────────────────────────────────────────────────
    extra = []
    if profile.mission_summary:
        extra.append(Paragraph(f"Mission: {profile.mission_summary}", S["subtitle"]))
    prog_parts = []
    if profile.primary_program_area:
        prog_parts.append(f"Program Area: <b>{profile.primary_program_area}</b>")
    if profile.clients_served_annually:
        yr = f" ({profile.clients_served_year})" if profile.clients_served_year else ""
        prog_parts.append(f"Clients Served{yr}: <b>{profile.clients_served_annually:,}</b>")
    if prog_parts:
        extra.append(Paragraph("  |  ".join(prog_parts), S["subtitle"]))

    header_tbl, report_date = build_header(profile, usable_w, S, extra_lines=extra)
    story += [header_tbl, Spacer(1, 4)]

    # ── Pre-render charts ─────────────────────────────────────────────────
    rev_hist_buf = revenue_history_chart(profile.revenue_history) \
                   if profile.revenue_history else None
    rev_mix_buf  = nonprofit_revenue_mix_chart(profile.revenue_mix_history) \
                   if profile.revenue_mix_history else None

    # ── ROW 1: Revenue history | Revenue mix ──────────────────────────────
    half_w = usable_w * 0.50

    hist_cell = [Paragraph("REVENUE & EXPENSE TREND", S["section"])]
    if rev_hist_buf:
        hist_cell.append(_img_from_buf(rev_hist_buf, half_w - 8))
    else:
        hist_cell.append(Paragraph("No revenue history provided.", S["small"]))

    mix_cell = [Paragraph("REVENUE MIX", S["section"])]
    if rev_mix_buf:
        mix_cell.append(_img_from_buf(rev_mix_buf, half_w - 8))
    else:
        mix_cell.append(Paragraph("No revenue mix data provided.", S["small"]))

    row1 = Table([[hist_cell, mix_cell]], colWidths=[half_w, half_w])
    row1.setStyle(_row_style())
    story += [row1, Spacer(1, 4)]

    # ── ROW 2: Program metrics (full width) ───────────────────────────────
    prog_cell = [Paragraph("PROGRAM METRICS", S["section"])]
    if profile.program_metrics:
        for pm in profile.program_metrics:
            yr = f" ({pm.year})" if pm.year else ""
            line = f"<b>{pm.name}{yr}:</b> {pm.value}"
            if pm.notes:
                line += f"  — {pm.notes}"
            prog_cell.append(Paragraph(line, S["body"]))
    else:
        prog_cell.append(Paragraph("No program metrics provided.", S["small"]))

    row2 = Table([[prog_cell]], colWidths=[usable_w])
    row2.setStyle(_row_style())
    story += [row2, Spacer(1, 4)]

    # ── ROW 3: Financial summary | Analyst notes ──────────────────────────
    fin_w  = usable_w * 0.38
    note_w = usable_w * 0.62

    fin_cell = [Paragraph("FINANCIAL SUMMARY", S["section"])]
    fin_items = []
    if profile.operating_reserve_months is not None:
        yr = f" ({profile.operating_reserve_year})" if profile.operating_reserve_year else ""
        fin_items.append(Paragraph(
            f"<b>Operating Reserve{yr}:</b> {profile.operating_reserve_months:.1f} months",
            S["body"]
        ))
    if profile.last_audit_year:
        fin_items.append(Paragraph(
            f"<b>Last Audit ({profile.last_audit_year}):</b> {profile.audit_outcome or '—'}",
            S["body"]
        ))
    if profile.irs_form_990_year:
        fin_items.append(Paragraph(
            f"<b>Most Recent Form 990:</b> {profile.irs_form_990_year}", S["body"]
        ))
    if profile.accountability:
        a = profile.accountability
        fin_items.append(Paragraph(
            f"<b>Accountability ({a.rating_year}):</b> {a.rating}", S["body"]
        ))
        fin_items.append(Paragraph(f"<b>Framework:</b> {a.framework}", S["body"]))
        if a.notes:
            fin_items.append(Paragraph(a.notes, S["note"]))
    fin_cell.extend(fin_items if fin_items else [Paragraph("—", S["small"])])

    note_cell = [Paragraph("ANALYST NOTES", S["section"])]
    note_cell.append(
        Paragraph(profile.analyst_notes, S["note"]) if profile.analyst_notes
        else Paragraph("—", S["small"])
    )

    row3 = Table([[fin_cell, note_cell]], colWidths=[fin_w, note_w])
    row3.setStyle(_row_style())
    story.append(row3)

    story += build_footer(profile, usable_w, report_date, S)
    return story
