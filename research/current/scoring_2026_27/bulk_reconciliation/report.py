"""Render compact result documentation from the current findings."""
from pathlib import Path
import json
import pandas as pd
P=Path(__file__).resolve().parent

def main():
 f=json.loads((P/'findings.json').read_text());field=pd.read_csv(P/'field_summary.csv')
 pilot=pd.read_csv(P/'pilot_conservation.csv');hold=pd.read_csv(P/'holdout_conservation.csv')
 c=pd.concat([pilot.assign(cohort='pilot'),hold.assign(cohort='later_temporal')]);c.groupby(['cohort','field','reason']).size().rename('team_field_groups').reset_index().to_csv(P/'control_summary.csv',index=False)
 control=dict(pilot_fixtures=12,later_temporal_fixtures=12,explicit_balanced_groups=int(c.zero_certified.sum()),explicit_unbalanced_groups=int(c.reason.isin(['aggregate_conflict','unallocated_positive_residual']).sum()),omitted_team_totals=int(c.total.isna().sum()),individual_player_holdout_accuracy_not_estimated=True,independent_provider_validation=False)
 (P/'control_findings.json').write_text(json.dumps(control,indent=2)+'\n')
 changes='\n'.join(f'| {r.field} | {int(r.newly_available):,} | {int(r.open_cells):,} |' for r in field[field.newly_available.gt(0)].itertuples())
 text=f'''# Bulk reconciliation: current requirements ledger

8 October 2026. Historical FPL remains authoritative for compatible fields.
This phase follows `assist_reconciliation/` and changes only missing external
counters. No raw sources, approved keepers, assists or locked scoring labels change.

## Result

**{f['newly_available_cells']:,} missing field requirements are now available**
({100*f['newly_available_cells']/f['old_open_cells']:.1f}% of the previous open queue).
The new queue contains **{f['open_cells']:,} open cells in
{f['unique_affected_player_matches']:,} unique player-matches**.

| Field | Newly available | Still open |
|---|---:|---:|
{changes}

Player-match input inventories complete: **{f['available_player_matches']:,}**,
of which **{f['newly_available_player_matches']:,}** are newly complete.
Whole-fixture inventories complete: **{f['available_complete_fixtures']:,}**,
of which **{f['newly_available_complete_fixtures']:,}** are newly complete.
These are available input inventories, not final points/BPS/bonus labels.
**Zero fixtures receive newly qualified bonus labels in this phase.**
Season-specific BPS qualification, clipping/revision rules and quality caveats
remain explicit gates. Readiness is reported for all 77,280 active player-match
records and 2,660 fixtures, including the known FPL extraction exception.

## Four-step workflow

1. **Find shared causes.** The four large groups were sparse won/net tackles,
   line clearances, fouls won and shots on target. Ordinary source blanks are
   not generally observed zeros. Explicit zero total tackles does, however,
   bound both won and lost tackles to zero under the qualified definition.
2. **Probe before scaling.** Twelve pilot fixtures across six seasons produced
   consistent explicit team totals. Twelve preselected later fixtures confirmed
   the same mapping: **{control['explicit_balanced_groups']} explicit comparisons
   agree, {control['explicit_unbalanced_groups']} disagree**. Missing team totals
   are excluded, not counted as correct zeros. A second archive was rejected:
   its new normalized zeros lack demonstrated observational provenance.
   The useful source was then collected once per match for all 2,280 fixtures
   in 2019/20–2024/25, replacing tens of thousands of player requests.
3. **Apply and check in bulk.** Only exact nonnegative sum conservation and the
   explicit tackle-zero subset are used. Every team/field is checked, along
   with population identity, integer domains, contradictory event evidence,
   source preservation and deduplicated change accounting. Failed groups stay
   visible. Further quality work is grouped by field/season plus exceptions,
   not scheduled as one manual task per available cell.
4. **Measure complete units.** `player_match_readiness.csv.gz` and
   `match_readiness.csv` show availability before and after, remaining fields,
   source-quality needs and the separate scoring/bonus qualification gate.

## Why these zeros are justified

The [Opta definitions](https://www.statsperform.com/opta-event-definitions/)
partition tackles into won and lost. Therefore a compatible explicit total of
zero proves both subcounts zero. FotMob explicitly records total tackles;
43,185 overlapping explicit archive totals were screened, with eight
counter disagreements retained. Known contradictory event counts also prevent
a subset derivation. Definition agreement does not independently verify every
FotMob row; the external-source caveat is retained.

For team conservation, all explicit player counts, including bench/non-FPL
players, are summed. When an explicit official team total equals this known
sum, the remaining nonnegative contributions must be zero. A missing team
total or a positive/unexplained residual never licenses a zero. Team and player
IDs, fixture code/date/result, counter domains and source scope are checked.
No positive residual is assigned to an arbitrary player. The primary team field
`fk_foul_won` is checked against player `wasFouled`; it is not a player alias.

For net tackles, use `2 * won - total` only with compatible observed/derived
inputs; retain negative results. This resolves a raw statistic, **not** the
still-unqualified historical BPS clipping rule. Existing source conflicts are
not overwritten. Missing primary line-clearance totals are particularly common
and remain an important blocker; no global omission-to-zero rule was adopted.
A proposed line-clearance bound from clearances plus blocks was rejected after
three observed counterexamples (`line_subset_counterexamples.csv`). This avoids
a fast but incorrect reduction of the queue.

## Quality and validation limits

The control method and plans were frozen before the later 12-fixture responses.
The 194 agreeing controls compare aggregate totals; they do not estimate
individual-player accuracy. Archive and primary responses share Opta ancestry.
Exact aggregate agreement can still coexist with compensating source errors,
so new cells are `external_derived`, not individually primary-verified.

There are {f['quality_cells']:,} available external cells with retained quality
caveats. This is a coverage/assurance count, **not that many manual jobs**.
`quality_review_groups.csv` groups the population by field/season and
`automated_quality.json` records population checks. The unique union of open
requirements and source-quality caveats is {f['unique_open_or_quality_player_matches']:,}
player-matches. It must not be added to open-field counts.

## Files and reproduction

- `requirements.csv.gz`: latest full ledger with previous values/statuses.
- `derived_values.csv.gz`: exact changed cells, method, parent value and group ID.
- `conservation.csv.gz`: successful and rejected team/field proofs.
- `field_summary.csv`, `remaining_player_matches.csv.gz`, `player_summary.csv`:
  field/player queues; keys include season, fixture and FPL player code.
- `match_readiness.csv`, `player_match_readiness.csv.gz`: complete input units.
- `full_team_totals.csv`, `full_sources.json`, `inputs/matches/`: primary evidence.
- `protocol.json`, `control_summary.csv`, `definitions.json`: method and controls.

The collector is resumable and bounded at four concurrent requests and at most
two new request starts per second. It stops new submissions after HTTP
401/403/429. Every stored response is hashed; raw files support offline replay.
No paid data, model training or main merge. Cost: 0 NOK.

```sh
python collect.py plan
python collect.py pilot
python prepare.py
python probe.py pilot
# protocol.json was frozen before collecting the later controls
python collect.py holdout
python probe.py holdout
python collect.py full
python build.py
python report.py
python -m unittest discover -s . -p 'test_*.py'
```

`prepare.py` needs the pinned raw player archive and pyarrow; its compact inputs
are committed, so the build itself needs only pandas and the committed files.
All locked FPL/keeper/assist and model artifacts remain unchanged.
'''
 (P/'README.md').write_text(text)
if __name__=='__main__':main()
