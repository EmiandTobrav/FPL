"""Coverage audit of pinned FPL-Core-Insights 2024/25 files; no scoring equivalence claim."""
from pathlib import Path
import json, hashlib
import pandas as pd
P=Path(__file__).resolve().parent
D=P/'raw'
def run():
    paths=sorted(D.glob('GW*.csv'))
    assert len(paths)==38
    d=pd.concat([pd.read_csv(p).assign(source=p.stem) for p in paths],ignore_index=True)
    players=pd.read_csv(D/'players.csv');matches=pd.read_csv(D/'matches.csv')
    assert not d.duplicated(['player_id','match_id']).any()
    assert not players.player_id.duplicated().any() and not matches.match_id.duplicated().any()
    fields=['tackles','tackles_won','interceptions','recoveries','blocks','clearances','penalties_scored']
    assert d[fields].notna().all().all() and (d[fields]>=0).all().all()
    assert set(d.match_id)==set(matches.match_id)
    j=d.merge(players,on='player_id',how='left',validate='many_to_one').merge(matches[['match_id','kickoff_time']],on='match_id',validate='many_to_one')
    assert j.position.notna().all()
    # Date + FPL player ID is a diagnostic join only, not a production fixture mapping.
    j['date']=pd.to_datetime(j.kickoff_time,utc=True,format='mixed').dt.strftime('%Y-%m-%d')
    official=pd.read_csv(P.parents[1]/'project/data/2024-25_gw.csv')
    official=official[(official.minutes>0)&(official.position!='AM')].copy()
    official['date']=pd.to_datetime(official.kickoff_time,utc=True).dt.strftime('%Y-%m-%d')
    assert not official.duplicated(['element','date']).any()
    assert not j.duplicated(['player_id','date']).any()
    joined=j.merge(official[['element','date','minutes','goals_scored','assists','position']],left_on=['player_id','date'],right_on=['element','date'],how='outer',indicator=True,suffixes=('_source','_fpl'),validate='one_to_one')
    common=joined[joined._merge=='both']
    missing=joined[joined._merge!='both']
    missing[['player_id','element','date','match_id','_merge']].to_csv(P/'unmatched.csv',index=False)
    result={'source':'https://github.com/olbauday/FPL-Core-Insights','source_tree':'1c9191ab6b0c191378ea27f257fdab2bae63caba','season':'2024-25','files':len(paths),'rows':len(d),'matches':int(d.match_id.nunique()),'players':int(d.player_id.nunique()),'duplicate_player_match_keys':int(d.duplicated(['player_id','match_id']).sum()),'null_cells':int(d.isna().sum().sum()),'defensive_fields':fields,'rows_per_match_min':int(d.groupby('match_id').size().min()),'rows_per_match_max':int(d.groupby('match_id').size().max()),'official_active_rows':len(official),'diagnostic_join':joined._merge.value_counts().to_dict(),'matched_minutes_disagreements':int((common.minutes_played!=common.minutes).sum()),'matched_goal_disagreements':int((common.goals!=common.goals_scored).sum()),'matched_assist_disagreements':int((common.assists_source!=common.assists_fpl).sum()),'exact_defcon_verified':False,'exact_target_bps_ready':False,'missing_explicit_fields':['saved_shot_location','goalline_clearances','target_rule_assists'],'note':'Non-null columns do not establish semantic completeness. Tackles and blocks require FPL-equivalence validation; assists definitions differ. Do not use as exact historical test labels yet.'}
    (P/'coverage.json').write_text(json.dumps(result,indent=2)+'\n')
    files=paths+[D/'players.csv',D/'matches.csv']
    (P/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':run()
