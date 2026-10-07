"""Freeze event-counter diagnostics; absence of a marker never certifies zero."""
from pathlib import Path
import hashlib,json,argparse
import pandas as pd
import pyarrow.parquet as pq
P=Path(__file__).resolve().parent

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,default=P.parent/'keeper_recovery/raw/events_EPL.parquet');args=parser.parse_args()
 raw=args.archive
 digest=hashlib.sha256(raw.read_bytes()).hexdigest()
 if digest!='a69184e1c0d35ed39e1146b748f0ff3b649750bb1d52624286406e0cacd4b6f2':raise ValueError('Event source drift')
 e=pq.read_table(raw,columns=['match_id','event_id','type_id','player_id','outcome','qualifier_json'],filters=[('season','in',[f'{y}-{y+1}' for y in range(2019,2027)]),('type_id','in',[7,10,12,45])]).to_pandas()
 if e.duplicated(['match_id','event_id']).any():raise ValueError('Duplicate event')
 e['line_marker']=e.type_id.isin([10,12])&e.qualifier_json.map(lambda s:'14' in json.loads(s) if isinstance(s,str) and s.strip() else False)
 e['tackle']=e.type_id.eq(7);e['won']=e.tackle&e.outcome.eq(1);e['lost']=e.tackle&e.outcome.eq(0)
 e['challenge']=e.type_id.eq(45)
 counts=e.groupby(['match_id','player_id']).agg(event_total_tackle=('tackle','sum'),event_won_tackle=('won','sum'),event_lost_tackle=('lost','sum'),event_challenge_lost=('challenge','sum'),event_line_markers=('line_marker','sum')).reset_index()
 counts.to_csv(P/'inputs/event_counts.csv.gz',index=False,compression={'method':'gzip','mtime':0})
 e[e.line_marker].to_csv(P/'inputs/line_marker_events.csv.gz',index=False,compression={'method':'gzip','mtime':0})
 (P/'inputs/event_source.json').write_text(json.dumps(dict(sha256=digest,types=[7,10,12,45],line_marker_candidate=14,role='Diagnostics only; published parser mapping is not provider-certified. No new absent-marker zeros.',source='https://github.com/andrewRowlinson/optasoccer/blob/825cadb56c9c976a8c34c9d5da26d6e37c6ff239/optasoccer/metadata.py'),indent=2)+'\n')
 print(dict(events=len(e),player_matches=len(counts),line_markers=int(e.line_marker.sum())))
if __name__=='__main__':main()
