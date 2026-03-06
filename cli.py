#!/usr/bin/env python3
"""
Borrower Metrics Tool — CLI entry point.

Usage examples:

  # Generate reports for a built-in sample
  python cli.py sample charter_school --out ./output

  # Generate reports from a JSON file
  python cli.py from-json my_borrower.json --out ./output

  # List available samples
  python cli.py samples
"""
import json
import sys
import click

from borrower_metrics.generate import generate_reports
from borrower_metrics.models import (
    BorrowerProfile, CharterEvent, EnrollmentYear,
    Demographics, AcademicYear, AccountabilityStatus, LoanInfo
)
from borrower_metrics.sample_data import ALL_SAMPLES


# ── JSON → model helpers ───────────────────────────────────────────────────

def _profile_from_dict(d: dict) -> BorrowerProfile:
    """
    Build a BorrowerProfile from a plain dict (e.g. loaded from JSON).
    All sub-objects are optional; missing keys are silently skipped.
    """
    charter_events = [
        CharterEvent(**e) for e in d.get("charter_events", [])
    ]
    enrollment_history = [
        EnrollmentYear(**e) for e in d.get("enrollment_history", [])
    ]
    demo_raw = d.get("demographics")
    demographics = Demographics(**demo_raw) if demo_raw else None

    acad_history = [
        AcademicYear(**a) for a in d.get("academic_history", [])
    ]
    acct_raw = d.get("accountability")
    accountability = AccountabilityStatus(**acct_raw) if acct_raw else None

    loan_raw = d.get("loan")
    loan = LoanInfo(**loan_raw) if loan_raw else None

    return BorrowerProfile(
        name=d["name"],
        org_type=d.get("org_type", "nonprofit"),
        location=d.get("location", ""),
        ein=d.get("ein"),
        website=d.get("website"),
        year_founded=d.get("year_founded"),
        authorizer=d.get("authorizer"),
        grade_span=d.get("grade_span"),
        charter_events=charter_events,
        enrollment_history=enrollment_history,
        demographics=demographics,
        academic_history=acad_history,
        accountability=accountability,
        loan=loan,
        analyst_notes=d.get("analyst_notes", ""),
        prepared_by=d.get("prepared_by", ""),
        report_date=d.get("report_date", ""),
    )


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

    profile = _profile_from_dict(data)
    click.echo(f"Generating reports for: {profile.name}")
    pdf, xlsx = generate_reports(profile, output_dir=out, stem=stem)
    click.secho(f"  PDF   → {pdf}",  fg="green")
    click.secho(f"  Excel → {xlsx}", fg="green")


@cli.command("export-template")
@click.argument("org_type",
                type=click.Choice(["charter_school","health_center","early_care","nonprofit"]))
@click.argument("output_file", default="borrower_template.json")
def export_template(org_type, output_file):
    """Export a JSON template for a given borrower type to fill in."""
    template = {
        "name": "Your Organization Name",
        "org_type": org_type,
        "location": "City, State",
        "ein": "XX-XXXXXXX",
        "website": "https://example.org",
        "year_founded": 2000,
        "authorizer": "Name of authorizer (charter schools only)",
        "grade_span": "K-8 (charter schools only)",
        "prepared_by": "Analyst Name",
        "report_date": "",
        "analyst_notes": "Enter narrative underwriting notes here.",
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
            "asian": 5.0, "other": 10.0,
            "free_reduced_lunch": 80.0,
            "english_learners": 15.0,
            "special_education": 12.0
        },
        "academic_history": [
            {"year": "2022-23",
             "ela_proficiency": 40.0, "math_proficiency": 35.0,
             "ela_growth": 52.0, "math_growth": 50.0,
             "graduation_rate": None, "attendance_rate": 93.5},
            {"year": "2023-24",
             "ela_proficiency": 44.0, "math_proficiency": 38.0,
             "ela_growth": 54.0, "math_growth": 52.0,
             "graduation_rate": None, "attendance_rate": 94.2}
        ],
        "accountability": {
            "rating_year": "2023-24",
            "rating": "Recognized",
            "framework": "ESSA / State Accountability System",
            "subgroup_flags": [],
            "notes": ""
        },
        "loan": {
            "amount": 5000000,
            "purpose": "Describe the use of loan proceeds.",
            "financing_type": "NMTC",
            "proposed_term_years": 7,
            "collateral": "First mortgage on property."
        }
    }

    with open(output_file, "w") as f:
        json.dump(template, f, indent=2)

    click.secho(f"Template written to: {output_file}", fg="cyan")
    click.echo("Fill in the values and run: python cli.py from-json <file> --out ./output")


if __name__ == "__main__":
    cli()
