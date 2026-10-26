"""Add population-readiness gate to the independently checked V1 mechanics."""
import sys,json,lzma
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import test_xg_adaptation_v2 as config
from scripts import verify_xg_adaptation as verify
import numpy as np,pandas as pd
from model_lab.common import atomic_json,sha
P=config.P;D=config.D

def population():
    sources=json.load(open(D/'xg_sources.json'));q=pd.read_csv(D/'xg_qualification.csv.gz');bad=[]
    for s in sources:
        if not s['valid']:continue
        data=json.load(lzma.open(R/s['file'],'rt'));players=[e for e in data['elements'] if e['element_type'] in [1,2,3,4]];minutes=sum(float(e.get('minutes') or 0) for e in players);positive_xg=sum(float(e.get('expected_goals') or 0)>0 for e in players);positive_xa=sum(float(e.get('expected_assists') or 0)>0 for e in players);ready=minutes==0 or (positive_xg>0 and positive_xa>0);assert ready==s['expected_statistics_populated']
        if not ready:
            z=q[q.season.eq(s['season'])&q['round'].eq(s['round'])];assert not z.qualified.any();bad.append(dict(season=s['season'],round=s['round'],rows=len(z),minutes=minutes))
    d=pd.read_pickle(D/'xg_features.pkl');z=d[d.season.eq('2022-23')&d['round'].eq(16)];cols=json.load(open(D/'schema.json'))['feature_groups']['expected_attack'];assert z[cols].isna().all().all();assert d.loc[d.season.eq('2022-23')&d['round'].eq(19),'xg_reported_change_3'].isna().all();assert d.loc[d.season.eq('2022-23')&d['round'].eq(26),'xg_reported_change_10'].isna().all()
    # A real individual zero remains usable once the family is populated.
    positive=d[d.season.eq('2025-26')&d['round'].gt(1)];assert positive.xg_current_total.eq(0).any() and positive.xg_current_total.gt(0).any()
    atomic_json(P/'population_verification.json',dict(passed=True,unpopulated_families_marked_unknown=True,specific_GW16_and_both_dependent_windows_checked=True,legitimate_individual_zeroes_preserved=True,not_populated_origins=bad,files={str(p.relative_to(R)):sha(p) for p in [Path(__file__),D/'xg_features.pkl',D/'xg_sources.json']}));print('POPULATION QUALIFICATION PASSED',flush=True)

if __name__=='__main__':
    if sys.argv[1]=='dataset':population();verify.dataset()
    elif sys.argv[1]=='predictions':verify.predictions(sys.argv[2])
    elif sys.argv[1]=='preflight':verify.preflight(sys.argv[2])
    elif sys.argv[1]=='intervals':
        from scripts import verify_xg_intervals as intervals
        intervals.D=D;intervals.P=P;intervals.main()
    else:raise ValueError(sys.argv[1])
