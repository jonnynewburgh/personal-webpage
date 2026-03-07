#!/usr/bin/env python3
"""
Borrower Metrics Tool — CLI entry point.

Usage examples:

  # List available samples
  python cli.py samples

  # Generate reports for a built-in sample
  python cli.py sample fqhc --out ./output
  python cli.py sample charter_school --out ./output
  python cli.py sample early_care --out ./output
  python cli.py sample nonprofit --out ./output

  # Generate reports from a JSON file
  python cli.py from-json my_borrower.json --out ./output

  # Export a blank JSON template for a given borrower type
  python cli.py export-template fqhc fqhc_template.json
"""
import json
import dataclasses
import sys
import click

from borrower_metrics.generate import generate_reports
from borrower_metrics.models import (
    BaseBorrowerProfile, LoanInfo, Demographics, AccountabilityStatus,
    # Charter
    CharterSchoolProfile, CharterEvent, EnrollmentYear, AcademicYear,
    # FQHC
    FQHCProfile, PatientYear, PayerMix, FQHCRevenueMix, QualityMeasure, HRSAGrantInfo,
    # Early Care
    EarlyCareProfile, AgeGroupEnrollment, EarlyCareRevenueMix,
    StaffQualifications, SchoolReadinessOutcome,
    # Nonprofit
    NonprofitProfile, RevenueYear, NonprofitRevenueMix, ProgramMetric,
)
from borrower_metrics.sample_data import ALL_SAMPLES


# ── Type-aware JSON deserializer ───────────────────────────────────────────

PROFILE_CLASSES = {
    "charter_school": CharterSchoolProfile,
    "fqhc":           FQHCProfile,
    "early_care":     EarlyCareProfile,
    "nonprofit":      NonprofitProfile,
}


