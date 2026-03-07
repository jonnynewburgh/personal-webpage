from borrower_metrics.models import (
    NonprofitProfile, RevenueYear, NonprofitRevenueMix, ProgramMetric,
    AccountabilityStatus, LoanInfo,
)

SAMPLE_NONPROFIT = NonprofitProfile(
    name="Greater Metro Food Security Alliance",
    org_type="nonprofit",
    location="Columbus, OH",
    ein="31-1876543",
    website="https://gmfsa.org",
    year_founded=1994,
    prepared_by="J. Underwriter",

    # Mission
    mission_summary="Eliminate food insecurity in Franklin County through direct distribution, "
                    "advocacy, and community partnerships.",
    primary_program_area="Food Security",
    clients_served_annually=42_000,
    clients_served_year="FY 2024",

    # Financial health
    operating_reserve_months=4.8,
    operating_reserve_year="FY 2024",

    # Revenue history (5 years)
    revenue_history=[
        RevenueYear("FY 2020", total_revenue=5_820_000, total_expenses=5_610_000, net_assets=3_140_000),
        RevenueYear("FY 2021", total_revenue=7_450_000, total_expenses=6_980_000, net_assets=3_610_000),
        RevenueYear("FY 2022", total_revenue=8_100_000, total_expenses=7_760_000, net_assets=3_950_000),
        RevenueYear("FY 2023", total_revenue=8_640_000, total_expenses=8_290_000, net_assets=4_300_000),
        RevenueYear("FY 2024", total_revenue=9_210_000, total_expenses=8_760_000, net_assets=4_750_000),
    ],

    # Revenue mix
    revenue_mix_history=[
        NonprofitRevenueMix("FY 2022", government_grants_pct=52.0, foundation_grants_pct=21.0,
                            corporate_contributions_pct=8.0, individual_contributions_pct=9.0,
                            earned_revenue_pct=7.0, other_pct=3.0),
        NonprofitRevenueMix("FY 2023", government_grants_pct=50.0, foundation_grants_pct=22.0,
                            corporate_contributions_pct=9.0, individual_contributions_pct=10.0,
                            earned_revenue_pct=7.0, other_pct=2.0),
        NonprofitRevenueMix("FY 2024", government_grants_pct=48.0, foundation_grants_pct=23.0,
                            corporate_contributions_pct=10.0, individual_contributions_pct=11.0,
                            earned_revenue_pct=6.0, other_pct=2.0),
    ],

    # Program metrics
    program_metrics=[
        ProgramMetric("Individuals served annually", "42,000", "FY 2024",
                      "Unique unduplicated clients"),
        ProgramMetric("Pounds of food distributed", "6.8 million lbs", "FY 2024"),
        ProgramMetric("Meals equivalent distributed", "5.7 million meals", "FY 2024"),
        ProgramMetric("Partner agency network", "84 pantries and meal sites", "FY 2024"),
        ProgramMetric("% clients at/below 100% FPL", "78%", "FY 2024"),
        ProgramMetric("Waitlist / unmet need", "~4,200 households on waiting list", "FY 2024"),
    ],

    # Compliance
    last_audit_year="FY 2024",
    audit_outcome="Unmodified (clean)",
    irs_form_990_year="FY 2023",

    accountability=AccountabilityStatus(
        rating_year="2024",
        rating="Accredited",
        framework="Feeding America Network / Ohio Association of Food Banks",
        notes="National Feeding America member. Annual network audit completed. "
              "Clean Form 990 for five consecutive years.",
    ),

    loan=LoanInfo(
        amount=4_500_000,
        purpose="Construction of expanded cold-storage and distribution warehouse (18,000 SF)",
        financing_type="NMTC",
        proposed_term_years=7,
        collateral="First mortgage on warehouse; assignment of government grant receivables",
    ),

    analyst_notes=(
        "Revenue has grown 58% over five years ($5.8M → $9.2M) driven by government grants "
        "and diversifying private support. Government grant concentration declining (52% → 48%) "
        "as foundation and corporate support grows — a positive trend. "
        "Operating reserve of 4.8 months is above the 3-month threshold; "
        "net assets growing consistently. Clean audits for 5+ years. "
        "Facility expansion addresses critical cold-storage bottleneck limiting throughput. "
        "NMTC eligibility supported by census tract (QCT) and 78% of clients at/below 100% FPL. "
        "Key risk: government grant concentration (USDA, CDBG); recommend reserve fund covenant "
        "and annual evidence of grant renewal."
    ),
)
