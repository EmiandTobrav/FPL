"""Rebuild only the three new event projections from the pinned raw archive."""
from pathlib import Path
import sys,json,gzip
import pyarrow.parquet as pq
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent/'bps_recovery'))
from prepare_sources import verify

def main():
    cases=json.loads((P/'inputs/cases.json').read_text())
    ids=sorted({r['match_id'] for r in cases if r['cohort']!='six_development_examples'})
    source=verify('events_EPL.parquet')
    events=pq.read_table(source,filters=[('match_id','in',ids)]).to_pandas()
    assert set(events.match_id.unique())==set(ids)
    assert not events.duplicated(['match_id','event_id']).any()
    (P/'inputs/challenge_match_events.csv.gz').write_bytes(gzip.compress(events.to_csv(index=False).encode(),mtime=0))
    print(len(events),len(ids))
if __name__=='__main__':main()
