"""Complete fixed, non-retried season attempts, including explicit cap failures."""
import os,sys,time,subprocess,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts.common_season_comparison import P,ARMS,CONTROLS,WEATHER,EVAL
from model_lab.common import atomic_json,sha,verify_files
def run(*args,allow_failed_attempts=False):
    print('STAGE',' '.join(args),flush=True);result=subprocess.run([sys.executable,*args],cwd=R,env=os.environ.copy())
    if result.returncode and not allow_failed_attempts:raise RuntimeError('Stage failed: '+' '.join(args))
def terminal(season,arm):
    folder=P/'manager'/f'{season}_{arm}'
    if (folder/'summary.json').exists():return True
    log=P/'logs'/f'manager_{season}_{arm}.log'
    return log.exists() and 'ControlledSolverError: Solver exceeded declared node limit' in log.read_text()
def main():
    known=P/'logs/manager_2023-24_fixed_history.log';assert 'ControlledSolverError: Solver exceeded declared node limit' in known.read_text()
    files=[Path(__file__),R/'scripts/verify_common_seasons_v2.py',R/'scripts/report_common_seasons.py',P/'proposal.json',known]
    atomic_json(P/'completion_addendum.json',dict(reason='Original fixed_history 2023/24 manager attempt failed native declared node cap. No model, forecast, manager, success criterion, solver resource setting or candidate changed.',treatment='Do not retry. Finish each already submitted independent attempt once. Recompute every saved settlement, including partial failed attempts. Exclude incomplete seasons from full-season totals and require both complete years for means/utility gates. Weather scenarios remain hindsight-only.',known_stop='2023-24_fixed_history',original_planned_maximum_seasons=46,maximum_attempts_unchanged=True,extra_training_fits=0,extra_manager_decisions=0,input_hashes={str(p.relative_to(R)):sha(p) for p in files}))
    while not all(terminal(s,a) for s in EVAL for a in ARMS+CONTROLS):time.sleep(10)
    while not (P/'weather_forecast_verification.json').exists():time.sleep(10)
    # The original finisher propagates the declared primary failure and cannot
    # dispatch this weather stage; no weather manager has run yet.
    assert not any((P/'manager'/f'{s}_{a}').exists() for s in EVAL for a in WEATHER)
    run('scripts/common_season_comparison.py','weather_managers',allow_failed_attempts=True)
    assert all(terminal(s,a) for s in EVAL for a in WEATHER)
    verify_files(R,json.loads((P/'completion_addendum.json').read_text())['input_hashes'])
    run('scripts/verify_common_seasons_v2.py','managers');run('scripts/report_common_seasons.py');run('scripts/research.py','complete','common-season-comparison-20261025-v1',str((P/'result.json').relative_to(R)))
    v=json.loads((P/'manager_verification.json').read_text());atomic_json(P/'completion_complete.json',dict(passed=True,attempted_seasons=46,full_seasons=v['full_seasons'],technical_stops=v['technical_stops'],decisions_verified=v['decisions_replayed'],overview='overview/COMMON_MODEL_RESULTS_2026_10_25.md'));print('FORECASTS AND ALL SEASON ATTEMPTS VERIFIED',flush=True)
if __name__=='__main__':main()
