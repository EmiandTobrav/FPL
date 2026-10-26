"""Same selected H5component with a versioned fresh external observation source.

Old runtimes and forecast receipts remain immutable. Source expiry and four-round
model reuse are inherited; switching policy never refreshes a data receipt.
"""
import os
from contextlib import contextmanager
from pathlib import Path
import copy
import numpy as np
import pandas as pd
from model_lab import recent_component_forecaster as recent
from model_lab.common import ROOT as R, read, sha, verify_files, atomic_json
core=recent.core
CONFIG_PATH=R/'reports/component_plan5_activation_2026_10_26/runtime_config.json'
P=Path(os.environ.get('FPL_COMPONENT_RELEASE',str(R/'reports/component_live_2026_10_26_fresh')))
EXTERNAL=R/'datasets/fpl_external_live_2026_10_26'
D=CONFIG_PATH.parent/'training_input'
FIT=CONFIG_PATH.parent/'teachers'
SEASON=recent.SEASON;REFITS=recent.REFITS
MODEL_ID='common_component_h8_recent180_plan5_calendar_v1'
load=core.load;save=core.save;utc=core.utc;common=core.common;projection=core.projection


def configuration():
    config=read(CONFIG_PATH)
    if config['planning_horizon']!=5 or config['forecast_horizon']!=8:
        raise ValueError('Wrong selected manager horizon')
    verify_files(R,config['files'])
    verify_files(EXTERNAL,read(EXTERNAL/'manifest.json')['files'])
    return config


@contextmanager
def binding():
    configuration()
    original_isolated=core.inputs.isolated_module
    def isolated(name,path,register=()):
        if Path(path)==R/'datasets/fpl_all_competitions_context_v1/build_context.py':path=EXTERNAL/'build_context.py'
        return original_isolated(name,path,register)
    names=['P','D','FIT'];saved=[(module,name,getattr(module,name)) for module in [core,recent] for name in names]
    try:
        for module in [core,recent]:module.P=P;module.D=D;module.FIT=FIT
        core.inputs.isolated_module=isolated
        yield
    finally:
        core.inputs.isolated_module=original_isolated
        for module,name,value in saved:setattr(module,name,value)


def prepare():
    with binding():return core.prepare()


def fit_base(g):
    with binding():return core.fit_base(g)


def reuse_base(g):
    with binding():return core.reuse_base(g)


def _fit_heads():
    current=load(P/'current.pkl');info=read(P/'prepared.json');g=info['round']
    if info['previous_release']:
        prior=load(P/'prior_oof.pkl');basecols=common.KEY+['component_p1','component_m1','component_p3','component_m3'];prior=current[current['round'].lt(g)].merge(prior[basecols],on=common.KEY,how='inner',validate='one_to_one');q=recent.pd.concat([prior,load(P/f'base_gw{g:02d}.pkl')],ignore_index=True)
    else:q=recent.pd.concat([load(P/f'base_gw{r:02d}.pkl') for r in [1,5,g]],ignore_index=True)
    assert not q.duplicated(common.KEY).any();save(P/'current_oof.pkl',q)
    past=pd.read_pickle(FIT/'head_data.pkl');teacher=recent.pd.concat([past,q],ignore_index=True);at=q[q['round'].eq(g)].forecast_at.iloc[0]
    complete=teacher[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=teacher[[f'y_at_{j}' for j in range(3)]].max(axis=1);out=q[q['round'].eq(g)].copy();audits=[];heads={}
    for j in range(8):
        tr=teacher[teacher.teacher_eligible&teacher.forecast_at.lt(at)&teacher[f'y_{j}'].notna()&teacher[f'y_at_{j}'].lt(at)&complete&h3.lt(at)].copy()
        if info['previous_release'] and g not in REFITS:
            model=read(R/info['previous_release']/'heads.json')[str(j)]
            if model.get('half_life_days')!=recent.HALF_LIFE_DAYS:raise ValueError('Calibration recipe change requires an explicit refit')
            reused=True
        else:model,_=recent.fit_recent(tr,j,at);reused=False
        heads[j]=model;out[f'xp_{j}']=projection.predict_projection(out,'component',model)
        audits.append(dict(offset=j,cutoff=str(at),fitted_at=model['fitted_at'],rows=model['rows'],current_trainable_rows=len(tr),current_rows=int(tr.season.eq(SEASON).sum()),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'y_at_{j}'].max()),max_h3_label=str(h3.loc[tr.index].max()),keys_sha256=model['teacher_keys_sha256'],reused_between_refits=reused,half_life_days=recent.HALF_LIFE_DAYS,current_season_weight=model['current_season_weight']))
        mask=out.known_departed|(out.confirmed_out_current if j==0 else False);out.loc[mask,f'xp_{j}']=0.
    atomic_json(P/'heads.json',{str(k):v for k,v in heads.items()});atomic_json(P/'head_audit.json',audits);save(P/'live_features.pkl',out)
    out[common.KEY+['forecast_at','name','position','club','price_tenths','can_buy','confirmed_out_current','known_departed']+[f'can_start_{j}' for j in range(8)]+[f'xp_{j}' for j in range(8)]].to_csv(P/'forecasts.csv',index=False)
    assert recent.np.isfinite(out[[f'xp_{j}' for j in range(8)]]).all().all()
    context=EXTERNAL/'manifest.json'
    files=[P/n for n in ['forecasts.csv','live_features.pkl','heads.json','head_audit.json','prepared.json','current_oof.pkl','current.pkl','native_current.pkl','timing.csv.gz','origins.json','raw/receipts.json']]+list((P/'models').glob('*.pkl'))+[Path(__file__),R/'model_lab/recent_component_forecaster.py',R/'model_lab/component_forecaster.py',R/'scripts/common_season_comparison.py',context]
    atomic_json(P/'forecast_seal.json',dict(model=MODEL_ID,issued_at=str(at),sealed_at=str(recent.pd.Timestamp.now(tz='UTC')),source_capture_reused=bool(info.get('source_capture_reused')),deadline=info['deadline'],round=g,prospective=True,files={str(p.relative_to(R)):sha(p) for p in files},teacher_clock='origin, offset label and all H3 teacher outcomes strictly before fit',refits=list(REFITS),expiry_hours=24,calibration_half_life_days=recent.HALF_LIFE_DAYS,external_context_created_at=read(context)['created_at']))


