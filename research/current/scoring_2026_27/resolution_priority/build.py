"""Separate statistic gaps from scoring dependencies. No locked-label writes.

Source-conflict ranges are conditional on the recorded candidate values, not
certified bounds on truth. Missing counters never enter arithmetic as zero.
"""
from pathlib import Path
import hashlib
import json
import math

import pandas as pd

P = Path(__file__).resolve().parent
S = P.parent
L = S/'remaining_ledger'
KEY = ['season','fixture','code']
SOURCES = ['fpl','fotmob','archive','primary','primary_followup','reconstruction']
HASHES = {}


def read(path):
    HASHES[str(path.relative_to(S.parent))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path, low_memory=False)


def bands(minutes):
    return (0 if minutes <= 0 else 2 if minutes >= 60 else 1,
            0 if minutes <= 0 else 6 if minutes > 60 else 3)


def pass_score(attempted, completed):
    if not 0 <= completed <= attempted:
        raise ValueError('Invalid passing pair')
    if attempted < 30:
        return 0
    ratio = completed / attempted
    return 6 if ratio >= .9 else 4 if ratio >= .8 else 2 if ratio >= .7 else 0


def defensive_bounds(position, values):
    """Unknown nonnegative counts have unbounded upper limit, not value zero."""
    if position == 'GK':
        return 0, 0
    threshold = 10 if position == 'DEF' else 12
    relevant = values[:2] if position == 'DEF' else values
    lower = sum(v for v in relevant if pd.notna(v))
    if lower >= threshold:
        return 2, 2
    return (0, 0) if all(pd.notna(v) for v in relevant) else (0, 2)


def winner_zero(own_score, other_score):
    return pd.notna(own_score) and pd.notna(other_score) and own_score <= other_score


def contribution(field, value, position):
    """One component only, using the existing qualified candidate formula."""
    basic_goal = {'GK':10,'DEF':6,'MID':5,'FWD':4}[position]
    bps_goal = {'GK':12,'DEF':12,'MID':18,'FWD':24}[position]
    if field == 'goals': return basic_goal*value, bps_goal*value
    if field == 'penalty_goals': return 0, (12-bps_goal)*value
    if field == 'saves': return math.floor(value/3), 2*value
    if field in ['recoveries','clearances_blocks_interceptions']:
        return None, math.floor(value/3)
    if field == 'total_tackles': return None,0
    if field in ['passes_attempted','passes_completed']: return 0,None
    weights = {'yellow_cards':(-1,-3),'red_cards':(-3,-9),'own_goals':(-2,-6),
        'penalties_saved':(5,7),'penalties_missed':(-2,-6),'assists_2026_27':(3,9),
        'saves_inside_box':(0,1),'big_chance_saves':(0,1),
        'won_tackles':(0,2),'noncorner_crosses':(0,1),'big_chances_created':(0,3),
        'chances_created':(0,1),'successful_dribbles':(0,1),'winning_goal':(0,3),
        'goal_line_clearances':(0,9),'fouls_won':(0,1),'shots_on_target':(0,2),
        'penalties_conceded':(0,-3),'big_chances_missed':(0,-3),
        'errors_to_goal':(0,-3),'errors_to_shot':(0,-1),'fouls':(0,-1),
        'offsides':(0,-1),'shots_off_target':(0,-1)}
    if field not in weights:
        raise ValueError(f'Unhandled component {field}')
    a,b = weights[field]
    return a*value,b*value


def save(frame, name):
    frame.to_csv(P/name,index=False,compression={'method':'gzip','mtime':0} if name.endswith('.gz') else None)


