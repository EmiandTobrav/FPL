"""Refresh deduplicated priorities from the published cumulative snapshot."""
from pathlib import Path
import pandas as pd,json,gzip
P=Path(__file__).resolve().parent;S=P.parent/'followup_2026_10_08';K=['season','fixture','code']
def save(d,n):(P/n).write_bytes(gzip.compress(d.to_csv(index=False).encode(),mtime=0) if n.endswith('.gz') else d.to_csv(index=False).encode())
def main():
 current=json.loads((S.parent/'CURRENT.json').read_text());r=pd.read_csv(S.parent/current['requirements'],low_memory=False);pending=r[r.is_open];pcounts=pending.groupby(K).size().to_dict();mcounts=pending.groupby(K[:2]).size().to_dict();q=r[r.needs_external_quality_review];save(q.groupby(['field','season']).agg(fields=('code','size'),player_matches=('code','size')).reset_index(),'quality_groups.csv')
 # One field/season row is a review group, not a queue of individual manual jobs.
 quality={'field_season_groups':len(q.groupby(['field','season'])),'external_quality_fields':len(q),'quality_player_matches':len(q[K].drop_duplicates()),'open_or_quality_player_matches':len(r[r.is_open|r.needs_external_quality_review][K].drop_duplicates())};(P/'quality_summary.json').write_text(json.dumps(quality,indent=2)+'\n')
 totals=pd.read_csv(S/'assist_touch_bounds/results/player_match_totals.csv.gz',dtype={'unresolved_goal_ids':'string'},low_memory=False);a=pending[pending.field.eq('assists_2026_27')][K].merge(totals,on=K,validate='one_to_one');groups=pd.read_csv(P/'goal_group_classification.csv.gz');mapping=groups.set_index(['match_id','event_id']).group.to_dict();rows=[];key_goals={}
 for x in a.itertuples():
  key=(x.season,x.fixture,x.code);ids=[] if pd.isna(x.unresolved_goal_ids) else [int(v) for v in str(x.unresolved_goal_ids).split('|') if v]
  key_goals[key]={(x.match_id,e) for e in ids}
  for e in ids:rows.append(dict(season=x.season,fixture=x.fixture,code=x.code,match_id=x.match_id,event_id=e,group=mapping.get((x.match_id,e),'unclassified'),sole_blocker=len(ids)==1))
 deps=pd.DataFrame(rows);save(deps,'assist_dependencies.csv.gz');out=[]
 for group,g in deps.groupby('group'):
  goalset=set(zip(g.match_id,g.event_id));resolved={k for k,gs in key_goals.items() if gs and gs<=goalset};newcomplete={k for k in resolved if pcounts[k]==1};closed_per_match={}
  for key in resolved:closed_per_match[key[:2]]=closed_per_match.get(key[:2],0)+1
  out.append(dict(group=group,goals=len(goalset),open_assist_fields_touched=len(g[K].drop_duplicates()),conditional_resolved_fields=len(resolved),conditional_complete_player_matches=len(newcomplete),conditional_complete_matches=sum(v==mcounts[k] for k,v in closed_per_match.items())))
 save(pd.DataFrame(out).sort_values('conditional_resolved_fields',ascending=False),'assist_groups.csv');save(a[a.reason.eq('goal_coverage_or_identity_gap')][K+['name','match_id','team_id','reason']],'assist_inventory_gaps.csv.gz')
 summary={'open_assists':len(a),'with_goal_dependencies':len(deps[K].drop_duplicates()),'inventory_gaps':int(a.reason.eq('goal_coverage_or_identity_gap').sum()),'unclassified_dependencies':int(deps.group.eq('unclassified').sum()),'warning':'Conditional group ceilings, not forecasts or newly resolved values. Touched counts overlap; never sum them. Complete-match gains also require all other open fields closed.'};assert summary['with_goal_dependencies']+summary['inventory_gaps']==len(a);assert not summary['unclassified_dependencies'];(P/'assist_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(quality));print(pd.DataFrame(out).to_string(index=False))
if __name__=='__main__':main()
