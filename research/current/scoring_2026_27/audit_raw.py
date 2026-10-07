from pathlib import Path
import json,hashlib
from collections import Counter
import pandas as pd
P=Path(__file__).resolve().parent;H=P.parent/'rescoring_2025/harmonized';O=P/'results';D=P/'data';D.mkdir(exist_ok=True)
KEYS=['minutes_played','goals','assists','accurate_passes','chances_created','big_chance_created_team_title','big_chance_missed_title','accurate_crosses','dribbles_succeeded','ShotsOnTarget','ShotsOffTarget','Offsides','was_fouled','fouls','errors_led_to_goal','errors_led_to_shot','clearance_off_the_line','saves','saves_inside_box','big_chance_saved','conceded_penalties','penalties_won','matchstats.headers.tackles','clearances','shot_blocks','interceptions','recoveries']
def run():
 sources=json.loads((H/'results/sources.json').read_text());rows=[];inventory=Counter();shotkeys=Counter()
 for n,src in enumerate(sources,1):
  mid=src['match_id'];raw=next(p for p in [H/'raw'/f'fotmob_{mid}.json',H.parent/'missing_2021/raw'/f'fotmob_{mid}.json',H.parent/'final_gaps/raw'/f'fotmob_{mid}.json'] if p.exists());b=raw.read_bytes();assert hashlib.sha256(b).hexdigest()==src['sha256'];d=json.loads(b)
  for shot in d['content'].get('shotmap',{}).get('shots',[]):
   for key in shot:shotkeys[key]+=1
  for player in d['content'].get('playerStats',{}).values():
   if not player.get('optaId'):continue
   metrics={}
   for block in player.get('stats',[]):
    for m in block.get('stats',{}).values():
     key=m.get('key')
     if key:metrics[key]=m.get('stat',{})
   if metrics.get('minutes_played',{}).get('value',0)<=0:continue
   row=dict(season=src['season'],fixture=src['fixture'],match_id=mid,code=int(str(player['optaId']).lstrip('p')),name=player['name'],goalkeeper=player.get('isGoalkeeper',False))
   for k,v in metrics.items():inventory[(src['season'],k,'numeric' if isinstance(v.get('value'),(int,float)) else 'no_numeric_value')]+=1
   for k in KEYS:row[k]=metrics.get(k,{}).get('value')
   for k in ['accurate_passes','accurate_crosses','dribbles_succeeded']:row[k+'_attempted']=metrics.get(k,{}).get('total')
   rows.append(row)
  if n%500==0:print('parsed',n,flush=True)
 frame=pd.DataFrame(rows);assert not frame.duplicated(['season','fixture','code']).any();coverage=[]
 for season,g in frame.groupby('season'):
  dest=D/season;dest.mkdir(exist_ok=True)
  for i,start in enumerate(range(0,len(g),2000)):g.iloc[start:start+2000].to_csv(dest/f'part-{i:03d}.csv',index=False)
  for key in KEYS:
   relevant=g[g.goalkeeper] if key in ['saves','saves_inside_box','big_chance_saved'] else g
   coverage.append(dict(season=season,field=key,rows=len(relevant),explicit_values=int(relevant[key].notna().sum()),unknown_or_omitted=int(relevant[key].isna().sum()),nonzero=int(relevant[key].fillna(0).ne(0).sum())))
 pd.DataFrame(coverage).to_csv(O/'raw_field_coverage.csv',index=False)
 pd.DataFrame([dict(season=s,field=k,status=v,rows=n) for (s,k,v),n in sorted(inventory.items())]).to_csv(O/'all_metric_inventory.csv',index=False)
 (O/'shot_field_inventory.json').write_text(json.dumps(shotkeys,indent=2)+'\n')
 (O/'extraction_summary.json').write_text(json.dumps(dict(matches=len(sources),active_source_rows=len(frame),source_hashes_verified=True,missing_policy='Absent or valueless metrics remain unknown, never zero'),indent=2)+'\n')
 print('DONE',len(sources),len(frame))
if __name__=='__main__':run()