def main():
    for name in ['rules_2026_27.json','validate_bps.py']:
        HASHES[str((S/name).relative_to(S.parent))] = hashlib.sha256((S/name).read_bytes()).hexdigest()
    rules = json.loads((S/'rules_2026_27.json').read_text())
    assert rules['bps_component']['goals_scored'] == {'1':12,'2':12,'3':18,'4':24}
    assert rules['bps_component']['penalties_scored'] == 12
    # Validate the predecessor's frozen outputs before using its conclusions.
    manifest = json.loads((L/'manifest.json').read_text())
    for name, digest in manifest['outputs_sha256'].items():
        if hashlib.sha256((L/name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Changed ledger input: {name}')
    meta = read(L/'player_matches.csv.gz').set_index(KEY)
    ledger = read(L/'field_ledger.csv.gz')
    if ledger.duplicated(KEY+['field']).any():
        raise ValueError('Duplicate field key')
    fields = {name:g.set_index(KEY).reindex(meta.index) for name,g in ledger.groupby('field',sort=False)}
    pending = ledger[ledger.required_for_scoring & ledger.status.isin(['missing_data','source_conflict','rule_unresolved'])].copy()
    pending = pending.set_index(KEY).join(meta[['name','position','date','home','away','fixture_code','missing_archive_match','additional_event_gap']]).reset_index()
    own, other = {}, {}
    for season in meta.index.get_level_values('season').unique():
        fixtures = read(S.parent/f'project/data/{season}_fixtures.csv.gz').set_index('id')
        for key,r in meta.loc[season].iterrows():
            fixture,code = key
            f = fixtures.loc[fixture]
            # Both scores are official. Which side scored is already tied to
            # the player's historical FPL was_home in the predecessor ledger.
            own[(season,fixture,code)] = r.own_team_goals
            other[(season,fixture,code)] = f.team_h_score+f.team_a_score-r.own_team_goals
    own = pd.Series(own).reindex(meta.index)
    other = pd.Series(other).reindex(meta.index)

    # Audit this logical reconstruction against every explicit counter first.
    no_win = pd.Series([winner_zero(a,b) for a,b in zip(own,other)],index=meta.index)
    winner = fields['winning_goal']
    contrad = no_win & winner[SOURCES].gt(0).any(axis=1)
    save(winner.loc[contrad,SOURCES].join(meta[['name','date','home','away']]).reset_index(),'winning_goal_contradictions.csv')
    if contrad.any():
        raise ValueError('Winner zero rule contradicts explicit source counters')
    winner_resolved = no_win & winner.status.eq('missing_data')
    decisions = meta.loc[winner_resolved,['name','position','date','home','away','fixture_code']].copy()
    decisions['field'] = 'winning_goal'
    decisions['value'] = 0
    decisions['own_team_goals'] = own[winner_resolved]
    decisions['opponent_goals'] = other[winner_resolved]
    decisions['evidence'] = 'official_final_score_draw_or_loss_no_winning_goal'
    decisions['destination'] = 'separate_supplement_only'
    save(decisions.reset_index(),'documented_zero_supplement.csv')

    minute = fields['minutes']
    minutes = []
    for key,r in minute[minute.status.eq('source_conflict')].iterrows():
        vals = sorted(set(float(v) for v in r[SOURCES] if pd.notna(v)))
        base,bps = zip(*(bands(v) for v in vals))
        minutes.append(dict(zip(KEY,key),**{
            'candidate_minutes':json.dumps(vals),'base_minutes_min':min(base),'base_minutes_max':max(base),
            'bps_minutes_min':min(bps),'bps_minutes_max':max(bps),
            'participation_conflict':min(vals)<=0<max(vals),
            'minutes_component_invariant':len(set(base))==len(set(bps))==1,
            'scope':'recorded_candidates_only_not_true_bounds_or_whole_score',
        }))
    minutes = pd.DataFrame(minutes).set_index(KEY)
    save(minutes.join(meta[['name','position','date','home','away']]).reset_index(),'minute_conflicts.csv.gz')

    # Preserve paired pass observations by source; Cartesian pairs add a
    # conservative envelope, never assume min/max ratios pair naturally.
    pass_rows = []
    attempts,completed = fields['passes_attempted'],fields['passes_completed']
    mask = attempts.status.eq('source_conflict') | completed.status.eq('source_conflict')
    for key in meta.index[mask]:
        a,b = attempts.loc[key],completed.loc[key]
        av = sorted(set(a[SOURCES].dropna().astype(float)))
        bv = sorted(set(b[SOURCES].dropna().astype(float)))
        scores = [pass_score(x,y) for x in av for y in bv if 0<=y<=x]
        pairs = {source:[float(a[source]),float(b[source])] for source in SOURCES if pd.notna(a[source]) and pd.notna(b[source])}
        pass_rows.append(dict(zip(KEY,key),**{'source_pairs':json.dumps(pairs,sort_keys=True),
            'candidate_bps_min':min(scores) if scores else None,'candidate_bps_max':max(scores) if scores else None,
            'candidate_component_invariant':bool(scores) and min(scores)==max(scores),
            'scope':'valid_recorded_value_combinations_only_not_true_bounds'}))
    passes = pd.DataFrame(pass_rows).set_index(KEY)
    save(passes.join(meta[['name','position','date','home','away']]).reset_index(),'pass_conflicts.csv.gz')

    # Exact threshold awards can follow from partial nonnegative data. A
    # conflicting count contributes no guaranteed lower bound. This deliberately
    # does not assume the true value lies between conflicting source values.
    defensive = []
    for key,r in meta.iterrows():
        values = [fields[name].loc[key,'value'] for name in ['clearances_blocks_interceptions','total_tackles','recoveries']]
        lo,hi = defensive_bounds(r.position,values)
        active_dispute = not bool(r.fpl_active)
        if active_dispute:
            lo,hi = 0,2
        defensive.append(dict(zip(KEY,key),**{'defcon_lower':lo,'defcon_upper':hi,
            'exact_award_from_counts':lo==hi,'partial_counts':any(pd.isna(x) for x in (values[:2] if r.position=='DEF' else values)),
            'participation_disputed':active_dispute,'scope':'historical_position_target_thresholds_separate_diagnostic'}))
    defensive = pd.DataFrame(defensive).set_index(KEY)
    save(defensive.reset_index(),'defensive_thresholds.csv.gz')

    other_conflicts = []
    for _,r in pending[pending.status.eq('source_conflict') & pending.field.ne('minutes')].iterrows():
        key = tuple(r[k] for k in KEY)
        vals = sorted(set(float(v) for v in r[SOURCES] if pd.notna(v)))
        effects = [contribution(r.field,v,r.position) for v in vals]
        basic = [v[0] for v in effects if v[0] is not None]
        bps = [v[1] for v in effects if v[1] is not None]
        if r.field in ['total_tackles','recoveries','clearances_blocks_interceptions']:
            components = ['clearances_blocks_interceptions','total_tackles','recoveries']
            basis = [fields[c].loc[key,'value'] for c in components]
            for value in vals:
                candidate = basis.copy();candidate[components.index(r.field)] = value
                basic.extend(defensive_bounds(r.position,candidate))
        if r.field in ['passes_attempted','passes_completed']:
            row = passes.loc[key]
            bps = [row.candidate_bps_min,row.candidate_bps_max]
        other_conflicts.append(dict(zip(KEY,key),field=r.field,candidate_values=json.dumps(vals),
            basic_output_span=max(basic)-min(basic) if basic else None,
            bps_component_span=max(bps)-min(bps) if bps else None,
            basic_scope='defcon_award_with_other_known_counts' if r.field in ['total_tackles','recoveries','clearances_blocks_interceptions'] else 'single_component',
            evidence_scope='conditional_on_recorded_candidates_not_certified_true_bounds',
            **{source:r[source] for source in SOURCES}))
    other_conflicts = pd.DataFrame(other_conflicts)
    save(other_conflicts.set_index(KEY).join(meta[['name','position','date','home','away']]).reset_index(),'other_stat_conflicts.csv.gz')

    # Screen promising zero bounds, but do not approve cross-provider metric
    # relations without a documented compatible definition. Report violations.
    bound_checks, candidates = [], []
    for child,parent in [('won_tackles','total_tackles'),('big_chances_created','chances_created')]:
        a,b = fields[child],fields[parent]
        both = a.value.notna() & b.value.notna()
        violations = both & a.value.gt(b.value)
        potential = a.status.eq('missing_data') & b.value.eq(0)
        bound_checks.append(dict(field=child,parent=parent,explicit_pairs=int(both.sum()),
            violations=int(violations.sum()),potential_zero_cells=int(potential.sum()),approved=False,
            gate='prove_compatible_definition_and_resolve_counterexamples_before_using_subset_bound'))
        for key in meta.index[potential|violations]:
            candidates.append(dict(zip(KEY,key),field=child,parent=parent,parent_value=b.loc[key,'value'],
                child_value=a.loc[key,'value'],status='counterexample' if violations.loc[key] else 'unapproved_zero_candidate'))
    save(pd.DataFrame(bound_checks),'subset_bound_screen.csv')
    save(pd.DataFrame(candidates),'subset_bound_evidence.csv.gz')

    # Mutually exclusive action assignments make the queue additive. Broader
    # acquisition groups remain overlapping flags, as in the predecessor.
    pending['action'] = 'qualify_sparse_counter_semantics_or_complete_events'
    pending['tier'] = 3
    pending['scoring_scope'] = 'exact_input_missing_effect_not_bounded'
    conflicts = pending.status.eq('source_conflict')
    pending.loc[conflicts,['action','tier','scoring_scope']] = ['reconcile_stat_conflict',2,'no_source_selected_true_range_unknown']
    pending.loc[conflicts & pending.field.eq('goals'),['action','tier','scoring_scope']] = ['reconcile_goal_credit_conflict',1,'goal_credit_revision_policy_and_associated_own_goal_assist_effects']
    pending.loc[pending.field.eq('assists_2026_27'),['action','tier','scoring_scope']] = ['complete_goal_assist_adjudication',3,'both_basic_points_and_bps']
    pending.loc[pending.field.eq('big_chance_saves'),['action','tier','scoring_scope']] = ['obtain_remaining_keeper_evidence',3,'existing_keeper_bounds_no_point_imputation']
    invariant_split = pending.field.eq('penalty_goals') & pending.position.isin(['GK','DEF'])
    pending.loc[invariant_split,['action','tier','scoring_scope']] = ['penalty_split_irrelevant_to_scoring',0,'12_bps_for_either_goal_type_basic_goal_points_same']
    for idx,r in pending[pending.field.eq('winning_goal')].iterrows():
        key = tuple(r[k] for k in KEY)
        if winner_resolved.loc[key]:
            pending.loc[idx,['action','tier','scoring_scope']] = ['apply_documented_winner_zero_supplement',0,'exact_counter_proven_by_team_result']
    for idx,r in pending[pending.field.eq('minutes')].iterrows():
        key = tuple(r[k] for k in KEY)
        invariant = bool(minutes.loc[key,'minutes_component_invariant'])
        pending.loc[idx,['action','tier','scoring_scope']] = [
            'minutes_same_candidate_scoring_bands' if invariant else 'reconcile_minutes_scoring_band_change',
            4 if invariant else 2,'conditional_candidate_comparison_not_full_score']
    for idx,r in pending[pending.field.isin(['passes_attempted','passes_completed'])].iterrows():
        key = tuple(r[k] for k in KEY)
        if key in passes.index and passes.loc[key,'candidate_component_invariant']:
            pending.loc[idx,['action','tier','scoring_scope']] = ['passes_same_candidate_bps_band',4,'conditional_on_recorded_values_and_current_formula']
    pending['raw_stat_still_unresolved'] = ~pending.action.eq('apply_documented_winner_zero_supplement')
    pending['scoring_requirement_discharged'] = pending.tier.eq(0)
    columns = KEY+['name','position','date','home','away','fixture_code','field','status','action','tier','scoring_scope','raw_stat_still_unresolved','scoring_requirement_discharged','missing_archive_match','additional_event_gap']
    save(pending[columns].sort_values(['tier','action']+KEY+['field']),'resolution_queue.csv.gz')
    rows = []
    for (tier,action,field),g in pending.groupby(['tier','action','field'],sort=True):
        rows.append(dict(tier=tier,action=action,field=field,cells=len(g),
            unique_player_matches=len(g[KEY].drop_duplicates()),fixtures=len(g[['season','fixture']].drop_duplicates()),
            success_forecast='not_estimated_affected_population_only'))
    save(pd.DataFrame(rows),'action_field_summary.csv')
    actions = pending.groupby(['tier','action'],sort=True).apply(lambda g:pd.Series({'cells':len(g),
        'unique_player_matches':len(g[KEY].drop_duplicates()),'fixtures':len(g[['season','fixture']].drop_duplicates())}),include_groups=False).reset_index()
    actions = actions.sort_values(['tier','unique_player_matches','action'],ascending=[True,False,True])
    save(actions,'action_summary.csv')
    acquisition = []
    for flag in ['missing_archive_match','additional_event_gap']:
        for field,g in pending[pending[flag]].groupby('field'):
            acquisition.append(dict(source_flag=flag,field=field,cells=len(g),
                unique_player_matches=len(g[KEY].drop_duplicates()),fixtures=len(g[['season','fixture']].drop_duplicates()),
                scope='overlapping_source_flag_not_an_additional_requirement'))
    save(pd.DataFrame(acquisition),'acquisition_scope.csv')
    catalog = {
        'priority_basis':'Tier 0 local proofs; 1 four goal-credit conflicts with direct scoring consequences; 2 minute band changes and other explicit conflicts; 3 missing evidence; 4 candidate-invariant conflicts. Action summary within tiers is sorted by affected population, not estimated success.',
        'tiers_are_not_forecast_roi':True,
        'proof_requirements':{
            'qualify_sparse_counter_semantics_or_complete_events':'Document omission semantics for the exact source version, field and season, or reconstruct from independently complete event inventories. Two omitted fields do not verify zero.',
            'reconcile_stat_conflict':'Check raw payloads, timestamps/revisions and metric definitions. Preserve conflicting values; do not select source by order.',
            'reconcile_goal_credit_conflict':'Obtain official goal-credit/revision evidence and distinguish original FPL scoring from later event adjudication. Audit linked own-goal and assist credits before choosing a historical target policy.',
            'complete_goal_assist_adjudication':'Exhaustive goal/candidate coverage, verified receiving/touch/intent facts and supported rule route; new frozen holdout controls before historical approval.',
            'obtain_remaining_keeper_evidence':'Use the existing 38-row request and approved bounds; explicit big-chance/blocked-shot evidence or verified keeper counter. No xG proxy.',
            'reconcile_minutes_scoring_band_change':'Verify participation and official FPL versus provider minute conventions at zero, 60 and >60. Candidate span does not prove which source is right.',
            'minutes_same_candidate_scoring_bands':'Retain source conflict; deprioritize minute-component review only. Clean sheets, goals conceded and complete labels are separate.',
            'passes_same_candidate_bps_band':'Retain raw conflicts; equal output across valid recorded combinations is conditional on source candidates and qualified pass formula.',
            'apply_documented_winner_zero_supplement':'Official final result is a draw or loss; all explicit winner counters checked for contradictions. Supplement remains separate from locked labels.',
            'penalty_split_irrelevant_to_scoring':'Historical roster position GK/DEF gives 12 BPS for either goal type. Leave penalty count unknown; total goals and other components still require resolution.',
        },
        'new_source_search_policy':'Use the existing 21 missing-match, three missing-event-match and 38 keeper queues; do not repeat previously documented blocked or exhausted sources.',
    }
    (P/'action_catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    # Field summaries after the proved zero supplement and score-independent
    # split exclusion. Conditional candidate agreements remain unresolved.
    remaining = pending[~pending.scoring_requirement_discharged]
    save(remaining.groupby(['field','status'],sort=True).size().rename('cells').reset_index(),'remaining_scoring_requirements.csv')
    players = remaining.groupby(KEY).agg(unresolved_fields=('field','size'),minimum_unresolved_tier=('tier','min'))
    players = players.join(meta[['name','position','date','home','away','missing_archive_match','additional_event_gap']])
    save(players.reset_index(),'prioritized_player_matches.csv.gz')
    findings = dict(base_commit='2aded7f657f33d921d9e18ee35dbc3c95a5d48b2',input_open_cells=len(pending),
        new_documented_zero_counters=len(decisions),irrelevant_penalty_split_cells=int(invariant_split.sum()),
        discharged_scoring_requirements=int(pending.scoring_requirement_discharged.sum()),
        discharged_unique_player_matches=len(pending.loc[pending.scoring_requirement_discharged,KEY].drop_duplicates()),
        remaining_raw_stat_or_rule_cells=len(pending)-len(decisions),
        remaining_scoring_requirement_cells=len(remaining),remaining_unique_player_matches=len(remaining[KEY].drop_duplicates()),
        next_conflict_review_unique_player_matches=len(remaining.loc[remaining.tier.isin([1,2]),KEY].drop_duplicates()),
        minute_conflicts=len(minutes),minute_candidate_invariant=int(minutes.minutes_component_invariant.sum()),
        minute_candidate_sensitive=int((~minutes.minutes_component_invariant).sum()),
        pass_conflict_player_matches=len(passes),pass_candidate_invariant=int(passes.candidate_component_invariant.sum()),
        other_conflict_cells=len(other_conflicts),other_conflict_unique_player_matches=len(other_conflicts[KEY].drop_duplicates()),
        subset_candidates_approved=0,defcon_exact_from_counts=int(defensive.exact_award_from_counts.sum()),
        defcon_exact_with_partial_counts=int((defensive.exact_award_from_counts&defensive.partial_counts&meta.position.ne('GK')).sum()),
        full_bps_or_bonus_labels_produced=0,locked_labels_modified=False,keeper_values_modified=False,
        source_conflict_ranges_are_conditional=True,full_historical_harmonization_complete=False,cost_nok=0)
    (P/'findings.json').write_text(json.dumps(findings,indent=2)+'\n')
    (P/'manifest.json').write_text(json.dumps({'inputs_sha256':HASHES,
        'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(P.glob('*.py'))},
        'outputs_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(P.iterdir()) if p.suffix in ['.csv','.gz','.json'] and p.name not in ['manifest.json','validation.json']}},indent=2)+'\n')
    print(json.dumps(findings,indent=2))


if __name__ == '__main__':
    main()
