"""Extract clock evidence from the already pinned public event archive.

Usage: python prepare_inputs.py /path/to/events_EPL.parquet
Requires pyarrow only for extraction; committed extracts rebuild offline.
"""
from pathlib import Path
import hashlib
import json
import sys
import pandas as pd
import pyarrow.parquet as pq

P=Path(__file__).resolve().parent
S=P.parent
EXPECTED='a69184e1c0d35ed39e1146b748f0ff3b649750bb1d52624286406e0cacd4b6f2'
TYPES=[17,18,19,20,21,30,32,34,43,76,79,84]


def main(source):
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    if digest!=EXPECTED: raise ValueError('Unqualified source revision')
    path=S/'resolution_priority/minute_conflicts.csv.gz'
    targets=pd.read_csv(path)
    targets=targets[~targets.minutes_component_invariant & ~targets.participation_conflict]
    inputs=[path,*sorted((S/'bps_recovery/inputs').glob('counts-*.csv.gz'))]
    archive=pd.concat(pd.read_csv(p) for p in inputs[1:])
    targets=targets.merge(archive[['season','fixture','code','match_id','player_id','team_id','minsPlayed']],
                          on=['season','fixture','code'],validate='one_to_one')
    events=pq.read_table(source,filters=[('type_id','in',TYPES),('match_id','in',targets.match_id.dropna().tolist())]).to_pandas()
    (P/'inputs').mkdir(exist_ok=True)
    targets.to_csv(P/'inputs/targets.csv',index=False)
    events.to_csv(P/'inputs/clock_events.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    provenance=dict(source_url='https://github.com/peteowen1/pannadata/releases/tag/opta-latest',source_file='events_EPL.parquet',
        source_sha256=digest,extract_types=TYPES,rows=len(events),targets=len(targets),
        input_sha256={str(p.relative_to(S.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        schema_url='https://github.com/andrewRowlinson/optasoccer/blob/825cadb56c9c976a8c34c9d5da26d6e37c6ff239/optasoccer/metadata.py',
        schema_sha256='e0400475f9fc07644e835402fc29d32385858c20801ebb2011fffcad098323d0',
        schema_authority='Published parser implementation, not provider-certified. Lineup slots and position arrays cross-validated.',
        events={'18':'player_off','19':'player_on','34':'team_set_up','30':'end','32':'start'},
        qualifiers={'30':'lineup_involved','44':'player_position','131':'team_player_formation','32':'second_yellow','33':'red_card'},
        rule_source='https://www.premierleague.com/en/news/4661030',rule_accessed='2026-10-07',
        rule_paraphrase='FPL counts completed regulation minutes; exiting between 59:00 and 59:59 does not meet the 60-minute threshold.',
        bps_rule_source='https://www.premierleague.com/en/news/4661029',
        bps_rule_limitation='Published 1-60 versus over-60 table does not settle conversion of fractional match-clock duration to BPS minutes. Abstain for 60:01-60:59.',
        adjudication='Both components discharged only for validated continuous starters with paired exit timestamps corroborating FPL completed minutes and invariant BPS across whole-minute/clock readings.')
    (P/'inputs/provenance.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')


if __name__=='__main__': main(Path(sys.argv[1]))
