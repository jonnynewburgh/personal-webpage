"""
Shared ReportLab styles, colour constants, and helper functions
used by all per-type PDF builders.
"""
import io
from datetime import date
from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, Image, HRFlowable

# ── Colours ────────────────────────────────────────────────────────────────
NAVY  = colors.HexColor("#1B3A6B")
TEAL  = colors.HexColor("#2A7F8F")
GOLD  = colors.HexColor("#C8952A")
LIGHT = colors.HexColor("#E8EDF4")
GRAY  = colors.HexColor("#6C757D")
GREEN = colors.HexColor("#2E7D4F")
RED   = colors.HexColor("#C0392B")
WHITE = colors.white

# ── Page geometry ──────────────────────────────────────────────────────────
PAGE_W, PAGE_H = landscape(letter)
MARGIN = 0.35 * inch

ORG_TYPE_LABEL = {
    "charter_school": "Charter School",
    "fqhc":           "Federally Qualified Health Center",
    "health_center":  "Federally Qualified Health Center",  # legacy key
    "early_care":     "Early Care & Education Program",
    "nonprofit":      "Nonprofit Organization",
}


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
        "title":      _p("title",   fontSize=13, textColor=NAVY,  fontName="Helvetica-Bold",
                          leading=15, spaceAfter=2),
        "subtitle":   _p("subtitle",fontSize=8,  textColor=GRAY,  fontName="Helvetica",
                          leading=10, spaceAfter=1),
        "section":    _p("section", fontSize=8,  textColor=WHITE, fontName="Helvetica-Bold",
                          leading=10, backColor=NAVY, borderPadding=(2,4,2,4)),
        "section_teal": _p("section_teal", fontSize=8, textColor=WHITE,
                            fontName="Helvetica-Bold", leading=10,
                            backColor=TEAL, borderPadding=(2,4,2,4)),
        "body":       _p("body",    fontSize=7.5,textColor=colors.black, fontName="Helvetica",
                          leading=10),
        "small":      _p("small",   fontSize=6.5,textColor=GRAY,  fontName="Helvetica",
                          leading=9),
        "label":      _p("label",   fontSize=7,  textColor=NAVY,  fontName="Helvetica-Bold",
                          leading=9),
        "value":      _p("value",   fontSize=7.5,textColor=colors.black, fontName="Helvetica",
                          leading=9),
        "note":       _p("note",    fontSize=7,  textColor=colors.black,
                          fontName="Helvetica-Oblique", leading=9),
        "rating_ok":  _p("rating_ok",  fontSize=18, textColor=GREEN, fontName="Helvetica-Bold",
                          alignment=TA_CENTER),
        "rating_warn":_p("rating_warn",fontSize=18, textColor=GOLD,  fontName="Helvetica-Bold",
                          alignment=TA_CENTER),
        "rating_bad": _p("rating_bad", fontSize=18, textColor=RED,   fontName="Helvetica-Bold",
                          alignment=TA_CENTER),
        "qris_badge": _p("qris_badge", fontSize=14, textColor=GREEN, fontName="Helvetica-Bold",
                          alignment=TA_CENTER),
        "footer":     _p("footer",  fontSize=6,  textColor=GRAY, alignment=TA_CENTER),
    }


def _rating_style(rating: str, styles):
    pos = {"exemplary","recognized","meets standard","good standing","commended","approved",
           "4-star","5-star","level 4","level 5","excelling"}
    neg = {"improvement required","probation","revoked","not renewed","unsatisfactory",
           "adverse","corrective action","deficiency"}
    r = rating.lower()
    if any(w in r for w in pos):
        return styles["rating_ok"]
    if any(w in r for w in neg):
        return styles["rating_bad"]
    return styles["rating_warn"]


def _row_style():
    """Standard cell style for content rows."""
    return TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("BOX",          (0,0), (-1,-1), 0.3, GRAY),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",  (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING",   (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
    ])


def build_header(profile, usable_w, S, extra_lines=None):
    """
    Build the standard header table (name, type, location, loan, metadata).
    extra_lines: list of Paragraph objects to append to the left column.
    """
    org_label = ORG_TYPE_LABEL.get(profile.org_type,
                                    profile.org_type.replace("_", " ").title())
    header_left = [
        Paragraph(profile.name, S["title"]),
        Paragraph(
            f"{org_label}  •  {profile.location}" +
            (f"  •  Founded {profile.year_founded}" if profile.year_founded else "") +
            (f"  •  EIN: {profile.ein}" if profile.ein else ""),
            S["subtitle"]
        ),
    ]
    if extra_lines:
        header_left.extend(extra_lines)

    report_date = profile.report_date or date.today().strftime("%B %d, %Y")
    header_right = [
        Paragraph(f"Report Date: {report_date}", S["small"]),
        Paragraph(f"Prepared by: {profile.prepared_by or '—'}", S["small"]),
    ]
    if profile.loan:
        loan = profile.loan
        header_right += [
            Paragraph("PROPOSED FINANCING", S["label"]),
            Paragraph(f"Amount: <b>${loan.amount:,.0f}</b>", S["body"]),
            Paragraph(f"Purpose: {loan.purpose}", S["body"]),
            Paragraph(f"Structure: {loan.financing_type}", S["body"]),
        ]
        if loan.proposed_term_years:
            header_right.append(Paragraph(f"Term: {loan.proposed_term_years} yrs", S["body"]))
        if loan.collateral:
            header_right.append(Paragraph(f"Collateral: {loan.collateral}", S["body"]))

    tbl = Table(
        [[header_left, header_right]],
        colWidths=[usable_w * 0.62, usable_w * 0.38],
    )
    tbl.setStyle(TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("BACKGROUND",   (0,0), (-1,-1), LIGHT),
        ("BOX",          (0,0), (-1,-1), 0.5, NAVY),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
    ]))
    return tbl, report_date


def build_accountability_cell(profile, S):
    """Build the accountability/rating cell content list."""
    cell = [Paragraph("ACCOUNTABILITY / STATUS", S["section"])]
    if profile.accountability:
        a = profile.accountability
        cell += [
            Spacer(1, 4),
            Paragraph(a.rating, _rating_style(a.rating, S)),
            Spacer(1, 4),
            Paragraph(f"<b>Framework:</b> {a.framework}", S["body"]),
            Paragraph(f"<b>Year:</b> {a.rating_year}", S["body"]),
        ]
        if a.subgroup_flags:
            cell.append(
                Paragraph("<b>Flags:</b> " + ", ".join(a.subgroup_flags), S["body"])
            )
        if a.notes:
            cell.append(Paragraph(a.notes, S["note"]))
    else:
        cell.append(Paragraph("No accountability data provided.", S["small"]))
    return cell


def build_footer(profile, usable_w, report_date, S):
    """Build footer HR + confidential stamp."""
    return [
        Spacer(1, 3),
        HRFlowable(width=usable_w, thickness=0.5, color=NAVY),
        Paragraph(
            f"CONFIDENTIAL — Borrower Metrics Report  |  {profile.name}  |  "
            f"Generated {report_date}  |  For internal underwriting use only.",
            S["footer"]
        ),
    ]
