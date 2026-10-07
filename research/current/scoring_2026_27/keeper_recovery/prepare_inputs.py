"""Download hash-pinned public archives and regenerate compact evidence inputs.

Requires pandas and pyarrow. No authentication, retries or access-control
workarounds. If a mutable release asset has changed, stop on its hash mismatch.
Routine replay uses recover.py and the committed inputs instead.
"""
import hashlib
import json
import urllib.request
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from recover import ROOT, build_targets


def save(frame, name):
    frame.to_csv(ROOT/'inputs'/name,index=False,compression={'method':'gzip','mtime':0})


def main():
    manifest=json.loads((ROOT/'source_manifest.json').read_text())
    raw=ROOT/'raw';raw.mkdir(exist_ok=True)
    (ROOT/'inputs').mkdir(exist_ok=True)
    for asset in manifest['assets']:
        path=raw/asset['name']
        if not path.exists():
            tmp=path.with_suffix(path.suffix+'.tmp')
            with urllib.request.urlopen(asset['url'],timeout=45) as response,tmp.open('wb') as out:
                while chunk:=response.read(1024*1024):out.write(chunk)
            if hashlib.sha256(tmp.read_bytes()).hexdigest()!=asset['sha256']:
                raise ValueError(f'External release changed: {asset["name"]}')
            tmp.replace(path)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=asset['sha256']:
            raise ValueError(f'Archive hash mismatch: {path.name}')
    seasons=[f'{y}-{y+1}' for y in range(2019,2027)]
    filters=[('competition','=','EPL'),('season','in',seasons)]
    sc=['match_id','season','player_id','player_name','first_name','last_name',
        'team_id','team_position','position','minsPlayed','saves','bigChanceSaves',
        'totalScoringAtt','bigChanceMissed','bigChanceScored']
    s=pq.read_table(raw/'opta_player_stats.parquet',columns=sc,filters=filters).to_pandas()
    f=pq.read_table(raw/'opta_fixtures.parquet',filters=filters).to_pandas()
    targets,matches=build_targets(s,f)
    save(targets,'targets.csv.gz')
    matches.to_csv(ROOT/'fixture_mapping.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    totals=s.groupby(['season','match_id','team_id']).agg(
        record_count=('player_id','size'),totalScoringAtt=('totalScoringAtt','sum'),
        bigChanceMissed=('bigChanceMissed','sum'),bigChanceScored=('bigChanceScored','sum')).reset_index()
    save(totals,'player_stats.csv.gz')
    hc=['match_id','event_id','player_name','team_id','minute','second','type_id',
        'big_chance','is_blocked','is_own_goal','season']
    h=pq.read_table(raw/'opta_shot_events.parquet',columns=hc,filters=filters).to_pandas()
    for season,g in h.groupby('season'):save(g,f'shots-{season}.csv.gz')
    ec=['match_id','event_id','type_id','player_id','player_name','team_id','minute',
        'second','period_id','qualifier_json','season']
    e=pq.read_table(raw/'events_EPL.parquet',columns=ec,
        filters=filters+[('type_id','in',[10,13,14,15,16])]).to_pandas()
    def prune(q):
        d=json.loads(q)
        # Preserve full BC evidence. Other rows only need the two exclusion
        # qualifiers; these are projections of complete payloads, not defaults.
        return json.dumps(d if '214' in d else {k:v for k,v in d.items() if k in ['82','94']},
                          ensure_ascii=False,separators=(',',':'))
    e.qualifier_json=e.qualifier_json.map(prune)
    for season,g in e.groupby('season'):save(g,f'events-{season}.csv.gz')
    current=s[s.season.eq('2026-2027')&s.position.eq('Goalkeeper')&s.minsPlayed.gt(0)]
    save(current[['match_id','player_id','player_name','team_id','saves','bigChanceSaves']],
         'current_validation_targets.csv.gz')
    print(f'Prepared {len(targets)} targets and {len(h)} shots')


if __name__=='__main__':main()
