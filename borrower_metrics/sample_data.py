"""
Sample borrower profiles for testing / demo purposes.
Replace field values with real borrower data for production use.
"""
from .models import (
    BorrowerProfile, CharterEvent, EnrollmentYear,
    Demographics, AcademicYear, AccountabilityStatus, LoanInfo
)


# ── Sample 1: Charter school (NMTC-financed facility) ─────────────────────

SAMPLE_CHARTER_SCHOOL = BorrowerProfile(
    name="Northside Academy Charter School",
    org_type="charter_school",
    location="Chicago, IL",
    ein="36-4123456",
    website="https://northsideacademy.org",
    year_founded=2006,
    authorizer="Chicago Board of Education",
    grade_span="K–8",
    prepared_by="J. Underwriter",

    charter_events=[
        CharterEvent(2006, "original",     "Initial 5-year charter granted.", "Chicago Board of Education"),
        CharterEvent(2011, "renewal",      "First renewal — 5 years."),
        CharterEvent(2014, "modification", "Added grades 7–8; capacity increased to 480."),
        CharterEvent(2016, "renewal",      "Second renewal — 5 years."),
        CharterEvent(2021, "renewal",      "Third renewal — 5 years, conditional on math improvement."),
    ],

    enrollment_history=[
        EnrollmentYear("2019-20", 398, 480),
        EnrollmentYear("2020-21", 371, 480),   # COVID dip
        EnrollmentYear("2021-22", 410, 480),
        EnrollmentYear("2022-23", 441, 480),
        EnrollmentYear("2023-24", 463, 480),
    ],

    demographics=Demographics(
        black=54.0,
        hispanic=28.0,
        white=6.0,
        asian=5.0,
        other=7.0,
        free_reduced_lunch=82.0,
        english_learners=18.0,
        special_education=12.0,
    ),

    academic_history=[
        AcademicYear("2018-19", ela_proficiency=38.0, math_proficiency=31.0, ela_growth=52.0, math_growth=48.0, attendance_rate=94.2),
        AcademicYear("2019-20", ela_proficiency=40.0, math_proficiency=33.0, ela_growth=54.0, math_growth=50.0, attendance_rate=94.8),
        # 2020-21 assessments not administered statewide
        AcademicYear("2021-22", ela_proficiency=35.0, math_proficiency=27.0, ela_growth=50.0, math_growth=44.0, attendance_rate=91.5),
        AcademicYear("2022-23", ela_proficiency=42.0, math_proficiency=34.0, ela_growth=56.0, math_growth=52.0, attendance_rate=93.7),
        AcademicYear("2023-24", ela_proficiency=47.0, math_proficiency=39.0, ela_growth=58.0, math_growth=55.0, attendance_rate=94.5),
    ],

    accountability=AccountabilityStatus(
        rating_year="2023-24",
        rating="Recognized",
        framework="ISBE ESSA / SQRP",
        subgroup_flags=["Students with Disabilities — Math"],
        notes="Met all renewal conditions. On track for full renewal in 2026.",
    ),

    loan=LoanInfo(
        amount=8_500_000,
        purpose="New construction of permanent school facility (currently leasing)",
        financing_type="NMTC",
        proposed_term_years=7,
        collateral="First mortgage on new facility; assignment of lease revenue",
    ),

    analyst_notes=(
        "Northside has demonstrated consistent enrollment growth (16% over five years) with "
        "utilization approaching 97% of capacity. Academic performance trends upward post-COVID. "
        "Third renewal was conditional; school has met all stated benchmarks. "
        "FRL of 82% supports NMTC eligibility. Largest credit risk: single-site operator; "
        "propose standard debt-service-coverage covenant of 1.15x."
    ),
)


# ── Sample 2: Federally Qualified Health Center (HTC + NMTC) ──────────────

SAMPLE_HEALTH_CENTER = BorrowerProfile(
    name="Community Roots Health Center",
    org_type="health_center",
    location="Detroit, MI",
    ein="38-2987654",
    year_founded=1998,
    prepared_by="J. Underwriter",

    enrollment_history=[
        EnrollmentYear("FY 2020", 14_820, None),
        EnrollmentYear("FY 2021", 15_400, None),
        EnrollmentYear("FY 2022", 16_210, None),
        EnrollmentYear("FY 2023", 17_055, None),
        EnrollmentYear("FY 2024", 17_890, None),
    ],  # "enrollment" = annual patient visits

    demographics=Demographics(
        black=62.0,
        hispanic=14.0,
        white=12.0,
        asian=4.0,
        other=8.0,
        free_reduced_lunch=0.0,
        english_learners=0.0,
        special_education=0.0,
    ),

    accountability=AccountabilityStatus(
        rating_year="2024",
        rating="Meets Standard",
        framework="HRSA UDS / FTCA Deeming",
        notes="FTCA deemed; active Health Center Program award through 2027.",
    ),

    loan=LoanInfo(
        amount=12_000_000,
        purpose="Expansion of primary care and behavioral health clinic (8,400 SF addition)",
        financing_type="NMTC + HTC",
        proposed_term_years=10,
        collateral="First mortgage on clinic building; pledge of FQHC grant receivables",
    ),

    analyst_notes=(
        "Patient volume has grown ~21% over five years. "
        "Federal 330 grant provides stable base revenue (~$2.1M annually). "
        "HTC equity (~$4.2M) substantially reduces effective loan basis. "
        "Combined NMTC + HTC structure requires coordination of two investor closing timelines. "
        "Recommend 12-month construction reserve."
    ),
)


# ── Sample 3: Early care program ──────────────────────────────────────────

SAMPLE_EARLY_CARE = BorrowerProfile(
    name="Bright Beginnings Early Learning Center",
    org_type="early_care",
    location="New Orleans, LA",
    ein="72-1456789",
    year_founded=2010,
    prepared_by="J. Underwriter",

    enrollment_history=[
        EnrollmentYear("2020-21", 88,  120),
        EnrollmentYear("2021-22", 102, 120),
        EnrollmentYear("2022-23", 114, 120),
        EnrollmentYear("2023-24", 119, 120),
    ],

    demographics=Demographics(
        black=71.0,
        hispanic=12.0,
        white=9.0,
        asian=2.0,
        other=6.0,
        free_reduced_lunch=88.0,
        english_learners=10.0,
        special_education=8.0,
    ),

    accountability=AccountabilityStatus(
        rating_year="2023-24",
        rating="4-Star (top tier)",
        framework="Louisiana Quality Start Rating System",
        notes="Maintained 4-Star since 2017. Head Start grantee.",
    ),

    loan=LoanInfo(
        amount=3_200_000,
        purpose="Renovation and expansion of licensed childcare facility",
        financing_type="NMTC",
        proposed_term_years=7,
        collateral="Leasehold mortgage; assignment of childcare subsidy receivables",
    ),

    analyst_notes=(
        "Near-full capacity utilization (99%) with 40-child waitlist. "
        "Revenue mix: ~55% state childcare subsidies, ~30% Head Start, ~15% private pay. "
        "NMTC eligibility supported by census tract and FRL demographics. "
        "Key risk: subsidy rate reductions; recommend reserve fund covenant."
    ),
)


ALL_SAMPLES = {
    "charter_school": SAMPLE_CHARTER_SCHOOL,
    "health_center":  SAMPLE_HEALTH_CENTER,
    "early_care":     SAMPLE_EARLY_CARE,
}
