"""
PDF story builder for EarlyCareProfile.
"""
from reportlab.platypus import Paragraph, Table, Spacer

from ..shared import (
    _img_from_buf, _row_style, _rating_style, build_header, build_footer,
    build_accountability_cell, GRAY, NAVY, GREEN, GOLD, RED,
)
from borrower_metrics.charts import (
    age_group_enrollment_chart, early_care_revenue_mix_chart,
    school_readiness_chart, staff_qualifications_chart, demographics_chart,
)


def build_story(profile, usable_w, usable_h, S):
    story = []

    # ── Header extra lines ────────────────────────────────────────────────
    extra = []
    qris_parts = []
    if profile.qris_rating:
        qris_parts.append(f"QRIS: <b>{profile.qris_rating}</b>")
    if profile.qris_framework:
        qris_parts.append(f"({profile.qris_framework})")
    if profile.qris_rating_year:
        qris_parts.append(profile.qris_rating_year)
    if qris_parts:
        extra.append(Paragraph("  ".join(qris_parts), S["subtitle"]))

    prog_parts = []
    if profile.head_start_grantee:
        prog_parts.append("Head Start Grantee")
    if profile.early_head_start_grantee:
        prog_parts.append("Early Head Start Grantee")
    if profile.licensed_capacity_total:
        prog_parts.append(f"Licensed Capacity: <b>{profile.licensed_capacity_total}</b>")
    if profile.number_of_classrooms:
        prog_parts.append(f"Classrooms: <b>{profile.number_of_classrooms}</b>")
    if prog_parts:
        extra.append(Paragraph("  |  ".join(prog_parts), S["subtitle"]))

    header_tbl, report_date = build_header(profile, usable_w, S, extra_lines=extra)
    story += [header_tbl, Spacer(1, 4)]

    # ── Pre-render charts ─────────────────────────────────────────────────
    enroll_buf = age_group_enrollment_chart(profile.age_group_enrollment_history) \
                 if profile.age_group_enrollment_history else None
    rev_buf    = early_care_revenue_mix_chart(profile.revenue_mix_history) \
                 if profile.revenue_mix_history else None
    sr_buf     = school_readiness_chart(profile.school_readiness_outcomes) \
                 if profile.school_readiness_outcomes else None
    staff_buf  = staff_qualifications_chart(profile.staff_qualifications_history) \
                 if profile.staff_qualifications_history else None
    demo_buf   = demographics_chart(profile.demographics) \
                 if profile.demographics else None

    # ── ROW 1: Age-group enrollment | Revenue mix ─────────────────────────
    half_w = usable_w * 0.50

    enroll_cell = [Paragraph("ENROLLMENT BY AGE GROUP", S["section"])]
    if enroll_buf:
        enroll_cell.append(_img_from_buf(enroll_buf, half_w - 8))
    else:
        enroll_cell.append(Paragraph("No enrollment data provided.", S["small"]))

    rev_cell = [Paragraph("REVENUE / SUBSIDY MIX", S["section"])]
    if rev_buf:
        rev_cell.append(_img_from_buf(rev_buf, half_w - 8))
    else:
        rev_cell.append(Paragraph("No revenue data provided.", S["small"]))

    row1 = Table([[enroll_cell, rev_cell]], colWidths=[half_w, half_w])
    row1.setStyle(_row_style())
    story += [row1, Spacer(1, 4)]

    # ── ROW 2: School readiness (full width) ──────────────────────────────
    sr_cell = [Paragraph("SCHOOL READINESS OUTCOMES", S["section"])]
    if sr_buf:
        sr_cell.append(_img_from_buf(sr_buf, usable_w - 8))
    else:
        sr_cell.append(Paragraph("No school readiness data provided.", S["small"]))

    row2 = Table([[sr_cell]], colWidths=[usable_w])
    row2.setStyle(_row_style())
    story += [row2, Spacer(1, 4)]

    # ── ROW 3: Staff qualifications | Service indicators ──────────────────
    staff_w = usable_w * 0.45
    ind_w   = usable_w * 0.55

    staff_cell = [Paragraph("STAFF QUALIFICATIONS", S["section"])]
    if staff_buf:
        staff_cell.append(_img_from_buf(staff_buf, staff_w - 8))
    else:
        staff_cell.append(Paragraph("No staff qualifications data provided.", S["small"]))

    svc_cell = [Paragraph("SERVICE INDICATORS & DEMOGRAPHICS", S["section"])]
    svc_items = []
    if profile.subsidized_enrollment_pct is not None:
        svc_items.append(Paragraph(
            f"<b>Subsidized Enrollment:</b> {profile.subsidized_enrollment_pct:.1f}%", S["body"]
        ))
    if profile.income_eligible_pct is not None:
        svc_items.append(Paragraph(
            f"<b>Income Eligible (at threshold):</b> {profile.income_eligible_pct:.1f}%", S["body"]
        ))
    if profile.english_learners_pct is not None:
        svc_items.append(Paragraph(
            f"<b>English Learners:</b> {profile.english_learners_pct:.1f}%", S["body"]
        ))
    if profile.special_education_pct is not None:
        svc_items.append(Paragraph(
            f"<b>Special Education (IEP/504):</b> {profile.special_education_pct:.1f}%", S["body"]
        ))
    if profile.last_monitoring_year:
        svc_items.append(Paragraph(
            f"<b>Last Monitoring ({profile.last_monitoring_year}):</b> "
            f"{profile.monitoring_outcome or '—'}",
            S["body"]
        ))
    svc_cell.extend(svc_items if svc_items else [Paragraph("—", S["small"])])
    if demo_buf:
        svc_cell.append(_img_from_buf(demo_buf, ind_w * 0.55 - 4))

    row3 = Table([[staff_cell, svc_cell]], colWidths=[staff_w, ind_w])
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

    story += build_footer(profile, usable_w, report_date, S)
    return story
