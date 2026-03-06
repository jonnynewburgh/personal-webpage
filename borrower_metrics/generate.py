"""
Orchestrator: run both PDF and Excel generators for a BorrowerProfile.
"""
import os
from .models import BorrowerProfile
from .pdf_report import generate_pdf
from .excel_report import generate_excel


def generate_reports(
    profile: BorrowerProfile,
    output_dir: str = ".",
    stem: str | None = None,
) -> tuple[str, str]:
    """
    Generate a PDF and Excel file for *profile*.

    Returns (pdf_path, excel_path).
    """
    os.makedirs(output_dir, exist_ok=True)
    if stem is None:
        stem = profile.name.replace(" ", "_").replace("/", "-")

    pdf_path   = os.path.join(output_dir, f"{stem}.pdf")
    excel_path = os.path.join(output_dir, f"{stem}.xlsx")

    generate_pdf(profile, pdf_path)
    generate_excel(profile, excel_path)

    return pdf_path, excel_path
