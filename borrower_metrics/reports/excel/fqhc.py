"""
Excel sheet builders for FQHCProfile.
"""
from .shared import (
    _header_row, _data_row, _pct, _set_col_widths, _embed_chart,
    _section_header, _font, NAVY_HEX, GREEN_HEX, RED_HEX, GOLD_HEX,
)
from borrower_metrics.charts import (
    patient_volume_chart, payer_mix_chart, quality_measures_chart,
    fqhc_revenue_mix_chart, demographics_chart,
)


def build_sheets(wb, profile) -> None:
    if profile.patient_history:
        _sheet_patient_volume(wb, profile)
    if profile.payer_mix_history:
        _sheet_payer_mix(wb, profile)
    if profile.revenue_mix_history:
        _sheet_revenue_mix(wb, profile)
    if profile.quality_measures:
        _sheet_clinical_quality(wb, profile)
    if profile.demographics:
        _sheet_demographics(wb, profile)
    if profile.accountability:
        _sheet_accountability(wb, profile)


def _sheet_patient_volume(wb, profile):
    ws = wb.create_sheet("Patient Volume")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, [
        "Year", "Total Patients", "Patient Visits",
        "New Patients", "Sliding Fee Patients", "Visits / Patient"
    ])
    for i, p in enumerate(profile.patient_history, start=2):
        ratio = p.patient_visits / p.total_patients if p.total_patients else None
        _data_row(ws, i, [
            p.year,
            f"{p.total_patients:,}",
            f"{p.patient_visits:,}",
            f"{p.new_patients:,}" if p.new_patients else "—",
            f"{p.sliding_fee_patients:,}" if p.sliding_fee_patients else "—",
            f"{ratio:.2f}" if ratio else "—",
        ], alt=(i % 2 == 0))

    _set_col_widths(ws, [12, 16, 16, 16, 20, 16])

    buf = patient_volume_chart(profile.patient_history)
    _embed_chart(ws, buf, "H2", width=440, height=260)


def _sheet_payer_mix(wb, profile):
    ws = wb.create_sheet("Payer Mix")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, [
        "Year", "Medicaid %", "Medicare %",
        "Private Insurance %", "Uninsured / Sliding Fee %", "Other %"
    ])
    for i, p in enumerate(profile.payer_mix_history, start=2):
        _data_row(ws, i, [
            p.year,
            _pct(p.medicaid_pct), _pct(p.medicare_pct),
            _pct(p.private_insurance_pct), _pct(p.uninsured_sliding_fee_pct),
            _pct(p.other_pct),
        ], alt=(i % 2 == 0))

    _set_col_widths(ws, [12, 14, 14, 22, 26, 12])

    buf = payer_mix_chart(profile.payer_mix_history)
    _embed_chart(ws, buf, "H2", width=440, height=260)


def _sheet_revenue_mix(wb, profile):
    ws = wb.create_sheet("Revenue Mix")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, [
        "Year", "330 Grant %", "Medicaid %", "Medicare %",
        "Private Insurance %", "Patient Fees %", "Other %"
    ])
    for i, r in enumerate(profile.revenue_mix_history, start=2):
        _data_row(ws, i, [
            r.year,
            _pct(r.grant_330_pct), _pct(r.medicaid_pct), _pct(r.medicare_pct),
            _pct(r.private_insurance_pct), _pct(r.patient_fees_pct), _pct(r.other_pct),
        ], alt=(i % 2 == 0))

    _set_col_widths(ws, [12, 14, 14, 14, 22, 16, 12])

    buf = fqhc_revenue_mix_chart(profile.revenue_mix_history)
    _embed_chart(ws, buf, "I2", width=440, height=260)


def _sheet_clinical_quality(wb, profile):
    ws = wb.create_sheet("Clinical Quality (UDS)")
    ws.sheet_view.showGridLines = False

    year_note = f" — {profile.quality_measures_year}" if profile.quality_measures_year else ""
    _section_header(ws, 1,
                    f"UDS Clinical Quality Measures{year_note}",
                    n_cols=5, fill_hex=NAVY_HEX)
    _header_row(ws, 2, [
        "Measure", "Rate (%)", "National Benchmark (%)", "Direction", "vs. Benchmark"
    ])

    for i, qm in enumerate(profile.quality_measures, start=3):
        bm = qm.national_benchmark
        if bm is not None:
            if qm.direction == "lower_is_better":
                gap_label = f"{'✓ Better' if qm.rate <= bm else '✗ Below'} ({qm.rate - bm:+.1f}%)"
            else:
                gap_label = f"{'✓ Better' if qm.rate >= bm else '✗ Below'} ({qm.rate - bm:+.1f}%)"
        else:
            gap_label = "No benchmark"

        _data_row(ws, i, [
            qm.name,
            f"{qm.rate:.1f}%",
            f"{bm:.1f}%" if bm is not None else "—",
            qm.direction.replace("_", " ").title(),
            gap_label,
        ], alt=(i % 2 == 0))

        # Color the gap cell
        gap_cell = ws.cell(row=i, column=5)
        if "✓" in gap_label:
            gap_cell.font = _font(bold=True, color=GREEN_HEX)
        elif "✗" in gap_label:
            gap_cell.font = _font(bold=True, color=RED_HEX)

    _set_col_widths(ws, [40, 14, 26, 22, 24])

    buf = quality_measures_chart(profile.quality_measures)
    _embed_chart(ws, buf, "G3", width=480, height=280)


def _sheet_demographics(wb, profile):
    ws = wb.create_sheet("Demographics")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, ["Category", "Percentage"])
    d = profile.demographics
    race_data = [
        ("Black / African American", d.black),
        ("Hispanic / Latino",        d.hispanic),
        ("White",                    d.white),
        ("Asian",                    d.asian),
        ("Other / Multiracial",      d.other),
    ]
    for i, (label, val) in enumerate(race_data, start=2):
        _data_row(ws, i, [label, _pct(val)], alt=(i % 2 == 0))

    _set_col_widths(ws, [36, 18])
    buf = demographics_chart(profile.demographics)
    _embed_chart(ws, buf, "D2", width=300, height=200)


def _sheet_accountability(wb, profile):
    ws = wb.create_sheet("Regulatory Status")
    ws.sheet_view.showGridLines = False

    a = profile.accountability
    fields = [
        ("Status",    a.rating),
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
    if any(w in rl for w in ["approved","meets","good","commended"]):
        rating_cell.font = _font(bold=True, color=GREEN_HEX, size=12)
    elif any(w in rl for w in ["improvement","probation","revoked","adverse"]):
        rating_cell.font = _font(bold=True, color=RED_HEX, size=12)
    else:
        rating_cell.font = _font(bold=True, color=GOLD_HEX, size=12)

    _set_col_widths(ws, [22, 60])
