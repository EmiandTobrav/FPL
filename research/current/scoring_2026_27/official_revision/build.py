"""Apply reviewed official revisions in a separate, reproducible supplement.

Never mutate historical labels or interpret provider omissions as zeros.
"""
from pathlib import Path
import hashlib
import json

import pandas as pd

P = Path(__file__).resolve().parent
S = P.parent
R = S.parent
KEY = ['season', 'fixture', 'code']
HASHES = {}


def read(path):
    HASHES[str(path.relative_to(R))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path, low_memory=False)


def save(frame, name):
    frame.to_csv(P/name, index=False, compression={'method':'gzip', 'mtime':0} if name.endswith('.gz') else None)


def paired_revision(frame, scorer, former_og):
    """A reviewed single event transfers attribution, preserving both team scores."""
    out = frame.copy()
    if scorer == former_og or not out.index.is_unique:
        raise ValueError('Invalid player identities')
    if out.loc[scorer, 'was_home'] == out.loc[former_og, 'was_home']:
        raise ValueError('Own goal must belong to the opposing team')
    if pd.isna(out.loc[scorer, 'goals_scored']) or out.loc[former_og, 'own_goals'] != 1:
        raise ValueError('Expected one explicit historical own goal')
    out.loc[scorer, 'goals_scored'] += 1
    out.loc[former_og, 'own_goals'] -= 1
    if team_totals(out) != team_totals(frame):
        raise ValueError('Unbalanced goal attribution')
    return out


def team_totals(frame):
    if frame[['goals_scored','own_goals','was_home']].isna().any().any():
        raise ValueError('Incomplete historical event counts')
    return tuple(int(frame.loc[frame.was_home.eq(side), 'goals_scored'].sum() +
                     frame.loc[frame.was_home.ne(side), 'own_goals'].sum()) for side in [True,False])


def minute_components(lower, upper):
    if not 0 <= lower <= upper:
        raise ValueError('Invalid minute bounds')
    bands = {(0 if m == 0 else 2 if m >= 60 else 1,
              0 if m == 0 else 6 if m > 60 else 3) for m in range(lower, upper+1)}
    if len(bands) != 1:
        raise ValueError('Minute bounds cross scoring threshold')
    return bands.pop()


def match_fpl(season, fixture, players):
    gw = read(R/f'project/data/{season}_gw.csv.gz')
    fixtures = read(R/f'project/data/{season}_fixtures.csv.gz').set_index('id')
    official = fixtures.loc[fixture]
    rows = gw[gw.fixture.eq(fixture) & gw.GW.eq(official.event) &
              pd.to_datetime(gw.kickoff_time, utc=True).eq(pd.to_datetime(official.kickoff_time, utc=True))]
    rows = rows.merge(players[['id','code']], left_on='element', right_on='id', validate='many_to_one')
    if rows.code.duplicated().any():
        raise ValueError('Duplicate player-match')
    return rows.set_index('code'), official


