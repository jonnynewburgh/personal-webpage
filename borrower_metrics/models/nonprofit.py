"""
Generic nonprofit borrower profile and supporting data classes.
Use for community organizations that don't fit charter, FQHC, or early care categories.
"""
from dataclasses import dataclass, field
from typing import Optional
from .base import BaseBorrowerProfile


@dataclass
class RevenueYear:
    year: str                           # fiscal year, e.g. "FY 2024"
    total_revenue: float                # total organizational revenue, dollars
    total_expenses: Optional[float] = None
    net_assets: Optional[float] = None


@dataclass
class NonprofitRevenueMix:
    """Revenue by source category as % of total. One record per year."""
    year: str
    government_grants_pct: float = 0.0          # federal, state, local grants & contracts
    foundation_grants_pct: float = 0.0
    corporate_contributions_pct: float = 0.0
    individual_contributions_pct: float = 0.0
    earned_revenue_pct: float = 0.0             # program service fees, contracts
    other_pct: float = 0.0


@dataclass
class ProgramMetric:
    """A single program output or outcome metric."""
    name: str                   # "Clients served annually", "Meals distributed", etc.
    value: str                  # string to accommodate counts, ranges, and narrative
    year: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class NonprofitProfile(BaseBorrowerProfile):
    # ── Mission & programs ───────────────────────────────────────────────────
    mission_summary: Optional[str] = None
    primary_program_area: Optional[str] = None  # "Housing", "Food Security", "Workforce Dev"
    clients_served_annually: Optional[int] = None
    clients_served_year: Optional[str] = None

    # ── Financial health ─────────────────────────────────────────────────────
    operating_reserve_months: Optional[float] = None    # months of operating expenses in reserve
    operating_reserve_year: Optional[str] = None

    # ── Historical data ───────────────────────────────────────────────────────
    revenue_history: list[RevenueYear] = field(default_factory=list)
    revenue_mix_history: list[NonprofitRevenueMix] = field(default_factory=list)
    program_metrics: list[ProgramMetric] = field(default_factory=list)

    # ── Compliance ───────────────────────────────────────────────────────────
    last_audit_year: Optional[str] = None
    audit_outcome: Optional[str] = None         # "Unmodified" | "Modified" | "Adverse"
    irs_form_990_year: Optional[str] = None
