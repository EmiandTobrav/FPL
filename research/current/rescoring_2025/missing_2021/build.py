"""Fill only previously unknown 2021/22 labels, retaining source and audit evidence."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import pandas as pd

P=Path(__file__).resolve().parent;R=P.parents[1];O=P/'results';H=P.parent/'historical_fbref';G=P.parent/'gap_repair'
sys.path.insert(0,str(G))
# repair imports the frozen historical module named build; avoid this file's name.
sys.path.insert(0,str(H))
from repair import OVERRIDES, source_frame, point_bounds, COUNTS
MAP={'tackles':'Tkl_Tackles','blocks':'Sh_Blocks','interceptions':'Int','clearances':'Clr','recoveries':'Recov'}

def run():
    for filename,expected in json.loads((P/'input_sha256.json').read_text()).items():
        assert hashlib.sha256((P.parents[3]/filename).read_bytes()).hexdigest()==expected,filename
    src=pd.read_csv(O/'fotmob_players.csv');assert not src.duplicated(['fixture','code']).any()
    manifest=pd.read_csv(O/'fixture_manifest.csv').set_index('id')
    players=pd.read_csv(R/'project/data/2021-22_players.csv')
    f=pd.read_csv(R/'project/data/2021-22_gw.csv')
    f=f.merge(players[['id','code']],left_on='element',right_on='id',validate='many_to_one')
    f=f[f.minutes>0].copy();f['position']=f.position.replace({'GKP':'GK'});assert not f.duplicated(['fixture','code']).any()
    f['expected_team']=f.fixture.map(manifest.home).where(f.was_home,f.fixture.map(manifest.away))
    j=f.merge(src,on=['fixture','code'],how='inner',suffixes=('_fpl','_source'),validate='one_to_one')
    j['minute_difference']=j.source_minutes-j.minutes
    j['identity_ok']=(j.source_team==j.expected_team)&(j.source_goals==j.goals_scored)&j.source_minutes.gt(0)&j.minute_difference.abs().le(2)
    j[['fixture','element','code','name_fpl','name_source','position','minutes','source_minutes','minute_difference','goals_scored','source_goals','expected_team','source_team','identity_ok']].to_csv(O/'identity_audit.csv',index=False)

    # Compare a fixed control sample to the archived original count definitions.
    master=pd.read_csv(H/'raw/Master.csv');master=master[master.fbref.notna()]
    for code,(old,new,name) in OVERRIDES.items():master.loc[master.code==code,'fbref']=new
    defense=source_frame(pd.read_csv(H/'raw/defense.csv'));misc=source_frame(pd.read_csv(H/'raw/misc.csv'))
    keys=['Season_End_Year','home','away','fbref']
    reference=defense.merge(misc[keys+['Recov']],on=keys,how='left',validate='one_to_one')
    reference=reference[reference.Season_End_Year==2022]
    c=j[(j.purpose=='control')&(j.position!='GK')&j.identity_ok].copy()
    c['home']=c.fixture.map(manifest.home);c['away']=c.fixture.map(manifest.away)
    c=c.merge(master[['code','fbref']],on='code',how='left',validate='many_to_one').merge(reference[['home','away','fbref']+COUNTS],on=['home','away','fbref'],how='left',validate='many_to_one')
    metrics=[]
    for new,old in MAP.items():
        ok=c[new].notna()&c[old].notna()
        metrics.append({'metric':new,'compared':int(ok.sum()),'equal':int((c.loc[ok,new]==c.loc[ok,old]).sum()),'mean_delta':float((c.loc[ok,new]-c.loc[ok,old]).mean())})
    old_points=point_bounds(c)[0]
    new_c=c.drop(columns=COUNTS).rename(columns=MAP)
    new_points=point_bounds(new_c)[0]
    c['reference_defcon']=old_points;c['fotmob_defcon']=new_points
    ok=old_points.notna()&new_points.notna()
    metrics.append({'metric':'defcon_points','compared':int(ok.sum()),'equal':int((old_points[ok]==new_points[ok]).sum()),'mean_delta':float((new_points[ok]-old_points[ok]).mean())})
    pd.DataFrame(metrics).to_csv(O/'control_metrics.csv',index=False)
    c[['fixture','element','code','name_fpl','position']+list(MAP)+COUNTS+['reference_defcon','fotmob_defcon']].to_csv(O/'control_comparison.csv',index=False)

    gaps=pd.read_csv(G/'results/remaining_gaps.csv');gaps=gaps[gaps.season=='2021-22'].copy()
    supplement=j[['element','fixture','code','source_minutes','source_goals','source_team','identity_ok','match_id']+list(MAP)]
    gaps=gaps.merge(supplement,on=['element','fixture'],how='left',validate='one_to_one')
    for new,old in MAP.items():
        gaps[old+'_before']=gaps[old]
        gaps[old]=gaps[old].where(gaps[old].notna(),gaps[new].where(gaps.identity_ok.eq(True)))
    ex,lo,hi,inferred=point_bounds(gaps)
    gaps['defcon_v3']=ex;gaps['defcon_lower_v3']=lo;gaps['defcon_upper_v3']=hi
    gaps['source_quality']='fbref_cbit_fotmob_recoveries_provisional'
    gaps.loc[gaps.reason=='defense_match_missing','source_quality']='fotmob_full_counts_provisional'
    gaps.loc[ex.isna(),'source_quality']='missing'
    gaps.to_csv(O/'gap_fill_audit.csv',index=False)
    baseline=pd.read_csv(G/'results/2021-22_labels.csv')
    keys=['element','fixture'];patch=gaps.loc[ex.notna(),keys+['defcon_v3','defcon_lower_v3','defcon_upper_v3','source_quality','match_id']]
    patched=baseline.merge(patch,on=keys,how='left',validate='one_to_one')
    changed=patched.defcon_v3.notna()
    assert patched.loc[changed,'defcon_v2'].isna().all()
    for dest,new in [('defcon_v2','defcon_v3'),('defcon_lower','defcon_lower_v3'),('defcon_upper','defcon_upper_v3'),('quality','source_quality')]:patched.loc[changed,dest]=patched.loc[changed,new]
    patched['historical_plus_defcon']=patched.total_points+patched.defcon_v2
    known=baseline.defcon_v2.notna()
    assert patched.loc[known,'defcon_v2'].equals(baseline.loc[known,'defcon_v2'])
    assert patched[['element','fixture','minutes','total_points']].equals(baseline[['element','fixture','minutes','total_points']])
    patched.rename(columns={'defcon_v2':'defcon'}).drop(columns=['defcon_v3','defcon_lower_v3','defcon_upper_v3','source_quality','match_id']).to_csv(O/'2021-22_labels.csv',index=False)
    patch.to_csv(O/'2021-22_patch.csv',index=False)
    gaps[gaps.defcon_v3.isna()].to_csv(O/'remaining_gaps.csv',index=False)
    active=(patched.minutes>0)&(patched.position!='GK')
    result={'season':'2021-22','target_matches':76,'fetched_target_matches':int(src.loc[src.purpose=='gap','fixture'].nunique()),'controls':int(src.loc[src.purpose=='control','fixture'].nunique()),'active_outfield_rows':int(active.sum()),'missing_before':len(gaps),'resolved':len(patch),'missing_after':int(patched.loc[active,'defcon_v2'].isna().sum()),'identity_rejected_active_outfield_rows':int(((~j.identity_ok)&(j.position!='GK')).sum()),'new_defcon_awards':int((patch.defcon_v3==2).sum()),'cost_nok':0}
    (O/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));print(pd.DataFrame(metrics).to_string(index=False))

if __name__=='__main__':run()
