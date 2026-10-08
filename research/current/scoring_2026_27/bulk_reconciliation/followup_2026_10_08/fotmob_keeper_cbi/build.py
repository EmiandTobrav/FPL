"""Role-scoped CBI validation; preserve the generic study and all its vetoes."""
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import lzma
import pandas as pd

P=Path(__file__).resolve().parent
B=P.parent.parent
S=B.parent
K=['season','fixture','code']
spec=importlib.util.spec_from_file_location('frozen_cbi_decoder',P.parent/'fotmob_cbi_conservation/build.py')
generic=importlib.util.module_from_spec(spec)
spec.loader.exec_module(generic)
FIELDS=generic.FIELDS
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(df,path):
    raw=df.to_csv(index=False,lineterminator='\n').encode()
    path.write_bytes(lzma.compress(raw) if path.suffix=='.xz' else raw)

def qualified_seasons(comparisons,protocol):
    rows=[]
    native=comparisons[comparisons.season.eq('2025-26')]
    native_good=bool(len(native)>=protocol['minimum_native_keeper_controls'] and
        native.fixture.nunique()>=protocol['minimum_native_control_fixtures'] and
        native.expected.gt(0).sum()>=protocol['minimum_native_nonzero_controls'] and
        native.agrees.all())
    for season,g in comparisons.groupby('season',sort=True):
        adequate=(len(g)>=protocol['minimum_closed_keeper_controls_per_historical_season'] and
                  g.expected.gt(0).sum()>=protocol['minimum_nonzero_closed_controls_per_historical_season'])
        rows.append(dict(season=season,controls=len(g),nonzero_controls=int(g.expected.gt(0).sum()),
            fixtures=int(g.fixture.nunique()),disagreements=int((~g.agrees).sum()),
            native_fpl_gate_passed=native_good,keeper_mapping_qualified=bool(adequate and g.agrees.all() and native_good)))
    return pd.DataFrame(rows),native_good

