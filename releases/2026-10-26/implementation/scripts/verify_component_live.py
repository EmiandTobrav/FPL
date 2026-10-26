"""Independent promotion gates for the operational component release."""
import copy,sys,json
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab import component_forecaster as c
from model_lab.common import sha,atomic_json,verify_files
P=c.P

def verify(manager=True):
    info=c.read(P/'prepared.json');seal=c.read(P/'forecast_seal.json');verify_files(R,seal['files']);verify_files(P,info['files']);cols=c.read(c.D/'schema.json')['features'];assert len(cols)==325
    d=c.load(P/'current.pkl');out=c.load(P/'live_features.pkl');xp=out[[f'xp_{j}' for j in range(8)]].to_numpy(float);assert len(out)==669 and np.isfinite(xp).all() and not out.code.duplicated().any()
    assert not d.duplicated(c.common.KEY).any();assert set(d.loc[d.train_eligible,'round'])==set(range(1,8));assert d.loc[d['round'].eq(9),'target_points_1'].isna().all()
    time=pd.read_csv(P/'timing.csv.gz');origin=pd.to_datetime(time.forecast_at,utc=True,format="mixed")
    for name in ['latest_history','latest_workload','latest_international','source_time','calendar_time']:
        latest=pd.to_datetime(time[name],utc=True,errors='coerce',format='mixed');assert (latest.isna()|latest.lt(origin)).all(),name
    assert (pd.to_datetime(time.source_time,utc=True,format="mixed")<origin).all();assert (origin-pd.to_datetime(time.source_time,utc=True,format="mixed")).le(pd.Timedelta(hours=24)).all()
    native=c.load(P/'native_current.pkl');assert len(native)==4242 and native.native_minutes.eq(0).sum()==2084 and native['round'].max()==7
    qualified=pd.read_pickle(c.D/'training.pkl');assert not qualified.loc[qualified.train_eligible,'target_history_eligible'].eq(False).any()
    base=[]
    for g in [1,5,9]:
        for a in c.read(P/f'base_audit_gw{g:02d}.json'):
            at=c.utc(a['cutoff']);assert c.utc(a['max_origin'])<at and c.utc(a['max_label'])<at;bundle=c.load(R/a['file']);assert bundle['columns']==cols;params=bundle['models'][0].get_params()
            assert all(params[k]==v for k,v in dict(iterations=150,depth=5,learning_rate=.05,l2_leaf_reg=5,random_seed=20261025,thread_count=1).items());assert bundle['name']=='component';base.append(a)
    assert all(a['current_rows']>0 for a in base if a['round'] in [5,9])
    heads=c.read(P/'head_audit.json');assert len(heads)==8
    for a in heads:
        at=c.utc(a['cutoff']);assert c.utc(a['max_origin'])<at and c.utc(a['max_label'])<at and c.utc(a['max_h3_label'])<at
    assert all(a['current_rows']>0 for a in heads[:5]);assert heads[0]['current_rows']>heads[-1]['current_rows']
    assert out.loc[~out.can_start_0,'xp_0'].eq(0).all();assert not out.loc[~out.can_start_0,'can_buy'].any()
    departed=out.known_departed;assert out.loc[departed,[f'xp_{j}' for j in range(8)]].eq(0).all().all()
    # A validated fitted bundle must reject changed files, stale information,
    # wrong rounds, naive timestamps and an already passed deadline.
    runtime=c.ComponentForecaster(P);runtime.forecast(dict(season=c.SEASON,round=9,forecast_at=seal['issued_at']))
    for at,g in [(c.utc(seal['issued_at'])+pd.Timedelta(hours=25),9),(c.utc(seal['issued_at']),10),(pd.Timestamp('2026-10-26'),9)]:
        try:runtime.forecast(dict(season=c.SEASON,round=g,forecast_at=at))
        except ValueError:pass
        else:raise AssertionError('Invalid runtime origin accepted')
    smoke=[]
    if manager:
        pool=out.copy();pool['market']=pool.price_tenths;mod,a=c.hard_manager();state=a.engine.initial_state(start_gw=9);hostile=xp.copy();hostile[~pool.can_start_0.to_numpy()]=10000
        choice=copy.deepcopy(a.decide(pool,hostile,state,9)['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()};after,choice=a.engine.apply_decision(state,choice,pool.to_dict('records'),9)
        assert not set(pool.loc[~pool.can_start_0,'pid'])&set(choice['squad']);assert len(a.ledger)<=40
        smoke.append(dict(kind='opening_hostile_unavailable_forecasts',solver_calls=len(a.ledger),choice=mod.clean(choice)))
        # Force a blocked existing holding onto the current team; it may stay
        # only on the ordinary bench, even when offered 10000 expected points.
        blocked=pool[~pool.can_start_0].iloc[0];same=next(i for i in choice['squad'] if pool.set_index('pid').at[i,'pos']==blocked.pos)
        state=copy.deepcopy(after);state['next_gw']=9;state['owned'][int(blocked.pid)]=state['owned'].pop(int(same));state['ownership_clubs'].pop(int(same),None);state['ownership_clubs'][int(blocked.pid)]=blocked.club
        mod,b=c.hard_manager();second=copy.deepcopy(b.decide(pool,hostile,state,9)['choice']);second['prices']={int(k):v for k,v in second['prices'].items()};b.engine.apply_decision(state,second,pool.to_dict('records'),9)
        assert int(blocked.pid) not in second['starters']+[second['captain'],second['vice']];assert len(b.ledger)<=40
        smoke.append(dict(kind='owned_confirmed_out',blocked_player=blocked['name'],solver_calls=len(b.ledger),choice=mod.clean(second)))
    result=dict(passed=True,checked_at=str(pd.Timestamp.now(tz='UTC')),features=325,players=len(out),blocked_players=int((~out.can_start_0).sum()),departed_players=int(departed.sum()),qualified_native_rows=len(native),genuine_zero_minutes=int(native.native_minutes.eq(0).sum()),new_base_fits=len(base),current_season_base_rows=[dict(round=a['round'],horizon=a['horizon'],rows=a['current_rows']) for a in base],current_season_teacher_rows=[a['current_rows'] for a in heads],all_clock_checks_passed=True,unreleased_round8_excluded=True,recipe_unchanged=True,source_expiry_and_wrong_origin_rejected=True,hard_manager_checked=manager,smoke=smoke,files={n:sha(P/n) for n in ['forecasts.csv','forecast_seal.json','head_audit.json','prepared.json']})
    atomic_json(P/'verification.json',result);print('READINESS PASSED',json.dumps({k:v for k,v in result.items() if k not in ['smoke','files']}),flush=True)
if __name__=='__main__':verify('--no-manager' not in sys.argv)
