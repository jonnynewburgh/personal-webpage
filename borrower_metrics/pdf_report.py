"""
One-page PDF report generator using ReportLab.
Layout (letter, landscape):
  ┌─────────────────────────── HEADER ────────────────────────────┐
  │  Name | Type | Location | EIN | Founded | Loan info            │
  ├──────────────┬──────────────────────┬─────────────────────────┤
  │ CHARTER INFO │   ENROLLMENT CHART   │   DEMOGRAPHICS CHARTS   │
  ├──────────────┴──────────────────────┴─────────────────────────┤
  │             ACADEMIC PERFORMANCE CHART (full width)            │
  ├────────────────────────────────────────────────────────────────┤
  │  CHARTER TIMELINE  (charter schools only)  | ACCOUNTABILITY    │
  ├────────────────────────────────────────────────────────────────┤
  │  ANALYST NOTES                                                 │
  └────────────────────────────────────────────────────────────────┘
"""
import io
from datetime import date
from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Table, TableStyle,
    Spacer, Image, HRFlowable, KeepInFrame
)
from reportlab.platypus.flowables import Flowable

from .models import BorrowerProfile
from . import charts

# ── Colours (matching charts.py palette) ──────────────────────────────────
NAVY  = colors.HexColor("#1B3A6B")
TEAL  = colors.HexColor("#2A7F8F")
GOLD  = colors.HexColor("#C8952A")
LIGHT = colors.HexColor("#E8EDF4")
GRAY  = colors.HexColor("#6C757D")
GREEN = colors.HexColor("#2E7D4F")
RED   = colors.HexColor("#C0392B")
WHITE = colors.white

PAGE_W, PAGE_H = landscape(letter)
MARGIN = 0.35 * inch


def _img_from_buf(buf, width, height=None):
    """Convert a BytesIO PNG buffer to a ReportLab Image, preserving aspect."""
    img = PILImage.open(buf)
    w_px, h_px = img.size
    if height is None:
        height = width * h_px / w_px
    buf.seek(0)
    return Image(buf, width=width, height=height)


