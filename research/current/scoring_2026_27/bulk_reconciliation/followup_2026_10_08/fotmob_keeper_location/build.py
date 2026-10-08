"""Count directly located keeper saves; reject incomplete or incompatible inventories."""
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import pandas as pd

P = Path(__file__).resolve().parent
B = P.parent.parent
S = B.parent
KEY = ['season','fixture','code']
COMMON = P.parent/'fotmob_shot_conservation/build.py'
spec = importlib.util.spec_from_file_location('shot_common',COMMON)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
count,digest = common.count,common.digest

def located_saves(shots,players,team_shots):
    """Return counts only if the complete inventory identifies every keeper save."""
    reasons = []
    if len({s.get('id') for s in shots})!=len(shots) or any(s.get('id') is None for s in shots):
        reasons.append('duplicate_or_missing_shot_id')
    per_keeper = {pid:[] for pid,p in players.items() if p['is_goalkeeper']}
    counts = {tid:0 for tid in team_shots}
    for shot in shots:
        team = shot.get('teamId')
        if team not in counts or type(shot.get('isOwnGoal')) is not bool:
            reasons.append('unknown_shot_team_or_own_goal_flag')
            continue
        if shot['isOwnGoal']:
            continue
        counts[team] += 1
        if shot.get('eventType')!='AttemptSaved':
            continue
        flags = ['isBlocked','isSavedOffLine','isOnTarget']
        if not all(type(shot.get(k)) is bool for k in flags):
            reasons.append('missing_save_classification')
            continue
        if shot['isBlocked'] or shot['isSavedOffLine'] or not shot['isOnTarget']:
            continue
        keeper = players.get(shot.get('keeperId'))
        if keeper is None or not keeper['is_goalkeeper'] or keeper['team_id']==team or keeper['code'] is None:
            reasons.append('unknown_or_wrong_keeper')
            continue
        if type(shot.get('isFromInsideBox')) is not bool:
            reasons.append('missing_explicit_shot_origin')
            continue
        per_keeper[shot['keeperId']].append(shot)
    if any(total is None or counts[tid]!=total for tid,total in team_shots.items()):
        reasons.append('incomplete_team_shot_inventory')
    return per_keeper,sorted(set(reasons))

def decode(row,raw):
    d = json.loads(raw)
    g = d['general']
    assert int(g['matchId'])==int(row['fotmob_match_id']) and g['leagueId']==47 and g['finished']
    assert g['matchTimeUTCDate'][:10]==row['date']
    assert [common.ALIASES.get(g[k]['name'],g[k]['name']) for k in ['homeTeam','awayTeam']]==[row['home'],row['away']]
    team_ids = [int(g[k]['id']) for k in ['homeTeam','awayTeam']]
    assert [int(t['id']) for t in d['header']['teams']]==team_ids
    assert [int(t['score']) for t in d['header']['teams']]==[row['team_h_score'],row['team_a_score']]
    totals = []
    for block in d['content']['stats']['Periods']['All']['stats']:
        for metric in block.get('stats',[]):
            if metric.get('key')=='total_shots':
                assert metric.get('format')=='integer'
                rs = metric.get('rawStats',[])
                assert len(rs)==2
                totals.append([count(x.get('value')) if isinstance(x,dict) else None for x in rs])
    assert not totals or all(t==totals[0] for t in totals)
    team_shots = dict(zip(team_ids,totals[0] if totals else [None,None]))
    players = {}
    for player in d['content']['playerStats'].values():
        code = player.get('optaId')
        code = int(str(code).lstrip('p')) if code is not None else None
        metrics = {m.get('key'):m.get('stat',{}).get('value') for block in player.get('stats',[]) for m in block.get('stats',{}).values()}
        pid = int(player['id'])
        assert pid not in players and int(player['teamId']) in team_ids
        players[pid] = dict(code=code,name=player['name'],team_id=int(player['teamId']),
                            is_goalkeeper=player.get('isGoalkeeper') is True,
                            source_saves=count(metrics.get('saves')),
                            source_minutes=count(metrics.get('minutes_played')))
    codes = [p['code'] for p in players.values() if p['code'] is not None]
    assert len(codes)==len(set(codes))
    shotmap = d['content'].get('shotmap',{})
    shots = shotmap.get('shots') if isinstance(shotmap,dict) else None
    if not isinstance(shots,list):
        return players,{},['missing_shot_inventory']
    saves,reasons = located_saves(shots,players,team_shots)
    return players,saves,reasons

