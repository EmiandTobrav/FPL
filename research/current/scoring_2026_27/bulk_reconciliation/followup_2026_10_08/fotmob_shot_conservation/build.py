"""Validate explicit shot totals and apply exact, vetoed conservation proofs."""
from pathlib import Path
import gzip
import hashlib
import json
import pandas as pd

P = Path(__file__).resolve().parent
B = P.parent.parent
S = B.parent
KEY = ['season','fixture','code']
ALIASES = {'Manchester City':'Man City','Manchester United':'Man Utd',
 'Newcastle United':'Newcastle','West Ham United':'West Ham',
 'Wolverhampton Wanderers':'Wolves','Tottenham Hotspur':'Spurs','Tottenham':'Spurs',
 'Brighton & Hove Albion':'Brighton','Brighton and Hove Albion':'Brighton',
 'Nottingham Forest':"Nott'm Forest",'Leicester City':'Leicester','Leeds United':'Leeds',
 'Norwich City':'Norwich','Sheffield United':'Sheffield Utd','AFC Bournemouth':'Bournemouth',
 'Luton Town':'Luton','West Bromwich Albion':'West Brom','Ipswich Town':'Ipswich'}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def count(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int,float)) or value < 0 or int(value) != value:
        raise ValueError(f'Invalid counter: {value!r}')
    return int(value)

def residual_zero(total, values):
    total = count(total)
    values = [count(v) for v in values]
    if total is None:
        return False
    return sum(v for v in values if v is not None) == total

def decode(row, raw):
    d = json.loads(raw)
    g = d['general']
    assert int(g['matchId']) == int(row['fotmob_match_id']) and g['leagueId'] == 47 and g['finished']
    assert g['matchTimeUTCDate'][:10] == row['date']
    clubs = [row['home'],row['away']]
    assert [ALIASES.get(g[k]['name'],g[k]['name']) for k in ['homeTeam','awayTeam']] == clubs
    assert [int(t['id']) for t in d['header']['teams']] == [int(g[k]['id']) for k in ['homeTeam','awayTeam']]
    assert [int(t['score']) for t in d['header']['teams']] == [row['team_h_score'],row['team_a_score']]
    sides = {int(g[k]['id']):side for k,side in [('homeTeam','home'),('awayTeam','away')]}
    total_candidates = []
    for block in d['content']['stats']['Periods']['All']['stats']:
        for metric in block.get('stats',[]):
            if metric.get('key') == 'ShotsOnTarget':
                assert metric.get('format') == 'integer'
                values = metric.get('rawStats',[])
                assert len(values) == 2
                total_candidates.append([count(x.get('value')) if isinstance(x,dict) else None for x in values])
    assert total_candidates and all(x == total_candidates[0] for x in total_candidates)
    players = []
    for player in d['content']['playerStats'].values():
        metrics = {}
        for block in player.get('stats',[]):
            for metric in block.get('stats',{}).values():
                k = metric.get('key')
                v = metric.get('stat',{}).get('value')
                if k in metrics and metrics[k] != v:
                    raise ValueError('Conflicting duplicate player metric')
                metrics[k] = v
        opta = player.get('optaId')
        value = count(metrics.get('ShotsOnTarget'))
        side = sides.get(int(player['teamId']))
        assert side is not None
        code = int(str(opta).lstrip('p')) if opta is not None else None
        players.append(dict(season=row['season'],fixture=int(row['fixture']),code=code,
                            side=side,source_name=player.get('name'),explicit_sot=value,
                            explicit_goals=count(metrics.get('goals'))))
    codes = [x['code'] for x in players if x['code'] is not None]
    assert len(codes) == len(set(codes))
    return players, dict(zip(['home','away'],total_candidates[0]))

