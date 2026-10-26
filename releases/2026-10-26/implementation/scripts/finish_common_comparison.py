"""Complete the already authorized comparison and publish its local overview.

Waits for the in-progress model train. Executes each following stage once;
stops on any verification error. No deployment, account change or messaging.
"""
import os,sys,time,json,subprocess,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json
B=R/'reports/common_model_retest_2026_10_25_v3';W=R/'reports/common_weather_proxy_2026_10_25';D=R/'datasets/fpl_common_training_v1'

def command(*args):
    print('STAGE',' '.join(args),flush=True)
    subprocess.run([sys.executable,*args],cwd=R,env=os.environ.copy(),check=True)

def main():
    assert not (B/'completion_workflow_started.json').exists()
    atomic_json(B/'completion_workflow_started.json',dict(started_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),authorization='User requested common training table, model retests and consolidated overview; subsequently requested actual-weather proxy study.'))
    while not (B/'prediction_lock.json').exists():time.sleep(10)
    print('MAIN TRAINING SEALED',flush=True)
    # Freeze the completed control evidence before either new study is scored.
    p=W/'proposal.json';spec=json.loads(p.read_text());paths=[B/'proposal.json',B/'prediction_lock.json',B/'fit_audit.csv']
    paths+=list((B/'folds').glob('*/lock.json'))+list((B/'folds').glob('*/catboost.csv.gz'))
    spec['input_hashes'].update({str(x.relative_to(R)):sha(x) for x in paths});p.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
    command('scripts/research.py','register',str(p.relative_to(R)))
    command('scripts/common_model_retest_v3.py','score')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        weather=pool.submit(command,'scripts/common_weather_proxy.py','train')
        command('scripts/common_model_retest_v3.py','verify')
        command('scripts/common_model_retest_v3.py','anchor')
        command('scripts/common_model_retest_v3.py','report')
        command('scripts/research.py','complete','common-model-retest-20261025-v3',str((B/'result.json').relative_to(R)))
        weather.result()
    command('scripts/common_weather_proxy.py','score')
    command('scripts/research.py','complete','common-weather-proxy-20261025-v1',str((W/'result.json').relative_to(R)))
    readme=D/'README.md';text=readme.read_text().replace('reports/common_model_retest_2026_10_25/RESULTATER.md','reports/common_model_retest_2026_10_25_v3/RESULTATER.md');readme.write_text(text)
    command('scripts/publish_common_comparison.py')
    overview=R/'overview/COMMON_MODEL_RESULTS_2026_10_25.md'
    status=dict(status='completed_verified_forecast_comparison',dataset='fpl_common_training_v1',dataset_manifest='datasets/fpl_common_training_v1/manifest.json',dataset_manifest_sha256=sha(D/'manifest.json'),selected_model_feature_variants=18,main_result='reports/common_model_retest_2026_10_25_v3/result.json',weather_result='reports/common_weather_proxy_2026_10_25/result.json',overview=str(overview.relative_to(R)),overview_sha256=sha(overview),manager_simulations_run=False,production_changed=False,operational_benchmark='fixed_season_h8_adaptive_v1',original_common_basis_preserved=True)
    atomic_json(R/'overview/COMMON_COMPARISON_STATUS.json',status)
    atomic_json(R/'datasets/COMMON_TRAINING_ACTIVE.json',dict(id='fpl_common_training_v1',role='common_research_training_view_not_operational_pipeline_replacement',table='fpl_common_training_v1/training.pkl',portable_table='fpl_common_training_v1/training.csv.gz',schema='fpl_common_training_v1/schema.json',manifest='fpl_common_training_v1/manifest.json',verification='fpl_common_training_v1/verification.json',target_horizons=[1,3],production_changed=False))
    project=R/'overview/PROJECT.json';obj=json.loads(project.read_text());obj['dataset']['common_research_training_view']=dict(id='fpl_common_training_v1',pointer='datasets/COMMON_TRAINING_ACTIVE.json',overview=str(overview.relative_to(R)),production_changed=False);project.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    root=R/'README.md';text=root.read_text();banner='\n**Felles modelltest fullført:** [Én samlet resultatoversikt](overview/COMMON_MODEL_RESULTS_2026_10_25.md) dekker 18 modell-/featurevarianter på [felles treningstabell](datasets/fpl_common_training_v1/README.md), pluss en separat faktisk-vær-proxy. Poeng, minutter, sannsynligheter og fryst operativ referanse holdes adskilt. Ingen ny manager-/produksjonsmodell er valgt.\n';text=text.replace('# FPL prosjektoversikt\n','# FPL prosjektoversikt\n'+banner,1);root.write_text(text)
    nextfile=R/'overview/NEXT.md';nextfile.write_text('# Felles datagrunnlag og modelltester – fullført 25. oktober 2026\n\n[Samlet oversikt](COMMON_MODEL_RESULTS_2026_10_25.md) og [forskningsstatus](COMMON_COMPARISON_STATUS.json) angir den nye, verifiserte sammenligningen. Nye sammenligninger bruker én eksplisitt versjon av den felles treningstabellen; gamle resultater er historiske. Vær med faktisk målkampvær er en separat, optimistisk proxy. Ingen nye sesongsimuleringer er utført; dagens operative modell og fryste prospektive prognoser er bevart. Eldre neste-steg-notater nedenfor beskriver sine opprinnelige faser.\n\n'+nextfile.read_text())
    methods=R/'overview/METHODS.md';methods.write_text(methods.read_text()+'\n## Felles modellgrunnlag og faktisk-vær-proxy, 25. oktober 2026\n\n[Samlet resultatoversikt](COMMON_MODEL_RESULTS_2026_10_25.md): 182 939 spiller–runde-rader, 325 tillatte grunnfeatures, 18 modell-/featurevarianter, H1/H3 og fire sesonger. Samme trenings- og evalueringsnøkler per fold. Tidligere forkastede familier testet på nytt. Separat værstudie bruker rekonstruert faktisk kampvær og to faste syntetiske feilscenarioer; dette er ikke historiske førfristvarsler. Dagens operative prognoser er scoret på de samme nye fasitene i tilgjengelige arkivår, med opprinnelig trening bevart. Ingen produksjonsendring eller ny netto sesongpoengpåstand.\n')
    atomic_json(B/'completion_workflow_complete.json',status);print('ALL VERIFIED AND PUBLISHED',overview,flush=True)

if __name__=='__main__':main()
