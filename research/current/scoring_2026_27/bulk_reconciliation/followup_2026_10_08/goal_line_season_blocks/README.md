# Exact primary season-block exhaustion — 9 October 2026

Six small public primary responses close **303 more goal-line-clearance gaps**.
The remaining queue falls from 12,779 to **12,476**; 241 more player-matches become
input-complete. Whole-fixture readiness remains 768. No BPS, bonus, point labels,
features or models are changed.

| Input metric | Before | After |
|---|---:|---:|
| Open field requirements | 12,779 | 12,476 |
| Goal-line-clearance gaps | 878 | 575 |
| Affected player-matches | 12,075 | 11,834 |
| Input-complete player-matches | 65,205 | 65,446 |
| Input-complete whole fixtures | 768 | 768 |

All 303 new values are zero: 41 in 2019/20, 118 in 2020/21, 69 in 2021/22 and 75 in
2024/25. Earlier gap batches and their frozen inputs/results remain unchanged.

## New primary data and exact proof

`plan.json` records the six explicit `outfielder_block` ranking URLs, one for
each season 2019/20–2024/25. Exact response bytes and SHA256 are stored in
`inputs/`. Each response has one complete page and exactly the 20 stable primary
team IDs appearing in that season's verified 380-fixture catalog.

The batch reuses every primary match total in the six completed seasons. Each
of 120 team–season groups contains 38 distinct fixtures. For every group, the sum
of explicitly known nonnegative match block counts equals the explicit season
total exactly. Therefore the 327 omitted match block totals are proven zero.
Positive residuals, invalid counters, incomplete scopes and missing totals would
withhold that group; no empty response is interpreted as zero.

A whole-team block total of zero bounds each player's goal-line clearances to
zero, including players whose individual counters are omitted. This is a
team-scope subset proof. It does not require reconstruction of individual
playing-time bookkeeping or individual archive identity. Native player membership
uses original FPL `was_home`, historical team, fixture date and both scores,
all checked against the verified primary fixture scope.

54 newly closed cases have source/FPL minute disagreement. Their FPL minutes
are preserved; no minute is adjusted or assumed equivalent. The zero applies
to every native team member because the entire team's nonnegative block total
is zero. The previous event-inventory batch and its minute/control gates stay
frozen unchanged. No protected conflict cell is overwritten.

## Compatibility controls and limits

The protocol and source plan were fixed before collection. Source hashes and
team predictions were frozen before comparing goal-line outcomes. 4,377 closed
historical controls agree, with zero discrepancies in every season. No explicit
positive source goal-line counter occurs in a certified zero-block team.

These are exact primary conservation and reused source-regression checks.
They share Opta lineage; they are not independent holdout, native FPL goal-line
observations or full scoring/training qualification. Derived cells retain
external-quality-review flags for the later collective QA phase.

All 774,945 other ledger rows remain identical. Source/FPL and previous-value
columns are preserved over the full 775,248-row ledger. Existing scoring versions,
approved reconstructions and locked model outputs are untouched.

## Remaining gaps and next action

575 goal-line requirements remain: 536 with source/FPL minute disagreement and
39 with missing archive/identity mapping. The previous 249 unqualified-block-
inventory cases are now closed. Archive/identity gaps in positive-block teams
still need actual compatible event evidence.

For the 536 player-minute cases, investigate field-specific identity and complete
event evidence before deciding whether the counter can be qualified independently
of minute arithmetic. Preserve authoritative FPL minutes and the earlier frozen
results. Do not repeat the old general BPS/minute reconstruction attempts.

## Offline reproduction

Five focused tests pass. A fresh offline temporary tree reproduces eleven
result files and the frozen prediction record byte-identically. Only this
datagap batch is replayed; no full-repository CI or new full-training replay is
claimed. Python3.12 and pandas2.2.3 are sufficient:

```sh
python test_season_blocks.py
python reproduce.py
```

`inputs/parent_CURRENT.json` fixes the 12,779-gap parent. Later changes to the
root CURRENT pointer do not alter this replay.
