"""Freeze raw participant counters for aggregate conservation tests."""
from pathlib import Path
import hashlib,json
import pandas as pd
import pyarrow.parquet as pq
P=Path(__file__).resolve().parent;S=P.parent
KEY=['season','fixture','code']
FIELDS=['totalTackle','wonTackle','wasFouled','ontargetScoringAtt','clearanceOffLine','totalScoringAtt','saves','goals','ownGoals','totalClearance','outfielderBlock','interception']
def main():
 path=Path('/private/tmp/fpl_opta_player_stats.parquet')
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 if digest!='2765b1771493c917ce7c544b01cf3a151e159a818abb889c7fcbd746353eaead':raise ValueError('Unpinned players')
 d=pq.read_table(path,columns=['match_id','player_id','team_id','team_position','minsPlayed']+FIELDS,filters=[('season','in',[f'{y}-{y+1}' for y in range(2019,2025)])]).to_pandas()
 plan=pd.read_csv(P/'collection_plan.csv');d=d[d.match_id.isin(plan.match_id.dropna())]
 if d.duplicated(['match_id','player_id']).any():raise ValueError('Ambiguous source player')
 d=d.merge(plan.loc[plan.match_id.notna(),['season','fixture','match_id']],on='match_id',validate='many_to_one')
 d=d.sort_values(['season','fixture','team_id','player_id']);d.to_csv(P/'inputs/source_players.csv.gz',index=False,compression={'method':'gzip','mtime':0})
 fm=pd.concat([pd.read_csv(f,usecols=KEY+['matchstats.headers.tackles']) for f in sorted((S/'data').glob('*/part-*.csv'))],ignore_index=True)
 fm.to_csv(P/'inputs/fotmob_total_tackles.csv.gz',index=False,compression={'method':'gzip','mtime':0})
 source={'player_archive_sha256':digest,'player_archive_url':'https://github.com/peteowen1/pannadata/releases/download/opta-latest/opta_player_stats.parquet','method':'Preserve explicit counts. Empty cells remain empty. Sums of known nonnegative contributions are lower bounds, not imputed player values.'}
 (P/'inputs/source.json').write_text(json.dumps(source,indent=2)+'\n')
 print('source players',len(d),flush=True)
if __name__=='__main__':main()
