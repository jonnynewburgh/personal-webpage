"""
Orchestrator: generate PDF and Excel reports for any typed borrower profile.
"""
import os
from .models import BaseBorrowerProfile
from .reports.pdf import generate_pdf
from .reports.excel import generate_excel


def generate_reports(
    profile: BaseBorrowerProfile,
    output_dir: str = ".",
    stem: str | None = None,
) -> tuple[str, str]:
    """
    Generate a PDF and Excel file for *profile* (any BaseBorrowerProfile subclass).

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
