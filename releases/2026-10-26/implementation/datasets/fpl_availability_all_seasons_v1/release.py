"""Activate the combined v3 master after all-season availability checks pass."""
import importlib.util,shutil,zipfile
from common import *
def dump(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def archive(folder,raw=False):
 path=folder.with_suffix('.zip')
 with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
  for file in sorted(folder.rglob('*')):
   if file.is_file() and '__pycache__' not in file.parts and (raw or 'raw' not in file.relative_to(folder).parts):z.write(file,str(file.relative_to(folder.parent)))
 return path
def main():
 verified=json.loads((P/'verification.json').read_text());metadata=json.loads((P/'metadata_verification.json').read_text());summary=json.loads((P/'summary.json').read_text());assert verified['passed'] and metadata['passed'] and verified['master_rows_preserved']==190124
 inputs=json.loads((P/'input_hashes.json').read_text())|metadata['metadata_hashes']
 for name,digest in inputs.items():assert sha(R/name)==digest,name
 for file in (P/'raw').glob('*'):
  if file.is_file():inputs[str(file.relative_to(R))]=sha(file)
 for season in verified['season_rows']:
  for suffix in ['players','teams']:
   file=R/'FPL_training_dataset/research/current/project/data'/f'{season}_{suffix}.csv.gz';inputs[str(file.relative_to(R))]=sha(file)
 dump(P/'source_inventory.json',inputs)
 (P/'RESULTATER.txt').write_text('SKADESTATUS OG LAGKAMERATFRAVÆR INNE I SAMLET MASTER V3\n\n190 124 opprinnelige PL-rader og alle v2-felt er bevart.\n80 nye tilgjengelighetsfelt, inklusive kilde- og kvalitetsmarkeringer.\n154 506 rader har godkjent kilde (81,3 %); 35 618 er ukjente.\nHoveddelen av hullene ligger i 2019/20 og 2020/21.\n272 arkivkilder er undersøkt; 214 passerer alders-/tidskrav.\nTrenerbrikker er utelatt fra lagkameratgrunnlaget.\nTo tidligere faktiske FPL-frister er håndtert og merket.\nGit-tider er fortsatt proxyer. Ingen modell er trent eller endret.\n\n'+json.dumps(verified,indent=2)+'\n')
 context_manifest=dict(version=P.name,role='all_season_availability_and_teammate_context',seasons=list(verified['season_rows']),master_dataset=OUT.name,master_rows=190124,known_master_rows=verified['known_master_rows'],unknown_master_rows=verified['unknown_master_rows'],source_tier='git_timestamp_proxy',strict_historical_qualified=False,source_inventory='source_inventory.json',raw_sources_in_archive=False,model_enabled=False,files={})
 for file in P.iterdir():
  if file.is_file() and file.name!='manifest.json':context_manifest['files'][file.name]=sha(file)
 dump(P/'manifest.json',context_manifest)
 for name in ['verification.json','metadata_verification.json','coverage.csv']:shutil.copy2(P/name,OUT/name)
 master_manifest=dict(version=OUT.name,role='combined_all_season_FPL_observation_master',rows=190124,fixtures=2730,seasons=list(verified['season_rows']),completed_current_round=7,history_eligible_rows=159881,history_excluded_rows=30243,previous_master=MASTER.name,previous_master_sha256=sha(MASTER/'player_matches.csv.xz'),availability_dataset=P.name,availability_manifest_sha256=sha(P/'manifest.json'),availability_columns=summary['availability_columns'],known_availability_rows=verified['known_master_rows'],unknown_availability_rows=verified['unknown_master_rows'],strict_availability_historical_qualified=False,weather_is_retrospective=True,all_competitions_complete=False,model_changed=False,files={})
 for file in OUT.iterdir():
  if file.is_file() and file.name!='manifest.json':master_manifest['files'][file.name]=sha(file)
 dump(OUT/'manifest.json',master_manifest)
 spec=importlib.util.spec_from_file_location('master_v3_loader',OUT/'loader.py');loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
 assert sum(1 for _ in loader.iter_records())==190124
 assert sum(1 for _ in loader.iter_records('history'))==159881
 context_zip=archive(P);master_zip=archive(OUT)
 pointer=dict(id=P.name,role='all_season_availability_context_materialized_in_master',seasons=list(verified['season_rows']),directory=P.name,manifest=P.name+'/manifest.json',loader=P.name+'/loader.py',joined_master=OUT.name+'/player_matches.csv.xz',player_match_context=P.name+'/player_match_context.csv.xz',player_round_context=P.name+'/player_round_context.csv.xz',rows=190124,source_matched_rows=verified['known_master_rows'],source_unknown_rows=verified['unknown_master_rows'],feature_columns=len(summary['availability_columns']),source_tier='git_timestamp_proxy',strict_historical_qualified=False,model_enabled=False,previous_pilot=PILOT.name,archive=context_zip.name,archive_sha256=sha(context_zip))
 master_pointer_path=R/'datasets/MASTER_ACTIVE.json';active=json.loads(master_pointer_path.read_text());assert active['version']==MASTER.name
 previous=dict(version=active['version'],master_table=active['master_table'],archive=active['archive'])
 active.update(version=OUT.name,role='combined_all_season_observations_weather_loan_workload_calendar_availability',release_directory=OUT.name,master_table=OUT.name+'/player_matches.csv.xz',loader=OUT.name+'/loader.py',manifest=OUT.name+'/manifest.json',archive=master_zip.name,archive_sha256=sha(master_zip),previous_master=previous,availability_context=pointer,availability_fields_materialized_in_master=True)
 dump(R/'datasets/AVAILABILITY_ACTIVE.json',pointer);dump(master_pointer_path,active)
 project_path=R/'overview/PROJECT.json';project=json.loads(project_path.read_text());project['observation_master'].update(id=OUT.name,directory='datasets/'+OUT.name,master_table='datasets/'+active['master_table'],loader='datasets/'+active['loader'],availability_columns=len(summary['availability_columns']),workload_calendar_columns=245,context_columns=245+len(summary['availability_columns']),known_availability_rows=verified['known_master_rows'],unknown_availability_rows=verified['unknown_master_rows'],updated_date='2026-10-25',previous_master=previous)
 project['availability_context']=dict(pointer,active_pointer='datasets/AVAILABILITY_ACTIVE.json',verification='datasets/'+P.name+'/verification.json');project['availability_pilot']['status']='retained_frozen_pilot_extended_to_all_seasons';dump(project_path,project)
 print(json.dumps(dict(published=True,master_table=active['master_table'],rows=190124,known_availability_rows=verified['known_master_rows'],unknown_availability_rows=verified['unknown_master_rows'],master_archive_bytes=master_zip.stat().st_size,context_archive_bytes=context_zip.stat().st_size,loader_checks_passed=True,model_enabled=False),indent=2),flush=True)
if __name__=='__main__':main()
