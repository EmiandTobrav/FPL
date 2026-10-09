# Exact zero subset: two factual tackle counters

Two missing fields for Joel Ward (2020/21 fixture 31, code 55494) are closed:
won tackles 0 and signed legacy net tackles 0. His already approved total
tackles is explicitly 0. Missing totals never become zero; positive totals
without known wins abstain. Protected conflicts remain open.

[Opta event definitions](https://www.statsperform.com/opta-event-definitions/)
classify won and lost outcomes as tackles. The nonnegative won count is a
subset of the total; signed legacy net remains `2*won-total`, including
negative values. Historical BPS clipping remains unqualified.

The frozen regression checks all 61,148 approved counter pairs in 2,280
fixtures, including 27,873 positive wins and 24,097 explicit zero totals.
There are zero subset, zero-bound or known-zero-net discrepancies. These
checks share existing upstream evidence and are not independent holdout
validation or collective dataset QA.

Open requirements fall **11,236 → 11,234**. Input-complete player-matches
increase **66,476 → 66,477**; input-complete whole fixtures remain **824**.
All 775,246 non-target rows and original source columns are unchanged.
Three boundary/preservation tests pass; 15 generated files reproduce
byte-identically in a fresh offline tree. No new points, bonus or features.

From the repository root:

```sh
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/tackle_subset_bounds/test_bounds.py
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/tackle_subset_bounds/reproduce.py
```

Quick reuse checks also rejected three routes with no candidates: no primary
team positive residual has exactly one unknown player; none of the 38 open
big-chance-save rows has native saves 0; and no expected-statistic field is
present in the 685 cached complete primary player responses. These scans
close zero additional requirements and justify moving to another data route.
