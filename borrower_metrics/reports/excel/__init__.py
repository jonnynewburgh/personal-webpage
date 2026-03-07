"""
Excel generation dispatcher.
"""
import openpyxl

from .shared import build_summary_sheet
from borrower_metrics.models import (
    CharterSchoolProfile, FQHCProfile, EarlyCareProfile, NonprofitProfile
)


def generate_excel(profile, output_path: str) -> str:
    """Generate a multi-sheet Excel workbook for any profile subtype."""
    if isinstance(profile, CharterSchoolProfile):
        from .charter import build_sheets
    elif isinstance(profile, FQHCProfile):
        from .fqhc import build_sheets
    elif isinstance(profile, EarlyCareProfile):
        from .early_care import build_sheets
    elif isinstance(profile, NonprofitProfile):
        from .nonprofit import build_sheets
    else:
        raise TypeError(f"Unknown profile type: {type(profile).__name__}")

    wb = openpyxl.Workbook()
    del wb[wb.sheetnames[0]]          # remove default empty sheet

    build_summary_sheet(wb, profile)  # always first
    build_sheets(wb, profile)         # type-specific sheets

    wb.save(output_path)
    return output_path
