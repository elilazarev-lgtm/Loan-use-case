"""Bank of Israel mortgage limits (Proper Conduct of Banking Business Directive 329).

These are the regulatory ceilings. Individual banks usually apply stricter
internal policies (e.g. a PTI cap of 30-40%), so the values are exposed as
constants that callers can override.
"""

from enum import Enum


class BorrowerType(Enum):
    """Purpose of the purchase, which determines the maximum LTV."""

    FIRST_HOME = "first_home"  # דירה יחידה - borrower owns no other apartment
    REPLACEMENT_HOME = "replacement_home"  # משפרי דיור - will sell current home
    INVESTMENT = "investment"  # דירה להשקעה / additional apartment
    FOREIGN_RESIDENT = "foreign_resident"  # תושב חוץ


# Maximum loan-to-value ratio per borrower type (Directive 329).
MAX_LTV = {
    BorrowerType.FIRST_HOME: 0.75,
    BorrowerType.REPLACEMENT_HOME: 0.70,
    BorrowerType.INVESTMENT: 0.50,
    BorrowerType.FOREIGN_RESIDENT: 0.50,
}

# Payment-to-income: loans above 50% are prohibited; 40%-50% are permitted but
# carry a higher capital risk weight and are treated as high-risk by banks.
MAX_PTI = 0.50
HIGH_RISK_PTI = 0.40

# At least one third of the loan must be at a fixed interest rate.
MIN_FIXED_RATE_SHARE = 1 / 3

# Maximum loan term.
MAX_TERM_YEARS = 30