def _load_profile(data: dict) -> BaseBorrowerProfile:
    org_type = data.get("org_type")
    if org_type not in PROFILE_CLASSES:
        raise ValueError(
            f"Unknown org_type '{org_type}'. "
            f"Must be one of: {list(PROFILE_CLASSES.keys())}"
        )

    # Common optional sub-objects
    loan = LoanInfo(**data["loan"]) if data.get("loan") else None
    demo_raw = data.get("demographics")
    demographics = Demographics(**demo_raw) if demo_raw else None
    acct_raw = data.get("accountability")
    accountability = AccountabilityStatus(**acct_raw) if acct_raw else None

    base = dict(
        name=data["name"],
        org_type=org_type,
        location=data.get("location", ""),
        ein=data.get("ein"),
        website=data.get("website"),
        year_founded=data.get("year_founded"),
        analyst_notes=data.get("analyst_notes", ""),
        prepared_by=data.get("prepared_by", ""),
        report_date=data.get("report_date", ""),
        loan=loan,
        demographics=demographics,
        accountability=accountability,
    )

    if org_type == "charter_school":
        return CharterSchoolProfile(
            **base,
            authorizer=data.get("authorizer"),
            grade_span=data.get("grade_span"),
            management_org=data.get("management_org"),
            management_org_type=data.get("management_org_type"),
            facility_status=data.get("facility_status"),
            per_pupil_revenue=data.get("per_pupil_revenue"),
            per_pupil_revenue_year=data.get("per_pupil_revenue_year"),
            free_reduced_lunch_pct=data.get("free_reduced_lunch_pct"),
            english_learners_pct=data.get("english_learners_pct"),
            special_education_pct=data.get("special_education_pct"),
            charter_events=[CharterEvent(**e) for e in data.get("charter_events", [])],
            enrollment_history=[EnrollmentYear(**e) for e in data.get("enrollment_history", [])],
            academic_history=[AcademicYear(**a) for a in data.get("academic_history", [])],
        )

    if org_type == "fqhc":
        hrsa_raw = data.get("hrsa_grant")
        hrsa_grant = HRSAGrantInfo(**hrsa_raw) if hrsa_raw else None
        return FQHCProfile(
            **base,
            hrsa_grant=hrsa_grant,
            ftca_deemed=data.get("ftca_deemed"),
            number_of_sites=data.get("number_of_sites"),
            service_area=data.get("service_area"),
            patient_history=[PatientYear(**p) for p in data.get("patient_history", [])],
            payer_mix_history=[PayerMix(**p) for p in data.get("payer_mix_history", [])],
            revenue_mix_history=[FQHCRevenueMix(**r) for r in data.get("revenue_mix_history", [])],
            quality_measures=[QualityMeasure(**q) for q in data.get("quality_measures", [])],
            quality_measures_year=data.get("quality_measures_year"),
            last_osa_review_year=data.get("last_osa_review_year"),
            osa_outcome=data.get("osa_outcome"),
        )

    if org_type == "early_care":
        return EarlyCareProfile(
            **base,
            qris_rating=data.get("qris_rating"),
            qris_framework=data.get("qris_framework"),
            qris_rating_year=data.get("qris_rating_year"),
            head_start_grantee=data.get("head_start_grantee", False),
            early_head_start_grantee=data.get("early_head_start_grantee", False),
            licensed_capacity_total=data.get("licensed_capacity_total"),
            number_of_classrooms=data.get("number_of_classrooms"),
            subsidized_enrollment_pct=data.get("subsidized_enrollment_pct"),
            english_learners_pct=data.get("english_learners_pct"),
            special_education_pct=data.get("special_education_pct"),
            income_eligible_pct=data.get("income_eligible_pct"),
            age_group_enrollment_history=[
                AgeGroupEnrollment(**e) for e in data.get("age_group_enrollment_history", [])
            ],
            revenue_mix_history=[
                EarlyCareRevenueMix(**r) for r in data.get("revenue_mix_history", [])
            ],
            staff_qualifications_history=[
                StaffQualifications(**q) for q in data.get("staff_qualifications_history", [])
            ],
            school_readiness_outcomes=[
                SchoolReadinessOutcome(**o) for o in data.get("school_readiness_outcomes", [])
            ],
            last_monitoring_year=data.get("last_monitoring_year"),
            monitoring_outcome=data.get("monitoring_outcome"),
            deficiency_history=data.get("deficiency_history"),
        )

    if org_type == "nonprofit":
        return NonprofitProfile(
            **base,
            mission_summary=data.get("mission_summary"),
            primary_program_area=data.get("primary_program_area"),
            clients_served_annually=data.get("clients_served_annually"),
            clients_served_year=data.get("clients_served_year"),
            operating_reserve_months=data.get("operating_reserve_months"),
            operating_reserve_year=data.get("operating_reserve_year"),
            revenue_history=[RevenueYear(**r) for r in data.get("revenue_history", [])],
            revenue_mix_history=[
                NonprofitRevenueMix(**r) for r in data.get("revenue_mix_history", [])
            ],
            program_metrics=[ProgramMetric(**m) for m in data.get("program_metrics", [])],
            last_audit_year=data.get("last_audit_year"),
            audit_outcome=data.get("audit_outcome"),
            irs_form_990_year=data.get("irs_form_990_year"),
        )


# ── JSON templates (minimal placeholder data per type) ─────────────────────

