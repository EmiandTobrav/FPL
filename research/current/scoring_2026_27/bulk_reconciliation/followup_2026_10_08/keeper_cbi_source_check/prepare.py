"""Check whether an alternative archived source resolves the frozen keeper vetoes."""
from pathlib import Path
import gzip,hashlib,json,sys
import pandas as pd
P=Path(__file__).resolve().parent;S=P.parent;R=S.parent.parent.parent

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def main():
    import pyarrow.parquet as pq
    raw=Path(sys.argv[1]);assert digest(raw)=='2765b1771493c917ce7c544b01cf3a151e159a818abb889c7fcbd746353eaead'
    controls_path=S/'fotmob_keeper_cbi/results/control_comparisons.csv'
    controls=pd.read_csv(controls_path);bad=controls[controls.season.eq('2025-26')&~controls.agrees]
    projection_path=R/'scoring_2026_27/delta_input_audit/inputs/archive_projection.csv.gz'
    projection=pd.read_csv(projection_path,low_memory=False)
    keys=['season','fixture','code'];mapping=bad[keys+['expected','actual']].merge(projection[keys+['match_id','player_id']],on=keys,validate='one_to_one')
    fotmob_path=S/'fotmob_keeper_cbi/results/keeper_predictions.csv'
    fotmob=pd.read_csv(fotmob_path)
    mapping=mapping.merge(fotmob[keys+['clearances']],on=keys,validate='one_to_one').rename(columns={'clearances':'fotmob_explicit_clearances'})
    assert len(mapping)==6
    fields=['match_id','player_id','totalClearance','effectiveClearance','outfielderBlock','interception','interceptionWon']
    source=pq.read_table(raw,columns=fields,filters=[('competition','=','EPL'),('season','=','2025-2026'),('match_id','in',mapping.match_id.tolist())]).to_pandas()
    compared=mapping.merge(source,on=['match_id','player_id'],validate='one_to_one').sort_values(keys)
    assert compared.totalClearance.eq(compared.fotmob_explicit_clearances).all()
    compared['clearance_alone_exceeds_native_cbi']=compared.totalClearance.gt(compared.expected)
    files=[Path(__file__),controls_path,projection_path,fotmob_path]
    primary=[]
    sources=pd.read_csv(S/'primary_keeper_location/inputs/source_manifest.csv')
    for row in compared.itertuples():
        f=S/f'primary_keeper_location/inputs/raw/{row.code}_{row.fixture}.json.gz'
        if not f.exists():continue
        recorded=sources[sources.code.eq(row.code)&sources.fixture.eq(row.fixture)].iloc[0]
        assert digest(f)==recorded.file_sha256
        body=gzip.decompress(f.read_bytes());assert hashlib.sha256(body).hexdigest()==recorded.raw_sha256
        response=json.loads(body);assert response['entity']['altIds']['opta']==f'p{row.code}'
        stats={item['name']:item['value'] for item in response['stats']}
        primary.append(dict(season=row.season,fixture=row.fixture,code=row.code,explicit_primary_clearance=stats.get('total_clearance'),archive_clearance=row.totalClearance,native_cbi=row.expected))
        files.append(f)
    files.append(S/'primary_keeper_location/inputs/source_manifest.csv')
    (P/'archive_comparison.csv').write_text(compared.to_csv(index=False))
    (P/'primary_comparison.csv').write_text(pd.DataFrame(primary).to_csv(index=False))
    report={'source_sha256':digest(raw),'native_veto_cases':len(compared),'clearance_lower_bound_conflicts':int(compared.clearance_alone_exceeds_native_cbi.sum()),'existing_primary_witnesses':len(primary),'all_primary_clearances_agree_with_archive':all(r['explicit_primary_clearance']==r['archive_clearance'] for r in primary),'new_fields':0,'route':'Stop archive-only keeper CBI route; unchanged native counters and original failed gates remain protected.'}
    (P/'findings.json').write_text(json.dumps(report,indent=2)+'\n')
    manifest={'inputs':{str(f.relative_to(R)):digest(f) for f in files},'outputs':{f.name:digest(f) for f in [P/'archive_comparison.csv',P/'primary_comparison.csv',P/'findings.json']}}
    (P/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(report)
if __name__=='__main__':main()
