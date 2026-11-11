"""Example: first-home buyer with a typical three-track mix."""

from israeli_mortgage import (
    BorrowerType,
    MortgageApplication,
    Track,
    TrackType,
    assess,
    max_loan_by_pti,
)

app = MortgageApplication(
    borrower_type=BorrowerType.FIRST_HOME,
    purchase_price=2_500_000,
    appraisal_value=2_450_000,
    net_monthly_income=30_000,
    other_monthly_debt_payments=1_200,  # e.g. car loan
    max_pti=0.40,  # bank's internal policy, stricter than the 50% ceiling
    tracks=[
        Track(TrackType.FIXED_UNLINKED, 620_000, 0.0480, 25),
        Track(TrackType.PRIME, 600_000, 0.0600, 25),
        Track(TrackType.FIXED_CPI_LINKED, 600_000, 0.0330, 25),
    ],
)

print(assess(app).summary())

print()
print("Stress test (+2% on prime/variable tracks):")
app.rate_shock = 0.02
print(assess(app).summary())

print()
cap = max_loan_by_pti(30_000, annual_rate=0.05, term_years=25,
                      other_monthly_debt_payments=1_200, max_pti=0.40)
print(f"Max loan by PTI (40%, 5%, 25y): {cap:,.0f} ILS")
