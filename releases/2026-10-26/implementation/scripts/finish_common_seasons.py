"""Complete all user-requested seasonal comparisons after forecast sealing."""
import os,sys,time,subprocess,concurrent.futures,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import atomic_json
P=R/'reports/common_season_comparison_2026_10_25';W=R/'reports/common_weather_proxy_2026_10_25';B=R/'reports/common_model_retest_2026_10_25_v3'
def run(*args):
    print('STAGE',' '.join(args),flush=True);subprocess.run([sys.executable,*args],cwd=R,env=os.environ.copy(),check=True)
def wait(path):
    while not path.exists():time.sleep(10)
def main():
    atomic_json(P/'completion_started.json',dict(full_season_simulations_explicitly_requested=True,arms=23,seasons=2))
    wait(P/'causal_prediction_lock.json');wait(P/'reference_prediction_lock.json');run('scripts/verify_common_seasons.py','forecasts','causal')
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        managers=pool.submit(run,'scripts/common_season_comparison.py','managers')
        wait(W/'prediction_lock.json');run('scripts/common_season_comparison.py','weather_base');run('scripts/common_season_comparison.py','weather_project');run('scripts/verify_common_seasons.py','forecasts','weather');managers.result()
    run('scripts/common_season_comparison.py','weather_managers');run('scripts/verify_common_seasons.py','managers')
    wait(B/'completion_workflow_complete.json');run('scripts/report_common_seasons.py');run('scripts/research.py','complete','common-season-comparison-20261025-v1',str((P/'result.json').relative_to(R)));atomic_json(P/'completion_complete.json',dict(passed=True,full_seasons=46,decisions=1748,overview='overview/COMMON_MODEL_RESULTS_2026_10_25.md'))
    print('FORECASTS AND FULL SEASONS COMPLETE',flush=True)
if __name__=='__main__':main()
