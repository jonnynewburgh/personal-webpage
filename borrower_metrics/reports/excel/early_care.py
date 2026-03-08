"""
Excel sheet builders for EarlyCareProfile.
"""
from .shared import (
    _header_row, _data_row, _pct, _set_col_widths, _embed_chart,
    _section_header, _font, NAVY_HEX, GREEN_HEX, RED_HEX, GOLD_HEX,
)
from borrower_metrics.charts import (
    age_group_enrollment_chart, early_care_revenue_mix_chart,
    school_readiness_chart, staff_qualifications_chart, demographics_chart,
)


def build_sheets(wb, profile) -> None:
    if profile.age_group_enrollment_history:
        _sheet_enrollment(wb, profile)
    if profile.revenue_mix_history:
        _sheet_revenue_mix(wb, profile)
    if profile.school_readiness_outcomes:
        _sheet_school_readiness(wb, profile)
    if profile.staff_qualifications_history:
        _sheet_staff(wb, profile)
    if profile.demographics or any([
        profile.subsidized_enrollment_pct, profile.income_eligible_pct,
        profile.english_learners_pct, profile.special_education_pct,
    ]):
        _sheet_demographics(wb, profile)
    if profile.accountability:
        _sheet_accountability(wb, profile)


def _sheet_enrollment(wb, profile):
    ws = wb.create_sheet("Enrollment by Age Group")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, ["Year", "Age Group", "Enrolled", "Licensed Capacity", "Utilization %"])
    for i, e in enumerate(profile.age_group_enrollment_history, start=2):
        util = (e.enrolled / e.licensed_capacity * 100) if e.licensed_capacity else None
        _data_row(ws, i, [
            e.year, e.age_group, e.enrolled,
            e.licensed_capacity or "—",
            f"{util:.1f}%" if util else "—",
        ], alt=(i % 2 == 0))

    _set_col_widths(ws, [12, 22, 12, 18, 16])

    buf = age_group_enrollment_chart(profile.age_group_enrollment_history)
    _embed_chart(ws, buf, "G2", width=440, height=260)


def _sheet_revenue_mix(wb, profile):
    ws = wb.create_sheet("Revenue Mix")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, [
        "Year", "CCDF %", "Head Start %", "State Pre-K %",
        "Private Tuition %", "Other Grants %", "Other %"
    ])
    for i, r in enumerate(profile.revenue_mix_history, start=2):
        _data_row(ws, i, [
            r.year, _pct(r.ccdf_pct), _pct(r.head_start_pct), _pct(r.state_prek_pct),
            _pct(r.private_tuition_pct), _pct(r.other_grants_pct), _pct(r.other_pct),
        ], alt=(i % 2 == 0))

    _set_col_widths(ws, [12, 12, 16, 16, 20, 18, 12])

    buf = early_care_revenue_mix_chart(profile.revenue_mix_history)
    _embed_chart(ws, buf, "I2", width=440, height=260)


def _sheet_school_readiness(wb, profile):
    ws = wb.create_sheet("School Readiness")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, [
        "Year", "Assessment Tool", "Domain", "% On Track", "Benchmark %", "Gap"
    ])
    for i, o in enumerate(profile.school_readiness_outcomes, start=2):
        gap = None
        if o.pct_on_track is not None and o.benchmark_pct is not None:
            gap = o.pct_on_track - o.benchmark_pct
        _data_row(ws, i, [
            o.year, o.assessment_tool, o.domain,
            _pct(o.pct_on_track), _pct(o.benchmark_pct),
            f"{gap:+.1f}%" if gap is not None else "—",
        ], alt=(i % 2 == 0))

        if gap is not None:
            cell = ws.cell(row=i, column=6)
            cell.font = _font(bold=True, color=GREEN_HEX if gap >= 0 else RED_HEX)

    _set_col_widths(ws, [12, 26, 20, 14, 16, 12])

    buf = school_readiness_chart(profile.school_readiness_outcomes)
    _embed_chart(ws, buf, "H2", width=440, height=260)


def _sheet_staff(wb, profile):
    ws = wb.create_sheet("Staff Qualifications")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, ["Year", "BA+ %", "CDA %", "Annual Turnover %"])
    for i, q in enumerate(profile.staff_qualifications_history, start=2):
        _data_row(ws, i, [
            q.year,
            _pct(q.bachelors_or_higher_pct),
            _pct(q.cda_pct),
            _pct(q.annual_turnover_rate),
        ], alt=(i % 2 == 0))

    _set_col_widths(ws, [12, 12, 12, 20])

    buf = staff_qualifications_chart(profile.staff_qualifications_history)
    _embed_chart(ws, buf, "F2", width=360, height=220)


def _sheet_demographics(wb, profile):
    ws = wb.create_sheet("Demographics")
    ws.sheet_view.showGridLines = False

    row = 1
    if profile.demographics:
        _section_header(ws, row, "── Race / Ethnicity ──", n_cols=2, fill_hex="2A7F8F")
        row += 1
        _header_row(ws, row, ["Category", "Percentage"])
        row += 1
        d = profile.demographics
        for label, val in [
            ("Black / African American", d.black),
            ("Hispanic / Latino",        d.hispanic),
            ("White",                    d.white),
            ("Asian",                    d.asian),
            ("Other / Multiracial",      d.other),
        ]:
            _data_row(ws, row, [label, _pct(val)], alt=(row % 2 == 0))
            row += 1
        row += 1

    _section_header(ws, row, "── Service Indicators ──", n_cols=2, fill_hex="2A7F8F")
    row += 1
    svc_data = [
        ("Subsidized Enrollment %", profile.subsidized_enrollment_pct),
        ("Income Eligible %",       profile.income_eligible_pct),
        ("English Learners %",      profile.english_learners_pct),
        ("Special Education %",     profile.special_education_pct),
    ]
    for label, val in svc_data:
        _data_row(ws, row, [label, _pct(val)], alt=(row % 2 == 0))
        row += 1

    _set_col_widths(ws, [36, 18])
    if profile.demographics:
        buf = demographics_chart(profile.demographics)
        _embed_chart(ws, buf, "D2", width=300, height=200)


def _sheet_accountability(wb, profile):
    ws = wb.create_sheet("Quality Rating")
    ws.sheet_view.showGridLines = False

    a = profile.accountability
    fields = [
        ("Rating",    a.rating),
        ("Framework", a.framework),
        ("Year",      a.rating_year),
        ("Notes",     a.notes or "—"),
    ]
    _header_row(ws, 1, ["Field", "Value"])
    for i, (label, val) in enumerate(fields, start=2):
        _data_row(ws, i, [label, val], alt=(i % 2 == 0))
        ws.cell(row=i, column=1).font = _font(bold=True, color=NAVY_HEX)

    rating_cell = ws.cell(row=2, column=2)
    rl = a.rating.lower()
    if any(w in rl for w in ["4-star","5-star","level 4","level 5","excelling","top"]):
        rating_cell.font = _font(bold=True, color=GREEN_HEX, size=12)
    elif any(w in rl for w in ["1-star","level 1","unacceptable","probation"]):
        rating_cell.font = _font(bold=True, color=RED_HEX, size=12)
    else:
        rating_cell.font = _font(bold=True, color=GOLD_HEX, size=12)

    _set_col_widths(ws, [22, 60])
