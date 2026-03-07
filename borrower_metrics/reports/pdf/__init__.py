"""
PDF generation dispatcher. Routes to the correct per-type story builder.
"""
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, KeepInFrame

from ..shared import PAGE_W, PAGE_H, MARGIN, _styles, build_header, build_footer
from borrower_metrics.models import (
    CharterSchoolProfile, FQHCProfile, EarlyCareProfile, NonprofitProfile
)


def generate_pdf(profile, output_path: str) -> str:
    """Render a single-page landscape PDF for any profile subtype."""
    S = _styles()
    usable_w = PAGE_W - 2 * MARGIN
    usable_h = PAGE_H - 2 * MARGIN

    if isinstance(profile, CharterSchoolProfile):
        from .charter import build_story
    elif isinstance(profile, FQHCProfile):
        from .fqhc import build_story
    elif isinstance(profile, EarlyCareProfile):
        from .early_care import build_story
    elif isinstance(profile, NonprofitProfile):
        from .nonprofit import build_story
    else:
        raise TypeError(f"Unknown profile type: {type(profile).__name__}")

    story = build_story(profile, usable_w, usable_h, S)

    frame = Frame(MARGIN, MARGIN, usable_w, usable_h, id="main",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(output_path, pagesize=landscape(letter),
                          leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=MARGIN, bottomMargin=MARGIN)
    doc.addPageTemplates([PageTemplate(id="single", frames=[frame])])

    kif = KeepInFrame(usable_w, usable_h, story, mode="shrink")
    doc.build([kif])
    return output_path
