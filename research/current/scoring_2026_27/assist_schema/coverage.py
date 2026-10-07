"""Survey explicit marker presence; never label a missing subtype as non-pass."""
from pathlib import Path
import sys,json,gzip
import pandas as pd
import pyarrow.parquet as pq
P=Path(__file__).resolve().parent;S=P.parent
sys.path.insert(0,str(S/'bps_recovery'))
from prepare_sources import verify

def main():
    source=verify('events_EPL.parquet')
    frame=pq.read_table(source,columns=['match_id','season','event_id','player_id','type_id','qualifier_json'],filters=[('season','in',[f'{y}-{y+1}' for y in range(2019,2026)]),('type_id','in',[7,8,16])]).to_pandas()
    allowed=pd.read_csv(S/'bps_recovery/goal_match_coverage.csv').match_id.dropna()
    frame=frame[frame.match_id.isin(allowed)].copy()
    frame['q']=frame.qualifier_json.map(lambda x:json.loads(x) if pd.notna(x) else {})
    for key in ['328','383','384','385','154','280','281']:frame['q'+key]=frame.q.map(lambda q:key in q)
    frame['subtype_count']=frame[['q383','q384','q385']].sum(axis=1)
    coverage=[]
    for season,g in frame.groupby('season'):
        t=g[g.type_id.isin([7,8])];goals=g[g.type_id.eq(16)]
        coverage.append(dict(season=season,tackles_interceptions=len(t),explicit_control=int(t.q383.sum()),explicit_pass=int(t.q384.sum()),explicit_clearance=int(t.q385.sum()),no_subtype=int(t.subtype_count.eq(0).sum()),conflicting_subtypes=int(t.subtype_count.gt(1).sum()),goal_events=len(goals),goals_first_touch=int(goals.q328.sum()),goals_intentional_assist_marker=int(goals.q154.sum()),goals_fantasy_assister_marker=int(goals.q281.sum())))
    pd.DataFrame(coverage).to_csv(P/'marker_coverage.csv',index=False)
    # Minimal marker ledger allows source-linked goal review without loading
    # the full 310 MB archive. It does not contain new assist decisions.
    goals=frame[frame.type_id.eq(16)].drop(columns=['q','subtype_count'])
    (P/'goal_markers.csv.gz').write_bytes(gzip.compress(goals.to_csv(index=False).encode(),mtime=0))
    subtype=frame[frame.type_id.isin([7,8])]
    findings=dict(rows=len(frame),goal_events=len(goals),first_touch_goals=int(goals.q328.sum()),tackles_interceptions=len(subtype),explicit_pass_subtype=int(subtype.q384.sum()),missing_subtype=int(subtype.subtype_count.eq(0).sum()),conflicting_subtypes=int(subtype.subtype_count.gt(1).sum()),absence_means_non_pass=False,first_touch_marker_alone_proves_assist=False)
    (P/'coverage_findings.json').write_text(json.dumps(findings,indent=2)+'\n')
    print(pd.DataFrame(coverage).to_string(index=False));print(findings)
if __name__=='__main__':main()