def main():
    protocol = json.loads((P/'protocol.json').read_text())
    assert digest(P/'plan.csv')==protocol['plan_sha256']
    pointer = json.loads((P/'inputs/parent_CURRENT.json').read_text())
    req_path = B/pointer['requirements']
    assert digest(req_path)==protocol['parent_requirements_sha256']==pointer['requirements_sha256']
    before = pd.read_csv(req_path,low_memory=False)
    prior = before[before.field.eq('saves_outside_box')].set_index(KEY)
    inv_path = S.parent/'training_dataset/scoring/results/historical_inventory.csv.xz'
    native = pd.read_csv(inv_path,usecols=KEY+['saves','minutes']).set_index(KEY)
    plan = pd.read_csv(P/'plan.csv')
    manifests = pd.read_csv(P/'inputs/source_manifest.csv').set_index(['season','fixture'])
    predictions,events = [],[]
    for row in plan.to_dict('records'):
        fk = (row['season'],row['fixture'])
        manifest = manifests.loc[fk]
        raw_path = P/manifest['path']
        assert digest(raw_path)==manifest.file_sha256
        raw = gzip.decompress(raw_path.read_bytes())
        assert hashlib.sha256(raw).hexdigest()==manifest.raw_sha256
        players,saves,match_reasons = decode(row,raw)
        by_code = {p['code']:(pid,p) for pid,p in players.items() if p['code'] is not None}
        for key,r in prior.loc[(prior.index.get_level_values('season')==fk[0]) & (prior.index.get_level_values('fixture')==fk[1])].iterrows():
            reasons = list(match_reasons)
            entry = by_code.get(key[2])
            actual = None
            save_count = None
            native_saves = int(native.loc[key,'saves']) if key in native.index else None
            source_saves = None
            if entry is None or not entry[1]['is_goalkeeper']:
                reasons.append('missing_keeper_identity')
            else:
                pid,p = entry
                keeper_saves = saves.get(pid,[])
                save_count = len(keeper_saves)
                source_saves = p['source_saves']
                if native_saves is None or source_saves is None or save_count!=native_saves or save_count!=source_saves:
                    reasons.append('save_count_mismatch_or_missing')
                if p['source_minutes'] is None or p['source_minutes']<=0:
                    reasons.append('missing_active_keeper')
                if not reasons:
                    actual = sum(s['isFromInsideBox'] is False for s in keeper_saves)
                    for shot in keeper_saves:
                        events.append(dict(zip(KEY,key),shot_id=shot['id'],keeper_id=pid,shooting_team_id=shot['teamId'],is_from_inside_box=shot['isFromInsideBox'],outside_award=int(shot['isFromInsideBox'] is False)))
            reference = r['value'] if not r['is_open'] else None
            agrees = actual==reference if actual is not None and reference is not None else None
            if agrees is not None and not bool(agrees):
                reasons.append('closed_outside_count_conflict')
            predictions.append(dict(zip(KEY,key),name=r['name'],purpose=row['purpose'],native_saves=native_saves,source_saves=source_saves,located_saves=save_count,candidate_outside=actual,reference_outside=reference,eligible=not reasons,agrees=agrees,reason='|'.join(sorted(set(reasons))) or 'complete_located_save_inventory'))
    predictions = pd.DataFrame(predictions)
    bad_matches = set(map(tuple,predictions.loc[predictions.agrees.eq(False),['season','fixture']].to_numpy()))
    if bad_matches:
        bad_match = predictions[['season','fixture']].apply(tuple,axis=1).isin(bad_matches)
        predictions.loc[bad_match,'eligible'] = False
        predictions.loc[bad_match,'reason'] += '|closed_outside_count_conflict_in_match'
    controls = predictions[predictions.purpose.eq('control')]
    comparable = controls[controls.agrees.notna()]
    bad = int(comparable.agrees.eq(False).sum())
    qualified = len(comparable)>=protocol['minimum_eligible_control_keeper_rows'] and bad==0
    pi = predictions.set_index(KEY)
    after = before.copy()
    changes = []
    for i,r in before[before.is_open & before.status.eq('missing_data') & before.field.eq('saves_outside_box')].iterrows():
        key = tuple(r[k] for k in KEY)
        if not qualified or key not in pi.index or not bool(pi.loc[key,'eligible']):
            continue
        value = int(pi.loc[key,'candidate_outside'])
        for col,v in [('value',value),('status','external_derived'),('quality_status','qualified_complete_located_save_inventory'),('provenance','fotmob_keeper_location/results/keeper_predictions.csv + save_evidence.csv'),('is_open',False),('is_zero',value==0),('needs_external_quality_review',True),('bulk_method','direct_saved_shot_origin_with_native_save_count_gate'),('bulk_parent_value',pi.loc[key,'native_saves']),('bulk_group_id',':'.join(map(str,key))+':located_keeper_saves')]:
            after.at[i,col] = v
        changes.append(dict(zip(KEY,key),field='saves_outside_box',value=value,native_saves=pi.loc[key,'native_saves']))
    changed = before.is_open & ~after.is_open
    assert int(changed.sum())==len(changes)
    pd.testing.assert_frame_equal(before.loc[~changed],after.loc[~changed],check_dtype=False)
    assert not after.duplicated(KEY+['field']).any()
    out = P/'results'
    out.mkdir(exist_ok=True)
    def save(data,name):
        data.to_csv(out/name,index=False,compression='xz' if name.endswith('.xz') else None)
    save(predictions,'keeper_predictions.csv');save(pd.DataFrame(events),'save_evidence.csv');save(comparable,'control_comparisons.csv');save(pd.DataFrame(changes,columns=KEY+['field','value','native_saves']),'derived_values.csv')
    save(after,'requirements.csv.xz');save(after[after.is_open],'remaining_fields.csv.xz')
    readiness = after.groupby(KEY).agg(open_fields=('is_open','sum'),quality_fields=('needs_external_quality_review','sum')).reset_index()
    readiness['inputs_available'] = readiness.open_fields.eq(0)
    readiness['scoring_qualified'] = False
    save(readiness,'player_match_readiness.csv.xz')
    matches = readiness.groupby(['season','fixture']).agg(player_matches=('code','size'),open_fields=('open_fields','sum'),quality_fields=('quality_fields','sum')).reset_index()
    matches['inputs_available'] = matches.open_fields.eq(0)
    matches['bonus_ready'] = False
    save(matches,'match_readiness.csv')
    save(after.groupby('field').agg(required=('field','size'),open_cells=('is_open','sum'),quality_cells=('needs_external_quality_review','sum')).reset_index(),'field_summary.csv')
    old_matches = int(before.groupby(['season','fixture']).is_open.sum().eq(0).sum())
    summary = dict(old_open_fields=int(before.is_open.sum()),new_fields=len(changes),open_fields=int(after.is_open.sum()),old_complete_matches=old_matches,complete_matches=int(matches.inputs_available.sum()),new_complete_matches=int(matches.inputs_available.sum())-old_matches,complete_player_matches=int(readiness.inputs_available.sum()),unique_affected_player_matches=int(readiness.open_fields.gt(0).sum()),source_mapping_qualified=qualified,eligible_control_keepers=len(comparable),control_location_disagreements=bad,control_abstentions=int(controls.agrees.isna().sum()),prediction_status=predictions.reason.value_counts().to_dict(),qualified_scoring_matches=0,scoring_qualified=False,raw_fpl_preserved=True)
    (out/'findings.json').write_text(json.dumps(summary,indent=2)+'\n')
    inputs = [P/'plan.csv',P/'protocol.json',P/'inputs/parent_CURRENT.json',P/'inputs/source_manifest.csv',req_path,inv_path,COMMON,P/'build.py']
    # The training inventory lives beside scoring_2026_27; replay retains that layout.
    (out/'manifest.json').write_text(json.dumps(dict(input_sha256={str(x.relative_to(S.parent)):digest(x) for x in inputs},path_root='research/current',raw_sources=len(plan),outputs_sha256={x.name:digest(x) for x in sorted(out.iterdir()) if x.is_file() and x.name!='manifest.json'}),indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    main()
