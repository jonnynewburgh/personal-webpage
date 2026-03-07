"""
Excel sheet builders for CharterSchoolProfile.
"""
from .shared import (
    _header_row, _data_row, _pct, _set_col_widths, _embed_chart,
    _section_header, GREEN_HEX, RED_HEX, GOLD_HEX, NAVY_HEX, GRAY_HEX,
    _font,
)
from borrower_metrics.charts import (
    enrollment_chart, academic_chart, charter_timeline_chart,
    student_indicators_chart, demographics_chart,
)


def build_sheets(wb, profile) -> None:
    if profile.enrollment_history:
        _sheet_enrollment(wb, profile)
    if profile.demographics or any([
        profile.free_reduced_lunch_pct, profile.english_learners_pct, profile.special_education_pct
    ]):
        _sheet_demographics(wb, profile)
    if profile.academic_history:
        _sheet_academics(wb, profile)
    if profile.charter_events:
        _sheet_charter_log(wb, profile)
    if profile.accountability:
        _sheet_accountability(wb, profile)


def _sheet_enrollment(wb, profile):
    ws = wb.create_sheet("Enrollment")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, ["Year", "Enrollment", "Capacity", "Utilization %"])
    for i, e in enumerate(profile.enrollment_history, start=2):
        util = (e.total / e.capacity * 100) if e.capacity else None
        _data_row(ws, i, [
            e.year, e.total, e.capacity or "—",
            f"{util:.1f}%" if util else "—"
        ], alt=(i % 2 == 0))

    _set_col_widths(ws, [12, 14, 14, 16])
    buf = enrollment_chart(profile.enrollment_history)
    _embed_chart(ws, buf, "F2", width=400, height=240)


def _sheet_demographics(wb, profile):
    ws = wb.create_sheet("Demographics")
    ws.sheet_view.showGridLines = False

    row = 1
    _section_header(ws, row, "── Race / Ethnicity ──", n_cols=2, fill_hex="2A7F8F")
    row += 1
    _header_row(ws, row, ["Category", "Percentage"])
    row += 1

    if profile.demographics:
        d = profile.demographics
        race_data = [
            ("Black / African American", d.black),
            ("Hispanic / Latino",        d.hispanic),
            ("White",                    d.white),
            ("Asian",                    d.asian),
            ("Other / Multiracial",      d.other),
        ]
        for label, val in race_data:
            _data_row(ws, row, [label, _pct(val)], alt=(row % 2 == 0))
            row += 1

    row += 1
    _section_header(ws, row, "── Student Service Indicators ──", n_cols=2, fill_hex="2A7F8F")
    row += 1
    svc_data = [
        ("Free / Reduced Lunch (FRL)", profile.free_reduced_lunch_pct),
        ("English Language Learners (ELL)", profile.english_learners_pct),
        ("Special Education (IEP/504)",     profile.special_education_pct),
    ]
    for label, val in svc_data:
        _data_row(ws, row, [label, _pct(val)], alt=(row % 2 == 0))
        row += 1

    _set_col_widths(ws, [36, 18])

    if profile.demographics:
        buf = demographics_chart(profile.demographics)
        _embed_chart(ws, buf, "D2", width=300, height=200)
    if any([profile.free_reduced_lunch_pct, profile.english_learners_pct,
            profile.special_education_pct]):
        buf2 = student_indicators_chart(
            profile.free_reduced_lunch_pct,
            profile.english_learners_pct,
            profile.special_education_pct,
        )
        _embed_chart(ws, buf2, "D14", width=280, height=160)


def _sheet_academics(wb, profile):
    ws = wb.create_sheet("Academic Performance")
    ws.sheet_view.showGridLines = False

    headers = ["Year", "ELA Proficiency %", "Math Proficiency %",
               "ELA Growth (SGP)", "Math Growth (SGP)",
               "Graduation Rate %", "Attendance Rate %"]
    _header_row(ws, 1, headers)

    for i, a in enumerate(profile.academic_history, start=2):
        _data_row(ws, i, [
            a.year,
            _pct(a.ela_proficiency), _pct(a.math_proficiency),
            _pct(a.ela_growth),      _pct(a.math_growth),
            _pct(a.graduation_rate), _pct(a.attendance_rate),
        ], alt=(i % 2 == 0))

    _set_col_widths(ws, [12, 20, 20, 18, 18, 18, 18])

    buf = academic_chart(profile.academic_history)
    _embed_chart(ws, buf, "I2", width=460, height=260)


def _sheet_charter_log(wb, profile):
    ws = wb.create_sheet("Charter Log")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, ["Year", "Event Type", "Authorizer", "Description"])
    color_map = {
        "original":     NAVY_HEX,
        "renewal":      GREEN_HEX,
        "modification": GOLD_HEX,
        "probation":    RED_HEX,
        "revocation":   "8B0000",
    }
    for i, ev in enumerate(sorted(profile.charter_events, key=lambda e: e.year), start=2):
        _data_row(ws, i, [
            ev.year, ev.event_type.title(),
            ev.authorizer or profile.authorizer or "—",
            ev.description,
        ], alt=(i % 2 == 0))
        ws.cell(row=i, column=2).font = _font(
            bold=True, color=color_map.get(ev.event_type, GRAY_HEX)
        )

    _set_col_widths(ws, [8, 18, 24, 60])

    buf = charter_timeline_chart(profile.charter_events)
    anchor = "A" + str(len(profile.charter_events) + 4)
    _embed_chart(ws, buf, anchor, width=520, height=130)


def _sheet_accountability(wb, profile):
    ws = wb.create_sheet("Accountability")
    ws.sheet_view.showGridLines = False

    a = profile.accountability
    fields = [
        ("Rating",         a.rating),
        ("Framework",      a.framework),
        ("Rating Year",    a.rating_year),
        ("Subgroup Flags", ", ".join(a.subgroup_flags) if a.subgroup_flags else "None"),
        ("Notes",          a.notes or "—"),
    ]
    _header_row(ws, 1, ["Field", "Value"])
    for i, (label, val) in enumerate(fields, start=2):
        _data_row(ws, i, [label, val], alt=(i % 2 == 0))
        ws.cell(row=i, column=1).font = _font(bold=True, color=NAVY_HEX)

    rating_cell = ws.cell(row=2, column=2)
    rl = a.rating.lower()
    if any(w in rl for w in ["exemplary","recognized","meets","good","commended"]):
        rating_cell.font = _font(bold=True, color=GREEN_HEX, size=12)
    elif any(w in rl for w in ["improvement","probation","revoked","unsatisfactory"]):
        rating_cell.font = _font(bold=True, color=RED_HEX, size=12)
    else:
        rating_cell.font = _font(bold=True, color=GOLD_HEX, size=12)

    _set_col_widths(ws, [22, 60])
