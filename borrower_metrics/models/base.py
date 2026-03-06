"""
Base borrower profile and shared data classes.
All org-type-specific models inherit from BaseBorrowerProfile.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LoanInfo:
    amount: float                       # dollars
    purpose: str
    financing_type: str                 # "NMTC" | "HTC" | "Conventional" | "NMTC + HTC"
    proposed_term_years: Optional[int] = None
    collateral: Optional[str] = None


@dataclass
class Demographics:
    """Race/ethnicity percentages (0–100). Service indicators are subclass-specific."""
    black: float = 0.0
    hispanic: float = 0.0
    white: float = 0.0
    asian: float = 0.0
    other: float = 0.0


@dataclass
class AccountabilityStatus:
    """Generic accountability/regulatory status — meaning varies by org type."""
    rating_year: str
    rating: str
    framework: str                      # e.g. "ESSA", "HRSA UDS", "Louisiana Quality Start"
    subgroup_flags: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class BaseBorrowerProfile:
    # ── Identity ──────────────────────────────────────────────────────────────
    name: str
    org_type: str                       # discriminator key
    location: str                       # "City, ST"
    ein: Optional[str] = None
    website: Optional[str] = None
    year_founded: Optional[int] = None

    # ── Report metadata ───────────────────────────────────────────────────────
    analyst_notes: str = ""
    prepared_by: str = ""
    report_date: str = ""

    # ── Shared optional fields ────────────────────────────────────────────────
    loan: Optional[LoanInfo] = None
    demographics: Optional[Demographics] = None     # race/ethnicity
    accountability: Optional[AccountabilityStatus] = None
