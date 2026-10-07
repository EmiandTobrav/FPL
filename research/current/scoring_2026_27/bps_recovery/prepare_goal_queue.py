"""Enumerate source goal events; every entry still requires rule adjudication."""
from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq
from prepare_sources import verify
P=Path(__file__).resolve().parent

def main():
    source=verify('events_EPL.parquet');fixtures_source=verify('opta_fixtures.parquet')
    pop=pd.concat(pd.read_csv(f) for f in sorted((P/'inputs').glob('counts-*.csv.gz')))
    pop=pop[pop.season.ne('2026-27')]
    target=pop[['season','fixture','fixture_code','match_id','date','home','away']].drop_duplicates()
    events=pq.read_table(source,filters=[('type_id','=',16),('season','in',[f'{y}-{y+1}' for y in range(2019,2026)])]).to_pandas().drop(columns=['season'])
    fixtures=pq.read_table(fixtures_source,columns=['match_id','home_score','away_score'],filters=[('competition','=','EPL'),('season','in',[f'{y}-{y+1}' for y in range(2019,2026)])]).to_pandas()
    assert not events.duplicated(['match_id','event_id']).any()
    assert not target[target.match_id.notna()].match_id.duplicated().any()
    target=target.merge(fixtures,on='match_id',how='left',validate='many_to_one')
    target['expected_goals']=pd.to_numeric(target.home_score)+pd.to_numeric(target.away_score)
    counts=events.groupby('match_id').size()
    target['source_goal_events']=target.match_id.map(counts).fillna(0)
    target.loc[target.match_id.isna(),'source_goal_events']=float('nan')
    target['goal_count_matches_score']=target.expected_goals.eq(target.source_goal_events)&target.expected_goals.notna()
    queue=events.merge(target[target.match_id.notna()],on='match_id',validate='many_to_one')
    queue['status']='unadjudicated_goal_not_an_assist_label'
    queue.to_csv(P/'goal_review_queue.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    target.to_csv(P/'goal_match_coverage.csv',index=False)
    result=dict(target_matches=len(target),mapped_matches=int(target.match_id.notna().sum()),missing_matches=int(target.match_id.isna().sum()),goal_events=len(queue),mapped_matches_with_goal_count_equal_score=int(target.goal_count_matches_score.sum()),count_check_proves_event_sequence_completeness=False,new_assist_labels=0)
    (P/'goal_queue_findings.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
