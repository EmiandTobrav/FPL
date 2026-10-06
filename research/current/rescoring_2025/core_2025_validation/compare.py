"""Validate source counts against official FPL; preserve missing data explicitly."""
from pathlib import Path
import json, hashlib
import pandas as pd
P=Path(__file__).resolve().parent
ALIASES={'Bournemouth':'afc-bournemouth','Brighton':'brighton-hove-albion','Leeds':'leeds-united','Man City':'manchester-city','Man Utd':'manchester-united','Newcastle':'newcastle-united',"Nott'm Forest":'nottingham-forest','Spurs':'tottenham-hotspur','West Ham':'west-ham-united','Wolves':'wolverhampton-wanderers'}
def slug(s):return ALIASES.get(s,s.lower().replace(' ','-'))
def points(pos,cbit,recoveries):
    counts=cbit.where(pos=='DEF',cbit+recoveries)
    eligible=pos.isin(['DEF','MID','FWD'])
    p=2*(counts>=pos.map({'DEF':10,'MID':12,'FWD':12})).astype(float)
    p.loc[eligible&counts.isna()]=float('nan')
    p.loc[~eligible]=0
    return p

def self_test():
    pos=pd.Series(['DEF','DEF','MID','MID','FWD','GK','DEF','MID'])
    cbit=pd.Series([10.,9.,10.,10.,11.,100.,float('nan'),10.])
    recoveries=pd.Series([float('nan'),100.,2.,1.,1.,100.,0.,float('nan')])
    actual=points(pos,cbit,recoveries)
    assert actual.iloc[:6].tolist()==[2.,0.,2.,0.,2.,0.]
    assert actual.iloc[6:].isna().all()

def run():
    self_test()
    files=sorted((P/'raw').glob('*.csv'))
    source=pd.concat([pd.read_csv(x).assign(source_file=x.name) for x in files if 'playermatchstats' in x.name],ignore_index=True)
    assert not source.duplicated(['player_id','match_id']).any()
    f=pd.read_csv(P.parents[1]/'project/data/2025-26_gw.csv')
    duplicated=f[f.duplicated(['element','fixture'],keep=False)]
    cols=['position','minutes','tackles','recoveries','clearances_blocks_interceptions','defensive_contribution']
    assert not (duplicated.groupby(['element','fixture'])[cols].nunique(dropna=False)>1).any().any()
    f=f.drop_duplicates(['element','fixture']).copy()
    fixtures=[]
    for fixture,g in f.groupby('fixture'):
        home=g.loc[g.was_home,'team'].unique();away=g.loc[~g.was_home,'team'].unique()
        assert len(home)==len(away)==1
        fixtures.append({'fixture':fixture,'match_id':'25-26-prem-'+slug(home[0])+'-vs-'+slug(away[0])})
    mapping=pd.DataFrame(fixtures)
    assert not mapping.match_id.duplicated().any()
    assert set(source.match_id)==set(mapping.match_id)
    f=f.merge(mapping,on='fixture',validate='many_to_one')
    active=f[f.minutes>0].copy()
    j=active.merge(source,left_on=['element','match_id'],right_on=['player_id','match_id'],how='left',validate='one_to_one',suffixes=('_fpl','_source'),indicator=True)
    j['cbi_source']=j[['clearances','blocks','interceptions']].sum(axis=1,min_count=3)
    j['cbit_source']=j.cbi_source+j.tackles_source
    j['cbit_fpl']=j.clearances_blocks_interceptions+j.tackles_fpl
    j['points_fpl']=points(j.position,j.cbit_fpl,j.recoveries_fpl)
    j['points_source']=points(j.position,j.cbit_source,j.recoveries_source)
    # Alternative is diagnostic only, never a silently selected replacement.
    j['points_won_tackles']=points(j.position,j.cbi_source+j.tackles_won,j.recoveries_source)
    out=j[j.position!='GK']
    metrics=[]
    for name,a,b in [('CBI','cbi_source','clearances_blocks_interceptions'),('tackles','tackles_source','tackles_fpl'),('recoveries','recoveries_source','recoveries_fpl'),('CBIT','cbit_source','cbit_fpl'),('defcon_points','points_source','points_fpl'),('won_tackles_points','points_won_tackles','points_fpl')]:
        valid=out[a].notna()&out[b].notna();delta=out.loc[valid,a]-out.loc[valid,b]
        metrics.append({'metric':name,'eligible_outfield_rows':len(out),'compared':int(valid.sum()),'missing':int((~valid).sum()),'matches':int((delta==0).sum()),'mismatches':int((delta!=0).sum()),'agreement_pct':100*float((delta==0).mean()),'mean_abs_error':float(delta.abs().mean()),'sum_difference':float(delta.sum())})
    pd.DataFrame(metrics).to_csv(P/'metrics.csv',index=False)
    grouped=[]
    for keys,g in out.groupby(['round','position']):
        v=g.points_source.notna()
        grouped.append({'round':int(keys[0]),'position':keys[1],'rows':len(g),'compared':int(v.sum()),'missing':int((~v).sum()),'false_positive':int(((g.points_source==2)&(g.points_fpl==0)).sum()),'false_negative':int(((g.points_source==0)&(g.points_fpl==2)).sum())})
    pd.DataFrame(grouped).to_csv(P/'by_round_position.csv',index=False)
    inspect=['name','element','fixture','match_id','round','position','minutes','minutes_played','clearances','blocks','interceptions','cbi_source','clearances_blocks_interceptions','tackles_source','tackles_fpl','recoveries_source','recoveries_fpl','points_source','points_fpl','source_file']
    bad=out[out.points_source.isna()|(out.points_source!=out.points_fpl)]
    bad[inspect].to_csv(P/'point_disagreements.csv',index=False)
    j[inspect].to_csv(P/'comparison.csv',index=False)
    report={'source_rows':len(source),'source_matches':int(source.match_id.nunique()),'official_active_rows':len(active),'matched_active_rows':int((j._merge=='both').sum()),'unmatched_active_rows':int((j._merge!='both').sum()),'outfield_rows':len(out),'outfield_missing_points':int(out.points_source.isna().sum()),'false_positive_points':int(((out.points_source==2)&(out.points_fpl==0)).sum()),'false_negative_points':int(((out.points_source==0)&(out.points_fpl==2)).sum()),'official_defcon_awards':int((out.points_fpl==2).sum()),'source_tree':'1c9191ab6b0c191378ea27f257fdab2bae63caba','fixture_join':'Exact season plus home and away club; explicit club aliases; player FPL ID','scope':'Defensive count and threshold equivalence. Not full BPS/assist rescoring.'}
    (P/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    hashes={str(x.relative_to(P)):hashlib.sha256(x.read_bytes()).hexdigest() for x in files}
    official=P.parents[1]/'project/data/2025-26_gw.csv';hashes['../../project/data/2025-26_gw.csv']=hashlib.sha256(official.read_bytes()).hexdigest()
    (P/'sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print(json.dumps(report,indent=2));print(pd.DataFrame(metrics).to_string(index=False))
if __name__=='__main__':run()
