from borrower_metrics.models import (
    CharterSchoolProfile, CharterEvent, EnrollmentYear, AcademicYear,
    AccountabilityStatus, LoanInfo, Demographics,
)

SAMPLE_CHARTER_SCHOOL = CharterSchoolProfile(
    name="Northside Academy Charter School",
    org_type="charter_school",
    location="Chicago, IL",
    ein="36-4123456",
    website="https://northsideacademy.org",
    year_founded=2006,
    prepared_by="J. Underwriter",

    # Charter governance
    authorizer="Chicago Board of Education",
    grade_span="K–8",
    facility_status="Leasing (seeking permanent facility)",
    per_pupil_revenue=9_240,
    per_pupil_revenue_year="2023-24",

    # Student indicators
    free_reduced_lunch_pct=82.0,
    english_learners_pct=18.0,
    special_education_pct=12.0,

    charter_events=[
        CharterEvent(2006, "original",     "Initial 5-year charter granted.",
                     "Chicago Board of Education"),
        CharterEvent(2011, "renewal",      "First renewal — 5 years."),
        CharterEvent(2014, "modification", "Added grades 7–8; capacity increased to 480."),
        CharterEvent(2016, "renewal",      "Second renewal — 5 years."),
        CharterEvent(2021, "renewal",
                     "Third renewal — 5 years, conditional on math improvement."),
    ],

    enrollment_history=[
        EnrollmentYear("2019-20", 398, 480),
        EnrollmentYear("2020-21", 371, 480),   # COVID dip
        EnrollmentYear("2021-22", 410, 480),
        EnrollmentYear("2022-23", 441, 480),
        EnrollmentYear("2023-24", 463, 480),
    ],

    demographics=Demographics(
        black=54.0, hispanic=28.0, white=6.0, asian=5.0, other=7.0,
    ),

    academic_history=[
        AcademicYear("2018-19", ela_proficiency=38.0, math_proficiency=31.0,
                     ela_growth=52.0, math_growth=48.0, attendance_rate=94.2),
        AcademicYear("2019-20", ela_proficiency=40.0, math_proficiency=33.0,
                     ela_growth=54.0, math_growth=50.0, attendance_rate=94.8),
        AcademicYear("2021-22", ela_proficiency=35.0, math_proficiency=27.0,
                     ela_growth=50.0, math_growth=44.0, attendance_rate=91.5),
        AcademicYear("2022-23", ela_proficiency=42.0, math_proficiency=34.0,
                     ela_growth=56.0, math_growth=52.0, attendance_rate=93.7),
        AcademicYear("2023-24", ela_proficiency=47.0, math_proficiency=39.0,
                     ela_growth=58.0, math_growth=55.0, attendance_rate=94.5),
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
        "FRL of 82% supports NMTC eligibility. Per-pupil revenue of $9,240 in 2023-24 is "
        "consistent with CPS charter peers. Largest credit risk: single-site operator; "
        "propose standard debt-service-coverage covenant of 1.15x."
    ),
)
