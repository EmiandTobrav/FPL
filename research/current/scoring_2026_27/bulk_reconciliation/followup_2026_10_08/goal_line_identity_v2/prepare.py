"""Freeze actual fixture metadata; reuse the already pinned block-event archives."""
from pathlib import Path
import gzip, hashlib, json, sys
import pandas as pd
P=Path(__file__).resolve().parent;B=P.parent.parent;R=B.parent.parent
K=['season','fixture','code']
def digest(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()
def main():
    import pyarrow.parquet as pq
    raw=Path(sys.argv[1])
    expected='9dcdffe83ae68395b299c99bb867e644140a43af14d28ae1a90861cf343d208f'
    assert digest(raw)==expected, 'Source fixture archive changed'
    frame=pq.read_table(raw,filters=[('competition','=','EPL'),('season','in',[f'{y}-{y+1}' for y in range(2019,2026)])]).to_pandas()
    assert not frame.match_id.duplicated().any()
    fields=['match_id','match_date','match_status','home_team','away_team','home_team_id','away_team_id','home_score','away_score','season']
    path=P/'inputs/fixtures.csv.gz'
    payload=gzip.compress(frame[fields].sort_values('match_id').to_csv(index=False).encode(),mtime=0)
    if path.exists(): assert path.read_bytes()==payload
    path.write_bytes(payload)
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text())
    source=P.parent/'goal_line_events'
    files=[P/'protocol.json',Path(__file__),path,P/'inputs/parent_CURRENT.json',
      source/'predict.py',source/'inputs/events.csv.gz',source/'inputs/players.csv.gz',
      P.parent/'season_conservation/inputs/full_team_totals.csv',
      R/'scoring_2026_27/delta_input_audit/inputs/archive_projection.csv.gz',
      R/'training_dataset/scoring/results/historical_inventory.csv.xz',
      R/'scoring_2026_27/keeper_recovery/recover.py']
    files.extend(B/parent[k] for k in ['requirements','player_match_readiness','match_readiness'])
    manifest={'raw_fixtures_sha256':expected,'raw_fixture_source':'https://github.com/peteowen1/pannadata/releases/tag/opta-latest',
      'reused_raw_archives':json.loads((source/'inputs/manifest.json').read_text())['raw_archives'],
      'files':{str(f.relative_to(R)):digest(f) for f in files}}
    m=P/'inputs/manifest.json';payload=(json.dumps(manifest,indent=2)+'\n').encode()
    if m.exists(): assert m.read_bytes()==payload
    m.write_bytes(payload)
    print({'source_fixtures':len(frame),'reused_events_and_rosters':True})
if __name__=='__main__':main()
