# Paired tackle-event recovery — 8 October 2026

This increment resolves5,943 times_tackled field requirements:62.53% of the
9,504-field group and15.81% of the previous total queue. It counts actual,
uniquely paired defending events and applies explicit inventory/conservation
gates. It does NOT substitute ball-loss or dribbling statistics for times_tackled.

| Metric | Previous | Current |
| --- | ---: | ---: |
| Open fields | 37,601 | 31,658 |
| Open times_tackled fields | 9,504 | 3,561 |
| Unique affected player-matches | 30,358 | 26,566 |
| Input-complete player-matches | 46,922 | 50,714 |
| Input-complete whole fixtures | 468 | 468 |

The population remains77,280 player-matches in2,660 fixtures.2,475 newly
available values are zero and3,468 are positive.3,792 player-matches become
input-complete. No additional fixture becomes fully input-complete because
other open requirements remain. Input completeness is not harmonized scoring.

## Source acquisition and identity

The mutable public Opta release was checked before reuse. Both downloaded
archives matched the previously pinned hashes exactly:
* events_EPL.parquet,310,557,261 bytes:
  a69184e1c0d35ed39e1146b748f0ff3b649750bb1d52624286406e0cacd4b6f2
* opta_player_stats.parquet,316,399,136 bytes:
  2765b1771493c917ce7c544b01cf3a151e159a818abb889c7fcbd746353eaead
Source:https://github.com/peteowen1/pannadata/releases/tag/opta-latest

Compact, hash-frozen projections contain235,217 relevant events and103,786
player roster rows across the seven training seasons. The full raw archives
are not required for replay and are not duplicated into the deliverable.
Eight small primary season-statistic responses cover total_contest for seven
seasons and total_tackle for2025/26. Their exact URLs, bytes and hashes are
retained under inputs/primary. Team identities use explicit name aliases.
The initial primary gk_smother rank probe returned no entries and was NOT
interpreted as a zero. It is retained as an unsuccessful source attempt.

## Method and why missing is not zero

A type7 defending tackle must pair uniquely in both directions with the
opposite participant's corresponding duel event in the same match/period.
Native coordinates must mirror exactly at0.1 resolution; timestamps may differ
by at most3 seconds. Both rows require explicit opposite-reference233, unique
local-reference assignments, and unique source-roster identities. The raw
archive lacks local event IDs, so233 is NOT joined directly to global event_id.
Pairing is inferred from these joint constraints and remains a source-quality
limitation, not a provider-certified ID join.

Every tackle by the opposing team must be paired, and the number must equal
the explicit primary team-match total_tackle. A missing total, positive unmatched
residual, identity gap or ambiguous pairing blocks the entire recipient team.
Both won and lost tackles count; no historical net-tackle clipping is assumed.

Additional player-level completeness is required. The full take-on event
inventory must match that player's explicit totalContest. Missing counters
become zero only when the sum of known nonnegative player counters exactly
exhausts an explicit primary team-season total. A positive residual or missing
season total stays unknown. All failed take-on/dispossessed events must have
an actual paired tackle or separately checked keeper-smother event. An overrun,
missing counterpart or incomplete player inventory causes abstention.
These activity counters are coverage gates; the output value is the number of
actual, matched defending events, not a formula based on ball losses/dribbles.

Primary2025/26 team tackle inventories for the new control period are derived
with the same exact season-total conservation because the earlier primary
match extracts stop at2024/25. Earlier seasons keep the original direct primary
match totals. The audit distinguishes these source lineages.

Provider definitions:https://www.statsperform.com/opta-event-definitions/
Opta distinguishes tackle duels, their opposite actions, and keeper smothers.
The pinned numeric parser dictionary is an implementation reference, not a
provider-certified schema; it is included in assist_group_audit/parser_metadata.py.

## Failed control, revision and new temporal control

Version1 reconciled ground tackles alone. Development on the first20 fixtures
of2023/24 gave604 agreements. Its frozen2024/25 test then found3 disagreements
among11,221 comparisons:Kerkez,Durán andMinteh had keeper-smother situations.
The zero-error gate failed and NO values from version1 were applied. Its
protocol, predictions' hashes, comparisons and failure result are preserved.
Do not cite2024/25 as an independent holdout for the revised method.

Version2 adds the player inventory gates and separately checks possible smother
contributions against explicit gkSmother counters. It was frozen before its
2025/26 comparison. Results:
*2,997 ordinary player comparisons,0 disagreements;
*1,365 explicit zero and1,632 positive controls;
*0 qualifying smother-inclusive controls, so that subtype remains withheld;
*41,383 total known-counter comparisons across seasons after the test,0
 disagreements. This figure includes the2,997 held-out comparisons; do not add
 them or call the full set independent validation.

Only ordinary, zero-smother-contribution predictions passing all gates are
applied. Primary event, season and player sources share Opta provenance;
source quality and historical transfer still need collective qualification.
No points, BPS deltas, bonus ranking or models have been recomputed.

## Preservation and reproduction

Only previously missing_data times_tackled cells change. The existing explicit
conflict remains open. Every other ledger row and every protected source column
is asserted unchanged. Raw FPL, explicit zeros, approved keeper values, official
goal corrections, all assist work, and locked labels/models/benchmark remain
unchanged. The assist goals/exclusions remain in the preceding assist bundle.

Current ledger:results/requirements.csv.gz
Current queue:results/remaining_fields.csv.gz
New overlay:results/times_tackled_overlay.csv.gz
Source gates:team_gates.csv and season_conservation.csv
Player evidence:paired_events.csv.gz and player_predictions.csv.gz

Offline replay requires Python3.12 and pandas2.2.3 only:
    python3 tackle_event_recovery_v2/reproduce.py

The package contains all current replay dependencies and the preceding ledger.
It replays this increment, not every earlier project stage or the failed v1
experiment. Twenty focused tests check pair ambiguity, source references,
identity/time/period/coordinate guards, won/lost tackles and smother separation.
Full-repository tests and GitHub CI are not claimed.

Optional raw re-extraction uses prepare.py and DuckDB1.4.3, plus the two verified
raw archives at its documented relative paths. DuckDB was installed into a
workspace-local directory for extraction; it is not required for normal replay.
Do not reuse a machine-specific Python path or assume new release bytes match.

The source branch was checked again and remains
codex/keeper-primary-match-reconciliation at
5a68098541997eb0ff890998624d0e2f6aac85cb. This supplement is unpublished;
GitHub,main and other people's messages were not changed.

The large generated paired_events.csv.gz intermediate is omitted from this ZIP;
reproduce.py regenerates it from the included duel projection and verifies its
frozen hash before validation and aggregation. All nine final result files are
included and were compared in the separate replay.
