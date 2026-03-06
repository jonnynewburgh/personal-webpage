"""
Excel sheet builders for NonprofitProfile.
"""
from .shared import (
    _header_row, _data_row, _pct, _set_col_widths, _embed_chart,
    _section_header, _font, NAVY_HEX, GREEN_HEX, RED_HEX, GOLD_HEX,
)
from borrower_metrics.charts import (
    revenue_history_chart, nonprofit_revenue_mix_chart,
)


def build_sheets(wb, profile) -> None:
    if profile.revenue_history:
        _sheet_revenue_history(wb, profile)
    if profile.revenue_mix_history:
        _sheet_revenue_mix(wb, profile)
    if profile.program_metrics:
        _sheet_program_metrics(wb, profile)
    _sheet_financial_summary(wb, profile)


def _sheet_revenue_history(wb, profile):
    ws = wb.create_sheet("Revenue History")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, ["Year", "Total Revenue", "Total Expenses", "Net Surplus / (Deficit)", "Net Assets"])
    for i, r in enumerate(profile.revenue_history, start=2):
        net = (r.total_revenue - r.total_expenses) if r.total_expenses else None
        _data_row(ws, i, [
            r.year,
            f"${r.total_revenue:,.0f}",
            f"${r.total_expenses:,.0f}" if r.total_expenses else "—",
            f"${net:,.0f}" if net is not None else "—",
            f"${r.net_assets:,.0f}" if r.net_assets else "—",
        ], alt=(i % 2 == 0))

        # Color the surplus/deficit cell
        if net is not None:
            cell = ws.cell(row=i, column=4)
            cell.font = _font(bold=True, color=GREEN_HEX if net >= 0 else RED_HEX)

    _set_col_widths(ws, [12, 18, 18, 26, 18])

    buf = revenue_history_chart(profile.revenue_history)
    _embed_chart(ws, buf, "G2", width=440, height=260)


def _sheet_revenue_mix(wb, profile):
    ws = wb.create_sheet("Revenue Mix")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, [
        "Year", "Government Grants %", "Foundation Grants %",
        "Corporate %", "Individual %", "Earned Revenue %", "Other %"
    ])
    for i, r in enumerate(profile.revenue_mix_history, start=2):
        _data_row(ws, i, [
            r.year,
            _pct(r.government_grants_pct), _pct(r.foundation_grants_pct),
            _pct(r.corporate_contributions_pct), _pct(r.individual_contributions_pct),
            _pct(r.earned_revenue_pct), _pct(r.other_pct),
        ], alt=(i % 2 == 0))

    _set_col_widths(ws, [12, 22, 22, 15, 15, 20, 12])

    buf = nonprofit_revenue_mix_chart(profile.revenue_mix_history)
    _embed_chart(ws, buf, "I2", width=440, height=260)


def _sheet_program_metrics(wb, profile):
    ws = wb.create_sheet("Program Metrics")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, ["Metric Name", "Value", "Year", "Notes"])
    for i, pm in enumerate(profile.program_metrics, start=2):
        _data_row(ws, i, [
            pm.name, pm.value, pm.year or "—", pm.notes or "—"
        ], alt=(i % 2 == 0))

    _set_col_widths(ws, [36, 20, 12, 40])


def _sheet_financial_summary(wb, profile):
    ws = wb.create_sheet("Financial Summary")
    ws.sheet_view.showGridLines = False

    _header_row(ws, 1, ["Field", "Value"])
    fields = []
    if profile.operating_reserve_months is not None:
        fields.append(("Operating Reserve",
                        f"{profile.operating_reserve_months:.1f} months" +
                        (f" ({profile.operating_reserve_year})"
                         if profile.operating_reserve_year else "")))
    if profile.last_audit_year:
        fields.append(("Last Audit",
                        profile.last_audit_year +
                        (f" — {profile.audit_outcome}" if profile.audit_outcome else "")))
    if profile.irs_form_990_year:
        fields.append(("Form 990 Year", profile.irs_form_990_year))
    if profile.accountability:
        a = profile.accountability
        fields.append(("Accountability Status", a.rating))
        fields.append(("Framework", a.framework))
        fields.append(("Year", a.rating_year))
        if a.notes:
            fields.append(("Notes", a.notes))

    for i, (label, val) in enumerate(fields, start=2):
        _data_row(ws, i, [label, val], alt=(i % 2 == 0))
        ws.cell(row=i, column=1).font = _font(bold=True, color=NAVY_HEX)

    _set_col_widths(ws, [28, 60])
