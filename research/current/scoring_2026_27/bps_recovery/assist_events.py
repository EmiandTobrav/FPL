"""Freeze event windows for the six existing official decisions, not new labels."""
from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq
from prepare_sources import verify
P=Path(__file__).resolve().parent

def main():
    source=verify('events_EPL.parquet')
    decisions=pd.read_csv(P.parent/'acquisition_followup/assist_decisions.csv')
    counts=pd.read_csv(P/'inputs/counts-2024-25.csv.gz')
    matches=decisions.merge(counts[['season','fixture','code','match_id']],on=['season','fixture','code'],validate='one_to_one')
    events=pq.read_table(source,filters=[('match_id','in',matches.match_id.unique().tolist())]).to_pandas()
    events.to_csv(P/'inputs/official_assist_match_events.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    windows=[];summary=[]
    for r in matches.to_dict('records'):
        scorer=counts[counts.fixture.eq(r['fixture'])&counts.element.eq(r['goalscorer_element'])]
        assert len(scorer)==1 and scorer.iloc[0].mapping_status=='matched'
        goal=events[events.match_id.eq(r['match_id'])&events.player_id.eq(scorer.iloc[0].player_id)&events.type_id.eq(16)]
        assert len(goal)==1, (r['name'],len(goal))
        g=goal.iloc[0];t=g.minute*60+g.second
        seconds=events.minute*60+events.second
        window=events[events.match_id.eq(r['match_id'])&events.period_id.eq(g.period_id)&seconds.between(t-120,t+2)].copy()
        window['decision_code']=r['code'];window['decision_name']=r['name']
        window=window.sort_values(['minute','second','event_id'])
        windows.append(window)
        summary.append(dict(season=r['season'],fixture=r['fixture'],code=r['code'],name=r['name'],match_id=r['match_id'],goal_event_id=int(g.event_id),goalscorer=scorer.iloc[0]['name'],minute=g.minute,second=g.second,window_events=len(window),decision_source=r['source_url'],status='official_decision_control_only_not_an_automatic_rule'))
    pd.concat(windows,ignore_index=True).to_csv(P/'inputs/official_assist_event_windows.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    pd.DataFrame(summary).to_csv(P/'official_assist_event_index.csv',index=False)
    print(pd.DataFrame(summary)[['name','goalscorer','minute','second','window_events']].to_string(index=False))
if __name__=='__main__':main()
