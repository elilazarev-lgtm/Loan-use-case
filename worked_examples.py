"""Worked examples: every LTV / PTI calculation shown step by step.

Each example computes the result by hand (printing each step with the real
numbers) and then checks it against the library function, so you can see both
the formula and that the code produces the same answer.

Run:  python3 worked_examples.py
"""

from israeli_mortgage import (
    HIGH_RISK_PTI,
    MAX_LTV,
    MAX_PTI,
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


def title(text):
    print()
    print("=" * 72)
    print(text)
    print("=" * 72)


def step(text):
    print(f"  {text}")


def check(manual, library, label, pct=False):
    assert abs(manual - library) < 0.01, (label, manual, library)
    shown = f"{library:.2%}" if pct else f"{library:,.2f}"
    step(f"✓ library {label} = {shown} (matches)")


# --------------------------------------------------------------------------
def example_1_spitzer_payment():
    title("Example 1 - Monthly payment, Spitzer (שפיצר): 1,000,000 ILS, 5%, 25 years")
    P, annual, years = 1_000_000, 0.05, 25
    step("Formula:  PMT = P * r / (1 - (1 + r)^-n)")
    r = annual / 12
    n = years * 12
    step(f"r = annual rate / 12 = {annual} / 12 = {r:.6f}")
    step(f"n = years * 12 = {years} * 12 = {n}")
    factor = (1 + r) ** -n
    step(f"(1 + r)^-n = (1 + {r:.6f})^-{n} = {factor:.6f}")
    pmt = P * r / (1 - factor)
    step(f"PMT = {P:,} * {r:.6f} / (1 - {factor:.6f}) = {pmt:,.2f} ILS")
    step(f"Total paid over {n} months = {pmt * n:,.0f} ILS "
         f"(interest {pmt * n - P:,.0f} ILS)")
    check(pmt, monthly_payment(P, annual, years), "monthly_payment")


# --------------------------------------------------------------------------
def example_2_equal_principal():
    title("Example 2 - Monthly payment, equal principal (קרן שווה): 1,200,000 ILS, 6%, 20 years")
    P, annual, years = 1_200_000, 0.06, 20
    n, r = years * 12, annual / 12
    step("Formula:  PMT(first) = P / n + P * r")
    principal_part = P / n
    interest_part = P * r
    step(f"Principal part = {P:,} / {n} = {principal_part:,.2f}")
    step(f"Interest part  = {P:,} * {r:.4f} = {interest_part:,.2f}")
    first = principal_part + interest_part
    step(f"First payment  = {principal_part:,.2f} + {interest_part:,.2f} = {first:,.2f} ILS")
    last = principal_part + principal_part * r
    step(f"Last payment   = {principal_part:,.2f} + {principal_part:,.2f} * {r:.4f} = {last:,.2f} ILS")
    step("-> payment falls every month; PTI is measured on the first (highest) payment")
    check(first, monthly_payment(P, annual, years, Amortization.EQUAL_PRINCIPAL), "monthly_payment")


# --------------------------------------------------------------------------
def example_3_ltv_low_appraisal():
    title("Example 3 - LTV when the appraisal is below the purchase price")
    price, appraisal, loan = 2_500_000, 2_400_000, 1_850_000
    step(f"Purchase price = {price:,}   Appraisal = {appraisal:,}   Requested loan = {loan:,}")
    value = min(price, appraisal)
    step(f"Property value = min(price, appraisal) = min({price:,}, {appraisal:,}) = {value:,}")
    ltv = loan / value
    step(f"LTV = loan / value = {loan:,} / {value:,} = {ltv:.2%}")
    step(f"Naive LTV on price would be {loan / price:.2%} - looks OK, but is NOT the regulatory figure")
    limit = MAX_LTV[BorrowerType.FIRST_HOME]
    max_loan = limit * value
    step(f"First-home limit {limit:.0%} -> max loan = {limit} * {value:,} = {max_loan:,.0f}")
    step(f"Result: {ltv:.2%} {'>' if ltv > limit else '<='} {limit:.0%} -> "
         f"{'DECLINED' if ltv > limit else 'OK'}; reduce loan by {loan - max_loan:,.0f}")
    check(ltv, calculate_ltv(loan, price, appraisal), "calculate_ltv", pct=True)
    check(max_loan, max_loan_by_ltv(BorrowerType.FIRST_HOME, price, appraisal), "max_loan_by_ltv")


# --------------------------------------------------------------------------
def example_4_ltv_by_borrower_type():
    title("Example 4 - Max loan and required equity by borrower type, price 3,000,000 ILS")
    price = 3_000_000
    step("Max loan = max LTV * value      Equity = price - max loan")
    step(f"{'Borrower type':<20}{'Max LTV':>9}{'Max loan':>14}{'Equity':>14}")
    for bt in BorrowerType:
        lim = MAX_LTV[bt]
        loan = lim * price
        equity = price - loan
        step(f"{bt.value:<20}{lim:>9.0%}{loan:>14,.0f}{equity:>14,.0f}")
        check(equity, min_equity_required(bt, price), f"min_equity_required[{bt.value}]")


# --------------------------------------------------------------------------
def example_5_pti_with_other_debts():
    title("Example 5 - PTI including other loans")
    mortgage_pmt, other, income = 7_500, 1_500, 22_000
    step(f"Mortgage payment = {mortgage_pmt:,}   Car loan = {other:,}   Net income = {income:,}")
    step("Formula:  PTI = (mortgage payment + other loan payments) / net income")
    pti = (mortgage_pmt + other) / income
    step(f"PTI = ({mortgage_pmt:,} + {other:,}) / {income:,} = {mortgage_pmt + other:,} / {income:,} = {pti:.2%}")
    step(f"Mortgage-only PTI would be {mortgage_pmt / income:.2%} - other debts add "
         f"{other / income:.2%}")
    if pti > MAX_PTI:
        verdict = "PROHIBITED (> 50%)"
    elif pti > HIGH_RISK_PTI:
        verdict = "allowed but HIGH RISK (40%-50%)"
    else:
        verdict = "OK (<= 40%)"
    step(f"Result: {verdict}")
    check(pti, calculate_pti(mortgage_pmt, income, other), "calculate_pti", pct=True)


# --------------------------------------------------------------------------
def example_6_max_loan_by_pti():
    title("Example 6 - Largest loan the income supports (reverse PTI)")
    income, other, cap, annual, years = 25_000, 1_000, 0.35, 0.05, 30
    step(f"Net income {income:,}, other loans {other:,}, bank PTI cap {cap:.0%}, rate {annual:.0%}, {years}y")
    max_total = income * cap
    step(f"Max total repayments = {income:,} * {cap} = {max_total:,.2f}")
    max_pmt = max_total - other
    step(f"Max mortgage payment = {max_total:,.2f} - {other:,} = {max_pmt:,.2f}")
    r, n = annual / 12, years * 12
    step("Formula:  P = PMT * (1 - (1 + r)^-n) / r")
    factor = (1 + r) ** -n
    P = max_pmt * (1 - factor) / r
    step(f"P = {max_pmt:,.2f} * (1 - {factor:.6f}) / {r:.6f} = {P:,.0f} ILS")
    check(P, max_loan_by_pti(income, annual, years, other, cap), "max_loan_by_pti")


# --------------------------------------------------------------------------
def example_7_full_mix(rate_shock=0.0):
    label = "with +2% stress on prime/variable" if rate_shock else "base rates"
    title(f"Example 7 - Full application, 3-track mix ({label})")
    app = MortgageApplication(
        borrower_type=BorrowerType.FIRST_HOME,
        purchase_price=2_200_000,
        appraisal_value=2_250_000,
        net_monthly_income=26_000,
        other_monthly_debt_payments=800,
        max_pti=0.40,
        rate_shock=rate_shock,
        tracks=[
            Track(TrackType.FIXED_UNLINKED, 550_000, 0.0490, 25),
            Track(TrackType.PRIME, 550_000, 0.0600, 25),
            Track(TrackType.VARIABLE_CPI_LINKED, 450_000, 0.0350, 25),
        ],
    )
    loan = sum(t.amount for t in app.tracks)
    step(f"Loan = {' + '.join(f'{t.amount:,}' for t in app.tracks)} = {loan:,}")

    value = min(app.purchase_price, app.appraisal_value)
    ltv = loan / value
    step(f"Value = min({app.purchase_price:,}, {app.appraisal_value:,}) = {value:,}")
    step(f"LTV = {loan:,} / {value:,} = {ltv:.2%}  (limit {MAX_LTV[app.borrower_type]:.0%})")

    step("Payments per track:")
    total = 0.0
    for t in app.tracks:
        rate = t.annual_rate + (0 if t.track_type.is_fixed else rate_shock)
        pmt = monthly_payment(t.amount, rate, t.term_years)
        total += pmt
        shock = f" (+{rate_shock:.0%} shock)" if rate_shock and not t.track_type.is_fixed else ""
        step(f"   {t.track_type.value:<22}{t.amount:>10,} @ {rate:.2%}{shock:<14} -> {pmt:>9,.2f}")
    step(f"   Total mortgage payment = {total:,.2f}")

    pti = (total + app.other_monthly_debt_payments) / app.net_monthly_income
    step(f"PTI = ({total:,.2f} + {app.other_monthly_debt_payments:,}) / {app.net_monthly_income:,} = {pti:.2%}"
         f"  (bank cap {app.max_pti:.0%})")

    fixed = sum(t.amount for t in app.tracks if t.track_type.is_fixed)
    step(f"Fixed share = {fixed:,} / {loan:,} = {fixed / loan:.2%}  (min 33.3%)")

    result = assess(app)
    check(ltv, result.ltv, "ltv", pct=True)
    check(total, result.monthly_payment, "monthly_payment")
    check(pti, result.pti, "pti", pct=True)
    print()
    print("\n".join("  " + line for line in result.summary().splitlines()))


# --------------------------------------------------------------------------
def example_8_investor_binding_limit():
    title("Example 8 - Investor: which limit binds, LTV or PTI?")
    price, other, annual, years = 1_800_000, 0, 0.052, 25
    for income in (35_000, 9_000):
        step(f"Investment apartment {price:,}, net income {income:,}, rate {annual:.1%}, {years}y")
        ltv_cap = MAX_LTV[BorrowerType.INVESTMENT] * price
        step(f"  LTV cap = 50% * {price:,} = {ltv_cap:,.0f}")
        pti_cap = max_loan_by_pti(income, annual, years, other, MAX_PTI)
        step(f"  PTI cap = loan whose payment = 50% * {income:,} = {income * MAX_PTI:,.0f}/month -> {pti_cap:,.0f}")
        max_loan = min(ltv_cap, pti_cap)
        binding = "LTV" if ltv_cap < pti_cap else "PTI"
        step(f"  Max loan = min({ltv_cap:,.0f}, {pti_cap:,.0f}) = {max_loan:,.0f}  -> {binding} binds")
        step(f"  Equity needed = {price:,} - {max_loan:,.0f} = {price - max_loan:,.0f}")
        print()


if __name__ == "__main__":
    example_1_spitzer_payment()
    example_2_equal_principal()
    example_3_ltv_low_appraisal()
    example_4_ltv_by_borrower_type()
    example_5_pti_with_other_debts()
    example_6_max_loan_by_pti()
    example_7_full_mix()
    example_7_full_mix(rate_shock=0.02)
    example_8_investor_binding_limit()
