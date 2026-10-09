# Withheld: opponent big-chance zero bounds

Four exact public ranked team-season totals (2019/20, 2020/21, 2022/23,
2024/25) were collected. Every one of 80 team-seasons has a complete
38-match official inventory and its known match sum exhausts the explicit
season total. The frozen projection proposes 16 missing keeper counters.

**The rule fails and zero candidates are applied.** Among 983 closed keeper
controls in 846 fixtures, one contradicts the proposed zero: Alex McCarthy,
2019/20 fixture 269, code 58376, has a previously approved big-chance save 1.
Aston Villa's official match counter is omitted. Exact season exhaustion does
not overcome this counterexample. The prior value, gate and all 16 open
requirements are preserved. Do not reuse the route without factual evidence
explaining the source/definition discrepancy; do not omit the failed control.

This was a factual data-source trial, not a scoring rule. Predictions were
frozen before comparison. No xG thresholds, proxy data or new point labels.
The mathematical candidate rationale uses the existing keeper audit's
non-goal-big-chance bound, but this source/version fails to implement it
consistently. [Opta definitions](https://www.statsperform.com/opta-event-definitions/)
are context, not evidence overriding the failed source control.

The first generic application attempt received an empty overlay and failed
its preservation assertion because assigning an empty object series changed
an in-memory dtype. No result ledger or authoritative change was written.
`build_attempt1.py` and `application_attempt1_freeze.json` retain that failed
attempt; the current builder immediately refuses unqualified data.

Reproduce from the repository root, offline:

```sh
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/big_chance_zero_bounds/reproduce.py
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/big_chance_zero_bounds/test_withholding.py
```

The [guarded source version](../big_chance_zero_bounds_guarded/README.md)
uses the previously approved event exception to withhold the whole incompatible
source team-season. This original version and its failed controls are unchanged.