def fit_heads():
    with binding():_fit_heads()
    config=configuration();seal=read(P/'forecast_seal.json');files=dict(config['files'])
    files.update({str(path.relative_to(R)):sha(path) for path in [Path(__file__),CONFIG_PATH,P/'forecast_seal.json',EXTERNAL/'manifest.json']})
    atomic_json(P/'operational_seal.json',dict(model_id=MODEL_ID,files=files,forecast_issued_at=seal['issued_at'],planning_horizon=5,forecast_horizon=8,historical_calendar=config['historical_calendar'],external_context=str(EXTERNAL.relative_to(R)),no_receipt_refresh_by_recipe_change=True))


def hard_manager():
    config=configuration();folder=R/config['backend'];hashes=read(R/config['backend_hashes']);verify_files(folder,hashes)
    mod=common.module('_operational_plan5_controlled',folder/'controlled_policy_v1.py');mod.OLD=folder;mod.EXPECTED={k:hashes[k] for k in ['engine.py','planner.py','initial_optimizer.py','policy.py']}
    manager=mod.ControlledPolicy(mod.Budget(node_limit=16,max_calls=40));manager.options['node_limit']=15;original=manager.engine.apply_decision
    def checked(state,choice,records,gw=None,chip=None):
        byid={int(row['pid']):row for row in records}
        if not all(byid[int(i)]['can_start_0'] for i in choice['starters']+[choice['captain'],choice['vice']]):raise ValueError('Confirmed unavailable starter or captain')
        if not all(byid[int(i)]['can_buy'] for i in choice['incoming']):raise ValueError('Confirmed unavailable incoming player')
        if (chip if chip is not None else choice.get('chip'))=='bench_boost' and not all(byid[int(i)]['can_start_0'] for i in choice['squad']):raise ValueError('Bench boost requires15eligible players')
        return original(state,choice,records,gw,chip)
    manager.engine.apply_decision=checked
    return mod,manager


class ComponentForecaster(recent.ComponentForecaster):
    def __init__(self,release=P):super().__init__(release)

    def forecast(self,origin,horizon=8):
        config=configuration();seal=read(self.release/'operational_seal.json');verify_files(R,seal['files'])
        if seal['model_id']!=MODEL_ID or seal['planning_horizon']!=5 or seal['files'][str(CONFIG_PATH.relative_to(R))]!=sha(CONFIG_PATH):raise ValueError('Unverified operational configuration')
        now=utc(origin['forecast_at']);external=utc(read(EXTERNAL/'manifest.json')['created_at'])
        if now<external or now-external>recent.pd.Timedelta(hours=24):raise ValueError('Refresh and integrate external club/national feeds before recommending a team')
        frame,audit=core.ComponentForecaster.forecast(self,origin,horizon)
        audit.update(calibration_half_life_days=180,external_context=str(EXTERNAL.relative_to(R)),external_context_created_at=str(external))
        audit.update(model=MODEL_ID,planning_horizon=5,historical_calendar=config['historical_calendar'])
        return frame,audit

    def decide(self,state,forecast_at):
        seal=read(self.release/'forecast_seal.json');self.forecast(dict(season=SEASON,round=seal['round'],forecast_at=forecast_at))
        pool=load(self.release/'live_features.pkl');pool['market']=pool.price_tenths;mod,manager=hard_manager();xp=pool[[f'xp_{j}' for j in range(8)]].to_numpy(float)
        result=manager.decide(pool,xp,state,seal['round'])
        return result,dict(solver_calls=len(manager.ledger),planning_horizon=5,automatic_team_changes=False)
