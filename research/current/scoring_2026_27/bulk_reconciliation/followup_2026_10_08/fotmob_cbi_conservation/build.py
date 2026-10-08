"""Qualify CBI components and exact team-total exhaustion; preserve all conflicts."""
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
spec = importlib.util.spec_from_file_location('qualified_shot_rules',COMMON)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
count, digest, residual_zero = common.count, common.digest, common.residual_zero
FIELDS = {'clearances':('totalClearance','total_clearance'),
          'shot_blocks':('outfielderBlock','outfielder_block'),
          'interceptions':('interception','interception')}

def decode(row,raw):
    d = json.loads(raw)
    g = d['general']
    assert int(g['matchId'])==int(row['fotmob_match_id']) and g['leagueId']==47 and g['finished']
    assert g['matchTimeUTCDate'][:10]==row['date']
    assert [common.ALIASES.get(g[k]['name'],g[k]['name']) for k in ['homeTeam','awayTeam']]==[row['home'],row['away']]
    assert [int(t['id']) for t in d['header']['teams']]==[int(g[k]['id']) for k in ['homeTeam','awayTeam']]
    assert [int(t['score']) for t in d['header']['teams']]==[row['team_h_score'],row['team_a_score']]
    sides = {int(g[k]['id']):side for k,side in [('homeTeam','home'),('awayTeam','away')]}
    totals = {}
    for field in FIELDS:
        values = []
        for block in d['content']['stats']['Periods']['All']['stats']:
            for metric in block.get('stats',[]):
                if metric.get('key')==field:
                    assert metric.get('format')=='integer'
                    rs = metric.get('rawStats',[])
                    assert len(rs)==2
                    values.append([count(x.get('value')) if isinstance(x,dict) else None for x in rs])
        assert not values or all(x==values[0] for x in values)
        totals[field] = dict(zip(['home','away'],values[0] if values else [None,None]))
    players = []
    for player in d['content']['playerStats'].values():
        metrics = {}
        for block in player.get('stats',[]):
            for metric in block.get('stats',{}).values():
                key = metric.get('key')
                if key not in FIELDS:
                    continue
                value = count(metric.get('stat',{}).get('value'))
                assert key not in metrics or metrics[key]==value
                metrics[key] = value
        code = player.get('optaId')
        side = sides[int(player['teamId'])]
        players.append(dict(season=row['season'],fixture=int(row['fixture']),
                            code=int(str(code).lstrip('p')) if code is not None else None,
                            side=side,source_name=player.get('name'),
                            **{field:metrics.get(field) for field in FIELDS}))
    codes = [p['code'] for p in players if p['code'] is not None]
    assert len(codes)==len(set(codes))
    return players,totals

