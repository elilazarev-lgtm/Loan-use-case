import unittest

from israeli_mortgage import (
    Amortization,
    BorrowerType,
    MortgageApplication,
    Track,
    TrackType,
    assess,
    calculate_ltv,
    calculate_pti,
    max_loan_by_ltv,
    max_loan_by_pti,
    min_equity_required,
    monthly_payment,
)


class PaymentTests(unittest.TestCase):
    def test_spitzer(self):
        # 1,000,000 at 5% over 25 years -> 5,845.90
        self.assertAlmostEqual(monthly_payment(1_000_000, 0.05, 25), 5845.90, places=2)

    def test_zero_rate(self):
        self.assertAlmostEqual(monthly_payment(360_000, 0.0, 30), 1000.0)

    def test_equal_principal(self):
        p = monthly_payment(1_200_000, 0.06, 10, Amortization.EQUAL_PRINCIPAL)
        self.assertAlmostEqual(p, 10_000 + 6_000)


class LtvTests(unittest.TestCase):
    def test_uses_lower_of_price_and_appraisal(self):
        self.assertAlmostEqual(calculate_ltv(1_500_000, 2_000_000, 1_875_000), 0.80)

    def test_max_loan_per_borrower_type(self):
        self.assertEqual(max_loan_by_ltv(BorrowerType.FIRST_HOME, 2_000_000), 1_500_000)
        self.assertEqual(max_loan_by_ltv(BorrowerType.REPLACEMENT_HOME, 2_000_000), 1_400_000)
        self.assertEqual(max_loan_by_ltv(BorrowerType.INVESTMENT, 2_000_000), 1_000_000)

    def test_equity_when_appraisal_is_low(self):
        # price 2.0M, appraisal 1.8M -> max loan 1.35M -> equity 650K
        self.assertEqual(
            min_equity_required(BorrowerType.FIRST_HOME, 2_000_000, 1_800_000), 650_000
        )


class PtiTests(unittest.TestCase):
    def test_includes_other_debts(self):
        self.assertAlmostEqual(calculate_pti(8_000, 20_000, 2_000), 0.5)

    def test_max_loan_round_trip(self):
        loan = max_loan_by_pti(20_000, 0.05, 25, max_pti=0.4)
        self.assertAlmostEqual(monthly_payment(loan, 0.05, 25), 8_000, places=6)

    def test_rejects_non_positive_income(self):
        with self.assertRaises(ValueError):
            calculate_pti(1_000, 0)


class AssessTests(unittest.TestCase):
    def make(self, **kw):
        defaults = dict(
            borrower_type=BorrowerType.FIRST_HOME,
            purchase_price=2_000_000,
            net_monthly_income=30_000,
            tracks=[
                Track(TrackType.FIXED_UNLINKED, 500_000, 0.05, 25),
                Track(TrackType.PRIME, 500_000, 0.06, 25),
            ],
        )
        defaults.update(kw)
        return MortgageApplication(**defaults)

    def test_approved(self):
        result = assess(self.make())
        self.assertTrue(result.approved, result.violations)
        self.assertAlmostEqual(result.ltv, 0.5)

    def test_ltv_violation_for_investor(self):
        app = self.make(
            borrower_type=BorrowerType.INVESTMENT,
            tracks=[Track(TrackType.FIXED_UNLINKED, 1_200_000, 0.05, 25)],
        )
        result = assess(app)
        self.assertFalse(result.approved)
        self.assertIn("LTV", result.violations[0])

    def test_pti_violation(self):
        result = assess(self.make(net_monthly_income=10_000))
        self.assertFalse(result.approved)
        self.assertTrue(any("PTI" in v for v in result.violations))

    def test_fixed_share_and_term_violations(self):
        app = self.make(tracks=[
            Track(TrackType.FIXED_UNLINKED, 200_000, 0.05, 25),
            Track(TrackType.PRIME, 800_000, 0.06, 35),
        ])
        result = assess(app)
        self.assertTrue(any("fixed-rate" in v for v in result.violations))
        self.assertTrue(any("term" in v for v in result.violations))

    def test_rate_shock_only_affects_variable_tracks(self):
        base = assess(self.make())
        shocked = assess(self.make(rate_shock=0.02))
        fixed_only = assess(self.make(
            rate_shock=0.02,
            tracks=[Track(TrackType.FIXED_UNLINKED, 1_000_000, 0.05, 25)],
        ))
        self.assertGreater(shocked.pti, base.pti)
        self.assertAlmostEqual(fixed_only.monthly_payment, monthly_payment(1_000_000, 0.05, 25))


if __name__ == "__main__":
    unittest.main()