def main():
    protocol = json.loads((P / 'protocol.json').read_text())
    assert digest(P / 'plan.csv') == protocol['plan_sha256']
    current = json.loads((P / 'inputs/parent_CURRENT.json').read_text())
    req_path = B / current['requirements']
    assert digest(req_path) == protocol['parent_requirements_sha256'] == current['requirements_sha256']
    before = pd.read_csv(req_path,low_memory=False)
    meta_path = S / 'delta_input_audit/inputs/archive_projection.csv.gz'
    meta = pd.read_csv(meta_path,low_memory=False).dropna(subset=['match_id','player_id'])
    assert not meta.duplicated(['season','fixture','match_id','player_id']).any()
    source_path = B / 'inputs/source_players.csv.gz'
    source = pd.read_csv(source_path,low_memory=False)
    primary_teams_path = B / 'full_team_totals.csv'
    primary_teams = pd.read_csv(primary_teams_path)
    primary = source.merge(meta[KEY+['match_id','player_id']],on=['season','fixture','match_id','player_id'],how='left',validate='one_to_one')
    shot_requirements = before[before.field.eq('shots_on_target')]
    prior = shot_requirements.set_index(KEY)
    plan = pd.read_csv(P / 'plan.csv')
    manifest = pd.read_csv(P / 'inputs/source_manifest.csv').set_index(['season','fixture'])
    all_players, all_groups, comparisons = [], [], []
    positive_path = B / 'inputs/positive_event_evidence.csv.gz'
    positive = pd.read_csv(positive_path).merge(meta[KEY+['match_id','player_id']],on=['match_id','player_id'],how='left',validate='one_to_one')
    positive_keys = set(map(tuple,positive.loc[positive.positive_on_target.gt(0),KEY].dropna().to_numpy()))
    for row in plan.to_dict('records'):
        fkey = (row['season'],row['fixture'])
        proof = manifest.loc[fkey]
        path = P / proof['path']
        assert digest(path) == proof.file_sha256
        raw = gzip.decompress(path.read_bytes())
        assert hashlib.sha256(raw).hexdigest() == proof.raw_sha256
        players, totals = decode(row, raw)
        player_map = {p['code']:p for p in players if p['code'] is not None}
        for p in players:
            p['purpose'] = row['purpose']
        all_players.extend(players)
        anchors = primary[(primary.season==fkey[0])&(primary.fixture==fkey[1])]
        official_teams = primary_teams[(primary_teams.season==fkey[0])&(primary_teams.fixture==fkey[1])]
        for side in ['home','away']:
            group_players = [p for p in players if p['side']==side]
            total = totals[side]
            explicit_sum = sum(p['explicit_sot'] for p in group_players if p['explicit_sot'] is not None)
            reasons = []
            eligible = residual_zero(total,[p['explicit_sot'] for p in group_players])
            if total is None:
                reasons.append('missing_explicit_team_total')
            elif explicit_sum != total:
                reasons.append('nonzero_or_negative_residual')
            team_anchor = official_teams[official_teams.side==side]
            if len(team_anchor)==1 and pd.notna(team_anchor.iloc[0].ontarget_scoring_att):
                expected = int(team_anchor.iloc[0].ontarget_scoring_att)
                comparisons.append(dict(season=fkey[0],fixture=fkey[1],side=side,code=None,purpose=row['purpose'],kind='primary_team',expected=expected,actual=total,agrees=expected==total))
                if expected != total:
                    reasons.append('primary_team_conflict')
            for anchor in anchors[anchors.team_position==side].to_dict('records'):
                code = anchor.get('code')
                if pd.isna(code):
                    # An explicit unidentified positive cannot disappear from the inventory.
                    if pd.notna(anchor['ontargetScoringAtt']) and anchor['ontargetScoringAtt']>0:
                        reasons.append('unmapped_primary_positive')
                    continue
                p = player_map.get(int(code))
                if p is None:
                    reasons.append('primary_participant_missing')
                    continue
                if p['side'] != side:
                    reasons.append('primary_player_team_conflict')
                    continue
                actual = p['explicit_sot']
                derived = actual if actual is not None else (0 if eligible else None)
                key = (*fkey,int(code))
                if pd.notna(anchor['ontargetScoringAtt']):
                    expected = int(anchor['ontargetScoringAtt'])
                    if actual is not None:
                        comparisons.append(dict(season=fkey[0],fixture=fkey[1],side=side,code=int(code),purpose=row['purpose'],kind='primary_player_explicit',expected=expected,actual=actual,agrees=expected==actual))
                    if derived is not None and derived != expected:
                        reasons.append('primary_player_conflict')
                if key in prior.index and not bool(prior.loc[key,'is_open']) and derived is not None and derived != prior.loc[key,'value']:
                    reasons.append('closed_requirement_conflict')
                if derived == 0 and key in positive_keys:
                    reasons.append('positive_event_veto')
                if derived is not None and p['explicit_goals'] is not None and p['explicit_goals'] > derived:
                    reasons.append('goal_exceeds_sot')
            all_groups.append(dict(season=fkey[0],fixture=fkey[1],side=side,purpose=row['purpose'],team_total=total,explicit_player_sum=explicit_sum,source_players=len(group_players),missing_player_counters=sum(p['explicit_sot'] is None for p in group_players),zero_certified=eligible and not reasons,reason='|'.join(sorted(set(reasons))) or 'explicit_total_exhausted'))
    players = pd.DataFrame(all_players)
    groups = pd.DataFrame(all_groups)
    checks = pd.DataFrame(comparisons)
    controls = checks[checks.purpose.eq('control')]
    summaries = []
    for season in sorted(plan.season.unique()):
        c = controls[controls.season.eq(season)]
        fixtures = plan[(plan.season==season)&plan.purpose.eq('control')].fixture.nunique()
        pc = int(c.kind.eq('primary_player_explicit').sum())
        tc = int(c.kind.eq('primary_team').sum())
        bad = int((~c.agrees).sum())
        qualified = fixtures>=protocol['minimum_control_fixtures_per_season'] and pc>=protocol['minimum_explicit_player_comparisons_per_season'] and tc>=protocol['minimum_primary_team_comparisons_per_season'] and bad==0
        summaries.append(dict(season=season,control_fixtures=fixtures,explicit_player_checks=pc,primary_team_checks=tc,disagreements=bad,source_mapping_qualified=qualified))
    quality = pd.DataFrame(summaries)
    good = set(quality.loc[quality.source_mapping_qualified,'season'])
    gi = groups.set_index(['season','fixture','side'])
    pi = players.dropna(subset=['code']).set_index(KEY)
    after = before.copy()
    changes = []
    for i,r in before[before.is_open & before.status.eq('missing_data') & before.field.eq('shots_on_target')].iterrows():
        key = tuple(r[k] for k in KEY)
        if r.season not in good or key not in pi.index:
            continue
        player = pi.loc[key]
        group = gi.loc[(*key[:2],player.side)]
        if not group.zero_certified:
            continue
        value = int(player.explicit_sot) if pd.notna(player.explicit_sot) else 0
        method = 'explicit_fotmob_sot' if pd.notna(player.explicit_sot) else 'explicit_fotmob_team_total_exhausted'
        after.at[i,'value'] = value
        after.at[i,'status'] = 'external_derived'
        after.at[i,'quality_status'] = 'qualified_shared_opta_sot_conservation'
        after.at[i,'provenance'] = 'fotmob_shot_conservation/results/derived_values.csv + inputs/source_manifest.csv'
        after.at[i,'bulk_method'] = method
        after.at[i,'bulk_parent_value'] = group.team_total
        after.at[i,'bulk_group_id'] = ':'.join(map(str,(*key[:2],player.side)))+':ShotsOnTarget'
        after.at[i,'is_open'] = False
        after.at[i,'is_zero'] = value == 0
        after.at[i,'needs_external_quality_review'] = True
        changes.append(dict(zip(KEY,key),field='shots_on_target',value=value,method=method,side=player.side,team_total=group.team_total))
    changed = before.is_open & ~after.is_open
    assert int(changed.sum()) == len(changes)
    pd.testing.assert_frame_equal(before.loc[~changed],after.loc[~changed],check_dtype=False)
    assert not after.duplicated(KEY+['field']).any()
    assert after.loc[changed,'value'].ge(0).all() and after.loc[changed,'value'].mod(1).eq(0).all()
    out = P / 'results'
    out.mkdir(exist_ok=True)
    def save(data,name):
        data.to_csv(out/name,index=False,compression='xz' if name.endswith('.xz') else None)
    save(players,'source_player_shots.csv.xz');save(groups,'team_conservation.csv');save(checks,'source_comparisons.csv');save(quality,'source_quality_by_season.csv')
    save(pd.DataFrame(changes,columns=KEY+['field','value','method','side','team_total']),'derived_values.csv')
    save(after,'requirements.csv.xz');save(after[after.is_open],'remaining_fields.csv.xz')
    readiness = after.groupby(KEY).agg(open_fields=('is_open','sum'),quality_fields=('needs_external_quality_review','sum')).reset_index()
    readiness['inputs_available'] = readiness.open_fields.eq(0)
    readiness['scoring_qualified'] = False
    save(readiness,'player_match_readiness.csv.xz')
    matches = readiness.groupby(['season','fixture']).agg(player_matches=('code','size'),open_fields=('open_fields','sum'),quality_fields=('quality_fields','sum')).reset_index()
    matches['inputs_available'] = matches.open_fields.eq(0)
    matches['bonus_ready'] = False
    save(matches,'match_readiness.csv')
    fs = after.groupby('field').agg(required=('field','size'),open_cells=('is_open','sum'),quality_cells=('needs_external_quality_review','sum')).reset_index()
    save(fs,'field_summary.csv')
    old_complete = before.groupby(['season','fixture']).is_open.sum().eq(0).sum()
    summary = dict(old_open_fields=int(before.is_open.sum()),new_fields=len(changes),open_fields=int(after.is_open.sum()),old_complete_matches=int(old_complete),complete_matches=int(matches.inputs_available.sum()),new_complete_matches=int(matches.inputs_available.sum()-old_complete),complete_player_matches=int(readiness.inputs_available.sum()),unique_affected_player_matches=int(readiness.open_fields.gt(0).sum()),qualified_scoring_matches=0,scoring_qualified=False,raw_fpl_preserved=True,source_mapping_qualified_seasons=sorted(good),source_disagreements=int((~checks.agrees).sum()),new_fields_by_season=after.loc[changed].season.value_counts().sort_index().to_dict())
    (out/'findings.json').write_text(json.dumps(summary,indent=2)+'\n')
    inputs = [P/'plan.csv',P/'protocol.json',P/'inputs/parent_CURRENT.json',P/'inputs/source_manifest.csv',req_path,meta_path,source_path,primary_teams_path,positive_path]
    (out/'manifest.json').write_text(json.dumps(dict(input_sha256={str(x.relative_to(S)):digest(x) for x in inputs},raw_sources=120,outputs_sha256={x.name:digest(x) for x in sorted(out.iterdir()) if x.is_file() and x.name!='manifest.json'}),indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)

if __name__ == '__main__':
    main()