TEMPLATES = {
    "charter_school": {
        "org_type": "charter_school",
        "name": "Your Charter School Name",
        "location": "City, State",
        "ein": "XX-XXXXXXX",
        "website": "https://example.org",
        "year_founded": 2005,
        "prepared_by": "Analyst Name",
        "report_date": "",
        "analyst_notes": "Enter narrative underwriting notes here.",
        "authorizer": "Name of Authorizing Agency",
        "grade_span": "K-8",
        "management_org": None,
        "management_org_type": None,
        "facility_status": "Leasing",
        "per_pupil_revenue": None,
        "per_pupil_revenue_year": None,
        "free_reduced_lunch_pct": None,
        "english_learners_pct": None,
        "special_education_pct": None,
        "charter_events": [
            {"year": 2015, "event_type": "original",
             "description": "Initial charter granted.", "authorizer": None}
        ],
        "enrollment_history": [
            {"year": "2022-23", "total": 400, "capacity": 450},
            {"year": "2023-24", "total": 420, "capacity": 450}
        ],
        "demographics": {
            "black": 50.0, "hispanic": 25.0, "white": 10.0,
            "asian": 5.0, "other": 10.0
        },
        "academic_history": [
            {"year": "2022-23", "ela_proficiency": 40.0, "math_proficiency": 35.0,
             "ela_growth": 52.0, "math_growth": 50.0,
             "graduation_rate": None, "attendance_rate": 93.5},
            {"year": "2023-24", "ela_proficiency": 44.0, "math_proficiency": 38.0,
             "ela_growth": 54.0, "math_growth": 52.0,
             "graduation_rate": None, "attendance_rate": 94.2}
        ],
        "accountability": {
            "rating_year": "2023-24", "rating": "Recognized",
            "framework": "ESSA / State Accountability",
            "subgroup_flags": [], "notes": ""
        },
        "loan": {
            "amount": 5000000, "purpose": "Describe use of proceeds.",
            "financing_type": "NMTC", "proposed_term_years": 7,
            "collateral": "First mortgage on facility."
        }
    },

    "fqhc": {
        "org_type": "fqhc",
        "name": "Your Health Center Name",
        "location": "City, State",
        "ein": "XX-XXXXXXX",
        "website": "https://example.org",
        "year_founded": 1998,
        "prepared_by": "Analyst Name",
        "report_date": "",
        "analyst_notes": "Enter narrative underwriting notes here.",
        "number_of_sites": 1,
        "ftca_deemed": True,
        "service_area": "Describe the geographic service area.",
        "hrsa_grant": {
            "award_number": "H80CSXXXXX",
            "grant_amount_annual": 1500000,
            "award_period_start": "2022",
            "award_period_end": "2027",
            "look_alike": False
        },
        "last_osa_review_year": "2023",
        "osa_outcome": "Approved",
        "patient_history": [
            {"year": "FY 2023", "total_patients": 10000, "patient_visits": 32000,
             "new_patients": 2000, "sliding_fee_patients": 3500},
            {"year": "FY 2024", "total_patients": 11000, "patient_visits": 35000,
             "new_patients": 2200, "sliding_fee_patients": 3700}
        ],
        "payer_mix_history": [
            {"year": "FY 2023", "medicaid_pct": 58.0, "medicare_pct": 8.0,
             "private_insurance_pct": 12.0, "uninsured_sliding_fee_pct": 19.0, "other_pct": 3.0},
            {"year": "FY 2024", "medicaid_pct": 60.0, "medicare_pct": 8.0,
             "private_insurance_pct": 11.0, "uninsured_sliding_fee_pct": 18.0, "other_pct": 3.0}
        ],
        "revenue_mix_history": [
            {"year": "FY 2023", "grant_330_pct": 25.0, "medicaid_pct": 45.0,
             "medicare_pct": 8.0, "private_insurance_pct": 10.0,
             "patient_fees_pct": 9.0, "other_pct": 3.0},
            {"year": "FY 2024", "grant_330_pct": 24.0, "medicaid_pct": 47.0,
             "medicare_pct": 8.0, "private_insurance_pct": 10.0,
             "patient_fees_pct": 8.0, "other_pct": 3.0}
        ],
        "quality_measures": [
            {"name": "Diabetes Control (HbA1c < 9%)", "rate": 70.0,
             "national_benchmark": 70.0, "direction": "higher_is_better",
             "uds_measure_id": "QM 10"}
        ],
        "quality_measures_year": "UDS 2024",
        "demographics": {
            "black": 55.0, "hispanic": 18.0, "white": 15.0,
            "asian": 5.0, "other": 7.0
        },
        "accountability": {
            "rating_year": "2024", "rating": "Approved",
            "framework": "HRSA Health Center Program / UDS",
            "subgroup_flags": [], "notes": ""
        },
        "loan": {
            "amount": 8000000, "purpose": "Describe use of proceeds.",
            "financing_type": "NMTC", "proposed_term_years": 7,
            "collateral": "First mortgage on clinic building."
        }
    },

    "early_care": {
        "org_type": "early_care",
        "name": "Your Early Care Program Name",
        "location": "City, State",
        "ein": "XX-XXXXXXX",
        "website": "https://example.org",
        "year_founded": 2005,
        "prepared_by": "Analyst Name",
        "report_date": "",
        "analyst_notes": "Enter narrative underwriting notes here.",
        "qris_rating": "4-Star",
        "qris_framework": "State QRIS Framework Name",
        "qris_rating_year": "2024",
        "head_start_grantee": False,
        "early_head_start_grantee": False,
        "licensed_capacity_total": 100,
        "number_of_classrooms": 6,
        "subsidized_enrollment_pct": 80.0,
        "income_eligible_pct": 90.0,
        "english_learners_pct": None,
        "special_education_pct": None,
        "last_monitoring_year": "2024",
        "monitoring_outcome": "No Findings",
        "age_group_enrollment_history": [
            {"year": "2023-24", "age_group": "Infant (0-12mo)", "enrolled": 10, "licensed_capacity": 12},
            {"year": "2023-24", "age_group": "Toddler (1-3yr)", "enrolled": 26, "licensed_capacity": 28},
            {"year": "2023-24", "age_group": "Preschool (3-5yr)", "enrolled": 60, "licensed_capacity": 60}
        ],
        "revenue_mix_history": [
            {"year": "FY 2024", "ccdf_pct": 40.0, "head_start_pct": 0.0,
             "state_prek_pct": 15.0, "private_tuition_pct": 35.0,
             "other_grants_pct": 7.0, "other_pct": 3.0}
        ],
        "staff_qualifications_history": [
            {"year": "2023-24", "bachelors_or_higher_pct": 55.0, "cda_pct": 30.0,
             "annual_turnover_rate": 20.0}
        ],
        "school_readiness_outcomes": [
            {"year": "2023-24", "assessment_tool": "Teaching Strategies GOLD",
             "domain": "Literacy", "pct_on_track": 70.0, "benchmark_pct": 68.0},
            {"year": "2023-24", "assessment_tool": "Teaching Strategies GOLD",
             "domain": "Math", "pct_on_track": 65.0, "benchmark_pct": 65.0}
        ],
        "demographics": {
            "black": 55.0, "hispanic": 20.0, "white": 12.0,
            "asian": 4.0, "other": 9.0
        },
        "accountability": {
            "rating_year": "2024", "rating": "4-Star",
            "framework": "State QRIS Framework",
            "subgroup_flags": [], "notes": ""
        },
        "loan": {
            "amount": 3000000, "purpose": "Describe use of proceeds.",
            "financing_type": "NMTC", "proposed_term_years": 7,
            "collateral": "Leasehold mortgage; childcare subsidy receivables."
        }
    },

    "nonprofit": {
        "org_type": "nonprofit",
        "name": "Your Nonprofit Name",
        "location": "City, State",
        "ein": "XX-XXXXXXX",
        "website": "https://example.org",
        "year_founded": 1995,
        "prepared_by": "Analyst Name",
        "report_date": "",
        "analyst_notes": "Enter narrative underwriting notes here.",
        "mission_summary": "Brief mission statement.",
        "primary_program_area": "Food Security / Housing / Workforce / etc.",
        "clients_served_annually": 10000,
        "clients_served_year": "FY 2024",
        "operating_reserve_months": 3.5,
        "operating_reserve_year": "FY 2024",
        "last_audit_year": "FY 2024",
        "audit_outcome": "Unmodified (clean)",
        "irs_form_990_year": "FY 2023",
        "revenue_history": [
            {"year": "FY 2022", "total_revenue": 4000000, "total_expenses": 3800000, "net_assets": 2000000},
            {"year": "FY 2023", "total_revenue": 4500000, "total_expenses": 4200000, "net_assets": 2300000},
            {"year": "FY 2024", "total_revenue": 5000000, "total_expenses": 4600000, "net_assets": 2700000}
        ],
        "revenue_mix_history": [
            {"year": "FY 2024", "government_grants_pct": 50.0, "foundation_grants_pct": 20.0,
             "corporate_contributions_pct": 8.0, "individual_contributions_pct": 10.0,
             "earned_revenue_pct": 9.0, "other_pct": 3.0}
        ],
        "program_metrics": [
            {"name": "Clients served", "value": "10,000", "year": "FY 2024", "notes": None}
        ],
        "accountability": {
            "rating_year": "2024", "rating": "Accredited",
            "framework": "Relevant accrediting body",
            "subgroup_flags": [], "notes": ""
        },
        "loan": {
            "amount": 5000000, "purpose": "Describe use of proceeds.",
            "financing_type": "NMTC", "proposed_term_years": 7,
            "collateral": "First mortgage on facility."
        }
    },
}


