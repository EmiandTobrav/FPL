"""2024/25 historical points plus provider-derived 2025/26 defcon.
Not a full 2025/26 rescore. Never overwrite original labels or benchmark inputs.
"""
from pathlib import Path
import json,hashlib
import pandas as pd
P=Path(__file__).resolve().parent
R=P.parents[1]
OUT=P/'results'
ALIASES={'Bournemouth':'afc-bournemouth','Brighton':'brighton-&-hove-albion','Ipswich':'ipswich-town','Leicester':'leicester-city','Man City':'manchester-city','Man Utd':'manchester-united','Newcastle':'newcastle-united',"Nott'm Forest":'nottingham-forest','Spurs':'tottenham-hotspur','West Ham':'west-ham-united','Wolves':'wolverhampton-wanderers'}
def slug(s):return ALIASES.get(s,s.lower().replace(' ','-'))
def award(position,count):
    threshold=position.map({'DEF':10,'MID':12,'FWD':12})
    result=2*(count>=threshold).astype(float)
    result.loc[threshold.notna()&count.isna()]=float('nan')
    return result

def self_test():
    p=pd.Series(['DEF','DEF','MID','MID','FWD','GK','DEF'])
    c=pd.Series([9,10,11,12,12,99,float('nan')])
    a=award(p,c)
    assert a.iloc[:6].tolist()==[0,2,0,2,2,0] and pd.isna(a.iloc[6])
    # Two matches in a DGW are scored separately before aggregation.
    assert award(pd.Series(['DEF','DEF']),pd.Series([6,6])).sum()==0
    assert award(pd.Series(['DEF','DEF']),pd.Series([10,10])).sum()==4

def run():
    self_test();OUT.mkdir(exist_ok=True)
    source_files=sorted((P.parent/'core_2024/raw').glob('GW*.csv'))
    source=pd.concat([pd.read_csv(p) for p in source_files],ignore_index=True)
    assert not source.duplicated(['player_id','match_id']).any()
    rawfile=R/'project/data/2024-25_gw.csv';raw=pd.read_csv(rawfile)
    assert not raw.duplicated(['element','fixture']).any()
    f=raw[raw.position.isin(['GK','DEF','MID','FWD'])].copy()
    mapping=[]
    for fixture,g in f.groupby('fixture'):
        home=g.loc[g.was_home,'team'].unique();away=g.loc[~g.was_home,'team'].unique()
        assert len(home)==len(away)==1
        mapping.append({'fixture':fixture,'match_id':'24-25-prem-'+slug(home[0])+'-vs-'+slug(away[0])})
    mp=pd.DataFrame(mapping);assert mp.match_id.nunique()==380
    assert set(mp.match_id)==set(source.match_id)
    f=f.merge(mp,on='fixture',validate='many_to_one')
    j=f.merge(source[['player_id','match_id','clearances','blocks','interceptions','tackles','recoveries']],left_on=['element','match_id'],right_on=['player_id','match_id'],how='left',validate='one_to_one',indicator=True)
    j['cbit']=j[['clearances','blocks','interceptions','tackles']].sum(axis=1,min_count=4)
    j['defcon_count']=j.cbit.where(j.position=='DEF',j.cbit+j.recoveries)
    j['defcon_estimated']=award(j.position,j.defcon_count)
    inactive=j.minutes==0; keeper=j.position=='GK'; eligible=~inactive&~keeper
    j.loc[inactive|keeper,'defcon_estimated']=0
    j['quality']='provider_reconstruction'
    j.loc[inactive,'quality']='zero_official_no_minutes'
    j.loc[keeper,'quality']='zero_ineligible_position'
    j.loc[eligible&j.defcon_estimated.isna(),'quality']='missing'
    assert not j.loc[eligible,'defcon_estimated'].isna().any()
    j['historical_points']=j.total_points
    j['historical_plus_defcon']=j.historical_points+j.defcon_estimated
    # Explicit +-1 action perturbation; sensitivity scenario, NOT confidence bounds.
    j['defcon_minus1']=award(j.position,j.defcon_count-1)
    j['defcon_plus1']=award(j.position,j.defcon_count+1)
    j.loc[inactive|keeper,['defcon_minus1','defcon_plus1']]=0
    j['season']='2024-25'
    cols=['season','fixture','element','round','position','historical_points','defcon_estimated','historical_plus_defcon','quality','defcon_count','defcon_minus1','defcon_plus1']
    for gw,g in j.groupby('round'):
        g[cols].sort_values(['fixture','element']).to_csv(OUT/f'GW{gw:02d}.csv',index=False)
    players=j.groupby(['element','name','position'],as_index=False).agg(historical_points=('historical_points','sum'),defcon_estimated=('defcon_estimated','sum'),historical_plus_defcon=('historical_plus_defcon','sum'),defcon_minus1=('defcon_minus1','sum'),defcon_plus1=('defcon_plus1','sum'))
    players.sort_values(['defcon_estimated','element'],ascending=[False,True]).to_csv(OUT/'players.csv',index=False)
    positions=j.groupby('position',as_index=False).agg(rows=('element','size'),awards=('defcon_estimated',lambda x:int((x==2).sum())),added_points=('defcon_estimated','sum'),minus1_points=('defcon_minus1','sum'),plus1_points=('defcon_plus1','sum'))
    positions.to_csv(OUT/'positions.csv',index=False)
    # Source-only records are never allowed to create a new FPL appearance.
    extra=source.merge(f[['element','match_id']],left_on=['player_id','match_id'],right_on=['element','match_id'],how='left',indicator=True)
    extra[extra._merge=='left_only'].to_csv(OUT/'source_only.csv',index=False)
    manifest={'dataset_id':'historical_plus_defcon_2025_v1','season':'2024-25','rows':len(j),'fixtures':int(j.fixture.nunique()),'active_rows':int((j.minutes>0).sum()),'excluded_manager_rows':int((raw.position=='AM').sum()),'missing_active_defcon':int(j.loc[eligible,'defcon_estimated'].isna().sum()),'awards':int((j.defcon_estimated==2).sum()),'added_player_points':float(j.defcon_estimated.sum()),'full_2025_26_rescore':False,'unchanged_components':['historical assists','historical bonus/BPS','all other historical player points'],'quality':'Provider-derived defcon; approved for research by user. Not exact official target labels.','validation_reference':'../../core_2025_validation/README.md','temporal_note':'No learned correction from 2025/26. Final events used for labels only; predictive features must be lagged. Source choice was checked on 2025/26, so no untouched holdout is claimed.','sensitivity':'minus1/plus1 perturb defensive count by one per player/match; not statistical confidence bounds','benchmark_changed':False,'cost_nok':0}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    inputs=[rawfile]+source_files
    (OUT/'input_sha256.json').write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},indent=2)+'\n')
    assert j.historical_plus_defcon.sub(j.historical_points).equals(j.defcon_estimated)
    assert players.defcon_estimated.sum()==positions.added_points.sum()==j.defcon_estimated.sum()
    print(json.dumps(manifest,indent=2));print(positions.to_string(index=False));print(players.sort_values('defcon_estimated',ascending=False).head(10).to_string(index=False))
if __name__=='__main__':run()
