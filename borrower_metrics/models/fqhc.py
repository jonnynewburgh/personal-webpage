"""
Federally Qualified Health Center (FQHC) borrower profile and supporting data classes.
"""
from dataclasses import dataclass, field
from typing import Optional
from .base import BaseBorrowerProfile


@dataclass
class PatientYear:
    year: str                               # e.g. "FY 2024"
    total_patients: int                     # unique patients served
    patient_visits: int                     # total encounters/visits
    new_patients: Optional[int] = None
    sliding_fee_patients: Optional[int] = None  # patients on FQHC sliding-fee scale


@dataclass
class PayerMix:
    """Payer distribution as % of patients or revenue. One record per year."""
    year: str
    medicaid_pct: float = 0.0
    medicare_pct: float = 0.0
    private_insurance_pct: float = 0.0
    uninsured_sliding_fee_pct: float = 0.0
    other_pct: float = 0.0


@dataclass
class FQHCRevenueMix:
    """Revenue by source as % of total operating revenue. One record per year."""
    year: str
    grant_330_pct: float = 0.0              # HRSA Section 330 grant
    medicaid_pct: float = 0.0              # Medicaid FFS + managed care
    medicare_pct: float = 0.0
    private_insurance_pct: float = 0.0
    patient_fees_pct: float = 0.0          # sliding-fee and self-pay collections
    other_pct: float = 0.0


@dataclass
class QualityMeasure:
    """A single UDS (Uniform Data System) clinical quality measure."""
    name: str                               # e.g. "Diabetes Control (HbA1c < 9%)"
    rate: float                             # borrower rate, 0–100
    national_benchmark: Optional[float] = None
    direction: str = "higher_is_better"    # "higher_is_better" | "lower_is_better"
    uds_measure_id: Optional[str] = None   # e.g. "QM 10"


@dataclass
class HRSAGrantInfo:
    award_number: Optional[str] = None
    grant_amount_annual: Optional[float] = None   # dollars
    award_period_start: Optional[str] = None      # e.g. "2022"
    award_period_end: Optional[str] = None        # e.g. "2026"
    look_alike: bool = False                      # True = look-alike, not full grantee


@dataclass
class FQHCProfile(BaseBorrowerProfile):
    # ── HRSA program status ──────────────────────────────────────────────────
    hrsa_grant: Optional[HRSAGrantInfo] = None
    ftca_deemed: Optional[bool] = None          # Federal Tort Claims Act deeming status
    number_of_sites: Optional[int] = None
    service_area: Optional[str] = None         # e.g. "3 counties, SW Detroit"

    # ── Patient volume ───────────────────────────────────────────────────────
    patient_history: list[PatientYear] = field(default_factory=list)

    # ── Financial mix (multi-year trend) ─────────────────────────────────────
    payer_mix_history: list[PayerMix] = field(default_factory=list)
    revenue_mix_history: list[FQHCRevenueMix] = field(default_factory=list)

    # ── Clinical quality (UDS measures) ──────────────────────────────────────
    quality_measures: list[QualityMeasure] = field(default_factory=list)
    quality_measures_year: Optional[str] = None

    # ── Regulatory / compliance ───────────────────────────────────────────────
    last_osa_review_year: Optional[str] = None  # HRSA Operational Site Visit
    osa_outcome: Optional[str] = None           # "Approved" | "Approved with Conditions"