# ── CLI commands ───────────────────────────────────────────────────────────

@click.group()
def cli():
    """Borrower Metrics Tool — generate PDF + Excel reports for loan underwriting."""


@cli.command("samples")
def list_samples():
    """List available built-in sample borrower profiles."""
    click.echo("\nAvailable samples:")
    for key, profile in ALL_SAMPLES.items():
        click.echo(f"  {key:20s}  →  {profile.name}")
    click.echo('\nRun: python cli.py sample <key> --out ./output\n')


@cli.command("sample")
@click.argument("key", type=click.Choice(list(ALL_SAMPLES.keys())))
@click.option("--out", default="./output", show_default=True,
              help="Output directory for PDF and Excel files.")
def run_sample(key, out):
    """Generate reports for a built-in sample borrower."""
    profile = ALL_SAMPLES[key]
    click.echo(f"Generating reports for: {profile.name}")
    pdf, xlsx = generate_reports(profile, output_dir=out)
    click.secho(f"  PDF   → {pdf}",  fg="green")
    click.secho(f"  Excel → {xlsx}", fg="green")


@cli.command("from-json")
@click.argument("json_file", type=click.Path(exists=True, readable=True))
@click.option("--out", default="./output", show_default=True,
              help="Output directory for PDF and Excel files.")
