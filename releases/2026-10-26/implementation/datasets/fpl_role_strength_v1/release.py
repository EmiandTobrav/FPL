"""Publish v5 after independent checks; leave model inputs and releases frozen."""
import importlib.util,shutil,zipfile
from common import *
def archive(folder):
 path=folder.with_suffix('.zip')
 with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
  for f in sorted(folder.iterdir()):
   if f.is_file():z.write(f,str(f.relative_to(folder.parent)))
 return path
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 v=json.loads((P/'verification.json').read_text());s=json.loads((P/'summary.json').read_text());assert v['passed'] and v['master_rows_preserved']==190124 and v['team_start_conservation_checks']==5460
 assert len(s['role_columns'])==69 and len(s['strength_columns'])==32
 for name,h in json.loads((P/'input_hashes.json').read_text()).items():assert sha(R/name)==h,name
 totals={k:sum(a.get(k,0) for a in s['coverage'].values()) for k in next(iter(s['coverage'].values()))}
 dump(P/'coverage_totals.json',totals)
 (P/'RESULTATER.txt').write_text('START-/INNBYTTERMØNSTRE OG STYRKE INNE I MASTER V5\n\n190 124 opprinnelige PL-rader og alle v4-felt er bevart.\n69 rollehistorikkfelt og 32 beskrivende styrkefelt er lagt til.\n5 460 lag-/kampgrupper har elleve registrerte starter.\nAlle 101 nye felt bruker historikk strengt før effektiv prognosegrense.\nKorte/manglende spillerhistorikker og nøytral lagprior er merket.\nStyrken er målbasert og motstandsjustert, ikke en kalibrert prognose.\nXG er holdt utenfor grunnet kildekvalitet og ukvalifiserte lagtotaler.\nHistorisk mottakstid er fortsatt proxy. Ingen modeller er endret.\n\n'+json.dumps(dict(coverage=totals,verification=v),indent=2,ensure_ascii=False)+'\n')
 context=dict(version=P.name,role='all_season_player_role_history_and_descriptive_dynamic_strength',master_dataset=OUT.name,master_rows=190124,player_round_role_rows=182939,seasons=list(v['season_rows']),role_columns=s['role_columns'],strength_columns=s['strength_columns'],contract_sha256=sha(P/'contract.json'),coverage=totals,source_tier='existing_archived_outcomes_with_kickoff_plus_24h_availability_proxy',strict_historical_qualified=False,xg_used=False,model_enabled=False,raw_sources_in_archive=False,source_inventory='input_hashes.json')
 context['files']={f.name:sha(f) for f in P.iterdir() if f.is_file() and f.name!='manifest.json'};dump(P/'manifest.json',context)
 for name in ['verification.json','coverage.csv','coverage_totals.json']:shutil.copy2(P/name,OUT/name)
 manifest=dict(version=OUT.name,role='combined_all_season_FPL_observation_master',rows=190124,fixtures=2730,seasons=list(v['season_rows']),completed_current_round=7,history_eligible_rows=159881,history_excluded_rows=30243,previous_master=OLD.name,previous_master_sha256=sha(OLD/'player_matches.csv.xz'),role_strength_dataset=P.name,role_strength_manifest_sha256=sha(P/'manifest.json'),role_columns=s['role_columns'],strength_columns=s['strength_columns'],strict_role_strength_historical_qualified=False,strength_xg_used=False,strength_is_calibrated_forecast=False,weather_is_retrospective=True,all_competitions_complete=False,model_changed=False)
 manifest['files']={f.name:sha(f) for f in OUT.iterdir() if f.is_file() and f.name!='manifest.json'};dump(OUT/'manifest.json',manifest)
 m=load(OUT/'loader.py','master_v5_loader');assert sum(1 for _ in m.iter_records())==190124;assert sum(1 for _ in m.iter_records('history'))==159881
 m=load(P/'loader.py','role_strength_loader');assert sum(1 for _ in m.iter_context())==190124;assert sum(1 for _ in m.iter_context(by_round=True))==182939;assert sum(1 for _ in m.iter_context(strict=True))==0
 cz=archive(P);mz=archive(OUT)
 pointer=dict(id=P.name,role='player_role_history_and_dynamic_strength_materialized_in_master',seasons=list(v['season_rows']),directory=P.name,manifest=P.name+'/manifest.json',loader=P.name+'/loader.py',joined_master=OUT.name+'/player_matches.csv.xz',player_match_context=P.name+'/player_match_context.csv.xz',player_round_role_context=P.name+'/player_round_role_context.csv.xz',rows=190124,feature_columns=101,role_columns=69,strength_columns=32,coverage=totals,strict_historical_qualified=False,xg_used=False,model_enabled=False,archive=cz.name,archive_sha256=sha(cz))
 path=R/'datasets/MASTER_ACTIVE.json';active=json.loads(path.read_text());assert active['version']==OLD.name
 previous=dict(version=active['version'],master_table=active['master_table'],archive=active['archive'])
 active.update(version=OUT.name,release_directory=OUT.name,master_table=OUT.name+'/player_matches.csv.xz',loader=OUT.name+'/loader.py',manifest=OUT.name+'/manifest.json',archive=mz.name,archive_sha256=sha(mz),previous_master=previous,role_strength_context=pointer,role_strength_fields_materialized_in_master=True,competition_data_contract='COMPETITION_DATA_CONTRACT_V5.json',role='combined_all_season_observations_weather_loan_workload_calendar_availability_set_pieces_role_strength')
 dump(R/'datasets/ROLE_STRENGTH_ACTIVE.json',pointer);dump(path,active)
 path=R/'overview/PROJECT.json';project=json.loads(path.read_text());project['observation_master'].update(id=OUT.name,directory='datasets/'+OUT.name,master_table='datasets/'+active['master_table'],loader='datasets/'+active['loader'],role_history_columns=69,dynamic_strength_columns=32,context_columns=519,updated_date='2026-10-25',previous_master=previous)
 project['competition_data_contract']='datasets/COMPETITION_DATA_CONTRACT_V5.json';project['role_strength_context']=dict(pointer,active_pointer='datasets/ROLE_STRENGTH_ACTIVE.json',verification='datasets/'+P.name+'/verification.json');dump(path,project)
 # Release code is restricted to observational navigation. Frozen training pointer stays byte-identical.
 inputs=json.loads((P/'input_hashes.json').read_text());assert sha(R/'datasets/ACTIVE.json')==inputs['datasets/ACTIVE.json']
 print(json.dumps(dict(published=True,master=OUT.name,rows=190124,new_fields=101,coverage=totals,loader_checks_passed=True,models_changed=False),indent=2),flush=True)
if __name__=='__main__':main()
