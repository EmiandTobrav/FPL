"""Offline, nullable cross-source requirements ledger; never writes scoring labels."""
from pathlib import Path
import gzip
import hashlib
import json

import pandas as pd

P = Path(__file__).resolve().parent
S = P.parent
R = S.parent
KEY = ['season', 'fixture', 'code']
SEASONS = [f'{y}-{str(y+1)[2:]}' for y in range(2019, 2026)]
INPUTS = {}


def read(path):
    INPUTS[str(path.relative_to(R))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path)


def unique(frame):
    if frame[KEY].isna().any().any() or frame.duplicated(KEY).any():
        raise ValueError('Missing or duplicate player-match keys')
    return frame.set_index(KEY).sort_index()


# name, archive, FotMob, FPL, scope. Similar-looking but different metrics
# (total/won tackles and all/non-corner crosses) deliberately stay separate.
SPECS = [
    ('minutes','minsPlayed','minutes_played','minutes','all'),
    ('goals','goals','goals','goals_scored','all'),
    ('penalty_goals','attPenGoal',None,None,'all'),
    ('clean_sheets',None,None,'clean_sheets','defensive_mid'),
    ('goals_conceded',None,None,'goals_conceded','defensive'),
    ('saves','saves','saves','saves','keeper'),
    ('saves_inside_box','savedIbox','saves_inside_box',None,'keeper'),
    ('big_chance_saves','bigChanceSaves','big_chance_saved',None,'keeper'),
    ('penalties_saved','penaltySave',None,'penalties_saved','keeper'),
    ('penalties_missed',None,None,'penalties_missed','all'),
    ('yellow_cards','yellowCard',None,'yellow_cards','all'),
    ('red_cards','redCard',None,'red_cards','all'),
    ('own_goals','ownGoals',None,'own_goals','all'),
    ('clearances','totalClearance','clearances',None,'all'),
    ('shot_blocks','outfielderBlock','shot_blocks',None,'all'),
    ('interceptions','interception','interceptions',None,'all'),
    ('recoveries','ballRecovery','recoveries','recoveries','all'),
    ('total_tackles',None,'matchstats.headers.tackles','tackles','outfield'),
    ('won_tackles','wonTackle',None,None,'all'),
    ('noncorner_crosses','accurateCrossNocorner',None,None,'all'),
    ('big_chances_created','bigChanceCreated','big_chance_created_team_title',None,'all'),
    ('chances_created','totalAttAssist','chances_created',None,'all'),
    ('successful_dribbles','wonContest','dribbles_succeeded',None,'all'),
    ('winning_goal','winningGoal',None,None,'all'),
    ('goal_line_clearances','clearanceOffLine','clearance_off_the_line',None,'all'),
    ('fouls_won','wasFouled','was_fouled',None,'all'),
    ('shots_on_target','ontargetScoringAtt','ShotsOnTarget',None,'all'),
    ('passes_attempted','totalPass','accurate_passes_attempted',None,'all'),
    ('passes_completed','accuratePass','accurate_passes',None,'all'),
    ('penalties_conceded','penaltyConceded','conceded_penalties',None,'all'),
    ('big_chances_missed','bigChanceMissed','big_chance_missed_title',None,'all'),
    ('errors_to_goal','errorLeadToGoal','errors_led_to_goal',None,'all'),
    ('errors_to_shot','errorLeadToShot','errors_led_to_shot',None,'all'),
    ('fouls','fouls','fouls',None,'all'),
    ('offsides','totalOffside','Offsides',None,'all'),
    ('shots_off_target','shotOffTarget','ShotsOffTarget',None,'all'),
]
PRIMARY = {
    'minutes':'mins_played','penalty_goals':'att_pen_goal',
    'saves_inside_box':'saved_ibox','penalties_saved':'penalty_save',
    'yellow_cards':'yellow_card','red_cards':'red_card',
    'clearances':'total_clearance','shot_blocks':'outfielder_block',
    'interceptions':'interception','recoveries':'ball_recovery',
    'total_tackles':'total_tackle','won_tackles':'won_tackle',
    'noncorner_crosses':'accurate_cross_nocorner',
    'big_chances_created':'big_chance_created','chances_created':'total_att_assist',
    'successful_dribbles':'won_contest','goal_line_clearances':'clearance_off_line',
    'fouls_won':'was_fouled','shots_on_target':'ontarget_scoring_att',
    'passes_attempted':'total_pass','passes_completed':'accurate_pass',
    'penalties_conceded':'penalty_conceded','big_chances_missed':'big_chance_missed',
    'errors_to_goal':'error_lead_to_goal','errors_to_shot':'error_lead_to_shot',
    'offsides':'total_offside','shots_off_target':'shot_off_target',
}


