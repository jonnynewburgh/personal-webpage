"""
PDF story builder for FQHCProfile.
"""
from reportlab.platypus import Paragraph, Table, Spacer

from ..shared import (
    _img_from_buf, _row_style, build_header, build_footer,
    build_accountability_cell, GRAY, NAVY, TEAL,
)
from borrower_metrics.charts import (
    patient_volume_chart, payer_mix_chart, quality_measures_chart,
    fqhc_revenue_mix_chart, demographics_chart,
)


def build_story(profile, usable_w, usable_h, S):
    story = []

    # ── Header extra lines ────────────────────────────────────────────────
    extra = []
    info_parts = []
    if profile.number_of_sites:
        info_parts.append(f"Sites: <b>{profile.number_of_sites}</b>")
    if profile.ftca_deemed is not None:
        info_parts.append(f"FTCA Deemed: <b>{'Yes' if profile.ftca_deemed else 'No'}</b>")
    if profile.hrsa_grant:
        g = profile.hrsa_grant
        if g.grant_amount_annual:
            info_parts.append(f"330 Award: <b>${g.grant_amount_annual:,.0f}/yr</b>")
        if g.award_period_start and g.award_period_end:
            info_parts.append(f"(through {g.award_period_end})")
        if g.look_alike:
            info_parts.append("Look-Alike")
    if info_parts:
        extra.append(Paragraph("  |  ".join(info_parts), S["subtitle"]))
    if profile.service_area:
        extra.append(Paragraph(f"Service area: {profile.service_area}", S["subtitle"]))

    header_tbl, report_date = build_header(profile, usable_w, S, extra_lines=extra)
    story += [header_tbl, Spacer(1, 4)]

    # ── Pre-render charts ─────────────────────────────────────────────────
    vol_buf  = patient_volume_chart(profile.patient_history) \
               if profile.patient_history else None
    pay_buf  = payer_mix_chart(profile.payer_mix_history) \
               if profile.payer_mix_history else None
    qm_buf   = quality_measures_chart(profile.quality_measures) \
               if profile.quality_measures else None
    rev_buf  = fqhc_revenue_mix_chart(profile.revenue_mix_history) \
               if profile.revenue_mix_history else None
    demo_buf = demographics_chart(profile.demographics) \
               if profile.demographics else None

    # ── ROW 1: Patient volume | Payer mix ────────────────────────────────
    half_w = usable_w * 0.50

    vol_cell = [Paragraph("PATIENT VOLUME", S["section"])]
    if vol_buf:
        vol_cell.append(_img_from_buf(vol_buf, half_w - 8))
    else:
        vol_cell.append(Paragraph("No patient volume data provided.", S["small"]))

    pay_cell = [Paragraph("PAYER MIX", S["section"])]
    if pay_buf:
        pay_cell.append(_img_from_buf(pay_buf, half_w - 8))
    else:
        pay_cell.append(Paragraph("No payer mix data provided.", S["small"]))

    row1 = Table([[vol_cell, pay_cell]], colWidths=[half_w, half_w])
    row1.setStyle(_row_style())
    story += [row1, Spacer(1, 4)]

    # ── ROW 2: Clinical quality measures (full width) ─────────────────────
    qm_cell = [Paragraph(
        f"CLINICAL QUALITY MEASURES (UDS)" +
        (f" — {profile.quality_measures_year}" if profile.quality_measures_year else ""),
        S["section"]
    )]
    if qm_buf:
        qm_cell.append(_img_from_buf(qm_buf, usable_w - 8))
    else:
        qm_cell.append(Paragraph("No UDS quality measures provided.", S["small"]))

    row2 = Table([[qm_cell]], colWidths=[usable_w])
    row2.setStyle(_row_style())
    story += [row2, Spacer(1, 4)]

    # ── ROW 3: Revenue mix | HRSA/compliance summary ──────────────────────
    rev_w  = usable_w * 0.55
    info_w = usable_w * 0.45

    rev_cell = [Paragraph("REVENUE MIX", S["section"])]
    if rev_buf:
        rev_cell.append(_img_from_buf(rev_buf, rev_w - 8))
    elif demo_buf:
        rev_cell.append(_img_from_buf(demo_buf, rev_w - 8))
    else:
        rev_cell.append(Paragraph("No revenue mix data provided.", S["small"]))

    hrsa_cell = [Paragraph("HRSA / COMPLIANCE SUMMARY", S["section"])]
    hrsa_items = []
    if profile.hrsa_grant:
        g = profile.hrsa_grant
        if g.award_number:
            hrsa_items.append(Paragraph(f"<b>Award #:</b> {g.award_number}", S["body"]))
        if g.grant_amount_annual:
            hrsa_items.append(Paragraph(
                f"<b>Annual Grant:</b> ${g.grant_amount_annual:,.0f}", S["body"]))
        if g.award_period_start:
            period = f"{g.award_period_start}"
            if g.award_period_end:
                period += f"–{g.award_period_end}"
            hrsa_items.append(Paragraph(f"<b>Award Period:</b> {period}", S["body"]))
        hrsa_items.append(Paragraph(
            f"<b>HRSA Type:</b> {'Look-Alike' if g.look_alike else 'Section 330 Grantee'}",
            S["body"]
        ))
    if profile.ftca_deemed is not None:
        hrsa_items.append(Paragraph(
            f"<b>FTCA Deemed:</b> {'Yes' if profile.ftca_deemed else 'No'}", S["body"]
        ))
    if profile.last_osa_review_year:
        hrsa_items.append(Paragraph(
            f"<b>Last OSV:</b> {profile.last_osa_review_year}" +
            (f" — {profile.osa_outcome}" if profile.osa_outcome else ""),
            S["body"]
        ))
    if profile.accountability:
        a = profile.accountability
        hrsa_items.append(Paragraph(
            f"<b>Status ({a.rating_year}):</b> {a.rating}", S["body"]
        ))
        hrsa_items.append(Paragraph(f"<b>Framework:</b> {a.framework}", S["body"]))
        if a.notes:
            hrsa_items.append(Paragraph(a.notes, S["note"]))
    if not hrsa_items:
        hrsa_items.append(Paragraph("No HRSA data provided.", S["small"]))
    hrsa_cell.extend(hrsa_items)

    row3 = Table([[rev_cell, hrsa_cell]], colWidths=[rev_w, info_w])
    row3.setStyle(_row_style())
    story += [row3, Spacer(1, 4)]

    # ── ROW 4: Analyst notes ──────────────────────────────────────────────
    note_cell = [Paragraph("ANALYST NOTES", S["section"])]
    note_cell.append(
        Paragraph(profile.analyst_notes, S["note"]) if profile.analyst_notes
        else Paragraph("—", S["small"])
    )
    row4 = Table([[note_cell]], colWidths=[usable_w])
    row4.setStyle(_row_style())
    story.append(row4)

    # ── Footer ────────────────────────────────────────────────────────────
    story += build_footer(profile, usable_w, report_date, S)
    return story
