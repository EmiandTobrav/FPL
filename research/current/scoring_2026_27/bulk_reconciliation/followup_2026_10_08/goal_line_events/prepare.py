"""Extract small frozen source inventories; raw archives are optional for replay."""
from pathlib import Path
import gzip
import hashlib
import json
import sys
import pandas as pd

P = Path(__file__).resolve().parent
B = P.parent.parent
R = B.parent.parent
K = ['season', 'fixture', 'code']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(frame, path):
    path.write_bytes(gzip.compress(frame.to_csv(index=False).encode(), mtime=0))

def main():
    import pyarrow.parquet as pq
    raw_events = Path(sys.argv[1])
    raw_players = Path(sys.argv[2])
    assert digest(raw_events) == 'a69184e1c0d35ed39e1146b748f0ff3b649750bb1d52624286406e0cacd4b6f2'
    assert digest(raw_players) == '2765b1771493c917ce7c544b01cf3a151e159a818abb889c7fcbd746353eaead'
    inp = P / 'inputs'
    inp.mkdir(exist_ok=True)
    (inp / 'parent_CURRENT.json').write_bytes((B / 'CURRENT.json').read_bytes())
    seasons = [f'{y}-{y+1}' for y in range(2019, 2026)]
    events = pq.read_table(raw_events, filters=[('season', 'in', seasons), ('type_id', '=', 10)],
                          columns=['match_id', 'event_id', 'player_id', 'team_id', 'period_id',
                                   'minute', 'second', 'type_id', 'qualifier_json']).to_pandas()
    assert not events.duplicated(['match_id', 'event_id']).any()
    save(events.sort_values(['match_id', 'event_id']), inp / 'events.csv.gz')
    players = pq.read_table(raw_players, filters=[('season', 'in', seasons), ('competition', '=', 'EPL')],
                           columns=['match_id', 'match_date', 'player_id', 'team_id', 'team_name',
                                    'team_position', 'season', 'minsPlayed', 'outfielderBlock',
                                    'clearanceOffLine']).to_pandas()
    assert not players.duplicated(['match_id', 'player_id']).any()
    save(players.sort_values(['match_id', 'player_id']), inp / 'players.csv.gz')
    projection = R / 'scoring_2026_27/delta_input_audit/inputs/archive_projection.csv.gz'
    native = R / 'training_dataset/scoring/results/historical_inventory.csv.xz'
    totals = P.parent / 'season_conservation/inputs/full_team_totals.csv'
    files = [projection, native, totals, P / 'protocol.json', Path(__file__), inp / 'events.csv.gz',
             inp / 'players.csv.gz', inp / 'parent_CURRENT.json']
    manifest = {'source_url': 'https://github.com/peteowen1/pannadata/releases/tag/opta-latest',
                'raw_archives': {raw_events.name: digest(raw_events), raw_players.name: digest(raw_players)},
                'files': {str(f.relative_to(R)): digest(f) for f in files}}
    (inp / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print({'events': len(events), 'source_roster_rows': len(players)})

if __name__ == '__main__':
    main()
