"""
Re-exports all borrower profile classes and supporting dataclasses.
Usage: from borrower_metrics.models import FQHCProfile, PatientYear, ...
"""
from .base import BaseBorrowerProfile, LoanInfo, Demographics, AccountabilityStatus
from .charter import (
    CharterSchoolProfile, CharterEvent, EnrollmentYear, AcademicYear
)
from .fqhc import (
    FQHCProfile, PatientYear, PayerMix, FQHCRevenueMix,
    QualityMeasure, HRSAGrantInfo
)
from .early_care import (
    EarlyCareProfile, AgeGroupEnrollment, EarlyCareRevenueMix,
    StaffQualifications, SchoolReadinessOutcome
)
from .nonprofit import (
    NonprofitProfile, RevenueYear, NonprofitRevenueMix, ProgramMetric
)

__all__ = [
    # Base
    "BaseBorrowerProfile", "LoanInfo", "Demographics", "AccountabilityStatus",
    # Charter
    "CharterSchoolProfile", "CharterEvent", "EnrollmentYear", "AcademicYear",
    # FQHC
    "FQHCProfile", "PatientYear", "PayerMix", "FQHCRevenueMix",
    "QualityMeasure", "HRSAGrantInfo",
    # Early Care
    "EarlyCareProfile", "AgeGroupEnrollment", "EarlyCareRevenueMix",
    "StaffQualifications", "SchoolReadinessOutcome",
    # Nonprofit
    "NonprofitProfile", "RevenueYear", "NonprofitRevenueMix", "ProgramMetric",
]
