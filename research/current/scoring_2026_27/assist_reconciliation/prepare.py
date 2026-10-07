"""Freeze label-free goal episodes and a new fixture-level evaluation plan."""
from pathlib import Path
import argparse,hashlib,json
import pandas as pd
import pyarrow.parquet as pq
P=Path(__file__).resolve().parent;S=P.parent;KEY=['season','fixture','code']

def save(df,name):df.to_csv(P/name,index=False,compression={'method':'gzip','mtime':0} if name.endswith('.gz') else None)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,required=True);args=parser.parse_args()
 digest=hashlib.sha256(args.archive.read_bytes()).hexdigest()
 if digest!='a69184e1c0d35ed39e1146b748f0ff3b649750bb1d52624286406e0cacd4b6f2':raise ValueError('Event archive changed')
 meta=pd.read_csv(S/'remaining_ledger/player_matches.csv.gz',usecols=KEY+['name','date','home','away','match_id','player_id','own_team_goals'],low_memory=False)
 source=pd.read_csv(S/'delta_input_audit/inputs/archive_projection.csv.gz',low_memory=False)
 participants=meta[KEY+['name','date','home','away','match_id','player_id','own_team_goals']].merge(source[KEY+['team_id']],on=KEY,validate='one_to_one')
 save(participants,'inputs/participants.csv.gz')
 fixtures=participants[['season','fixture','date','home','away','match_id']].drop_duplicates()
 save(fixtures,'inputs/fixtures.csv')
 # This selection reads no FPL assists, expected labels or engine predictions.
 used=[]
 for f in [S/'bps_recovery/inputs/primary_controls.csv.gz',S/'delta_input_audit/control_plan.csv',S/'delta_input_audit/inputs/targeted_primary_controls.csv']:
  used.append(pd.read_csv(f,low_memory=False)[['season','fixture']])
 cases=pd.DataFrame(json.loads((S/'assist_rules/inputs/cases.json').read_text()));used.append(cases[['season','fixture']])
 used=pd.MultiIndex.from_frame(pd.concat(used).drop_duplicates())
 sides=participants[participants.season.eq('2025-26')&participants.own_team_goals.eq(1)&participants.date.ge('2026-01-01')&participants.team_id.notna()][['season','fixture','date','home','away','match_id','team_id']].drop_duplicates()
 sides=sides[~pd.MultiIndex.from_frame(sides[['season','fixture']]).isin(used)].sort_values(['date','fixture','team_id']).head(40)
 if len(sides)!=40:raise ValueError('Insufficient new control teams')
 save(sides,'validation_plan.csv')
 (P/'validation_protocol.json').write_text(json.dumps(dict(selection='First 40 one-goal team/matches in date/fixture/team order from 2026-01-01 in 2025/26; exclude prior assist development and primary/delta controls. No assist outcomes read for selection.',unit='One goal by that team, so official FPL match assists uniquely identify its recipient or no recipient.',freeze='Freeze engine.py, rules.py and protocol SHA256 and write predictions before reading expected FPL assists.',acceptance='Zero incorrect resolved goal decisions. Unresolved decisions are reported separately, never counted correct. Any failed route is withheld from historical automatic approval; no tuning on these labels.',limits='Previously stored official FPL snapshots; new evaluation split, not fresh observations or independent Opta-provider validation. Rare routes may be absent; unit/development tests are not independent validation.'),indent=2)+'\n')
 events=pq.read_table(args.archive,filters=[('season','in',[f'{y}-{y+1}' for y in range(2019,2026)])]).to_pandas()
 events=events[events.match_id.isin(fixtures.match_id.dropna())].copy()
 if events.duplicated(['match_id','event_id']).any():raise ValueError('Duplicate event identity')
 events['clock']=events.minute*60+events.second
 goals=events[events.type_id.eq(16)].merge(fixtures[fixtures.match_id.notna()],on='match_id',suffixes=('_archive',''),validate='many_to_one')
 chunks=[];match_groups=events.groupby('match_id',sort=False)
 for mid,g in goals.groupby('match_id',sort=True):
  match=match_groups.get_group(mid)
  for goal in g.sort_values(['period_id','clock','event_id']).itertuples():
   q=json.loads(goal.qualifier_json) if goal.qualifier_json else {}
   window=600 if ('9' in q or '26' in q) else 60
   episode=match[match.period_id.eq(goal.period_id)&match.clock.between(goal.clock-window,goal.clock)].copy()
   episode['goal_event_id']=int(goal.event_id);chunks.append(episode)
 episode=pd.concat(chunks,ignore_index=True).sort_values(['match_id','goal_event_id','clock','event_id'])
 save(episode,'inputs/goal_episodes.csv.gz');save(goals,'inputs/goals.csv.gz')
 (P/'inputs/source.json').write_text(json.dumps(dict(archive_sha256=digest,goals=len(goals),episode_rows=len(episode),source_url='https://github.com/peteowen1/pannadata/releases/tag/opta-latest',window='60 seconds for open play; 600 seconds for explicit penalty/direct free-kick. Long/ambiguous causal chains abstain.'),indent=2)+'\n')
 print(dict(goals=len(goals),episodes=len(episode),validation_teams=len(sides)))
if __name__=='__main__':main()