def _styles():
    base = getSampleStyleSheet()
    def _p(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    return {
        "title":    _p("title",   fontSize=13, textColor=NAVY,  fontName="Helvetica-Bold",
                        leading=15, spaceAfter=2),
        "subtitle": _p("subtitle",fontSize=8,  textColor=GRAY,  fontName="Helvetica",
                        leading=10, spaceAfter=1),
        "section":  _p("section", fontSize=8,  textColor=WHITE, fontName="Helvetica-Bold",
                        leading=10, backColor=NAVY, borderPadding=(2,4,2,4)),
        "body":     _p("body",    fontSize=7.5,textColor=colors.black, fontName="Helvetica",
                        leading=10),
        "small":    _p("small",   fontSize=6.5,textColor=GRAY,  fontName="Helvetica",
                        leading=9),
        "label":    _p("label",   fontSize=7,  textColor=NAVY,  fontName="Helvetica-Bold",
                        leading=9),
        "value":    _p("value",   fontSize=7.5,textColor=colors.black, fontName="Helvetica",
                        leading=9),
        "note":     _p("note",    fontSize=7,  textColor=colors.black, fontName="Helvetica-Oblique",
                        leading=9),
        "rating_ok":  _p("rating_ok",  fontSize=18, textColor=GREEN, fontName="Helvetica-Bold",
                          alignment=TA_CENTER),
        "rating_warn":_p("rating_warn",fontSize=18, textColor=GOLD,  fontName="Helvetica-Bold",
                          alignment=TA_CENTER),
        "rating_bad": _p("rating_bad", fontSize=18, textColor=RED,   fontName="Helvetica-Bold",
                          alignment=TA_CENTER),
    }


def _rating_style(rating: str, styles):
    pos = {"exemplary","recognized","meets standard","good standing","commended"}
    neg = {"improvement required","probation","revoked","not renewed","unsatisfactory"}
    r = rating.lower()
    if any(w in r for w in pos):
        return styles["rating_ok"]
    if any(w in r for w in neg):
        return styles["rating_bad"]
    return styles["rating_warn"]


ORG_TYPE_LABEL = {
    "charter_school": "Charter School",
    "health_center":  "Federally Qualified Health Center",
    "early_care":     "Early Care & Education Program",
    "nonprofit":      "Nonprofit Organization",
}


def generate_pdf(profile: BorrowerProfile, output_path: str):
    """Render a single-page landscape PDF to *output_path*."""
    S = _styles()

    # ── Pre-render charts ──────────────────────────────────────────────────
    enroll_buf  = charts.enrollment_chart(profile.enrollment_history) \
                  if profile.enrollment_history else None
    demo_buf    = charts.demographics_chart(profile.demographics) \
                  if profile.demographics else None
    acad_buf    = charts.academic_chart(profile.academic_history) \
                  if profile.academic_history else None
    timeline_buf = charts.charter_timeline_chart(profile.charter_events) \
                   if profile.charter_events and profile.org_type == "charter_school" else None

    # ── Page geometry ─────────────────────────────────────────────────────
    usable_w = PAGE_W - 2 * MARGIN
    usable_h = PAGE_H - 2 * MARGIN

    story = []

    # ═══════════════════════════════════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════════════════════════════════
    org_label = ORG_TYPE_LABEL.get(profile.org_type, profile.org_type.replace("_", " ").title())
    header_left = [
        Paragraph(profile.name, S["title"]),
        Paragraph(
            f"{org_label}  •  {profile.location}" +
            (f"  •  Founded {profile.year_founded}" if profile.year_founded else "") +
            (f"  •  EIN: {profile.ein}" if profile.ein else ""),
            S["subtitle"]
        ),
        Paragraph(
            (f"Authorizer: <b>{profile.authorizer}</b>  |  " if profile.authorizer else "") +
            (f"Grades: <b>{profile.grade_span}</b>" if profile.grade_span else ""),
            S["subtitle"]
        ),
    ]

    loan_lines = []
    if profile.loan:
        loan_lines = [
            Paragraph("PROPOSED FINANCING", S["label"]),
            Paragraph(f"Amount: <b>${profile.loan.amount:,.0f}</b>", S["body"]),
            Paragraph(f"Purpose: {profile.loan.purpose}", S["body"]),
            Paragraph(f"Structure: {profile.loan.financing_type}", S["body"]),
        ]
        if profile.loan.proposed_term_years:
            loan_lines.append(Paragraph(f"Term: {profile.loan.proposed_term_years} yrs", S["body"]))
        if profile.loan.collateral:
            loan_lines.append(Paragraph(f"Collateral: {profile.loan.collateral}", S["body"]))

    report_date = profile.report_date or date.today().strftime("%B %d, %Y")
    header_right = [
        Paragraph(f"Report Date: {report_date}", S["small"]),
        Paragraph(f"Prepared by: {profile.prepared_by or '—'}", S["small"]),
    ] + loan_lines

    header_table = Table(
        [[header_left, header_right]],
        colWidths=[usable_w * 0.62, usable_w * 0.38],
        rowHeights=[None]
    )
    header_table.setStyle(TableStyle([
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("BACKGROUND", (0,0), (-1,-1), LIGHT),
        ("BOX",        (0,0), (-1,-1), 0.5, NAVY),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))

    # ═══════════════════════════════════════════════════════════════════════
    # ROW 1: Charter info  |  Enrollment chart  |  Demographics
    # ═══════════════════════════════════════════════════════════════════════
    col1_w = usable_w * 0.20
    col2_w = usable_w * 0.38
    col3_w = usable_w * 0.42

    # -- Charter info cell --
    charter_items = [Paragraph("CHARTER STATUS", S["section"])]
    if profile.charter_events:
        for ev in sorted(profile.charter_events, key=lambda e: e.year):
            icon = {"original":"◆","renewal":"✓","modification":"△",
                    "probation":"⚠","revocation":"✗"}.get(ev.event_type, "•")
            charter_items.append(
                Paragraph(f"{icon} <b>{ev.event_type.title()}</b> ({ev.year}): {ev.description}",
                          S["body"])
            )
    else:
        charter_items.append(Paragraph("No charter events on record.", S["small"]))

    # -- Enrollment chart cell --
    enroll_cell = [Paragraph("ENROLLMENT", S["section"])]
    if enroll_buf:
        enroll_cell.append(_img_from_buf(enroll_buf, col2_w - 8))
    else:
        enroll_cell.append(Paragraph("No enrollment data provided.", S["small"]))

    # -- Demographics cell --
    demo_cell = [Paragraph("DEMOGRAPHICS", S["section"])]
    if demo_buf:
        demo_cell.append(_img_from_buf(demo_buf, col3_w - 8))
    else:
        demo_cell.append(Paragraph("No demographics data provided.", S["small"]))

    row1 = Table(
        [[charter_items, enroll_cell, demo_cell]],
        colWidths=[col1_w, col2_w, col3_w],
    )
    row1.setStyle(TableStyle([
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("BOX",         (0,0), (-1,-1), 0.3, GRAY),
        ("INNERGRID",   (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",  (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING",   (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
    ]))
    story.append(row1)
    story.append(Spacer(1, 4))

    # ═══════════════════════════════════════════════════════════════════════
    # ROW 2: Academic performance (full width) | Accountability
    # ═══════════════════════════════════════════════════════════════════════
    acad_w  = usable_w * 0.65
    acct_w  = usable_w * 0.35

    acad_cell = [Paragraph("ACADEMIC PERFORMANCE", S["section"])]
    if acad_buf:
        acad_cell.append(_img_from_buf(acad_buf, acad_w - 8))
        # growth footnote
        for ay in profile.academic_history:
            if ay.ela_growth or ay.math_growth:
                parts = []
                if ay.ela_growth:
                    parts.append(f"ELA SGP {ay.ela_growth:.0f}")
                if ay.math_growth:
                    parts.append(f"Math SGP {ay.math_growth:.0f}")
                acad_cell.append(Paragraph(f"{ay.year} Growth — " + "  |  ".join(parts), S["small"]))
    else:
        acad_cell.append(Paragraph("No academic data provided.", S["small"]))

    # Accountability cell
    acct_cell = [Paragraph("ACCOUNTABILITY", S["section"])]
    if profile.accountability:
        a = profile.accountability
        rating_sty = _rating_style(a.rating, S)
        acct_cell += [
            Spacer(1, 4),
            Paragraph(a.rating, rating_sty),
            Spacer(1, 4),
            Paragraph(f"<b>Framework:</b> {a.framework}", S["body"]),
            Paragraph(f"<b>Year:</b> {a.rating_year}", S["body"]),
        ]
        if a.subgroup_flags:
            acct_cell.append(
                Paragraph("<b>Subgroup flags:</b> " + ", ".join(a.subgroup_flags), S["body"])
            )
        if a.notes:
            acct_cell.append(Paragraph(a.notes, S["note"]))
    else:
        acct_cell.append(Paragraph("No accountability data provided.", S["small"]))

    row2 = Table(
        [[acad_cell, acct_cell]],
        colWidths=[acad_w, acct_w],
    )
    row2.setStyle(TableStyle([
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("BOX",         (0,0), (-1,-1), 0.3, GRAY),
        ("INNERGRID",   (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",  (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING",   (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
    ]))
    story.append(row2)
    story.append(Spacer(1, 4))

    # ═══════════════════════════════════════════════════════════════════════
    # ROW 3: Timeline (charter) | Analyst notes
    # ═══════════════════════════════════════════════════════════════════════
    tl_w   = usable_w * 0.60 if timeline_buf else 0
    note_w = usable_w - tl_w

    tl_cell   = []
    note_cell = [Paragraph("ANALYST NOTES", S["section"])]

    if timeline_buf:
        tl_cell += [
            Paragraph("CHARTER TIMELINE", S["section"]),
            _img_from_buf(timeline_buf, tl_w - 8, height=0.85 * inch),
        ]

    if profile.analyst_notes:
        note_cell.append(Paragraph(profile.analyst_notes, S["note"]))
    else:
        note_cell.append(Paragraph("—", S["small"]))

    row3_data = [[tl_cell, note_cell]] if timeline_buf else [[note_cell]]
    row3_cols = [tl_w, note_w] if timeline_buf else [usable_w]

    row3 = Table(row3_data, colWidths=row3_cols)
    row3.setStyle(TableStyle([
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("BOX",         (0,0), (-1,-1), 0.3, GRAY),
        ("INNERGRID",   (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",  (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING",   (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
    ]))
    story.append(row3)

    # ── Footer stamp ──────────────────────────────────────────────────────
    story.append(Spacer(1, 3))
    story.append(HRFlowable(width=usable_w, thickness=0.5, color=NAVY))
    story.append(
        Paragraph(
            f"CONFIDENTIAL — Borrower Metrics Report  |  {profile.name}  |  "
            f"Generated {report_date}  |  For internal underwriting use only.",
            ParagraphStyle("footer", fontSize=6, textColor=GRAY, alignment=TA_CENTER)
        )
    )

    # ── Build PDF ─────────────────────────────────────────────────────────
    frame = Frame(MARGIN, MARGIN, usable_w, usable_h, id="main",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(output_path, pagesize=landscape(letter),
                          leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=MARGIN, bottomMargin=MARGIN)
    doc.addPageTemplates([PageTemplate(id="single", frames=[frame])])

    # Wrap the entire story in KeepInFrame to force single-page fit
    kif = KeepInFrame(usable_w, usable_h, story, mode="shrink")
    doc.build([kif])
    return output_path
