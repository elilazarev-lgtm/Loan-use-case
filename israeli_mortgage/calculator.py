"""LTV and PTI calculations for Israeli mortgages (משכנתא).

Definitions used by the Bank of Israel:

* LTV (שיעור מימון) = loan amount / property value, where the property value is
  the *lower* of the purchase price and the appraiser's valuation.
* PTI (יחס החזר) = total monthly loan repayments / net monthly income.

A typical Israeli mortgage is a "mix" (תמהיל) of several tracks, each with its
own rate, term and indexation. The monthly payment is the sum of the payments
of all tracks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .regulation import (
    HIGH_RISK_PTI,
    MAX_LTV,
    MAX_PTI,
    MAX_TERM_YEARS,
    MIN_FIXED_RATE_SHARE,
    BorrowerType,
)


class TrackType(Enum):
    FIXED_UNLINKED = "fixed_unlinked"  # קל"צ - קבועה לא צמודה
    FIXED_CPI_LINKED = "fixed_cpi_linked"  # ק"צ - קבועה צמודה למדד
    PRIME = "prime"  # פריים
    VARIABLE_UNLINKED = "variable_unlinked"  # משתנה לא צמודה
    VARIABLE_CPI_LINKED = "variable_cpi_linked"  # משתנה צמודה

    @property
    def is_fixed(self) -> bool:
        return self in (TrackType.FIXED_UNLINKED, TrackType.FIXED_CPI_LINKED)


class Amortization(Enum):
    SPITZER = "spitzer"  # שפיצר - equal monthly payments (annuity)
    EQUAL_PRINCIPAL = "equal_principal"  # קרן שווה


@dataclass
class Track:
    """One track (מסלול) of the mortgage mix."""

    track_type: TrackType
    amount: float
    annual_rate: float  # e.g. 0.045 for 4.5%
    term_years: int
    amortization: Amortization = Amortization.SPITZER

    def first_monthly_payment(self, rate_shock: float = 0.0) -> float:
        """Payment of the first month.

        ``rate_shock`` is added to the rate of non-fixed tracks, for stress
        testing PTI against future rate increases.
        """
        rate = self.annual_rate
        if not self.track_type.is_fixed:
            rate += rate_shock
        return monthly_payment(self.amount, rate, self.term_years, self.amortization)


def monthly_payment(
    principal: float,
    annual_rate: float,
    term_years: int,
    amortization: Amortization = Amortization.SPITZER,
) -> float:
    """First monthly payment for a loan."""
    if principal < 0:
        raise ValueError("principal must be non-negative")
    if term_years <= 0:
        raise ValueError("term_years must be positive")
    n = term_years * 12
    r = annual_rate / 12
    if amortization is Amortization.EQUAL_PRINCIPAL:
        return principal / n + principal * r
    if r == 0:
        return principal / n
    return principal * r / (1 - (1 + r) ** -n)


def max_principal_for_payment(
    payment: float, annual_rate: float, term_years: int
) -> float:
    """Largest Spitzer loan a given monthly payment can service."""
    n = term_years * 12
    r = annual_rate / 12
    if r == 0:
        return payment * n
    return payment * (1 - (1 + r) ** -n) / r


# --------------------------------------------------------------------------- LTV


def property_value(purchase_price: float, appraisal_value: float | None = None) -> float:
    """Value used for LTV: the lower of purchase price and appraisal."""
    if purchase_price <= 0:
        raise ValueError("purchase_price must be positive")
    if appraisal_value is None:
        return purchase_price
    if appraisal_value <= 0:
        raise ValueError("appraisal_value must be positive")
    return min(purchase_price, appraisal_value)


def calculate_ltv(
    loan_amount: float, purchase_price: float, appraisal_value: float | None = None
) -> float:
    return loan_amount / property_value(purchase_price, appraisal_value)


def max_loan_by_ltv(
    borrower_type: BorrowerType,
    purchase_price: float,
    appraisal_value: float | None = None,
) -> float:
    return MAX_LTV[borrower_type] * property_value(purchase_price, appraisal_value)


def min_equity_required(
    borrower_type: BorrowerType,
    purchase_price: float,
    appraisal_value: float | None = None,
) -> float:
    """Own capital (הון עצמי) needed, before taxes and fees."""
    return purchase_price - max_loan_by_ltv(borrower_type, purchase_price, appraisal_value)


# --------------------------------------------------------------------------- PTI


def calculate_pti(
    monthly_mortgage_payment: float,
    net_monthly_income: float,
    other_monthly_debt_payments: float = 0.0,
) -> float:
    """PTI on net (after-tax) income, including other loan repayments."""
    if net_monthly_income <= 0:
        raise ValueError("net_monthly_income must be positive")
    return (monthly_mortgage_payment + other_monthly_debt_payments) / net_monthly_income


def max_monthly_payment_by_pti(
    net_monthly_income: float,
    other_monthly_debt_payments: float = 0.0,
    max_pti: float = MAX_PTI,
) -> float:
    return max(0.0, net_monthly_income * max_pti - other_monthly_debt_payments)


def max_loan_by_pti(
    net_monthly_income: float,
    annual_rate: float,
    term_years: int,
    other_monthly_debt_payments: float = 0.0,
    max_pti: float = MAX_PTI,
) -> float:
    payment = max_monthly_payment_by_pti(net_monthly_income, other_monthly_debt_payments, max_pti)
    return max_principal_for_payment(payment, annual_rate, term_years)


# ---------------------------------------------------------------- Full assessment


@dataclass
class MortgageApplication:
    borrower_type: BorrowerType
    purchase_price: float
    net_monthly_income: float  # combined net income of all borrowers
    tracks: list[Track]
    appraisal_value: float | None = None
    other_monthly_debt_payments: float = 0.0
    max_pti: float = MAX_PTI  # override with the bank's internal policy
    rate_shock: float = 0.0  # stress add-on for variable/prime tracks

    @property
    def loan_amount(self) -> float:
        return sum(t.amount for t in self.tracks)


@dataclass
class Assessment:
    loan_amount: float
    property_value: float
    ltv: float
    max_ltv: float
    monthly_payment: float
    pti: float
    max_pti: float
    fixed_rate_share: float
    max_loan_by_ltv: float
    approved: bool
    high_risk_pti: bool
    violations: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Loan amount:        {self.loan_amount:>14,.0f} ILS",
            f"Property value:     {self.property_value:>14,.0f} ILS",
            f"LTV:                {self.ltv:>13.1%}  (max {self.max_ltv:.0%})",
            f"Max loan by LTV:    {self.max_loan_by_ltv:>14,.0f} ILS",
            f"Monthly payment:    {self.monthly_payment:>14,.0f} ILS",
            f"PTI:                {self.pti:>13.1%}  (max {self.max_pti:.0%})",
            f"Fixed-rate share:   {self.fixed_rate_share:>13.1%}  (min {MIN_FIXED_RATE_SHARE:.0%})",
            f"Decision:           {'APPROVED' if self.approved else 'DECLINED'}",
        ]
        if self.high_risk_pti:
            lines.append("Warning:            PTI above 40% - high-risk loan")
        lines += [f"  - {v}" for v in self.violations]
        return "\n".join(lines)


def assess(app: MortgageApplication) -> Assessment:
    """Check an application against the LTV, PTI, mix and term limits."""
    if not app.tracks:
        raise ValueError("application must contain at least one track")

    value = property_value(app.purchase_price, app.appraisal_value)
    loan = app.loan_amount
    ltv = loan / value
    max_ltv = MAX_LTV[app.borrower_type]

    payment = sum(t.first_monthly_payment(app.rate_shock) for t in app.tracks)
    pti = calculate_pti(payment, app.net_monthly_income, app.other_monthly_debt_payments)
    fixed_share = sum(t.amount for t in app.tracks if t.track_type.is_fixed) / loan

    violations = []
    if ltv > max_ltv + 1e-9:
        violations.append(f"LTV {ltv:.1%} exceeds {max_ltv:.0%} for {app.borrower_type.value}")
    if pti > app.max_pti + 1e-9:
        violations.append(f"PTI {pti:.1%} exceeds {app.max_pti:.0%}")
    if fixed_share < MIN_FIXED_RATE_SHARE - 1e-9:
        violations.append(f"fixed-rate share {fixed_share:.1%} is below one third")
    for t in app.tracks:
        if t.term_years > MAX_TERM_YEARS:
            violations.append(f"{t.track_type.value} term {t.term_years}y exceeds {MAX_TERM_YEARS}y")

    return Assessment(
        loan_amount=loan,
        property_value=value,
        ltv=ltv,
        max_ltv=max_ltv,
        monthly_payment=payment,
        pti=pti,
        max_pti=app.max_pti,
        fixed_rate_share=fixed_share,
        max_loan_by_ltv=max_ltv * value,
        approved=not violations,
        high_risk_pti=pti > HIGH_RISK_PTI,
        violations=violations,
    )
