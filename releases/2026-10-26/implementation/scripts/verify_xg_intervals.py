"""Independently reconcile every new rate/change against archived payloads."""
import sys,json,lzma
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json
D=R/'datasets/fpl_common_training_v4';P=R/'reports/xg_adaptation_2026_10_26'
def main():
    sources=json.load(open(D/'xg_sources.json'));payload={}
    for source in sources:
        if source['valid']:payload[(source['season'],source['round'])]={int(e['code']):e for e in json.load(lzma.open(R/source['file'],'rt'))['elements']}
    status=pd.read_csv(D/'xg_qualification.csv.gz').set_index(['season','round','code']);known=set(status[status.qualified].index);features=pd.read_pickle(D/'xg_features.pkl');checks=negative=0
    def source(s,g,code):
        if (s,g,code) not in known:return None
        e=payload[(s,g)][code];return (float(e['expected_goals']),float(e['expected_assists']),float(e['minutes']))
    def check(actual,expected):
        nonlocal checks
        if expected is None:assert pd.isna(actual)
        else:np.testing.assert_allclose(actual,expected,atol=1e-5,rtol=1e-7,equal_nan=True)
        checks+=1
    for r in features.itertuples():
        own=source(r.season,r.round,r.code);prior=source(r.season,1,r.code);cur=own
        if r.round==1 and own:cur=(0.,0.,0.)
        for index,kind in enumerate(['xg','xa']):
            check(getattr(r,kind+'_current_per90'),90*cur[index]/cur[2] if cur and cur[2]>0 else None)
            check(getattr(r,kind+'_previous_per90'),90*prior[index]/prior[2] if prior and prior[2]>0 else None)
        for w in [3,10]:
            g0=max(1,r.round-w);old=source(r.season,g0,r.code)
            if g0==1 and old:old=(0.,0.,0.)
            valid=cur is not None and old is not None and cur[2]>=old[2]
            for index,kind in enumerate(['xg','xa']):
                delta=cur[index]-old[index] if valid else None
                check(getattr(r,f'{kind}_reported_change_{w}'),delta)
                check(getattr(r,f'{kind}_change_per90_{w}'),90*delta/(cur[2]-old[2]) if valid and cur[2]>old[2] else None)
                if delta is not None and delta<0:negative+=1
    atomic_json(P/'interval_verification.json',dict(passed=True,rate_or_change_checks=checks,negative_reported_deltas_preserved=negative,all_zero_exposure_rates_missing=True,no_end_season_match_values_used=True,files={str(p.relative_to(R)):sha(p) for p in [Path(__file__),D/'xg_features.pkl',D/'xg_qualification.csv.gz',D/'xg_sources.json']}));print('XG INTERVALS VERIFIED',checks,negative,flush=True)
if __name__=='__main__':main()
