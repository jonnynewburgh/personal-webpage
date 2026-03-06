from borrower_metrics.models import (
    FQHCProfile, PatientYear, PayerMix, FQHCRevenueMix, QualityMeasure,
    HRSAGrantInfo, AccountabilityStatus, LoanInfo, Demographics,
)

SAMPLE_FQHC = FQHCProfile(
    name="Community Roots Health Center",
    org_type="fqhc",
    location="Detroit, MI",
    ein="38-2987654",
    website="https://communityroots.health",
    year_founded=1998,
    prepared_by="J. Underwriter",

    # HRSA program status
    hrsa_grant=HRSAGrantInfo(
        award_number="H80CS12345",
        grant_amount_annual=2_100_000,
        award_period_start="2022",
        award_period_end="2027",
        look_alike=False,
    ),
    ftca_deemed=True,
    number_of_sites=3,
    service_area="Southeast Detroit / Wayne County (3 clinic sites)",

    # Patient volume (unique patients + total visits)
    patient_history=[
        PatientYear("FY 2020", total_patients=10_840, patient_visits=32_500,
                    new_patients=1_820, sliding_fee_patients=3_910),
        PatientYear("FY 2021", total_patients=11_600, patient_visits=35_200,
                    new_patients=2_050, sliding_fee_patients=4_060),
        PatientYear("FY 2022", total_patients=12_880, patient_visits=39_100,
                    new_patients=2_310, sliding_fee_patients=4_250),
        PatientYear("FY 2023", total_patients=14_100, patient_visits=43_500,
                    new_patients=2_580, sliding_fee_patients=4_420),
        PatientYear("FY 2024", total_patients=15_340, patient_visits=47_800,
                    new_patients=2_800, sliding_fee_patients=4_630),
    ],

    # Payer mix (% of patients by insurance source)
    payer_mix_history=[
        PayerMix("FY 2022", medicaid_pct=58.0, medicare_pct=8.0,
                 private_insurance_pct=12.0, uninsured_sliding_fee_pct=19.0, other_pct=3.0),
        PayerMix("FY 2023", medicaid_pct=60.0, medicare_pct=8.0,
                 private_insurance_pct=11.0, uninsured_sliding_fee_pct=18.0, other_pct=3.0),
        PayerMix("FY 2024", medicaid_pct=61.0, medicare_pct=9.0,
                 private_insurance_pct=10.0, uninsured_sliding_fee_pct=17.0, other_pct=3.0),
    ],

    # Revenue mix (% of total operating revenue by source)
    revenue_mix_history=[
        FQHCRevenueMix("FY 2022", grant_330_pct=24.0, medicaid_pct=45.0,
                       medicare_pct=8.0, private_insurance_pct=10.0,
                       patient_fees_pct=9.0, other_pct=4.0),
        FQHCRevenueMix("FY 2023", grant_330_pct=23.0, medicaid_pct=47.0,
                       medicare_pct=8.0, private_insurance_pct=10.0,
                       patient_fees_pct=8.0, other_pct=4.0),
        FQHCRevenueMix("FY 2024", grant_330_pct=22.0, medicaid_pct=49.0,
                       medicare_pct=9.0, private_insurance_pct=9.0,
                       patient_fees_pct=8.0, other_pct=3.0),
    ],

    # UDS clinical quality measures vs. national benchmarks
    quality_measures=[
        QualityMeasure("Diabetes Control (HbA1c < 9%)",
                       rate=74.0, national_benchmark=70.0,
                       direction="higher_is_better", uds_measure_id="QM 10"),
        QualityMeasure("Hypertension Control (BP < 140/90)",
                       rate=68.0, national_benchmark=65.0,
                       direction="higher_is_better", uds_measure_id="QM 11"),
        QualityMeasure("Childhood Immunization — Combo 10",
                       rate=54.0, national_benchmark=58.0,
                       direction="higher_is_better", uds_measure_id="QM 12"),
        QualityMeasure("Cervical Cancer Screening",
                       rate=62.0, national_benchmark=60.0,
                       direction="higher_is_better", uds_measure_id="QM 13"),
        QualityMeasure("Depression Screening & Follow-Up",
                       rate=71.0, national_benchmark=66.0,
                       direction="higher_is_better", uds_measure_id="QM 14"),
        QualityMeasure("Prenatal Care — 1st Trimester",
                       rate=78.0, national_benchmark=72.0,
                       direction="higher_is_better", uds_measure_id="QM 15"),
    ],
    quality_measures_year="UDS 2024",

    # Regulatory
    last_osa_review_year="2023",
    osa_outcome="Approved",

    # Patient demographics (race/ethnicity)
    demographics=Demographics(
        black=62.0, hispanic=14.0, white=12.0, asian=4.0, other=8.0,
    ),

    accountability=AccountabilityStatus(
        rating_year="2024",
        rating="Approved",
        framework="HRSA Health Center Program / UDS",
        notes="FTCA deemed. Active Section 330 award through 2027. "
              "Last OSV (2023): Approved with no findings.",
    ),

    loan=LoanInfo(
        amount=12_000_000,
        purpose="Expansion of primary care and behavioral health clinic (8,400 SF addition)",
        financing_type="NMTC + HTC",
        proposed_term_years=10,
        collateral="First mortgage on clinic building; pledge of FQHC grant receivables",
    ),

    analyst_notes=(
        "Patient volume has grown 41% over five years (10,840 → 15,340 unique patients). "
        "HRSA Section 330 grant of $2.1M/year provides stable base revenue (~22% of total). "
        "Medicaid dependency (61%) is typical for FQHC peer group in MI; Medicaid Managed Care "
        "penetration increases predictability. Payer mix has been stable with slight Medicaid "
        "share growth. 5 of 6 UDS quality measures at or above national benchmark. "
        "HTC equity (~$4.2M) substantially reduces effective loan basis. "
        "Combined NMTC + HTC structure requires coordination of two investor closing timelines. "
        "FTCA deemed status eliminates commercial malpractice insurance cost (~$400K/yr). "
        "Recommend 12-month construction reserve and DSCR covenant of 1.20x."
    ),
)
