"""Project hash-pinned player stats. Does not download or modify source archives."""
from pathlib import Path
import hashlib
import pyarrow.parquet as pq
from audit import FIELDS,ASSIST_FIELDS
P=Path(__file__).resolve().parent
EXPECTED={
'opta_player_stats.parquet':'2765b1771493c917ce7c544b01cf3a151e159a818abb889c7fcbd746353eaead',
'opta_fixtures.parquet':'9dcdffe83ae68395b299c99bb867e644140a43af14d28ae1a90861cf343d208f',
'events_EPL.parquet':'a69184e1c0d35ed39e1146b748f0ff3b649750bb1d52624286406e0cacd4b6f2'}

def verify(name):
    path=P.parent/'keeper_recovery/raw'/name
    with path.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    if digest!=EXPECTED[name]:raise ValueError(f'Source changed: {name}: {digest}')
    return path

def main():
    path=verify('opta_player_stats.parquet');verify('opta_fixtures.parquet')
    meta=['match_id','match_date','player_id','player_name','first_name','last_name','team_id','team_name','team_position','position','season']
    cols=list(dict.fromkeys(meta+list(FIELDS)+ASSIST_FIELDS))
    frame=pq.read_table(path,columns=cols,filters=[('competition','=','EPL'),('season','in',[f'{y}-{y+1}' for y in range(2019,2027)]),('minsPlayed','>',0)]).to_pandas()
    assert not frame.duplicated(['match_id','player_id']).any()
    frame.to_parquet(P/'active_stats.parquet',index=False)
    print(len(frame))
if __name__=='__main__':main()
