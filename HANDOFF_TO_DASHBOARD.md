# Borrower Metrics Tool → CD Command Center Dashboard Handoff

## What This Tool Does

Generates **PDF and Excel reports** for loan underwriting, covering four borrower types:
- Charter Schools
- FQHCs (Federally Qualified Health Centers)
- Early Care centers
- Nonprofits

Each report includes visualizations (enrollment trends, academic performance, demographics charts) and structured data tables.

## Current Architecture

```
borrower_metrics/
├── models/           # Dataclass profiles for each org type
│   ├── base.py       # BaseBorrowerProfile (shared fields: name, EIN, loan info, demographics)
│   ├── charter.py    # CharterSchoolProfile (authorizer, enrollment, academics, charter events)
│   ├── fqhc.py       # FQHCProfile (UDS data, patient mix, quality measures)
│   ├── early_care.py # EarlyCareProfile (licensing, star rating, capacity)
│   └── nonprofit.py  # NonprofitProfile (990 data, program areas)
│
├── charts/           # Matplotlib chart generators → return BytesIO PNG buffers
│   ├── shared.py     # demographics_chart(), common styling
│   ├── charter.py    # enrollment_chart(), academic_chart(), charter_timeline_chart()
│   ├── fqhc.py       # patient_chart(), quality_chart()
│   ├── early_care.py # capacity_chart(), star_rating_chart()
│   └── nonprofit.py  # revenue_chart(), program_chart()
│
├── reports/
│   ├── pdf/          # ReportLab story builders per org type
│   └── excel/        # openpyxl workbook builders per org type
│
├── sample_data/      # Hardcoded example profiles (one per org type)
└── generate.py       # Orchestrator: generate_reports(profile) → (pdf_path, xlsx_path)
```

## Key Dependencies

| Package    | Purpose                        |
|------------|--------------------------------|
| reportlab  | PDF generation                 |
| matplotlib | Charts (PNG buffers)           |
| openpyxl   | Excel generation               |
| Pillow     | Image handling for charts      |

## What to Keep vs. Replace

### KEEP (valuable logic)
- **`models/`** — The dataclass schemas are well-designed. Charter model aligns closely with dashboard's existing `schools`, `charter_authorizers`, `authorizer_verdicts` tables.
- **`charts/`** — Matplotlib chart generators can be reused server-side or replaced with Recharts on frontend.
- **`reports/pdf/`** — PDF layout logic for downloadable reports.
- **`reports/excel/`** — Excel export logic.

### REPLACE
- **`sample_data/`** — Hardcoded fake data. Dashboard will pull real data from Postgres.
- **`app.py`** — Flask UI. Dashboard already has Next.js frontend + FastAPI backend.
- **`templates/index.html`** — Static HTML. Not needed.

## Integration Strategy

### Phase 1: Backend API (FastAPI)

Add endpoints to `cd-command-center-dashboard/backend/`:

```python
# routers/reports.py
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

class LoanInfoRequest(BaseModel):
    amount: float
    purpose: str
    financing_type: str  # "NMTC" | "HTC" | "Conventional" | "NMTC + HTC"
    proposed_term_years: Optional[int] = None
    collateral: Optional[str] = None

@router.post("/reports/{org_type}/{id}")
async def generate_report(
    org_type: Literal["charter", "fqhc", "early_care", "nonprofit"],
    id: str,
    format: Literal["pdf", "xlsx"],
    loan: Optional[LoanInfoRequest] = None,
    analyst_notes: str = "",
) -> StreamingResponse:
    """
    1. Query relevant tables for id (e.g., schools + school_accountability for charter)
    2. Build typed profile (CharterSchoolProfile, FQHCProfile, etc.)
    3. Generate report to BytesIO buffer
    4. Return StreamingResponse (no temp files)
    5. Persist to cloud storage for audit trail
    """
```

Publish `borrower_metrics` as an internal wheel (like `cdcc_db`) — avoids drift between repos.

### Phase 2: Data Mapping

| Borrower Metrics Field       | Dashboard Source                                      |
|------------------------------|-------------------------------------------------------|
| `name`, `location`           | `schools.name`, `schools.city + ', ' + schools.state` |
| `authorizer`                 | `charter_authorizers.name`                            |
| `grade_span`                 | `schools.lowest_grade` + `schools.highest_grade`      |
| `enrollment_history`         | `enrollment_history` table (already exists)           |
| `academic_history`           | `school_accountability` (proficiency scores)          |
| `accountability.rating`      | `authorizer_verdicts.verdict`                         |
| `demographics`               | `schools.pct_black`, `pct_hispanic`, etc.             |
| `free_reduced_lunch_pct`     | `schools.free_lunch_eligible + reduced_price_eligible`|
| `charter_events`             | NEW TABLE needed (charter renewals/modifications)     |
| `loan`                       | User input at report-generation time                  |
| `analyst_notes`              | User input at report-generation time                  |

### Phase 3: Frontend

Add a "Generate Report" button on org detail pages:
- `/schools/[nces_id]` → "Download Charter Report (PDF | Excel)"
- `/fqhcs/[id]` → "Download FQHC Report (PDF | Excel)"

Can be a simple dropdown + fetch to `/api/reports/{type}/{id}?format=pdf`.

## Missing Data for Full Reports

1. **Charter Events** — No table for charter renewals/modifications. Would need `charter_events(school_id, year, event_type, description)`.
2. ~~**Historical Enrollment**~~ — ✅ `enrollment_history` table exists with `get_enrollment_history(nces_id)` accessor.
3. ~~**FQHC UDS Data**~~ — ✅ `fqhc_uds_reports` table has patient counts, quality measures, payer mix. FQHC reports are nearly ready.
4. **Early Care Licensing** — `ece_centers` table is sparse. Needs more data.
5. **Nonprofit 990 Financials** — Partial coverage via existing 990 loaders (`irs_990_history`).

## Recommended First Step

Start with **Charter School reports** since the dashboard already has:
- `schools` with demographics
- `school_accountability` with test scores
- `charter_authorizers` + `authorizer_verdicts`
- `enrollment_history` with multi-year enrollment data

Minimal new work: add `charter_events` table, wire up the PDF generator, add a download button.

**FQHC reports are a close second** — `fqhc_uds_reports` already has patient/quality/payer data.

## Files to Copy

```
borrower_metrics/
├── __init__.py
├── generate.py
├── models/
├── charts/
└── reports/
```

Ignore: `sample_data/`, `app.py`, `templates/`, `cli.py`, `briefing.py`, `game.html`, `index.html`

## Notes

- The tool also contains unrelated code: `briefing.py` (morning briefing via Groq/Twilio) and `game.html`. Ignore these.
- `consent.jhnadvising.com` is served from this app's `/consent` route — leave as-is for now.

## Audit Trail

Generated reports should be persisted to cloud storage (S3/GCS) with metadata:
- `org_type`, `org_id`, `format`, `generated_at`, `generated_by`
- Enables compliance review and regeneration comparison
