# Assist reconciliation and current requirements ledger

7 October 2026. Continues draft PR #1 from `482b86d`.
**Latest consolidated requirements: [bulk_reconciliation/](../bulk_reconciliation/README.md).** This directory preserves the assist reconciliation snapshot. The
historical FPL authority policy in `../fpl_authority/` remains in force.

The four requested work stages are implemented: evidence-based target rules,
a separate frozen control evaluation, a run over all available historical goals,
and player-match aggregation with a new deduplicated ledger. This does **not**
mean every assist is resolved or historical points/BPS/bonus are ready.

## Results

- 7,543 archived goals processed, with candidate, reason and evidence identifiers.
- 9,681 previously open assist player-matches resolved: 820 positive totals and
  8,861 proven zeros. These zeros follow decided goal contributions or the
  impossibility of assisting one's own goal, never an omitted source counter.
- 39,035 assist player-matches remain open: 583 lack a complete goal inventory;
  38,452 need further causal evidence or qualification of an automatic route.
- Four newly complete totals differ from historical FPL: Marmoush (2024/25, 336),
  Pedro Porro (201), Alex Scott (312), Pickford (223), each 0 → 1. These are the
  four previously documented official target-rule examples, now checked across
  every goal in their team's match. No other complete historical total changes.
- All 11,492 official 2025/26 FPL assist totals are retained because the target
  assist rules are unchanged. All 17,072 pre-existing team-scoreless zeros remain.

Across all fields, **258,302 open cells affect 66,087 unique player-matches**,
against 267,983 / 66,109 previously. Resolving assists often leaves other missing
fields in the same match, so 9,681 closed cells remove only 22 player-matches
from the overall open set. Counts across fields must not be added as unique rows.

| Open field | Cells / distinct player-matches within that field |
|---|---:|
| Goal-line clearances | 65,301 |
| Target assists | 39,035 |
| Legacy signed net tackles | 38,090 |
| Won tackles | 38,087 |
| Fouls won | 30,049 |
| Shots on target | 28,590 |
| Times tackled | 9,504 |
| Clearances + blocks + interceptions | 4,818 |
| Penalty goals | 4,435 |
| Saves outside box | 342 |
| Big-chance saves | 38 |
| Total tackles | 11 |
| Recoveries | 1 |
| Known FPL BPS extraction exception | 1 |

The status split is 219,615 missing-data cells, 234 external conflicts,
38,452 pending target-assist adjudications and one FPL extraction exception.
`rule_recalculation` here means unresolved adjudication, including missing causal
facts; it does not assert that the published rule itself is unknown.
`assist_reason` distinguishes incomplete goal inventories from unresolved
per-goal facts. `goal_decisions.csv.gz` records the finer evidence/rule gate.

A separate 339,783 available external cells in 77,125 player-matches still need
individual primary checks; the **union** of that queue and open requirements is
77,214 player-matches. The 1,240 primary-checked external cells are preserved.
Source agreement with a shared Opta origin is not independent provider validation.

## Rules and evidence

`rules.py` is a three-valued fact evaluator: award, deny, or insufficient evidence.
It covers direct/deflected passes, inadvertent touches, shot rebounds, own goals,
fouls, handballs, self-assists, own rebounds, possession loss, and corner/throw
exclusions. Touch counts exclude the final own-goal scorer contact; a defensive
pass is a separate disqualifier. Shot facts require direct shot-to-goal causality
(including the final own-goal contact), and explicitly distinguish deflections
before and contacts after a rebound. Missing facts stay unknown.

