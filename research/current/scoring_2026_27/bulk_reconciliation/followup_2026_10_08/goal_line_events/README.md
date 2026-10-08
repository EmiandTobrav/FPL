# Direct goal-line block inventory — 9 October 2026

This data-gap batch closes **2,114 missing goal-line-clearance requirements**.
It uses actual defensive block events and complete counter inventories. It
does not create new BPS, bonus, points, training features or model results.

| Input metric | Before | After |
|---|---:|---:|
| Open field requirements | 14,893 | 12,779 |
| Goal-line-clearance gaps | 2,992 | 878 |
| Affected player-matches | 13,731 | 12,075 |
| Input-complete player-matches | 63,549 | 65,205 |
| Input-complete whole fixtures | 766 | 768 |

All 2,114 newly proved values are zero: 492 in 2019/20, 766 in 2020/21,
451 in 2021/22, 35 in 2022/23 and 370 in 2024/25. No 2023/24 requirement was
open. The batch makes 1,656 player-matches and two whole fixtures input-complete.
Input completeness is separate from scoring qualification and training readiness.

## Source and proof

The already pinned [public event archive](https://github.com/peteowen1/pannadata/releases/tag/opta-latest)
provides 34,692 type10 defensive-save/block records across the seven historical
seasons. The full player archive supplies 103,786 source-roster rows. Raw archive
hashes, compact projections and all replay dependencies are recorded in
`inputs/manifest.json`; no new network download was necessary.

The [pinned parser dictionary](https://github.com/andrewRowlinson/optasoccer/blob/825cadb56c9c976a8c34c9d5da26d6e37c6ff239/optasoccer/metadata.py)
defines marker94 as defensive block and marker14 as last-line defense. The actual
last-line events here always have both markers. This is a published parser,
not a provider-certified schema. Normal type12 clearances do not identify these
actions; development checked that hypothesis and rejected it.

An eligible player has one of two complete inventory proofs:

1. Its full defensive block-event count equals its explicit `outfielderBlock`
   source counter. This is a direct player-counter proof.
2. The full team's block-event count equals its explicit primary match
   `outfielder_block` total. Every actor has one unique source-roster identity,
   every qualifier inventory is valid, and every explicit player block counter
   agrees. This exact team proof covers zero-count players too.

The marked last-line subset is then counted directly. No missing goal-line
season total, empty API response or event omission alone is used as a zero.
Positive unallocated block residuals, missing totals, unknown actors, source/FPL
minute disagreements and malformed qualifiers abstain. Primary teams are mapped
by explicit fixture home/away roles; date, season and player identities are checked.

## Source compatibility and limits

Protocol and predictions were frozen before closed-ledger outcome comparison.
Development had already seen the positive source-count comparison and is
declared explicitly. Eligible checks give:

- 44,956 closed historical ledger controls, including 44,545 zeros; zero errors.
- 492 explicit positive archive controls, including 81 from 2025/26; zero errors.
- Every earlier season has at least 20 explicit positive controls.
- 411 explicit-source controls also occur among the closed-ledger controls;
  these figures must not be added as independent observations.

All controls share Opta lineage. These are field compatibility and preservation
checks, not untouched holdout, independent-provider verification, native FPL
goal-line observations or complete dataset/scoring qualification. New cells
retain external-quality-review flags for the later collective QA phase.

The missing-event fixture 2024/25-123 has a known positive Colwill source value
but an incomplete block inventory. It is excluded by the inventory gate rather
than counted as a successful zero control.

## Remaining work

878 goal-line requirements remain: 590 have source/FPL minute disagreements,
249 lack a qualified block inventory, and39 lack the source identity/archive
mapping. Of the 590 minute differences,537 are source +1 and43 are source −1;
these remain open and are not silently normalized.

The next inventory attempt should seek explicit primary season **block** totals
or a new compatible complete event source. Exact season exhaustion could prove
omitted match block totals; it must retain complete fixture/actor checks and
must not reinterpret missing goal-line totals as zero. Do not replay failed
goal-line season-total queries.

## Preservation and replay

773,134 other ledger rows are unchanged. Source/FPL columns are preserved over
all 775,248 rows. Only previously `missing_data` goal-line cells change; protected
conflicts, old labels and approved reconstructions remain untouched.

Five focused tests pass. A clean offline tree reproduces ten result files and
the frozen prediction record byte-identically. The previously recorded145-file
training-dataset replay is unchanged; it does not include this new input batch.
No full-repository CI run is claimed.

From this directory, with Python3.12 and pandas2.2.3:

```sh
python test_goal_line.py
python reproduce.py
```

Optional raw re-extraction additionally needs pyarrow and the two pinned archives:

```sh
python prepare.py /path/to/events_EPL.parquet /path/to/opta_player_stats.parquet
```

The frozen parent ledger is `inputs/parent_CURRENT.json`; the root CURRENT
pointer can advance without changing this replay.
