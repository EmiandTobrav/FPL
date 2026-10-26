"""Release verified reported set-piece roles and the combined v4 master."""
import importlib.util,shutil,zipfile
from common import *
def dump(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def archive(folder):
 path=folder.with_suffix('.zip')
 with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
  for file in sorted(folder.iterdir()):
   if file.is_file():z.write(file,str(file.relative_to(folder.parent)))
 return path
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def main():
 verified=json.loads((P/'verification.json').read_text());summary=json.loads((P/'summary.json').read_text())
 assert verified['passed'] and verified['master_rows_preserved']==190124 and len(summary['set_piece_columns'])==93
 inputs=json.loads((P/'input_hashes.json').read_text())
 for name,digest in inputs.items():assert sha(R/name)==digest,name
 assert json.loads((AV/'metadata_verification.json').read_text())['passed']
 (P/'RESULTATER.txt').write_text('DØDBALLROLLER INNE I SAMLET MASTER V4\n\n190 124 opprinnelige PL-rader og alle v3-felt er bevart.\n93 nye felt om oppførte straffe-, corner/indirekte frispark- og direkte frisparkroller.\n149 707 rader har kildedekning (78,7 %); 40 417 er ukjente.\nIngen dødballskjema i kildene fra 2019/20. Begrenset dekning i 2020/21.\nMulig opprykk ved rapportert fravær er scenarioer, ikke bekreftede kampoppgaver.\nDelte roller, hull i rekkefølgen, avreiser og ukjent status er merket.\nGit-tider er proxyer. Ingen modell er trent eller endret.\n\n'+json.dumps(verified,indent=2)+'\n')
 context=dict(version=P.name,role='all_season_reported_set_piece_context',seasons=list(verified['season_rows']),master_dataset=OUT.name,master_rows=190124,known_master_rows=149707,unknown_master_rows=40417,set_piece_columns=summary['set_piece_columns'],source_tier='git_timestamp_proxy',strict_historical_qualified=False,actual_taker_confirmed=False,raw_sources_in_archive=False,source_inventory='input_hashes.json',model_enabled=False)
 context['files']={f.name:sha(f) for f in P.iterdir() if f.is_file() and f.name!='manifest.json'};dump(P/'manifest.json',context)
 for name in ['verification.json','coverage.csv']:shutil.copy2(P/name,OUT/name)
 manifest=dict(version=OUT.name,role='combined_all_season_FPL_observation_master',rows=190124,fixtures=2730,seasons=list(verified['season_rows']),completed_current_round=7,history_eligible_rows=159881,history_excluded_rows=30243,previous_master=MASTER.name,previous_master_sha256=sha(MASTER/'player_matches.csv.xz'),set_piece_dataset=P.name,set_piece_manifest_sha256=sha(P/'manifest.json'),set_piece_columns=summary['set_piece_columns'],known_set_piece_rows=149707,unknown_set_piece_rows=40417,strict_set_piece_historical_qualified=False,actual_taker_confirmed=False,weather_is_retrospective=True,all_competitions_complete=False,model_changed=False)
 manifest['files']={f.name:sha(f) for f in OUT.iterdir() if f.is_file() and f.name!='manifest.json'};dump(OUT/'manifest.json',manifest)
 loader=load(OUT/'loader.py','master_v4_loader')
 assert sum(1 for _ in loader.iter_records())==190124
 assert sum(1 for _ in loader.iter_records('history'))==159881
 loader=load(P/'loader.py','set_piece_loader')
 assert sum(1 for _ in loader.iter_context())==190124
 assert sum(1 for _ in loader.iter_context(by_round=True))==182939
 assert sum(1 for _ in loader.iter_context(strict=True))==0
 context_zip=archive(P);master_zip=archive(OUT)
 pointer=dict(id=P.name,role='reported_set_piece_context_materialized_in_master',seasons=list(verified['season_rows']),directory=P.name,manifest=P.name+'/manifest.json',loader=P.name+'/loader.py',joined_master=OUT.name+'/player_matches.csv.xz',player_match_context=P.name+'/player_match_context.csv.xz',player_round_context=P.name+'/player_round_context.csv.xz',rows=190124,source_matched_rows=149707,source_unknown_rows=40417,feature_columns=93,source_tier='git_timestamp_proxy',strict_historical_qualified=False,actual_taker_confirmed=False,model_enabled=False,archive=context_zip.name,archive_sha256=sha(context_zip))
 path=R/'datasets/MASTER_ACTIVE.json';active=json.loads(path.read_text());assert active['version']==MASTER.name
 previous=dict(version=active['version'],master_table=active['master_table'],archive=active['archive'])
 active.update(version=OUT.name,role='combined_all_season_observations_weather_loan_workload_calendar_availability_set_pieces',release_directory=OUT.name,master_table=OUT.name+'/player_matches.csv.xz',loader=OUT.name+'/loader.py',manifest=OUT.name+'/manifest.json',archive=master_zip.name,archive_sha256=sha(master_zip),previous_master=previous,set_piece_context=pointer,set_piece_fields_materialized_in_master=True)
 dump(R/'datasets/SET_PIECE_ACTIVE.json',pointer);dump(path,active)
 path=R/'overview/PROJECT.json';project=json.loads(path.read_text());project['observation_master'].update(id=OUT.name,directory='datasets/'+OUT.name,master_table='datasets/'+active['master_table'],loader='datasets/'+active['loader'],set_piece_columns=93,context_columns=418,known_set_piece_rows=149707,unknown_set_piece_rows=40417,updated_date='2026-10-25',previous_master=previous)
 project['set_piece_context']=dict(pointer,active_pointer='datasets/SET_PIECE_ACTIVE.json',verification='datasets/'+P.name+'/verification.json');dump(path,project)
 print(json.dumps(dict(published=True,master_table=active['master_table'],rows=190124,set_piece_fields=93,loader_checks_passed=True,model_changed=False),indent=2),flush=True)
if __name__=='__main__':main()
