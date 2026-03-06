"""
Early Care & Education (ECE) borrower profile and supporting data classes.
Covers Head Start, Early Head Start, state pre-K, and licensed child care programs.
"""
from dataclasses import dataclass, field
from typing import Optional
from .base import BaseBorrowerProfile


@dataclass
class AgeGroupEnrollment:
    year: str
    age_group: str                      # "Infant (0-12mo)" | "Toddler (1-3yr)" | "Preschool (3-5yr)" | "School-age (5+)"
    enrolled: int
    licensed_capacity: Optional[int] = None


@dataclass
class EarlyCareRevenueMix:
    """Revenue/subsidy sources as % of total. One record per year."""
    year: str
    ccdf_pct: float = 0.0               # Child Care and Development Fund (state subsidy)
    head_start_pct: float = 0.0         # federal Head Start / Early Head Start
    state_prek_pct: float = 0.0         # state pre-K grant
    private_tuition_pct: float = 0.0
    other_grants_pct: float = 0.0
    other_pct: float = 0.0


@dataclass
class StaffQualifications:
    """Staff credential snapshot. One record per year."""
    year: str
    bachelors_or_higher_pct: float = 0.0    # % of lead teachers with BA+
    cda_pct: float = 0.0                    # % with Child Development Associate credential
    annual_turnover_rate: Optional[float] = None


@dataclass
class SchoolReadinessOutcome:
    """Aggregate school-readiness assessment result for a domain in a given year."""
    year: str
    assessment_tool: str        # "Teaching Strategies GOLD" | "ASQ-3" | "TS GOLD" | etc.
    domain: str                 # "Literacy" | "Math" | "Social-Emotional" | "Overall"
    pct_on_track: Optional[float] = None        # % of children meeting/exceeding benchmark
    benchmark_pct: Optional[float] = None       # normative or state benchmark


@dataclass
class EarlyCareProfile(BaseBorrowerProfile):
    # ── Quality credentials ──────────────────────────────────────────────────
    qris_rating: Optional[str] = None           # "4-Star", "Level 3", "Excelling"
    qris_framework: Optional[str] = None        # "Louisiana Quality Start", "Ohio Step Up to Quality"
    qris_rating_year: Optional[str] = None
    head_start_grantee: bool = False
    early_head_start_grantee: bool = False
    licensed_capacity_total: Optional[int] = None
    number_of_classrooms: Optional[int] = None

    # ── Student/family service indicators ────────────────────────────────────
    subsidized_enrollment_pct: Optional[float] = None   # % on subsidy (CCDF or HS)
    english_learners_pct: Optional[float] = None
    special_education_pct: Optional[float] = None
    income_eligible_pct: Optional[float] = None         # % at/below income eligibility threshold

    # ── Historical data ───────────────────────────────────────────────────────
    age_group_enrollment_history: list[AgeGroupEnrollment] = field(default_factory=list)
    revenue_mix_history: list[EarlyCareRevenueMix] = field(default_factory=list)
    staff_qualifications_history: list[StaffQualifications] = field(default_factory=list)
    school_readiness_outcomes: list[SchoolReadinessOutcome] = field(default_factory=list)

    # ── Regulatory / compliance ───────────────────────────────────────────────
    last_monitoring_year: Optional[str] = None
    monitoring_outcome: Optional[str] = None    # "No Findings" | "Corrective Action" | etc.
    deficiency_history: Optional[str] = None    # free-text summary