@click.option("--stem", default=None,
              help="Output filename stem (default: derived from borrower name).")
def run_from_json(json_file, out, stem):
    """Generate reports from a JSON file describing a borrower profile."""
    with open(json_file) as f:
        data = json.load(f)

    try:
        profile = _load_profile(data)
    except (ValueError, KeyError, TypeError) as e:
        click.secho(f"Error loading profile: {e}", fg="red", err=True)
        sys.exit(1)

    click.echo(f"Generating reports for: {profile.name} [{profile.org_type}]")
    pdf, xlsx = generate_reports(profile, output_dir=out, stem=stem)
    click.secho(f"  PDF   → {pdf}",  fg="green")
    click.secho(f"  Excel → {xlsx}", fg="green")


@cli.command("export-template")
@click.argument("org_type",
                type=click.Choice(list(TEMPLATES.keys())))
@click.argument("output_file", default="borrower_template.json")
def export_template(org_type, output_file):
    """Export a JSON template for a given borrower type to fill in."""
    template = TEMPLATES[org_type]
    with open(output_file, "w") as f:
        json.dump(template, f, indent=2)
    click.secho(f"Template written to: {output_file}", fg="cyan")
    click.echo(f"Org type: {org_type}")
    click.echo("Fill in the values and run: python cli.py from-json <file> --out ./output")


if __name__ == "__main__":
    cli()
