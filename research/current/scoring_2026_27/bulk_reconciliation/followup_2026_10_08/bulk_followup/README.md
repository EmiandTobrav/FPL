# FPL bulk follow-up — 8 October 2026

Unpublished supplement to EmiandTobrav/FPL, branch
`codex/keeper-primary-match-reconciliation`, published commit
`5a68098541997eb0ff890998624d0e2f6aac85cb`. No GitHub writes or main merge.
The local cumulative ledger, not the older published queue, is the baseline.

## Current result

- 2,724 new available field requirements (8.6045% of the incoming31,658).
- 1,868 times_tackled,52.46% of that remaining3,561-field group.
- 856 assists_2026_27:99 from154 new goal awards and757 from90 multi-actor
  bounds /1,084 additional candidate exclusions. These are distinct increments.
- 28,934 open requirements in24,716 unique player-matches.
- 52,564 input-complete player-matches (+1,850),479 whole fixtures (+11).
- 2,709 distinct player-matches gained at least one field; do not add field
  counts to obtain unique people/matches.
- Population remains77,280 active player-matches and2,660 fixtures.

`results/requirements.csv.gz` is the full current ledger.
`results/remaining_fields.csv.gz` is the current queue.
`results/new_fields.csv.gz` is this increment only.
`results/field_summary.csv` and readiness files retain both availability and
external quality requirements. Availability is NOT qualified points/BPS/bonus.

## Evidence and scope

### Match inventory recovery

Previous team-season conservation was blocked by missing archive fixtures.
297 explicit primary match responses (267 target fixtures and30 later-season
regression fixtures) permit exact per-match conservation of total_contest.
The pilot verified the metric and match/team identity before the batch.
Every raw response is included with URL and SHA256; missing totals remain
unknown. Individual missing counters become zero only when known nonnegative
counts exhaust the explicit compatible team total over the source roster.

This inferred zero is only the take-on inventory coverage gate. Output
still counts actual uniquely paired defender tackle events using the frozen
v2 method. Every failed take-on/dispossession must be paired, the opponent's
whole tackle inventory must reconcile, and smother contributions remain
excluded. No ball-loss/dribble proxy replaces times_tackled.

395 explicit later-season counter comparisons, zero disagreements. These
are regression controls already exposed in the previous v2 audit, NOT a new
independent holdout. The event rule itself retains its prior frozen2025/26
qualification. The single pre-existing times_tackled conflict is untouched.

### Null-valued positive pass marker

The source210 marker must actually be present; absence is not evidence.
The unchanged frozen clean-pass rule was previously withheld for14/20 controls.
A new outcome-blind selection includes ALL qualifying2020/21 multi-goal teams
outside old control fixtures whose whole goal inventory has approved compatible
assists or the frozen null-marker proposal. Five new vectors contain6 new
occurrences; all67 player totals agree with FPL. With the prior14 single-goal
checks, this is20 goal occurrences across19 team vectors. Two new proposed
awards share one vector, so match totals do NOT independently identify each
of those goals. This limitation is explicit, and no threshold was reduced.
Old control plans/results and predictor are unchanged.154 unknown goals gain
source-supported awards;99 previously missing complete player totals follow.

### Multi-actor candidate bounds

An explicit goal-linked certificate plus subsequent recorded attacking actors
can give a conservative candidate SET even when a single recipient cannot be
selected. All intervening attacking actors expand the set. Multiple source
certificates are unioned; missing identities block. No goal award comes from
this method. Set pieces and unvalidated routes remain withheld. A goal scorer
cannot assist their own normal goal; own-goal candidates are handled separately.

The predictor and plan were frozen before regression comparison. All566
2025/26 scoring-team vectors in353 fixtures remain feasible;7 applicable
single-goal checks agree, with no protected-award conflicts. There are26 new
unresolved controls in the3 qualified kinds: pass2108, lost pass12, own goal6.
POST has only1 and is withheld; other kinds without enough controls withheld.
These outcomes were used in prior experiments: this is temporal/shared-source
regression, NOT independent provider or blind holdout validation.

## Preservation

Only previously open, empty field cells are updated. All nonupdated rows and
all protected columns are asserted equal to the incoming ledger. Existing
complete assist totals are checked against the expanded goal inventory.
Raw FPL, explicit zeros, keeper values, approved official goal revisions,
frozen controls, points, BPS, bonus, models and benchmark remain unchanged.
All856 new assist totals happen to agree with historical FPL, but are derived
from explicit goal evidence/bounds, not copied from old totals.

## Replay

Python3.12 and pandas2.2.3. No downloads, DuckDB, training, raw archives or
machine-specific paths are required for the included replay:

    python3 bulk_followup/reproduce.py

The package contains inputs needed for THIS increment and the previous full
ledger, including compressed event projections and frozen paired events.
It does not claim to rebuild every earlier project stage. Source manifests
pin included inputs.26 focused tests cover exact conservation and candidate
set guards; full repo tests/GitHub CI are not claimed.

The large optional raw archives from the preceding turn remain pinned at:
- events_EPL.parquet: a69184e1c0d35ed39e1146b748f0ff3b649750bb1d52624286406e0cacd4b6f2
- opta_player_stats.parquet:2765b1771493c917ce7c544b01cf3a151e159a818abb889c7fcbd746353eaead
No new raw download was needed. Do not assume future mutable release bytes.

The remaining largest group is20,288 assist requirements. Source-not-assisted
markers alone still cannot establish target-rule zeros. Future work should
qualify causal/receiving facts for whole groups, not manually relabel all
quality flags or repeat failed times_tackled endpoints.

### Remaining tackle groups

`results/tackle_remaining_reasons.csv` partitions all1,693 remaining tackle
requirements without double counting:908 unpaired failed take-on/dispossession
cases,559 missing source/identity,221 incomplete opponent tackle inventories,
2 smother cases without subtype qualification,2 other inventory gaps,1 protected
explicit conflict. These are diagnostic blocking reasons, not inferred values.
