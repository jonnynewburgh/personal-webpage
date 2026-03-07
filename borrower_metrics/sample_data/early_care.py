from borrower_metrics.models import (
    EarlyCareProfile, AgeGroupEnrollment, EarlyCareRevenueMix,
    StaffQualifications, SchoolReadinessOutcome,
    AccountabilityStatus, LoanInfo, Demographics,
)

SAMPLE_EARLY_CARE = EarlyCareProfile(
    name="Bright Beginnings Early Learning Center",
    org_type="early_care",
    location="New Orleans, LA",
    ein="72-1456789",
    website="https://brightbeginningsela.org",
    year_founded=2010,
    prepared_by="J. Underwriter",

    # Quality credentials
    qris_rating="4-Star (top tier)",
    qris_framework="Louisiana Quality Start",
    qris_rating_year="2024",
    head_start_grantee=True,
    early_head_start_grantee=False,
    licensed_capacity_total=120,
    number_of_classrooms=8,

    # Service indicators
    subsidized_enrollment_pct=85.0,   # CCDF + Head Start
    income_eligible_pct=92.0,
    english_learners_pct=10.0,
    special_education_pct=8.0,

    # Enrollment by age group (most recent 3 years)
    age_group_enrollment_history=[
        AgeGroupEnrollment("2021-22", "Infant (0-12mo)",    12, 14),
        AgeGroupEnrollment("2021-22", "Toddler (1-3yr)",    28, 32),
        AgeGroupEnrollment("2021-22", "Preschool (3-5yr)",  62, 74),
        AgeGroupEnrollment("2022-23", "Infant (0-12mo)",    13, 14),
        AgeGroupEnrollment("2022-23", "Toddler (1-3yr)",    30, 32),
        AgeGroupEnrollment("2022-23", "Preschool (3-5yr)",  71, 74),
        AgeGroupEnrollment("2023-24", "Infant (0-12mo)",    14, 14),
        AgeGroupEnrollment("2023-24", "Toddler (1-3yr)",    31, 32),
        AgeGroupEnrollment("2023-24", "Preschool (3-5yr)",  74, 74),
    ],

    # Revenue / subsidy mix
    revenue_mix_history=[
        EarlyCareRevenueMix("FY 2022", ccdf_pct=38.0, head_start_pct=32.0,
                            state_prek_pct=8.0, private_tuition_pct=16.0,
                            other_grants_pct=4.0, other_pct=2.0),
        EarlyCareRevenueMix("FY 2023", ccdf_pct=40.0, head_start_pct=31.0,
                            state_prek_pct=9.0, private_tuition_pct=14.0,
                            other_grants_pct=4.0, other_pct=2.0),
        EarlyCareRevenueMix("FY 2024", ccdf_pct=41.0, head_start_pct=30.0,
                            state_prek_pct=10.0, private_tuition_pct=13.0,
                            other_grants_pct=4.0, other_pct=2.0),
    ],

    # Staff qualifications
    staff_qualifications_history=[
        StaffQualifications("2021-22", bachelors_or_higher_pct=52.0, cda_pct=31.0,
                            annual_turnover_rate=24.0),
        StaffQualifications("2022-23", bachelors_or_higher_pct=58.0, cda_pct=28.0,
                            annual_turnover_rate=20.0),
        StaffQualifications("2023-24", bachelors_or_higher_pct=62.0, cda_pct=26.0,
                            annual_turnover_rate=17.0),
    ],

    # School readiness outcomes (Teaching Strategies GOLD)
    school_readiness_outcomes=[
        SchoolReadinessOutcome("2023-24", "Teaching Strategies GOLD",
                               "Literacy", pct_on_track=71.0, benchmark_pct=68.0),
        SchoolReadinessOutcome("2023-24", "Teaching Strategies GOLD",
                               "Math", pct_on_track=67.0, benchmark_pct=65.0),
        SchoolReadinessOutcome("2023-24", "Teaching Strategies GOLD",
                               "Social-Emotional", pct_on_track=74.0, benchmark_pct=70.0),
        SchoolReadinessOutcome("2023-24", "Teaching Strategies GOLD",
                               "Physical", pct_on_track=78.0, benchmark_pct=72.0),
    ],

    # Monitoring
    last_monitoring_year="2024",
    monitoring_outcome="No Findings",

    # Race/ethnicity of children served
    demographics=Demographics(
        black=71.0, hispanic=12.0, white=9.0, asian=2.0, other=6.0,
    ),

    accountability=AccountabilityStatus(
        rating_year="2024",
        rating="4-Star (top tier)",
        framework="Louisiana Quality Start Rating System",
        notes="Maintained 4-Star since 2017. Head Start grantee. "
              "Last monitoring (2024): No Findings.",
    ),

    loan=LoanInfo(
        amount=3_200_000,
        purpose="Renovation and expansion of licensed childcare facility (+24 new slots)",
        financing_type="NMTC",
        proposed_term_years=7,
        collateral="Leasehold mortgage; assignment of childcare subsidy receivables",
    ),

    analyst_notes=(
        "Near-full capacity utilization (99% in preschool classrooms) with 40-child waitlist. "
        "Expansion adds 24 infant/toddler slots — highest-need age group in service area. "
        "Revenue mix is diversified across CCDF (41%), Head Start (30%), and state Pre-K (10%); "
        "private tuition declining as subsidy coverage grows. "
        "Staff BA+ rising from 52% to 62% over 3 years, turnover declining (24% → 17%); "
        "both trends positive for QRIS maintenance. "
        "All TS GOLD domains above state benchmark. "
        "NMTC eligibility supported by census tract and 92% income-eligible enrollment. "
        "Key risk: CCDF rate reductions by state; recommend 6-month subsidy reserve covenant."
    ),
)
