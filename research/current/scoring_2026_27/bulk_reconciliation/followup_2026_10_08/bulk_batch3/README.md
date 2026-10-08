# Batch 3: positive-event candidate bounds

**8,058 requirements closed (33.18% of the previous 24,285).** Remaining:
**16,227 fields in14,990 unique player-matches**. Complete inputs now cover
**62,290 player-matches (+7,506)** and **490 whole fixtures (+1)**, of the
unchanged77,280 /2,660 population. These are input counts, not qualified scoring.

All newly available fields are target-rule assists. The rules add candidate
exclusions from positively recorded actions, without assigning new goal assists:

| Stage | Additional complete fields | Cumulative against batch2 |
|---|---:|---:|
| Successful defensive pass boundary | 1,457 | 1,457 |
| Successful non-scorer attacking pass | 5,440 | 6,897 |
| Unsuccessful non-scorer attacking pass | 1,010 | 7,907 |
| Explicit non-scorer ball touch | 151 | 8,058 |

The final cumulative overlay contains7,691 zeros and367 positive totals. Positive
totals combine previously qualified goal awards with newly proven zero contributions
from other goals. No value comes from treating a missing assist marker as zero.
All previously complete values and all protected/raw columns remain unchanged.

Each rule has separately frozen predictions and a control plan before outcome
comparison, the same minimum20 applicable unresolved controls and20 one-goal
controls, and zero-error / zero-conflict gates. Counts of one-goal controls are
74 /185 /118 /40 respectively; applicable unresolved controls132 /287 /221 /78.
The controls overlap and **must not be added as independent observations**.

The intersection of **all qualified older and newer bounds** is also checked.
Known goal awards are forced and subtracted from observed FPL totals before
remaining goals are matched. All566 team vectors in3532025/26 fixtures are feasible,
with no protected-award conflicts. This remains temporal regression on previously
seen outcomes with a shared Opta source, not an independent provider test or holdout.
External quality flags are retained. Goal availability is not final goal/scoring
qualification; many remaining goals still have one possible but unqualified actor.
That is why player completeness rose sharply while whole-fixture completeness rose
by only one. The next priority is resolving those actual remaining goal contributions.

The documented new official SDP source pilot did not expose missing line-clearance
or player times-tackled values. No numerical fields or zeros were applied from it.
See `sdp_schema_pilot/README.md`; avoid repeating it without new relevant evidence.

`build.py` verifies the joint gate, applies the final disjoint overlay to the batch2
ledger and checks all protected rows/columns. `results/requirements.csv.xz` is the
new cumulative ledger. Historical outputs retain `published:false` as execution
metadata; CURRENT.json records the latest published snapshot.

Python3.12 and pandas suffice. From any checkout of this snapshot, run:

```sh
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/bulk_batch3/reproduce.py
```

No external archives, old machine directories, network requests or prior bootstrap
are required for this batch's replay. It copies committed inputs to a separate
working directory, removes generated outputs, regenerates every new stage and the
ledger, and compares exact hashes. All **63 regenerated output files** were identical. Fifteen new test methods cover the four routes,
ambiguous timing, missing identity, scorer exclusion and event interruption guards.
Full repository tests and GitHub CI are not claimed. Locked scores/BPS/bonus,
models and benchmark are unchanged; no training or scoring recalculation occurs.
