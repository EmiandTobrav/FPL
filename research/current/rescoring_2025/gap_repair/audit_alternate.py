"""Optional alternate RDS check; requires rdata, pandas and internet."""
from pathlib import Path
import hashlib
import urllib.request
import pandas as pd
import rdata

P = Path(__file__).resolve().parent
URL = 'https://github.com/JaseZiv/worldfootballR_data/releases/download/fb_advanced_match_stats/ENG_M_1st_misc_player_advanced_match_stats.rds'
EXPECTED = '9c8b96b0bf1166c51cd996b0b16eaebfaa633c0981d028feca71d6ea04e738c2'

def run():
    path = P / 'raw/misc.rds'
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        urllib.request.urlretrieve(URL, path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED
    alternate = rdata.read_rds(path)
    original = pd.read_csv(P.parent / 'historical_fbref/raw/misc.csv')
    keys = ['Season_End_Year', 'MatchURL', 'Player_Href']
    joined = original[keys + ['Recov']].merge(alternate[keys + ['Recov']], on=keys, how='outer', validate='one_to_one', indicator=True, suffixes=('_csv', '_rds'))
    assert len(joined) == 81328 and (joined['_merge'] == 'both').all()
    a, b = joined.Recov_csv, joined.Recov_rds
    assert ((a == b) | (a.isna() & b.isna())).all()
    print('81328 matched rows; zero recovery differences including missing values')

if __name__ == '__main__':
    run()