def classify(evidence, approved=None):
    """A blank is not a zero; conflicts cannot be resolved by source order."""
    conflict = evidence.nunique(axis=1, dropna=True).gt(1)
    value = evidence.bfill(axis=1).iloc[:, 0]
    status = pd.Series('documented_value', index=evidence.index)
    status.loc[value.eq(0)] = 'documented_zero'
    status.loc[value.isna()] = 'missing_data'
    status.loc[conflict] = 'source_conflict'
    value = value.mask(conflict)
    if approved is not None:
        # The existing keeper adjudications override candidates, even when
        # another source retains a contradictory older value.
        valid = approved.notna()
        value.loc[valid] = approved[valid]
        status.loc[valid] = 'documented_value'
        status.loc[valid & approved.eq(0)] = 'documented_zero'
    return value, status, conflict


def fpl_rows():
    parts, logs = [], []
    for season in SEASONS:
        f = read(R / f'project/data/{season}_gw.csv.gz').drop_duplicates()
        players = read(R / f'project/data/{season}_players.csv.gz')
        fixtures = read(R / f'project/data/{season}_fixtures.csv.gz').set_index('id')
        dup = f.duplicated(['element','fixture'], keep=False)
        retain = ~dup
        for (element, fixture), g in f[dup].groupby(['element','fixture']):
            official = fixtures.loc[fixture]
            ok = (pd.to_datetime(g.kickoff_time, utc=True).eq(pd.to_datetime(official.kickoff_time, utc=True)) & g.GW.eq(official.event))
            if ok.sum() != 1:
                raise ValueError(f'Unresolved FPL duplicate: {season}/{element}/{fixture}')
            retain.loc[g.index] = ok
            logs.append(dict(season=season, element=element, fixture=fixture, discarded=int((~ok).sum())))
        f = f[retain].merge(players[['id','code']], left_on='element', right_on='id', validate='many_to_one')
        f['season'] = season
        f['own_team_goals'] = f.fixture.map(fixtures.team_h_score).where(f.was_home, f.fixture.map(fixtures.team_a_score))
        parts.append(f)
    pd.DataFrame(logs).to_csv(P/'fpl_duplicate_resolution.csv', index=False)
    return unique(pd.concat(parts, ignore_index=True))


