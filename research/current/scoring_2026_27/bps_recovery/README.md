# Historical BPS source audit and assist recovery inputs

7 October 2026. Continued from PR #1 at `dfa2ff30b36e33c4b16f5402d25af9337266af3f`.
This is a supplemental source audit, **not a new points/BPS/bonus dataset**.
The locked labels, keeper adjudications, models and benchmark are unchanged.

## Result

- 76,687 / 77,280 historical active player observations are linked to the frozen
  Opta-based archive (99.23%). The 593 unmatched observations are in the same
  21 missing archive fixtures already identified by keeper recovery. There are
  no remaining name-only matching failures.
- 36 BPS-related counters and 14 assist-related counters are retained (with
  overlap between the lists). Missing source counters remain missing.
- In 327 historical primary controls, all 3,244 pairs of explicitly populated
  counters agree. One additional comparison has a missing archive counter:
  Bernd Leno, 2024/25 fixture 1, primary `big_chance_saves=3`. This demonstrates
  why a missing counter must not be interpreted as an observed zero.
- In 622 current controls, 6,229 / 6,273 explicit counter pairs agree; another
  five pairs differ in omission. These sources share Opta ancestry: this is
  not an independent-provider validation.
- Substituting archive counters in the existing formula gives 615 / 622 exact
  BPS and 622 / 622 exact bonus. Using the primary counters gives 620 / 622
  exact BPS. The archive changes computed BPS for seven observations, six in
  fixture 8 and Moore in fixture 2. GW1/GW2 were already used previously and
  are **not a new holdout**. The diagnostic retains official FPL assists and
  uses sparse-zero arithmetic solely to measure source differences.
- 245 source-vs-FotMob minute differences are recorded: 244 of one minute and
  Ben Osborn in 2023/24 fixture 299 at 86 vs 90. No minutes were overwritten.

`field_coverage.csv` separates explicit positive values, explicit zeros and
omissions for every season/field. For example, historical rows contain 32,501
positive won-tackle counts, 11,681 positive non-corner cross counts and 1,856
positive error-leading-to-shot counts. These numbers are **not counts of all
rows with known complete statistics**. Most counters contain no explicit zeros.

## Identity and provenance

Fixtures require the same season, date, normalized home/away clubs and both
final scores. Player matching uses exact normalized names, unique strongest
surname/web-name matches, and unanimous cross-match ID anchors. The nine
reviewed aliases in `identity_aliases.csv` record expanded source names and
punctuation/transliteration differences. An alias is accepted only when its
source player ID actually appears in that verified fixture. Duplicate target
keys and duplicate source identities within a match are rejected. No fuzzy
string-distance match or minutes-only identity matching is used.

The committed `inputs/counts-*.csv.gz` extracts contain the original nullable
counters, source player/match IDs, fixture keys, mapping status and FPL fixture
counts. The 949 frozen primary controls come from the existing two-round
collection and the 119-row acquisition follow-up; no additional online primary
requests were made for this audit. Fresh official FPL fixture/bootstrap
snapshots were needed to identify current players; they are compressed under
`inputs/`, with original URL and SHA-256 in `current_fpl_sources.json`.

Source archive: https://github.com/peteowen1/pannadata/releases/tag/opta-latest
at the previously frozen download, source repository commit
`8caf7733c07ab9326f7010f5192de18bdcfd291a`. The release is mutable. Exact raw
SHA-256 values are enforced by `prepare_sources.py`; do not silently replace
these assets with a later release. Per-file SHA-256 values for the deliverable
are in `manifest.json`. The giant raw Parquet assets are not duplicated here.

## Assists: what works, and what does not

The prespecified sum of ordinary assists plus saved-shot, post, blocked-shot,
own-goal, penalty-won, free-kick-won, handball-won and pass-lost categories
reproduces historical FPL assists in 76,677 / 76,687 linked historical rows.
It reproduces all 58 assists in the 622 current controls (53 positive rows).
This is useful for auditing the **historical awards**, but cannot establish
what an older season would receive under the target rules.

Most decisively, that sum detects **zero of the four known official additions**
(Marmoush, Porro, Scott and Pickford). All candidate counters for those four
rows are omitted. The two official negative examples are retained as controls.
No new assist labels have been approved. The previous four official additions
remain separate and unchanged.

Official examples:
https://www.premierleague.com/en/news/4362187/whats-new-in-202526-fantasy-changes-to-assists-rules
The target rule text is the FPL 2026/27 component documented with source hash
in `../acquisition_followup/README.md`; the 2025 announcement is evidence
for these six situations, not proof that every 2026/27 clause is identical.

`assist_review_candidates.csv.gz` lists 1,421 player/match candidates with
special categories or historical count disagreement, including current controls.
It is **not exhaustive**: the four known additions would escape this filter.
`goal_review_queue.csv.gz` therefore enumerates historical source goal events
without pretending that a candidate filter discovers every modern assist.
There are 7,543 source goal events. Of 2,639 mapped fixtures, 2,636 have goal-event
totals matching the score. Chelsea–Villa, Man Utd–Everton and Spurs–Fulham on
1 December 2024 have no event rows (nine goals in total), despite player stats
being available. These are additional event-source gaps, separate from the
21 missing fixtures. `goal_match_coverage.csv` compares totals with scores; matching
those totals does not establish completeness of touches before each goal.

The six official decisions are linked to exact goal events in
`official_assist_event_index.csv`. Full event records for their six matches,
including raw qualifiers, are frozen in `inputs/official_assist_match_events.csv.gz`.
Two-minute goal windows are convenience extracts only. In particular, the
Pickford handball precedes a penalty and VAR delay: consult the full match,
not only the short window. Event coordinates and goal locations alone do not
prove the scorer's receiving location, intended receiver or every defensive touch.

## Remaining readiness gates

| Component | Available evidence | Gate before exact historical rescoring |
|---|---|---|
| Keeper big-chance saves | Existing approved 5,343 / 5,381 | 38 unresolved rows remain; use keeper reconciliation outputs, not this sparse counter |
| Ordinary BPS counters | Linked extracts for 76,687 rows; primary comparisons | Missing 21 fixtures, sparse-field semantics and observed source conflicts |
| Non-corner crosses | Explicit source counter and current diagnostic | Preserve the tested `accurate_cross_nocorner` mapping; subtracting free-kick crosses was not validated |
| Assists under target rules | Four existing official additions, six event controls, goal queue | Goal-level rules using receiving position, defensive touches and rebound/handball context |
| Complete BPS/bonus | Formula previously controlled on GW1/GW2 | All required inputs must be resolved before ranking bonus within each fixture |

The next implementation should evaluate goal-event rules against the six fixed
examples, report unresolved interpretation explicitly, then evaluate fresh
current-season controls. It must not turn category sums or xG into exact labels.

## Reproduction

From this directory, with pandas installed:

```sh
python audit.py
python assist_audit.py
python -m unittest discover -p 'test_*.py'
```

These audits run offline from committed extracts and the existing repository
assist decisions. Eight identity-transformation tests cover fixture restrictions,
missing preservation, FPL position retention and collision rejection.

To rebuild the archive projections, place the original hash-pinned Parquet
assets in `../keeper_recovery/raw/`, install pyarrow, then run:

```sh
python prepare_sources.py
python audit.py --prepare
python assist_audit.py
python assist_events.py
python prepare_goal_queue.py
```

The preparation path also uses the repository's historical FPL snapshots and
FotMob partitions, plus the committed current FPL snapshots. No keeper pipeline
rerun is needed. Nothing here trains a model or changes benchmark inputs.
Cost: 0 NOK; no paid sources or provider contact.