def main():
    HASHES.clear()
    for path in [P/'build.py', S/'rules_2026_27.json', S/'keeper_recovery/keeper_counts.csv.gz']:
        HASHES[str(path.relative_to(R))] = hashlib.sha256(path.read_bytes()).hexdigest()
    HASHES[str((P/'decisions.json').relative_to(R))] = hashlib.sha256((P/'decisions.json').read_bytes()).hexdigest()
    policy = json.loads((P/'decisions.json').read_text())
    if policy['policy'] != 'final_official_revisions_with_2026_27_rules':
        raise ValueError('Retrospective policy must be explicitly selected')
    queue = read(S/'resolution_priority/resolution_queue.csv.gz')
    ledger = read(S/'remaining_ledger/field_ledger.csv.gz')
    meta = read(S/'remaining_ledger/player_matches.csv.gz').set_index(KEY)
    events = read(S/'bps_recovery/goal_review_queue.csv.gz')
    patches, audits, dependencies, views = [], [], [], []
    for case in policy['cases']:
        season, fixture = case['season'], case['fixture']
        archive = read(S/f'bps_recovery/inputs/counts-{season}.csv.gz')
        archive = archive[archive.fixture.eq(fixture)].set_index('code')
        players = read(R/f'project/data/{season}_players.csv.gz')
        historical, official = match_fpl(season, fixture, players)
        scorer, former = case['scorer_code'], case['former_own_goal_code']
        revised = paired_revision(historical, scorer, former)
        score = (int(official.team_h_score), int(official.team_a_score))
        if team_totals(historical) != score or team_totals(revised) != score:
            raise ValueError('Reconciliation must retain official score')
        event = events[events.season.eq(season) & events.fixture.eq(fixture) &
                       events.event_id.eq(float(case['revised_event_id']))]
        if len(event) != 1 or event.iloc[0].player_id != archive.loc[scorer,'player_id']:
            raise ValueError('Revised event identity mismatch')
        if archive.loc[scorer,'goals'] != revised.loc[scorer,'goals_scored']:
            raise ValueError('Archive does not corroborate revised scorer total')
        for code, field, column in [(scorer,'goals','goals_scored'),(former,'own_goals','own_goals')]:
            key = (season, fixture, code)
            old = ledger[ledger.season.eq(season) & ledger.fixture.eq(fixture) & ledger.code.eq(code) & ledger.field.eq(field)]
            if len(old) != 1 or old.iloc[0].fpl != historical.loc[code,column]:
                raise ValueError('Ledger source mismatch')
            patches.append(dict(season=season,fixture=fixture,code=code,name=meta.loc[key,'name'],field=field,
                historical_fpl_value=int(historical.loc[code,column]),revised_value=int(revised.loc[code,column]),
                previous_status=old.iloc[0].status,status='documented_zero' if revised.loc[code,column]==0 else 'documented_value',
                source_url=case['source_url'],revised_event_id=case['revised_event_id'],
                reason='reviewed_official_appeal_paired_goal_transfer'))
            hit = queue.season.eq(season) & queue.fixture.eq(fixture) & queue.code.eq(code) & queue.field.eq(field)
            queue.loc[hit, ['raw_stat_still_unresolved','scoring_requirement_discharged']] = [False, True]
            queue.loc[hit, ['action','tier','scoring_scope']] = ['apply_official_revision_supplement',0,'exact_counter_official_appeal']
        naive = historical.copy()
        naive.loc[scorer,'goals_scored'] = revised.loc[scorer,'goals_scored']
        audits.append(dict(season=season,fixture=fixture,home=archive.iloc[0]['home'],away=archive.iloc[0]['away'],
            official_home=score[0],official_away=score[1],historical_home=team_totals(historical)[0],historical_away=team_totals(historical)[1],
            naive_home=team_totals(naive)[0],naive_away=team_totals(naive)[1],
            revised_home=team_totals(revised)[0],revised_away=team_totals(revised)[1]))
        roles = [(scorer, 'revised_scorer'), (former, 'former_own_goal')]
        if case['ordinary_assist_candidate_code'] is not None:
            roles.append((case['ordinary_assist_candidate_code'], 'ordinary_assist_candidate'))
        for code, role in roles:
            views.append(dict(season=season, fixture=fixture, code=code, role=role, name=meta.loc[(season,fixture,code),'name'],
                historical_fpl_goals=historical.loc[code,'goals_scored'], historical_fpl_own_goals=historical.loc[code,'own_goals'],
                historical_fpl_assists=historical.loc[code,'assists'], archive_goals=archive.loc[code,'goals'],
                archive_own_goals=archive.loc[code,'ownGoals'], archive_ordinary_assists=archive.loc[code,'goalAssist'],
                target_assists_2026_27=None))
        # These are event dependencies, not additional missing counter cells.
        for field, reason in [('assists_2026_27','Re-evaluate the revised goal under target assist rules; no automatic historical own-goal assist carry-over.'),
                              ('shots_on_target','Check revised shot attribution against the linked event; do not infer a new total.'),
                              ('winning_goal','Check winning-goal attribution against the revised ordered scoring timeline.')]:
            dependencies.append(dict(season=season,fixture=fixture,code=scorer,field=field,
                revised_event_id=case['revised_event_id'],ordinary_assist_candidate_code=case['ordinary_assist_candidate_code'] if field=='assists_2026_27' else None,
                status='event_dependency_review',additional_missing_cell=False,reason=reason))
    minute = policy['minute_case']
    key = tuple(minute[k] for k in KEY)
    lower, upper = minute['accepted_minute_lower'], minute['accepted_minute_upper']
    base, bps = minute_components(lower, upper)
    minute_rows = ledger[ledger.season.eq(key[0]) & ledger.fixture.eq(key[1]) & ledger.code.eq(key[2]) & ledger.field.eq('minutes')]
    if len(minute_rows)!=1 or minute_rows.iloc[0].fpl != 0 or minute_rows.iloc[0].archive != 17 or minute_rows.iloc[0].fotmob != 17:
        raise ValueError('Unexpected Ferguson source evidence')
    hit = queue.season.eq(key[0]) & queue.fixture.eq(key[1]) & queue.code.eq(key[2]) & queue.field.eq('minutes')
    if hit.sum() != 1:
        raise ValueError('Missing Ferguson requirement')
    queue.loc[hit,['scoring_requirement_discharged','action','tier','scoring_scope']] = [True,'apply_proven_minute_component',0,'primary_participation_below_60_minutes_exact_count_open']
    save(pd.DataFrame([dict(**{k:minute[k] for k in KEY},name=meta.loc[key,'name'],exact_minutes=None,
        proven_minutes_lower=lower,proven_minutes_upper=upper,base_minute_points=base,bps_minute_points=bps,
        raw_stat_still_unresolved=True,source_url=minute['source_url'])]),'minute_component_supplement.csv')
    patch = pd.DataFrame(patches)
    if patch.duplicated(KEY+['field']).any():
        raise ValueError('Duplicate correction')
    save(patch,'counter_supplement.csv')
    save(pd.DataFrame(audits),'goal_balance_audit.csv')
    save(pd.DataFrame(views),'affected_source_values.csv')
    save(pd.DataFrame(dependencies),'event_dependencies.csv')
    save(queue,'resolution_queue.csv.gz')
    remaining = queue[~queue.scoring_requirement_discharged]
    raw = queue[queue.raw_stat_still_unresolved]
    summary=[]
    for field in sorted(ledger.loc[ledger.required_for_scoring, 'field'].unique()):
        group = queue[queue.field.eq(field)]
        pending = group[~group.scoring_requirement_discharged]
        summary.append(dict(field=field,remaining_scoring_cells=len(pending),remaining_raw_or_rule_cells=int(group.raw_stat_still_unresolved.sum()),
            unique_affected_player_matches=len(pending[KEY].drop_duplicates()),
            missing_data=int(pending.status.eq('missing_data').sum()),source_conflict=int(pending.status.eq('source_conflict').sum()),
            rule_unresolved=int(pending.status.eq('rule_unresolved').sum())))
    save(pd.DataFrame(summary),'field_summary.csv')
    save(remaining.groupby(KEY,sort=True).agg(name=('name','first'),date=('date','first'),home=('home','first'),away=('away','first'),
        remaining_scoring_fields=('field','size'),fields=('field',lambda s:'|'.join(sorted(s)))).reset_index(),'remaining_player_matches.csv.gz')
    save(remaining.groupby(['season','fixture'],sort=True).agg(date=('date','first'),home=('home','first'),away=('away','first'),
        remaining_scoring_fields=('field','size'),unique_affected_player_matches=('code','nunique')).reset_index(),'match_summary.csv')
    findings=dict(policy=policy['policy'],paired_goal_revisions=4,corrected_counter_cells=len(patch),
        corrected_unique_player_matches=len(patch[KEY].drop_duplicates()),closed_goal_conflicts=int(patch.previous_status.eq('source_conflict').sum()),
        proven_minute_components=1,exact_minute_counts_recovered=0,new_scoring_requirements_discharged=5,
        remaining_scoring_requirement_cells=len(remaining),remaining_raw_stat_or_rule_cells=len(raw),
        remaining_unique_player_matches=len(remaining[KEY].drop_duplicates()),event_dependency_reviews=len(dependencies),
        event_dependencies_are_additional_missing_cells=False,full_bps_or_bonus_labels_produced=0,locked_labels_modified=False,
        keeper_values_modified=False,full_historical_harmonization_complete=False,cost_nok=0)
    (P/'findings.json').write_text(json.dumps(findings,indent=2)+'\n')
    (P/'manifest.json').write_text(json.dumps(dict(inputs=HASHES),indent=2,sort_keys=True)+'\n')
    print(json.dumps(findings,indent=2))


if __name__=='__main__':
    main()
