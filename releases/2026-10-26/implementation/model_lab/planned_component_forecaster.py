"""Selected component recipe with qualified historical calendars and H5 policy.

Old runtimes and forecast receipts remain immutable. Source expiry and four-round
model reuse are inherited; switching policy never refreshes a data receipt.
"""
import os
from contextlib import contextmanager
from pathlib import Path
import copy
import numpy as np
from model_lab import recent_component_forecaster as recent
from model_lab.common import ROOT as R, read, sha, verify_files, atomic_json
core=recent.core
CONFIG_PATH=R/'reports/component_plan5_activation_2026_10_26/runtime_config.json'
P=Path(os.environ.get('FPL_COMPONENT_RELEASE',str(CONFIG_PATH.parent)))
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
    return config


@contextmanager
def binding():
    configuration()
    names=['P','D','FIT'];saved=[(module,name,getattr(module,name)) for module in [core,recent] for name in names]
    try:
        for module in [core,recent]:module.P=P;module.D=D;module.FIT=FIT
        yield
    finally:
        for module,name,value in saved:setattr(module,name,value)


def prepare():
    with binding():return core.prepare()


def fit_base(g):
    with binding():return core.fit_base(g)


def reuse_base(g):
    with binding():return core.reuse_base(g)


def fit_heads():
    with binding():recent.fit_heads()
    config=configuration();seal=read(P/'forecast_seal.json')
    files=dict(config['files']);files.update({str(path.relative_to(R)):sha(path) for path in [Path(__file__),CONFIG_PATH,P/'forecast_seal.json']})
    atomic_json(P/'operational_seal.json',dict(model_id=MODEL_ID,files=files,forecast_issued_at=seal['issued_at'],planning_horizon=5,forecast_horizon=8,historical_calendar=config['historical_calendar'],no_receipt_refresh_by_recipe_change=True))


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
        frame,audit=super().forecast(origin,horizon)
        audit.update(model=MODEL_ID,planning_horizon=5,historical_calendar=config['historical_calendar'])
        return frame,audit

    def decide(self,state,forecast_at):
        seal=read(self.release/'forecast_seal.json');self.forecast(dict(season=SEASON,round=seal['round'],forecast_at=forecast_at))
        pool=load(self.release/'live_features.pkl');pool['market']=pool.price_tenths;mod,manager=hard_manager();xp=pool[[f'xp_{j}' for j in range(8)]].to_numpy(float)
        result=manager.decide(pool,xp,state,seal['round'])
        return result,dict(solver_calls=len(manager.ledger),planning_horizon=5,automatic_team_changes=False)
