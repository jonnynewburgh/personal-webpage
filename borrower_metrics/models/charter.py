"""
Charter school borrower profile and supporting data classes.
"""
from dataclasses import dataclass, field
from typing import Optional
from .base import BaseBorrowerProfile


@dataclass
class CharterEvent:
    year: int
    event_type: str         # "original" | "renewal" | "modification" | "probation" | "revocation"
    description: str
    authorizer: Optional[str] = None


@dataclass
class EnrollmentYear:
    year: str               # e.g. "2022-23"
    total: int
    capacity: Optional[int] = None


@dataclass
class AcademicYear:
    year: str
    ela_proficiency: Optional[float] = None     # % proficient/advanced on state assessment
    math_proficiency: Optional[float] = None
    ela_growth: Optional[float] = None          # Student Growth Percentile (SGP)
    math_growth: Optional[float] = None
    graduation_rate: Optional[float] = None     # high schools only
    attendance_rate: Optional[float] = None


@dataclass
class CharterSchoolProfile(BaseBorrowerProfile):
    # ── Charter governance ───────────────────────────────────────────────────
    authorizer: Optional[str] = None
    grade_span: Optional[str] = None            # "K-8", "9-12", etc.
    management_org: Optional[str] = None        # CMO or EMO name
    management_org_type: Optional[str] = None   # "CMO" | "EMO"
    facility_status: Optional[str] = None       # "Leasing" | "Owner-occupied" | "Under construction"

    # ── Per-pupil revenue ────────────────────────────────────────────────────
    per_pupil_revenue: Optional[float] = None
    per_pupil_revenue_year: Optional[str] = None

    # ── Student service indicators ───────────────────────────────────────────
    free_reduced_lunch_pct: Optional[float] = None
    english_learners_pct: Optional[float] = None
    special_education_pct: Optional[float] = None

    # ── Historical data ───────────────────────────────────────────────────────
    charter_events: list[CharterEvent] = field(default_factory=list)
    enrollment_history: list[EnrollmentYear] = field(default_factory=list)
    academic_history: list[AcademicYear] = field(default_factory=list)