The rules are based on the [official 2026/27 scoring rules](https://www.premierleague.com/en/news/4661029),
[official assist-change examples](https://www.premierleague.com/en/news/4362187/whats-new-in-202526-fantasy-changes-to-assists-rules),
and [additional official decisions](https://www.premierleague.com/en/news/4655693).
The pinned parser dictionary is an implementation reference, not certified
provider documentation; see `../assist_schema/schema.json` and the
[Opta event definitions](https://www.statsperform.com/opta-event-definitions/).

`engine.py` automatically certifies only narrow explicit patterns:

- A unique successful intentional goal-creating pass, paired with an explicitly
  assisted intentional goal, with no intervening incompatible physical action.
- An explicit goal-linked penalty/free-kick winner and matching scoring team.
- An own-rebound negative candidate, which remains gated because the separate
  control set did not validate that automatic route.

No empty fantasy-assist field means “no assist.” No arbitrary deflected pass is
approved from qualifier 154. Qualifier 55 is a local source event reference;
it is **not** joined to the archive's global event ID. Same-second physical
ordering ambiguities abstain. Episodes are same-period, 60 seconds for open
play and 600 for penalties/direct free kicks; long/ambiguous chains abstain.
A matching final score is only a goal-inventory check, not proof that every
physical touch has been captured.

The fact evaluator covers more routes than the automatic source extractor can
certify. The remaining work is chiefly obtaining reliable causal facts and
validating additional source patterns, not treating all archived ordinary or
fantasy assists as target-rule assists. Older seasons have substantially fewer
qualifying explicit markers; the certificate coverage is not season-invariant.

## Separate validation

`validation_plan.csv` selects the first 40 one-goal scoring-team matches from
1 January 2026 in 2025/26, ordered by date/fixture/team and excluding previous
assist development and primary/delta controls. There are 30 distinct fixtures.
Selection uses no assist outcomes. Code, inputs, protocol and all predictions
were frozen before `validate.py` read the official FPL assist labels.
For a one-goal team, the compatible FPL match totals identify its recipient or
absence of one unambiguously.

**18 correct, 0 incorrect, 22 unresolved**: 15 direct-pass awards and 3 foul-winner
awards. Only these two automatic routes pass the predeclared gate. Unknowns are
not counted correct. An absent/failed route is withheld. This is a new temporal
assist evaluation split using stored official FPL snapshots, not fresh observations,
not a wholly independent data provider, and not proof of performance on every
season or rare route. The 10 old official narrative cases remain development
examples; their published decisions are separately labelled adjudications and
were never fed into the automatic predictor or holdout.

The fact-only replay of those ten narratives resolves nine; Pickford's old
fact object omits the new shot-deflection-context predicate and therefore
abstains. His **explicit published award**, rather than a silently completed
fact object, supports the separate official adjudication.

## Goal and match outputs

The final goal ledger contains 2,478 awards, 27 explicit no-assist decisions and
5,038 unresolved goals. It includes 2025/26 goal diagnostics, whose unresolved
individual goal attribution does not reopen authoritative FPL match totals.
Before 2025/26 there are 1,894 awarded goals and 4,604 unresolved goals; no
whole-goal negative automatic route has yet qualified. `remaining_goals.csv.gz`
contains only these 4,604 goals needing historical target adjudication:

- 3,814 lack a complete qualifying causal certificate;
- 546 lack set-piece causal evidence;
- 228 need own-goal action/contact context;
- 16 own-rebound candidates lack separate route validation.

This goal count is a different unit from missing player-match fields and must
not be added to the requirement counts. Missing goals cannot appear as rows in
the event ledger: `fixture_coverage.csv` separately retains 21 absent archive
fixtures and the 3 additional eventless fixtures with nine goals.
There are **zero observed scorer conflicts** after applying the eight previously
approved goal/own-goal revisions to the derived audit. Missing events remain
missing in that audit, not invented zero observations or source conflicts.

`player_match_totals.csv.gz` contains each participant's historical value,
nullable target total, known lower bound, unresolved goal IDs and reason.
A goal resolved to someone else contributes zero; an unresolved goal also
contributes zero to its own scorer, or to a specifically denied official
candidate. Other candidates remain unknown. A player total is final only if
**every goal contribution for that player** is known and source goal counts and
scorer identities pass. A partial award remains a lower bound, not a final total.
Own-goal credit goes to the opposing team. No timing or minute imputation is used.

`requirements.csv.gz` overlays only previously open assists on the prior ledger.
All other original cells and all previously closed assist cells are asserted
unchanged. `remaining_fields`, `remaining_player_matches`, `field_summary`,
`match_summary` and `player_summary` provide the actionable views. Keys are
season + fixture + FPL code (+ field); global unions use those keys once.
Raw FPL, 5,343 approved keeper values, 38 unresolved keeper observations,
locked points/BPS/bonus, models and benchmark are unchanged.

## Reproduction

Python with pandas and pyarrow; from this directory:

```sh
python prepare.py --archive /path/to/events_EPL.parquet
python predict.py
python validate.py
python build.py
python -m unittest discover -s . -p 'test_*.py'
```

`prepare.py` requires the pinned event archive SHA-256 in `inputs/source.json`.
Its compact projected inputs are committed, so the latter three stages need no
external archive or network. `predict.py` refuses changed frozen inputs/code
or predictions; future rule development needs a new version and control plan,
not silent retuning on these 40 outcomes. `manifest.json` records build inputs.
The source archive attempt history remains in `../bps_recovery/`,
`../assist_schema/`, `../acquisition_followup/` and `../keeper_recovery/`.
No new paid data was acquired; cost 0 NOK.

## Verification

38 new and 107 existing focused tests pass (145 total). All 34 generated data,
protocol and manifest files are byte-identical after rerunning preparation,
frozen prediction, validation and aggregation. See `test_results.json` and
`replay_verification.json`. Full repository tests and GitHub CI were not verified.
