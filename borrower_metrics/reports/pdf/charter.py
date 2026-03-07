"""
PDF story builder for CharterSchoolProfile.
"""
from reportlab.platypus import Paragraph, Table, Spacer

from ..shared import (
    _img_from_buf, _row_style, build_header, build_footer,
    build_accountability_cell, GRAY, NAVY
)
from borrower_metrics.charts import (
    enrollment_chart, academic_chart, charter_timeline_chart,
    student_indicators_chart, demographics_chart,
)


def build_story(profile, usable_w, usable_h, S):
    story = []

    # ── Header ────────────────────────────────────────────────────────────
    extra = []
    if profile.authorizer:
        extra.append(Paragraph(
            f"Authorizer: <b>{profile.authorizer}</b>" +
            (f"  |  Grades: <b>{profile.grade_span}</b>" if profile.grade_span else "") +
            (f"  |  {profile.management_org_type or 'Mgmt'}: {profile.management_org}"
             if profile.management_org else "") +
            (f"  |  Facility: {profile.facility_status}" if profile.facility_status else ""),
            S["subtitle"]
        ))
    if profile.per_pupil_revenue:
        yr = f" ({profile.per_pupil_revenue_year})" if profile.per_pupil_revenue_year else ""
        extra.append(Paragraph(
            f"Per-Pupil Revenue{yr}: <b>${profile.per_pupil_revenue:,.0f}</b>", S["subtitle"]
        ))

    header_tbl, report_date = build_header(profile, usable_w, S, extra_lines=extra)
    story += [header_tbl, Spacer(1, 4)]

    # ── Pre-render charts ─────────────────────────────────────────────────
    enroll_buf   = enrollment_chart(profile.enrollment_history) \
                   if profile.enrollment_history else None
    acad_buf     = academic_chart(profile.academic_history) \
                   if profile.academic_history else None
    timeline_buf = charter_timeline_chart(profile.charter_events) \
                   if profile.charter_events else None
    demo_buf     = demographics_chart(profile.demographics) \
                   if profile.demographics else None
    ind_buf      = student_indicators_chart(
                       profile.free_reduced_lunch_pct,
                       profile.english_learners_pct,
                       profile.special_education_pct,
                   ) if any([profile.free_reduced_lunch_pct,
                              profile.english_learners_pct,
                              profile.special_education_pct]) else None

    # ── ROW 1: Charter events | Enrollment | Demographics + Indicators ────
    c1_w = usable_w * 0.20
    c2_w = usable_w * 0.38
    c3_w = usable_w * 0.42

    charter_cell = [Paragraph("CHARTER STATUS", S["section"])]
    if profile.charter_events:
        for ev in sorted(profile.charter_events, key=lambda e: e.year):
            icon = {"original":"◆","renewal":"✓","modification":"△",
                    "probation":"⚠","revocation":"✗"}.get(ev.event_type, "•")
            charter_cell.append(
                Paragraph(f"{icon} <b>{ev.event_type.title()}</b> ({ev.year}): {ev.description}",
                          S["body"])
            )
    else:
        charter_cell.append(Paragraph("No charter events on record.", S["small"]))

    enroll_cell = [Paragraph("ENROLLMENT", S["section"])]
    if enroll_buf:
        enroll_cell.append(_img_from_buf(enroll_buf, c2_w - 8))
    else:
        enroll_cell.append(Paragraph("No enrollment data provided.", S["small"]))

    demo_cell = [Paragraph("DEMOGRAPHICS", S["section"])]
    if demo_buf:
        demo_cell.append(_img_from_buf(demo_buf, c3_w * 0.52 - 4))
    if ind_buf:
        demo_cell.append(_img_from_buf(ind_buf, c3_w * 0.48 - 4))
    if not demo_buf and not ind_buf:
        demo_cell.append(Paragraph("No demographics data provided.", S["small"]))

    row1 = Table([[charter_cell, enroll_cell, demo_cell]],
                 colWidths=[c1_w, c2_w, c3_w])
    row1.setStyle(_row_style())
    story += [row1, Spacer(1, 4)]

    # ── ROW 2: Academic performance | Accountability ──────────────────────
    acad_w = usable_w * 0.65
    acct_w = usable_w * 0.35

    acad_cell = [Paragraph("ACADEMIC PERFORMANCE", S["section"])]
    if acad_buf:
        acad_cell.append(_img_from_buf(acad_buf, acad_w - 8))
        for ay in profile.academic_history:
            if ay.ela_growth or ay.math_growth:
                parts = []
                if ay.ela_growth:
                    parts.append(f"ELA SGP {ay.ela_growth:.0f}")
                if ay.math_growth:
                    parts.append(f"Math SGP {ay.math_growth:.0f}")
                acad_cell.append(
                    Paragraph(f"{ay.year} Growth — " + "  |  ".join(parts), S["small"])
                )
    else:
        acad_cell.append(Paragraph("No academic data provided.", S["small"]))

    acct_cell = build_accountability_cell(profile, S)

    row2 = Table([[acad_cell, acct_cell]], colWidths=[acad_w, acct_w])
    row2.setStyle(_row_style())
    story += [row2, Spacer(1, 4)]

    # ── ROW 3: Timeline | Analyst notes ──────────────────────────────────
    from reportlab.lib.units import inch
    tl_w   = usable_w * 0.60 if timeline_buf else 0
    note_w = usable_w - tl_w

    tl_cell   = []
    note_cell = [Paragraph("ANALYST NOTES", S["section"])]

    if timeline_buf:
        tl_cell += [
            Paragraph("CHARTER TIMELINE", S["section"]),
            _img_from_buf(timeline_buf, tl_w - 8, height=0.85 * inch),
        ]

    note_cell.append(
        Paragraph(profile.analyst_notes, S["note"]) if profile.analyst_notes
        else Paragraph("—", S["small"])
    )

    row3_data = [[tl_cell, note_cell]] if timeline_buf else [[note_cell]]
    row3_cols = [tl_w, note_w] if timeline_buf else [usable_w]
    row3 = Table(row3_data, colWidths=row3_cols)
    row3.setStyle(_row_style())
    story.append(row3)

    # ── Footer ────────────────────────────────────────────────────────────
    story += build_footer(profile, usable_w, report_date, S)
    return story
