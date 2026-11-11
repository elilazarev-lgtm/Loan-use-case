# Israeli Mortgage LTV / PTI Calculator

Python (3.10+, no dependencies) calculations for Israeli mortgages under Bank of Israel Directive 329.

| Rule | Limit |
|---|---|
| LTV, first home (דירה יחידה) | 75% |
| LTV, replacement home (משפרי דיור) | 70% |
| LTV, investment / foreign resident | 50% |
| PTI (יחס החזר), on net income | max 50% (40%+ is high risk) |
| Fixed-rate portion of the mix | at least 1/3 |
| Term | max 30 years |

- **LTV** = loan / property value, where value is the lower of purchase price and appraisal.
- **PTI** = (mortgage payment + other loan payments) / net monthly income.
- Payments support Spitzer (annuity) and equal-principal amortization, per track of the mix (קל"צ, ק"צ, prime, variable).
- `rate_shock` stress-tests PTI by raising the rate on prime/variable tracks.

```bash
python3 example.py
python3 worked_examples.py   # step-by-step calculations, see WORKED_EXAMPLES.md
python3 -m unittest discover -s tests -t .
```

The limits are in `israeli_mortgage/regulation.py`; banks often use stricter internal caps (pass `max_pti=`). This is not financial advice.
