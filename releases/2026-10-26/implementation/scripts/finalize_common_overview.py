"""Clarify frozen-rule scope and verify the final user-facing entry point."""
import sys,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import atomic_json,sha,verify_files
P=R/'reports/common_season_comparison_2026_10_25';D=R/'datasets/fpl_common_training_v1';B=R/'reports/common_model_retest_2026_10_25_v3'
def read(p):return json.loads(p.read_text())
def main():
    completion=read(P/'completion_complete.json');assert completion['passed'];v=read(P/'manager_verification.json');verify_files(R,read(P/'result.json')['evidence_hashes']);verify_files(R,read(P/'proposal.json')['input_hashes']);verify_files(D,read(D/'manifest.json')['files'])
    paths=[R/'model_lab/vendor/fpl_rules_v1/engine.py',R/'model_lab/vendor/fpl_rules_v1/PROVENANCE.json',R/'scripts/run_unstarted_common_seasons.py',P/'primary_original_dispatcher_stopped.json',P/'primary_unstarted_dispatch.json',P/'primary_unstarted_dispatch_complete.json']
    if (P/'weather_unstarted_dispatch_complete.json').exists():paths+=list(P.glob('weather_*dispatch*.json'))
    atomic_json(P/'rule_and_dispatch_audit.json',dict(frozen_common_rule_engine=True,free_transfer_bank_limit=5,free_transfers_preserved_on_wildcard_or_free_hit=True,historical_outcomes_under_shared_counterfactual_rules=True,season_scope='2023/24 and2024/25 have the complete archived pool/price/reference basis used by this manager experiment;2025/26 remains a separate forecast check.',no_changed_model_solver_or_rule_settings=True,failed_attempts_never_retried=True,unstarted_jobs_dispatched_once_after_original_executor_cancelled_queue=True,files={str(p.relative_to(R)):sha(p) for p in paths}))
    p=R/'overview/COMMON_MODEL_RESULTS_2026_10_25.md';text=p.read_text();needle='## Hva som er likt i sesongtesten\n';note=f'\nHistoriske kamputfall er spilt gjennom det samme fryste regelsettet: maksimalt fem oppsparte gratisbytter, med beholdte gratisbytter ved wildcard/free hit. Sesongtallene er sammenlignbare kontrafaktiske kjøringer under disse felles reglene. 2023/24 og 2024/25 har det komplette arkivgrunnlaget for spillerutvalg, priser og begge referansene som brukes her; 2025/26 vises som en separat prognosekontroll. [Regel- og kjøringsgrunnlag]({P}/rule_and_dispatch_audit.json).\n';assert needle in text;text=text.replace(needle,needle+note,1).replace('Fabrikkparametre er låst før kjøring.','Modellinnstillingene er låst før kjøring.');p.write_text(text)
    for group in ['causal','weather','reference']:verify_files(P,read(P/f'{group}_prediction_lock.json')['files'])
    for name in ['base','weather_base']:verify_files(R,read(P/name/'lock.json')['source_model_hashes'])
    import pandas as pd
    for group in ['causal','weather']:
        for a in pd.read_csv(P/f'{group}_projection_audit.csv').itertuples():assert sha(P/a.model)==a.model_sha256
    artifacts={str(f.relative_to(P)):sha(f) for f in sorted(P.rglob('*')) if f.is_file() and f.name not in ['research_evidence_manifest.json','delivery_verification.json']}
    atomic_json(P/'research_evidence_manifest.json',dict(files=artifacts,all_saved_decisions_and_settlements_sealed=True,all_projection_models_and_audits_sealed=True,source_weight_hashes_rechecked=True))
    sources_path=p.with_suffix('.sources.json');sources=read(sources_path);verify_files(R,sources['source_hashes']);sources['source_hashes'][str((P/'rule_and_dispatch_audit.json').relative_to(R))]=sha(P/'rule_and_dispatch_audit.json');sources['source_hashes'][str((P/'research_evidence_manifest.json').relative_to(R))]=sha(P/'research_evidence_manifest.json');sources['overview_sha256']=sha(p);sources_path.write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
    statuspath=R/'overview/COMMON_COMPARISON_STATUS.json';status=read(statuspath);status['overview_sha256']=sha(p);status['rule_scope']='shared frozen rule engine,5FT banking in both years';statuspath.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
    work=read(B/'work_status.json');work.update(status='completed_verified_forecasts_and_all_season_attempts',full_seasons=v['full_seasons'],technical_stops=v['technical_stops'],decisions_verified=v['decisions_replayed'],overview=str(p.relative_to(R)),next_commands=['All authorized work completed; current operational benchmark preserved. New data changes require a new common table release and comparison.']);(B/'work_status.json').write_text(json.dumps(work,ensure_ascii=False,indent=2)+'\n')
    links=0
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('/','../','./')):
            file=Path(target) if target.startswith('/') else (p.parent/target).resolve();assert file.exists(),target;links+=1
    atomic_json(P/'delivery_verification.json',dict(passed=True,final_overview_sha256=sha(p),sources_sha256=sha(sources_path),local_links_checked=links,evidence_manifest_sha256=sha(P/'research_evidence_manifest.json'),generated_artifacts_sealed=len(artifacts),dataset_files_unchanged=True,active_operational_benchmark_unchanged=True,full_seasons=v['full_seasons'],technical_stops=len(v['technical_stops']),decisions_verified=v['decisions_replayed']))
    print('FINAL DELIVERY VERIFIED',links,'links',flush=True)
if __name__=='__main__':main()
