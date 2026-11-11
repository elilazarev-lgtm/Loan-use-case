# Worked Examples - LTV & PTI step by step

Output of `python3 worked_examples.py`. Every step is computed by hand and then checked against the library (✓ lines).

```text

========================================================================
Example 1 - Monthly payment, Spitzer (שפיצר): 1,000,000 ILS, 5%, 25 years
========================================================================
  Formula:  PMT = P * r / (1 - (1 + r)^-n)
  r = annual rate / 12 = 0.05 / 12 = 0.004167
  n = years * 12 = 25 * 12 = 300
  (1 + r)^-n = (1 + 0.004167)^-300 = 0.287250
  PMT = 1,000,000 * 0.004167 / (1 - 0.287250) = 5,845.90 ILS
  Total paid over 300 months = 1,753,770 ILS (interest 753,770 ILS)
  ✓ library monthly_payment = 5,845.90 (matches)

========================================================================
Example 2 - Monthly payment, equal principal (קרן שווה): 1,200,000 ILS, 6%, 20 years
========================================================================
  Formula:  PMT(first) = P / n + P * r
  Principal part = 1,200,000 / 240 = 5,000.00
  Interest part  = 1,200,000 * 0.0050 = 6,000.00
  First payment  = 5,000.00 + 6,000.00 = 11,000.00 ILS
  Last payment   = 5,000.00 + 5,000.00 * 0.0050 = 5,025.00 ILS
  -> payment falls every month; PTI is measured on the first (highest) payment
  ✓ library monthly_payment = 11,000.00 (matches)

========================================================================
Example 3 - LTV when the appraisal is below the purchase price
========================================================================
  Purchase price = 2,500,000   Appraisal = 2,400,000   Requested loan = 1,850,000
  Property value = min(price, appraisal) = min(2,500,000, 2,400,000) = 2,400,000
  LTV = loan / value = 1,850,000 / 2,400,000 = 77.08%
  Naive LTV on price would be 74.00% - looks OK, but is NOT the regulatory figure
  First-home limit 75% -> max loan = 0.75 * 2,400,000 = 1,800,000
  Result: 77.08% > 75% -> DECLINED; reduce loan by 50,000
  ✓ library calculate_ltv = 77.08% (matches)
  ✓ library max_loan_by_ltv = 1,800,000.00 (matches)

========================================================================
Example 4 - Max loan and required equity by borrower type, price 3,000,000 ILS
========================================================================
  Max loan = max LTV * value      Equity = price - max loan
  Borrower type         Max LTV      Max loan        Equity
  first_home                75%     2,250,000       750,000
  ✓ library min_equity_required[first_home] = 750,000.00 (matches)
  replacement_home          70%     2,100,000       900,000
  ✓ library min_equity_required[replacement_home] = 900,000.00 (matches)
  investment                50%     1,500,000     1,500,000
  ✓ library min_equity_required[investment] = 1,500,000.00 (matches)
  foreign_resident          50%     1,500,000     1,500,000
  ✓ library min_equity_required[foreign_resident] = 1,500,000.00 (matches)

========================================================================
Example 5 - PTI including other loans
========================================================================
  Mortgage payment = 7,500   Car loan = 1,500   Net income = 22,000
  Formula:  PTI = (mortgage payment + other loan payments) / net income
  PTI = (7,500 + 1,500) / 22,000 = 9,000 / 22,000 = 40.91%
  Mortgage-only PTI would be 34.09% - other debts add 6.82%
  Result: allowed but HIGH RISK (40%-50%)
  ✓ library calculate_pti = 40.91% (matches)

========================================================================
Example 6 - Largest loan the income supports (reverse PTI)
========================================================================
  Net income 25,000, other loans 1,000, bank PTI cap 35%, rate 5%, 30y
  Max total repayments = 25,000 * 0.35 = 8,750.00
  Max mortgage payment = 8,750.00 - 1,000 = 7,750.00
  Formula:  P = PMT * (1 - (1 + r)^-n) / r
  P = 7,750.00 * (1 - 0.223827) / 0.004167 = 1,443,683 ILS
  ✓ library max_loan_by_pti = 1,443,682.53 (matches)

========================================================================
Example 7 - Full application, 3-track mix (base rates)
========================================================================
  Loan = 550,000 + 550,000 + 450,000 = 1,550,000
  Value = min(2,200,000, 2,250,000) = 2,200,000
  LTV = 1,550,000 / 2,200,000 = 70.45%  (limit 75%)
  Payments per track:
     fixed_unlinked           550,000 @ 4.90%               ->  3,183.28
     prime                    550,000 @ 6.00%               ->  3,543.66
     variable_cpi_linked      450,000 @ 3.50%               ->  2,252.81
     Total mortgage payment = 8,979.75
  PTI = (8,979.75 + 800) / 26,000 = 37.61%  (bank cap 40%)
  Fixed share = 550,000 / 1,550,000 = 35.48%  (min 33.3%)
  ✓ library ltv = 70.45% (matches)
  ✓ library monthly_payment = 8,979.75 (matches)
  ✓ library pti = 37.61% (matches)

  Loan amount:             1,550,000 ILS
  Property value:          2,200,000 ILS
  LTV:                        70.5%  (max 75%)
  Max loan by LTV:         1,650,000 ILS
  Monthly payment:             8,980 ILS
  PTI:                        37.6%  (max 40%)
  Fixed-rate share:           35.5%  (min 33%)
  Decision:           APPROVED

========================================================================
Example 7 - Full application, 3-track mix (with +2% stress on prime/variable)
========================================================================
  Loan = 550,000 + 550,000 + 450,000 = 1,550,000
  Value = min(2,200,000, 2,250,000) = 2,200,000
  LTV = 1,550,000 / 2,200,000 = 70.45%  (limit 75%)
  Payments per track:
     fixed_unlinked           550,000 @ 4.90%               ->  3,183.28
     prime                    550,000 @ 8.00% (+2% shock)   ->  4,244.99
     variable_cpi_linked      450,000 @ 5.50% (+2% shock)   ->  2,763.39
     Total mortgage payment = 10,191.67
  PTI = (10,191.67 + 800) / 26,000 = 42.28%  (bank cap 40%)
  Fixed share = 550,000 / 1,550,000 = 35.48%  (min 33.3%)
  ✓ library ltv = 70.45% (matches)
  ✓ library monthly_payment = 10,191.67 (matches)
  ✓ library pti = 42.28% (matches)

  Loan amount:             1,550,000 ILS
  Property value:          2,200,000 ILS
  LTV:                        70.5%  (max 75%)
  Max loan by LTV:         1,650,000 ILS
  Monthly payment:            10,192 ILS
  PTI:                        42.3%  (max 40%)
  Fixed-rate share:           35.5%  (min 33%)
  Decision:           DECLINED
  Warning:            PTI above 40% - high-risk loan
    - PTI 42.3% exceeds 40%

========================================================================
Example 8 - Investor: which limit binds, LTV or PTI?
========================================================================
  Investment apartment 1,800,000, net income 35,000, rate 5.2%, 25y
    LTV cap = 50% * 1,800,000 = 900,000
    PTI cap = loan whose payment = 50% * 35,000 = 17,500/month -> 2,934,757
    Max loan = min(900,000, 2,934,757) = 900,000  -> LTV binds
    Equity needed = 1,800,000 - 900,000 = 900,000

  Investment apartment 1,800,000, net income 9,000, rate 5.2%, 25y
    LTV cap = 50% * 1,800,000 = 900,000
    PTI cap = loan whose payment = 50% * 9,000 = 4,500/month -> 754,652
    Max loan = min(900,000, 754,652) = 754,652  -> PTI binds
    Equity needed = 1,800,000 - 754,652 = 1,045,348

```
