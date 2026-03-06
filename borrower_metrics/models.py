"""
Data models for borrower metrics reporting.
Supports charter schools, health centers, early care programs, and other nonprofits.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CharterEvent:
    year: int
    event_type: str       # "original", "renewal", "modification", "probation", "revocation"
    description: str
    authorizer: Optional[str] = None


@dataclass
class EnrollmentYear:
    year: str             # e.g. "2019-20"
    total: int
    capacity: Optional[int] = None


@dataclass
class Demographics:
    """Percentages (0–100) for each category. Unknown/other fills remainder."""
    black: float = 0.0
    hispanic: float = 0.0
    white: float = 0.0
    asian: float = 0.0
    other: float = 0.0
    free_reduced_lunch: float = 0.0   # % eligible
    english_learners: float = 0.0     # % ELL
    special_education: float = 0.0    # % IEP/504


@dataclass
class AcademicYear:
    year: str             # e.g. "2022-23"
    ela_proficiency: Optional[float] = None   # % proficient/advanced
    math_proficiency: Optional[float] = None
    ela_growth: Optional[float] = None        # SGP or similar
    math_growth: Optional[float] = None
    graduation_rate: Optional[float] = None   # high schools
    attendance_rate: Optional[float] = None


@dataclass
class AccountabilityStatus:
    rating_year: str
    rating: str           # e.g. "Exemplary", "Recognized", "Acceptable", "Improvement Required"
    framework: str        # e.g. "ESSA", "State Accountability", "SQRP"
    subgroup_flags: list[str] = field(default_factory=list)   # underperforming subgroups
    notes: str = ""


@dataclass
class LoanInfo:
    amount: float                    # in dollars
    purpose: str
    financing_type: str              # e.g. "NMTC", "HTC", "Conventional", "NMTC + HTC"
    proposed_term_years: Optional[int] = None
    collateral: Optional[str] = None


@dataclass
class BorrowerProfile:
    # ── Organization identity ──────────────────────────────────────────────
    name: str
    org_type: str           # "charter_school" | "health_center" | "early_care" | "nonprofit"
    location: str           # City, State
    ein: Optional[str] = None
    website: Optional[str] = None
    year_founded: Optional[int] = None

    # ── Charter-specific ──────────────────────────────────────────────────
    authorizer: Optional[str] = None
    grade_span: Optional[str] = None          # e.g. "K-8"
    charter_events: list[CharterEvent] = field(default_factory=list)

    # ── Enrollment ────────────────────────────────────────────────────────
    enrollment_history: list[EnrollmentYear] = field(default_factory=list)

    # ── Demographics ──────────────────────────────────────────────────────
    demographics: Optional[Demographics] = None

    # ── Academic performance ──────────────────────────────────────────────
    academic_history: list[AcademicYear] = field(default_factory=list)

    # ── Accountability ────────────────────────────────────────────────────
    accountability: Optional[AccountabilityStatus] = None

    # ── Loan ─────────────────────────────────────────────────────────────
    loan: Optional[LoanInfo] = None

    # ── Analyst notes ─────────────────────────────────────────────────────
    analyst_notes: str = ""
    prepared_by: str = ""
    report_date: str = ""