def main():
    archive = unique(pd.concat([read(S/f'bps_recovery/inputs/counts-{s}.csv.gz') for s in SEASONS], ignore_index=True))
    fotmob = unique(pd.concat([read(p) for p in sorted((S/'data').glob('*/part-*.csv'))], ignore_index=True))
    if not archive.index.equals(fotmob.index):
        raise ValueError('Population mismatch')
    fpl_all = fpl_rows()
    fpl = fpl_all.reindex(archive.index)
    primary = unique(read(S/'bps_recovery/inputs/primary_controls.csv.gz')).reindex(archive.index)
    follow = unique(read(S/'keeper_recovery/followup/primary_verified/observations.csv')).reindex(archive.index)
    keeper = unique(read(S/'keeper_recovery/keeper_counts.csv.gz')).reindex(archive.index)
    old = unique(pd.concat([read(p) for p in sorted((R/'rescoring_2025/harmonized/dataset/counts').glob('*/part-*.csv'))], ignore_index=True)).reindex(archive.index)
    meta = archive[['name','element','position','fixture_code','date','home','away','match_id','player_id','mapping_status']].copy()
    meta['fotmob_match_id'] = fotmob.match_id
    meta['own_team_goals'] = fpl.own_team_goals
    # Different provider/FPL active denominators remain visible, never hidden.
    extra = fpl_all[fpl_all.minutes.gt(0) & ~fpl_all.index.isin(archive.index)]
    extra.reset_index().to_csv(P/'fpl_active_outside_population.csv', index=False)
    meta['fpl_row_present'] = fpl.minutes.notna()
    meta['fpl_active'] = fpl.minutes.gt(0)
    flags = pd.DataFrame(False, index=archive.index, columns=['missing_data','source_conflict','rule_unresolved'])
    counts = pd.Series(0, index=archive.index)
    nonminute_conflicts = pd.Series(False, index=archive.index)
    summaries = []
    pending_fields = {key: [] for key in archive.index}
    ledger_path = P/'field_ledger.csv.gz'
    rest_path = P/'remaining_fields.csv.gz'
    # Fixed gzip timestamp/name makes repeat output byte-identical.
    out = gzip.GzipFile(filename='', fileobj=ledger_path.open('wb'), mode='wb', mtime=0)
    rest = gzip.GzipFile(filename='', fileobj=rest_path.open('wb'), mode='wb', mtime=0)
    first = True
    first_rest = True
    components = {}

    def emit(name, evidence, scope, approved=None, rule=None, reason=None, required=True):
        nonlocal first, first_rest
        evidence = evidence.loc[scope]
        value, status, conflict = classify(evidence, approved.loc[scope] if approved is not None else None)
        g = evidence.copy()
        g['field'] = name
        g['value'] = value
        g['status'] = status
        g['source_disagreement'] = conflict
        g['required_for_scoring'] = required
        g['rule_unresolved'] = False if rule is None else rule.loc[scope]
        g['reason'] = '' if reason is None else reason.loc[scope]
        g.loc[g.reason.eq('') & g.status.eq('missing_data'), 'reason'] = 'all_compatible_sources_omit'
        g.loc[g.reason.eq('') & g.status.eq('source_conflict'), 'reason'] = 'explicit_values_disagree'
        # A required rule output has no candidate numeric value until calculated.
        if name == 'assists_2026_27':
            g.loc[g.rule_unresolved, 'status'] = 'rule_unresolved'
        unresolved = (g.status.isin(['missing_data','source_conflict','rule_unresolved']) | g.rule_unresolved) & required
        for kind in flags:
            mask = g.rule_unresolved if kind == 'rule_unresolved' else g.status.eq(kind)
            if required:
                flags.loc[g.index[mask], kind] = True
        if required and name != 'minutes':
            nonminute_conflicts.loc[g.index[g.status.eq('source_conflict')]] = True
        counts.loc[g.index] += unresolved.astype(int)
        for key in g.index[unresolved]:
            pending_fields[key].append(name)
        for season, group in g.groupby(level='season'):
            row = dict(season=season, field=name, required_for_scoring=required, applicable=len(group),
                       rule_unresolved=int(group.rule_unresolved.sum()),
                       source_disagreements=int(group.source_disagreement.sum()),
                       unresolved_cells=int(unresolved.loc[group.index].sum()))
            for kind in ['documented_value','documented_zero','missing_data','source_conflict']:
                row[kind] = int(group.status.eq(kind).sum())
            summaries.append(row)
        out.write(g.reset_index().to_csv(index=False, header=first).encode())
        first = False
        if unresolved.any():
            rest.write(g.loc[unresolved].join(meta.drop(columns=['own_team_goals'])).reset_index().to_csv(index=False, header=first_rest).encode())
            first_rest = False
        return value.reindex(archive.index), status.reindex(archive.index)

    resolved = {}
    all_rows = pd.Series(True, index=archive.index)
    old_map = {'clearances':'clearances','shot_blocks':'blocks','interceptions':'interceptions','recoveries':'recoveries','total_tackles':'tackles'}
    for name, a, fm, fp, scope_name in SPECS:
        scope = {'all':all_rows, 'keeper':archive.position.eq('GK'), 'outfield':archive.position.ne('GK'), 'defensive':archive.position.isin(['GK','DEF']), 'defensive_mid':archive.position.ne('FWD')}[scope_name]
        e = pd.DataFrame(float('nan'), index=archive.index, columns=['fpl','fotmob','archive','primary','primary_followup','reconstruction'])
        if a: e['archive'] = archive[a]
        if fm: e['fotmob'] = fotmob[fm]
        if fp: e['fpl'] = fpl[fp]
        alias = 'pl_' + PRIMARY.get(name, name)
        # FPL clean-sheet eligibility and conceded-goal scoring semantics are
        # intentionally not equated with similarly named provider counters.
        if name not in ['clean_sheets','goals_conceded','penalties_missed']:
            for label, frame in [('primary',primary),('primary_followup',follow)]:
                if alias in frame: e[label] = frame[alias]
        if name in old_map: e['reconstruction'] = old[old_map[name]]
        approved = None
        reason = pd.Series('', index=archive.index)
        if name == 'big_chance_saves':
            approved = keeper.big_chance_saves.where(keeper.status.eq('reconstructed'))
            e['reconstruction'] = approved
            reason = keeper.resolution_method.fillna(keeper.reason).fillna('')
        if name in ['penalty_goals','winning_goal']:
            goal_values, goal_status = resolved['goals']
            proven = goal_values.eq(0) & goal_status.isin(['documented_zero','documented_value'])
            e.loc[proven,'reconstruction'] = 0
            reason.loc[proven] = 'zero_goals_bound'
        # Global formula qualification is reported separately. It is not a
        # missing observation and must not inflate per-cell data requirements.
        rule = pd.Series(False, index=archive.index)
        is_component = name in ['clearances','shot_blocks','interceptions']
        if is_component:
            components[name] = e.copy()
        resolved[name] = emit(name,e,scope,approved,rule,reason,required=not is_component)

    # Both BPS and defensive contribution use the CBI sum. A documented FPL
    # aggregate can suffice even when an individual component is unavailable.
    # Keep the components as evidence, but never count them again as needs.
    e = pd.DataFrame({source:pd.concat([c[source] for c in components.values()],axis=1).sum(axis=1,min_count=3)
                      for source in ['fpl','fotmob','archive','primary','primary_followup','reconstruction']})
    e['fpl'] = fpl.clearances_blocks_interceptions
    e['reconstruction'] = pd.concat([resolved[name][0] for name in components],axis=1).sum(axis=1,min_count=3)
    emit('clearances_blocks_interceptions',e,all_rows,
         reason=pd.Series('explicit_CBI_or_three_resolved_components_no_sparse_zero_sum',index=archive.index))

    # Team score zero proves no assist award under any goal-assist interpretation.
    # Positive team scores require exhaustive candidate/goal adjudication; a
    # negative decision for one candidate does not settle a whole match total.
    e = pd.DataFrame(float('nan'), index=archive.index, columns=['fpl','fotmob','archive','primary','primary_followup','reconstruction'])
    zero_team = fpl.own_team_goals.eq(0)
    e.loc[zero_team,'reconstruction'] = 0
    reason = pd.Series('candidate_selection_touch_continuity_intention_and_rebound_rules', index=archive.index)
    reason.loc[zero_team] = 'official_own_team_score_zero_bound'
    emit('assists_2026_27',e,all_rows,rule=~zero_team,reason=reason)
    out.close(); rest.close()
    meta = meta.join(flags)
    meta['unresolved_fields'] = counts
    meta['required_fields'] = ['|'.join(pending_fields[k]) for k in archive.index]
    meta['historical_fpl_assists'] = fpl.assists
    meta['ordinary_archive_assists'] = archive.goalAssist
    meta['keeper_status'] = keeper.status
    meta['keeper_reason'] = keeper.reason
    meta['keeper_original_reason'] = keeper.original_reason
    meta['keeper_resolution_method'] = keeper.resolution_method
    meta['keeper_candidate_value'] = keeper.candidate_big_chance_saves
    additions = unique(read(S/'acquisition_followup/verified_assist_additions.csv')).reindex(archive.index)
    meta['has_official_assist_addition'] = additions.notna().any(axis=1)
    goal_coverage = read(S/'bps_recovery/goal_match_coverage.csv').set_index(['season','fixture'])
    fixture_keys = meta.index.droplevel('code')
    meta['goal_events_match_score'] = goal_coverage.goal_count_matches_score.reindex(fixture_keys).to_numpy()
    meta['missing_archive_match'] = meta.mapping_status.eq('missing_match')
    meta['additional_event_gap'] = ~meta.missing_archive_match & ~meta.goal_events_match_score.eq(True)
    meta.reset_index().to_csv(P/'player_matches.csv.gz', index=False, compression={'method':'gzip','mtime':0})
    summary = pd.DataFrame(summaries)
    summary.to_csv(P/'field_summary_by_season.csv', index=False)
    numeric = [c for c in summary if c not in ['season','field','required_for_scoring']]
    summary.groupby(['field','required_for_scoring'],sort=False)[numeric].sum().to_csv(P/'field_summary.csv')
    # Disjoint statuses versus overlapping player-match categories are separate
    # reports. Summing field or category counts is never a unique row count.
    meta.reset_index().groupby(['season','code'],sort=True).agg(
        name=('name','first'),player_matches=('fixture','size'),
        missing_data=('missing_data','sum'),source_conflict=('source_conflict','sum'),
        rule_unresolved=('rule_unresolved','sum'),
        affected_unique=('unresolved_fields',lambda x:int(x.gt(0).sum()))
    ).to_csv(P/'player_summary.csv')
    matches = meta.reset_index().groupby(['season','fixture'],sort=True).agg(
        date=('date','first'),home=('home','first'),away=('away','first'),
        player_matches=('code','size'),missing_data=('missing_data','sum'),
        source_conflict=('source_conflict','sum'),rule_unresolved=('rule_unresolved','sum'),
        affected_unique=('unresolved_fields',lambda x:int(x.gt(0).sum())),
        missing_archive_match=('missing_archive_match','max'),additional_event_gap=('additional_event_gap','max'))
    matches.to_csv(P/'match_summary.csv')
    results = dict(base_commit='f799229dfbecaa11baf5d2a86b431eff6368a6ab',
        population=len(meta),fixtures=len(matches),required_field_cells=int(summary.loc[summary.required_for_scoring,'applicable'].sum()),
        unresolved_field_cells=int(summary.unresolved_cells.sum()),
        affected_unique_player_matches=int(counts.gt(0).sum()),
        unique_by_category={k:int(flags[k].sum()) for k in flags},
        unique_nonminute_source_conflicts=int(nonminute_conflicts.sum()),
        category_overlap=flags.value_counts().rename('player_matches').reset_index().to_dict('records'),
        fpl_active_outside_population=len(extra),fpl_rows_missing=int(fpl.minutes.isna().sum()),
        source_active_fpl_inactive=int(fpl.minutes.eq(0).sum()),
        keeper_approved=int(keeper.status.eq('reconstructed').sum()),keeper_unresolved=int(keeper.status.eq('unresolved').sum()),
        missing_archive_player_matches=int(meta.missing_archive_match.sum()),
        missing_archive_matches=int(matches.missing_archive_match.sum()),
        additional_event_gap_matches=int(matches.additional_event_gap.sum()),
        additional_event_gap_player_matches=int(meta.additional_event_gap.sum()),
        additional_event_gap_goals=int(goal_coverage.loc[goal_coverage.index.isin(matches[matches.additional_event_gap].index),'expected_goals'].sum()),
        assists_zero_team_bound=int(zero_team.sum()),
        official_assist_additions_preserved=int(meta.has_official_assist_addition.sum()),
        full_historical_rescoring_ready=False,locked_labels_modified=False,cost_nok=0)
    (P/'findings.json').write_text(json.dumps(results,indent=2)+'\n')
    definitions = pd.DataFrame(SPECS+[
        ('clearances_blocks_interceptions','three_explicit_components','three_explicit_components','clearances_blocks_interceptions','all'),
        ('assists_2026_27',None,None,'own_team_goals_zero_bound_only','all'),
    ],columns=['field','archive','fotmob','fpl','scope'])
    definitions['required_for_scoring'] = ~definitions.field.isin(components)
    definitions['primary_alias'] = definitions.field.map(lambda x: 'pl_'+PRIMARY.get(x,x))
    definitions.loc[definitions.field.isin(['clean_sheets','goals_conceded','penalties_missed','clearances_blocks_interceptions','assists_2026_27']),'primary_alias'] = None
    definitions.to_csv(P/'field_definitions.csv',index=False)
    gates = {
        'not_counted_as_missing_cells': True,
        'gates': [
            'Non-corner cross mapping versus displayed open-play wording remains empirically qualified only on reused controls.',
            'Pass definitions and integer component thresholds require historical qualification; two current primary BPS residuals remain.',
            'Assists: exhaustive candidate selection, continuity, receiving location, intention, touch interpretation, own-goal/rebound routes and independent controls remain incomplete.',
            'Recompute BPS only with resolved inputs; rank bonus jointly within each full fixture; do not reuse historical BPS/bonus.',
            'Recompute basic points including goalkeeper goals and defensive awards; preserve the historical FPL roster position policy.',
            'Provider rows include one historically FPL-inactive appearance: adjudicate participation before final rescoring.',
        ],
    }
    (P/'rule_gates.json').write_text(json.dumps(gates,indent=2)+'\n')
    (P/'manifest.json').write_text(json.dumps({'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(P.glob('*.py'))},'inputs_sha256':INPUTS,'outputs_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(P.iterdir()) if p.suffix in ['.csv','.gz','.json'] and p.name not in ['manifest.json','validation.json']}},indent=2)+'\n')
    print(json.dumps(results,indent=2))


if __name__ == '__main__':
    main()
