"""Single operational entry point. Historical experiment defaults stay frozen."""
import argparse, importlib, json
from pathlib import Path
import pandas as pd
from .common import ROOT,read,sha

def forecaster():
    descriptor=read(ROOT/'overview/ACTIVE_TEAM_BENCHMARK.json')
    path=ROOT/descriptor['runtime']
    if sha(path)!=descriptor['runtime_sha256']:raise ValueError('Changed active runtime; review required')
    allowed={'common_component_h8_adaptive_v1':'model_lab/component_forecaster.py', 'common_component_h8_recent180_adaptive_v1':'model_lab/recent_component_forecaster.py', 'common_component_h8_recent180_plan5_calendar_v1':'model_lab/fresh_planned_component_forecaster.py'}
    if allowed.get(descriptor['id'])!=descriptor['runtime']:raise ValueError('Component activation has not passed')
    module=importlib.import_module(descriptor['runtime'][:-3].replace('/','.'))
    return module.ComponentForecaster(ROOT/descriptor['release']),descriptor

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['forecast','decide']);parser.add_argument('--state');args=parser.parse_args()
    model,descriptor=forecaster();now=pd.Timestamp.now(tz='UTC');origin=dict(season='2026-27',round=descriptor['live_round'],forecast_at=now)
    if args.action=='forecast':
        frame,audit=model.forecast(origin);print(frame.to_csv(index=False));print(json.dumps(audit),file=__import__('sys').stderr)
    else:
        if not args.state:raise ValueError('A verified current team state file is required')
        state=read(Path(args.state));state['owned']={int(k):v for k,v in state['owned'].items()};choice,audit=model.decide(state,now)
        from .component_forecaster import hard_manager
        module,_=hard_manager();print(json.dumps(module.clean(dict(result=choice,audit=audit)),indent=2))
if __name__=='__main__':main()