def build():
    protocol=json.loads((P/'protocol.json').read_text())
    lock=json.loads((P/'input_lock.json').read_text())
    for name,value in lock['input_sha256'].items():
        path=(S.parent if name in lock['outside_root_inputs'] else S)/name
        if sha(path)!=value:
            raise ValueError(f'Frozen input changed: {name}')
    pointer=json.loads((P/'inputs/parent_CURRENT.json').read_text())
    req_path=B/pointer['requirements']
    if sha(req_path)!=pointer['requirements_sha256']:
        raise ValueError('Keeper-study parent ledger fingerprint differs')
    before=pd.read_csv(req_path,low_memory=False)
    prior=before[before.field.eq('clearances_blocks_interceptions')].set_index(K)
    inv=pd.read_csv(S.parent/'training_dataset/scoring/results/historical_inventory.csv.xz',low_memory=False)
    inv=inv[inv.position.eq('GK')&inv.minutes.gt(0)].set_index(K)
    plan=pd.read_csv(P/'plan.csv')
    if sha(P/'plan.csv')!=protocol['plan_sha256']:
        raise ValueError('Frozen plan changed')
    veto=pd.read_csv(P.parent/'fotmob_cbi_conservation/results/team_conservation.csv')
    vi=veto.set_index(['season','fixture','side','field'])
    players,controls=[],[]
    for row in plan.to_dict('records'):
        raw=gzip.decompress((S/row['path']).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=row['raw_sha256']:
            raise ValueError('Raw response content fingerprint differs')
        decoded,totals=generic.decode(row,raw)
        body=json.loads(raw)
        roles={int(str(p['optaId']).lstrip('p')):p['isGoalkeeper']
            for p in body['content']['playerStats'].values() if p.get('optaId') is not None}
        for p in decoded:
            key=tuple(p[k] for k in K)
            if key not in inv.index:
                continue
            if roles.get(p['code']) is not True:
                raise ValueError('Native keeper has no explicit source keeper role')
            expected_side='home' if inv.loc[key,'was_home'] else 'away'
            if p['side']!=expected_side:
                raise ValueError('Native keeper/source club-side mismatch')
            values,proofs=[],[]
            compatible=True
            for field in FIELDS:
                people=[x for x in decoded if x['side']==p['side']]
                exhaustive=generic.residual_zero(totals[field][p['side']],[x[field] for x in people])
                value=p[field] if p[field] is not None else (0 if exhaustive else None)
                values.append(value)
                proofs.append('explicit' if p[field] is not None else ('full_team_exhaustion' if exhaustive else 'missing'))
                gkey=(*key[:2],p['side'],field)
                if gkey in vi.index and not vi.loc[gkey,'zero_certified']:
                    compatible=False
            candidate=sum(values) if all(v is not None for v in values) else None
            players.append(dict(zip(K,key),side=p['side'],candidate_cbi=candidate,
                historical_target_group_compatible=compatible,
                **{field:v for field,v in zip(FIELDS,values)},
                **{field+'_proof':v for field,v in zip(FIELDS,proofs)},
                is_control=key in prior.index and not prior.loc[key,'is_open']))
            if candidate is not None and key in prior.index and not prior.loc[key,'is_open']:
                expected=int(prior.loc[key,'value'])
                controls.append(dict(zip(K,key),expected=expected,actual=candidate,agrees=expected==candidate,
                    kind='native_fpl_keeper_cbi' if key[0]=='2025-26' else 'closed_historical_keeper_cbi'))
    predictions=pd.DataFrame(players)
    comparisons=pd.DataFrame(controls)
    if predictions.duplicated(K).any() or comparisons.duplicated(K).any():
        raise ValueError('Duplicate keeper observation')
    quality,native_good=qualified_seasons(comparisons,protocol)
    good=set(quality[quality.keeper_mapping_qualified].season)
    after=before.copy()
    pi=predictions.set_index(K)
    changes=[]
    for i,r in before[before.field.eq('clearances_blocks_interceptions')&before.status.eq('missing_data')&before.is_open].iterrows():
        key=tuple(r[k] for k in K)
        if r.position!='GK' or key[0] not in good or key not in pi.index:
            continue
        p=pi.loc[key]
        if pd.isna(p.candidate_cbi) or not p.historical_target_group_compatible:
            continue
        value=int(p.candidate_cbi)
        if value<0 or value!=p.candidate_cbi:
            raise ValueError('Non-integer keeper CBI')
        for field,v in [('value',value),('status','external_derived'),('is_open',False),('is_zero',value==0),
            ('needs_external_quality_review',True),('quality_status','qualified_keeper_cbi_component_conservation'),
            ('provenance','fotmob_keeper_cbi/results/derived_values.csv + plan.csv'),
            ('bulk_method','keeper_only_cbi_explicit_or_full_team_exhaustion')]:
            after.at[i,field]=v
        changes.append(dict(zip(K,key),field='clearances_blocks_interceptions',value=value,
            **{field:p[field] for field in FIELDS},**{field+'_proof':p[field+'_proof'] for field in FIELDS}))
    changed=before.is_open&~after.is_open
    pd.testing.assert_frame_equal(before.loc[~changed],after.loc[~changed],check_dtype=False)
    if int(changed.sum())!=len(changes) or after.duplicated(K+['field']).any():
        raise ValueError('Invalid keeper-only ledger application')
    out=P/'results';out.mkdir(exist_ok=True)
    readiness=after.groupby(K).agg(open_fields=('is_open','sum'),quality_fields=('needs_external_quality_review','sum')).reset_index()
    readiness['inputs_available']=readiness.open_fields.eq(0);readiness['scoring_qualified']=False
    matches=readiness.groupby(['season','fixture']).agg(player_matches=('code','size'),open_fields=('open_fields','sum'),quality_fields=('quality_fields','sum')).reset_index()
    matches['inputs_available']=matches.open_fields.eq(0);matches['bonus_ready']=False
    derived=pd.DataFrame(changes,columns=K+['field','value']+list(FIELDS)+[f+'_proof' for f in FIELDS])
    summary=dict(old_open_fields=int(before.is_open.sum()),new_fields=len(changes),open_fields=int(after.is_open.sum()),
        native_fpl_gate_passed=native_good,qualified_keeper_mapping_seasons=sorted(good),
        control_disagreements=int((~comparisons.agrees).sum()),native_control_keepers=int(comparisons.season.eq('2025-26').sum()),
        complete_matches=int(matches.inputs_available.sum()),complete_player_matches=int(readiness.inputs_available.sum()),
        unique_affected_player_matches=int(readiness.open_fields.gt(0).sum()),
        new_complete_matches=int(matches.inputs_available.sum())-int(before.groupby(['season','fixture']).is_open.sum().eq(0).sum()),
        new_fields_by_season=derived.season.value_counts().sort_index().to_dict(),scoring_qualified=False,
        generic_cbi_v1_unchanged=True,raw_fpl_preserved=True)
    for frame,name in [(predictions,'keeper_predictions.csv'),(comparisons,'control_comparisons.csv'),
        (quality,'source_quality_by_season.csv'),(derived,'derived_values.csv'),(after,'requirements.csv.xz'),
        (after[after.is_open],'remaining_fields.csv.xz'),(readiness,'player_match_readiness.csv.xz'),
        (matches,'match_readiness.csv'),(after.groupby('field').agg(required=('field','size'),open_cells=('is_open','sum'),quality_cells=('needs_external_quality_review','sum')).reset_index(),'field_summary.csv')]:
        save(frame,out/name)
    (out/'findings.json').write_text(json.dumps(summary,indent=2)+'\n')
    manifest=dict(path_root='research/current/scoring_2026_27',input_sha256=lock['input_sha256'],
        outside_root_inputs=lock['outside_root_inputs'],code_sha256={'build.py':sha(P/'build.py')},
        outputs_sha256={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json'})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    build()