def main():
    protocol = json.loads((P/'protocol.json').read_text())
    assert digest(P/'plan.csv')==protocol['plan_sha256']
    pointer = json.loads((P/'inputs/parent_CURRENT.json').read_text())
    req_path = B/pointer['requirements']
    assert digest(req_path)==protocol['parent_requirements_sha256']==pointer['requirements_sha256']
    before = pd.read_csv(req_path,low_memory=False)
    prior = before[before.field.eq('clearances_blocks_interceptions')].set_index(KEY)
    meta_path = S/'delta_input_audit/inputs/archive_projection.csv.gz'
    meta = pd.read_csv(meta_path,low_memory=False).dropna(subset=['match_id','player_id'])
    source_path = B/'inputs/source_players.csv.gz'
    source = pd.read_csv(source_path,low_memory=False).merge(meta[KEY+['match_id','player_id']],on=['season','fixture','match_id','player_id'],how='left',validate='one_to_one')
    team_path = B/'full_team_totals.csv'
    primary_teams = pd.read_csv(team_path)
    manifest_path = P/'inputs/source_manifest.csv'
    manifests = pd.read_csv(manifest_path).set_index(['season','fixture'])
    plan = pd.read_csv(P/'plan.csv')
    all_players,all_groups,checks = [],[],[]
    for row in plan.to_dict('records'):
        fk = (row['season'],row['fixture'])
        evidence = manifests.loc[fk]
        raw_path = P/evidence['path']
        assert digest(raw_path)==evidence.file_sha256
        raw = gzip.decompress(raw_path.read_bytes())
        assert hashlib.sha256(raw).hexdigest()==evidence.raw_sha256
        players,totals = decode(row,raw)
        pm = {p['code']:p for p in players if p['code'] is not None}
        anchors = source[(source.season==fk[0])&(source.fixture==fk[1])]
        ta = primary_teams[(primary_teams.season==fk[0])&(primary_teams.fixture==fk[1])]
        for side in ['home','away']:
            people = [p for p in players if p['side']==side]
            groups = {}
            for field,(src,team_src) in FIELDS.items():
                total = totals[field][side]
                known = sum(p[field] for p in people if p[field] is not None)
                exhausted = residual_zero(total,[p[field] for p in people])
                reasons = []
                if total is None:
                    reasons.append('missing_explicit_team_total')
                elif not exhausted:
                    reasons.append('nonzero_or_negative_residual')
                groups[field] = dict(season=fk[0],fixture=fk[1],side=side,field=field,purpose=row['purpose'],team_total=total,explicit_player_sum=known,source_players=len(people),omitted_players=sum(p[field] is None for p in people),exhausted=exhausted,reasons=reasons)
                target = ta[ta.side==side]
                if len(target)==1 and pd.notna(target.iloc[0][team_src]):
                    expected = int(target.iloc[0][team_src])
                    checks.append(dict(season=fk[0],fixture=fk[1],code=None,side=side,field=field,kind='primary_team',purpose=row['purpose'],expected=expected,actual=total,agrees=expected==total))
                    if expected!=total:
                        reasons.append('primary_team_conflict')
                for anchor in anchors[anchors.team_position==side].to_dict('records'):
                    if pd.isna(anchor.get('code')):
                        if pd.notna(anchor[src]) and anchor[src]>0:
                            reasons.append('unmapped_primary_positive')
                        continue
                    p = pm.get(int(anchor['code']))
                    if p is None or p['side']!=side:
                        reasons.append('primary_player_identity_gap')
                        continue
                    explicit = p[field]
                    actual = explicit if explicit is not None else (0 if exhausted else None)
                    if pd.notna(anchor[src]):
                        expected = int(anchor[src])
                        if explicit is not None:
                            checks.append(dict(season=fk[0],fixture=fk[1],code=int(anchor['code']),side=side,field=field,kind='primary_player_explicit',purpose=row['purpose'],expected=expected,actual=explicit,agrees=expected==explicit))
                        if actual is not None and actual!=expected:
                            reasons.append('primary_player_conflict')
            for p in people:
                values = [p[field] if p[field] is not None else (0 if groups[field]['exhausted'] else None) for field in FIELDS]
                p['candidate_cbi'] = sum(values) if all(v is not None for v in values) else None
                p['purpose'] = row['purpose']
                key = (*fk,p['code'])
                if key in prior.index and not prior.loc[key,'is_open'] and p['candidate_cbi'] is not None:
                    expected = int(prior.loc[key,'value'])
                    native = pd.notna(prior.loc[key,'fpl'])
                    checks.append(dict(season=fk[0],fixture=fk[1],code=p['code'],side=side,field='cbi',kind='native_fpl_cbi' if native else 'closed_cbi',purpose=row['purpose'],expected=expected,actual=p['candidate_cbi'],agrees=expected==p['candidate_cbi']))
                    if expected!=p['candidate_cbi']:
                        for group in groups.values():
                            group['reasons'].append('closed_cbi_conflict')
            all_groups.extend(dict(**{k:v for k,v in group.items() if k not in ['reasons','exhausted']},zero_certified=group['exhausted'] and not group['reasons'],reason='|'.join(sorted(set(group['reasons']))) or 'explicit_total_exhausted') for group in groups.values())
        all_players.extend(players)
    players,groups,comparisons = pd.DataFrame(all_players),pd.DataFrame(all_groups),pd.DataFrame(checks)
    control = comparisons[comparisons.purpose.eq('control')]
    quality_rows = []
    for season in sorted(plan.season.unique()):
        c = control[control.season.eq(season)]
        field_counts = {field:{kind:int(((c.field==field)&(c.kind==kind)).sum()) for kind in ['primary_team','primary_player_explicit']} for field in FIELDS}
        n_cbi = int(c.field.eq('cbi').sum())
        bad = int((~c.agrees).sum())
        n_fixtures = int(plan[(plan.season==season)&plan.purpose.eq('control')].fixture.nunique())
        qualified = n_fixtures>=protocol['minimum_control_fixtures_per_season'] and n_cbi>=protocol['minimum_closed_cbi_checks_per_season'] and bad==0 and all(n['primary_team']>=protocol['minimum_primary_team_checks_per_component_per_season'] and n['primary_player_explicit']>=protocol['minimum_explicit_player_checks_per_component_per_season'] for n in field_counts.values())
        quality_rows.append(dict(season=season,control_fixtures=n_fixtures,cbi_checks=n_cbi,native_fpl_cbi_checks=int(c.kind.eq('native_fpl_cbi').sum()),disagreements=bad,source_mapping_qualified=qualified,**{field+'_'+kind:n for field,ns in field_counts.items() for kind,n in ns.items()}))
    quality = pd.DataFrame(quality_rows)
    native = quality[quality.season.eq('2025-26')].iloc[0]
    native_gate = bool(native.source_mapping_qualified and native.native_fpl_cbi_checks>=protocol['minimum_closed_cbi_checks_per_season'])
    good = set(quality.loc[quality.source_mapping_qualified,'season']) if native_gate else set()
    pi = players.dropna(subset=['code']).set_index(KEY)
    gi = groups.set_index(['season','fixture','side','field'])
    after = before.copy()
    changes = []
    for i,r in before[before.is_open & before.status.eq('missing_data') & before.field.eq('clearances_blocks_interceptions')].iterrows():
        key = tuple(r[k] for k in KEY)
        if key[0] not in good or key not in pi.index:
            continue
        p = pi.loc[key]
        if pd.isna(p.candidate_cbi) or not all(gi.loc[(*key[:2],p.side,field),'zero_certified'] for field in FIELDS):
            continue
        value = int(p.candidate_cbi)
        for col,v in [('value',value),('status','external_derived'),('quality_status','qualified_cbi_explicit_component_conservation'),('provenance','fotmob_cbi_conservation/results/derived_values.csv + inputs/source_manifest.csv'),('is_open',False),('is_zero',value==0),('needs_external_quality_review',True),('bulk_method','cbi_from_explicit_or_team_exhausted_components'),('bulk_group_id',':'.join(map(str,(*key[:2],p.side)))+':CBI')]:
            after.at[i,col] = v
        changes.append(dict(zip(KEY,key),field='clearances_blocks_interceptions',value=value,side=p.side,**{field:p[field] for field in FIELDS}))
    changed = before.is_open & ~after.is_open
    assert int(changed.sum())==len(changes)
    pd.testing.assert_frame_equal(before.loc[~changed],after.loc[~changed],check_dtype=False)
    assert not after.duplicated(KEY+['field']).any()
    assert after.loc[changed,'value'].ge(0).all() and after.loc[changed,'value'].mod(1).eq(0).all()
    out = P/'results'
    out.mkdir(exist_ok=True)
    def save(data,name):
        data.to_csv(out/name,index=False,compression='xz' if name.endswith('.xz') else None)
    save(players,'source_player_components.csv.xz');save(groups,'team_conservation.csv');save(comparisons,'source_comparisons.csv');save(quality,'source_quality_by_season.csv')
    save(pd.DataFrame(changes,columns=KEY+['field','value','side']+list(FIELDS)),'derived_values.csv')
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
    summary = dict(old_open_fields=int(before.is_open.sum()),new_fields=len(changes),open_fields=int(after.is_open.sum()),old_complete_matches=old_matches,complete_matches=int(matches.inputs_available.sum()),new_complete_matches=int(matches.inputs_available.sum())-old_matches,complete_player_matches=int(readiness.inputs_available.sum()),unique_affected_player_matches=int(readiness.open_fields.gt(0).sum()),native_fpl_gate_passed=native_gate,source_mapping_qualified_seasons=sorted(good),control_disagreements=int((~control.agrees).sum()),all_source_disagreements=int((~comparisons.agrees).sum()),qualified_scoring_matches=0,scoring_qualified=False,raw_fpl_preserved=True,new_fields_by_season=after.loc[changed].season.value_counts().sort_index().to_dict())
    (out/'findings.json').write_text(json.dumps(summary,indent=2)+'\n')
    inputs = [P/'plan.csv',P/'protocol.json',P/'inputs/parent_CURRENT.json',manifest_path,req_path,meta_path,source_path,team_path,COMMON,P/'build.py']
    (out/'manifest.json').write_text(json.dumps(dict(input_sha256={str(x.relative_to(S)):digest(x) for x in inputs},raw_sources=len(plan),outputs_sha256={x.name:digest(x) for x in sorted(out.iterdir()) if x.is_file() and x.name!='manifest.json'}),indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    main()
