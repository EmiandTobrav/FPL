"""Activate a physically combined all-season master after the checks pass."""
import json,zipfile,importlib.util,collections,shutil
from common import *
from build_context import OUT
def dump(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def archive(folder,include_raw=False):
 path=folder.with_suffix('.zip')
 with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
  for file in sorted(folder.rglob('*')):
   if not file.is_file() or '__pycache__' in file.parts or (not include_raw and 'raw' in file.relative_to(folder).parts):continue
   z.write(file,str(file.relative_to(folder.parent)))
 return path
def main():
 verified=json.loads((P/'verification.json').read_text());assert verified['passed'] and verified['master_rows_preserved']==190124
 summary=json.loads((P/'context_summary.json').read_text());minutes=json.loads((P/'minute_summary.json').read_text());coverage=list(read(P/'context_coverage.csv'))
 # Complete source inventory, including summaries used for identity screening.
 sources={}
 for row in json.loads((P/'summary_sources.json').read_text()):
  assert not row['error'],row
  path=R/row['raw_file'];source=json.loads(path.with_name(path.name+'.source.json').read_text());assert sha(path)==source['sha256'];sources[row['raw_file']]=source['sha256']
 for path,digest in json.loads((P/'scoreboard_input_hashes.json').read_text()).items():
  assert digest and sha(R/path)==digest;sources[path]=digest
 for row in json.loads((P/'calendar_origin_selection.json').read_text()):
  if row['raw_file']:sources[row['raw_file']]=sha(R/row['raw_file'])
 for pid in json.loads((P/'profile_candidates.json').read_text()):
  path=locate(f'athlete_{pid}.json')
  if path.exists():sources[str(path.relative_to(R))]=sha(path)
 fixed=[MASTER/'player_matches.csv.xz',MASTER/'manifest.json',PILOT/'international_player_minutes.csv.gz',PILOT/'historical_announced_club_fixtures.csv',PILOT/'raw/current_fpl_bootstrap.json',CUP/'player_links.csv',CUP/'build.py',R/'reports/calendar_reconstruction_2026_10_16/fixture_snapshots.csv.gz']
 fixed+=list((R/'FPL_training_dataset/research/current/project/data').glob('*_players.csv.gz'))+list((R/'FPL_training_dataset/research/current/project/data').glob('*_teams.csv.gz'))
 for path in fixed:sources[str(path.relative_to(R))]=sha(path)
 for row in read(P/'historical_announced_club_fixtures.csv'):
  path=R/row['source_file'];sources[str(path.relative_to(R))]=sha(path)
 dump(P/'source_inventory.json',sources)
 unknown=sum(r['unknown_minute_rows'] for r in minutes['coverage']);known=sum(r['known_minute_rows'] for r in minutes['coverage'])
 release=dict(version=P.name,master_version=OUT.name,master_rows=190124,seasons=list(verified['season_rows']),player_round_rows=verified['player_round_rows'],new_context_columns=len(summary['context_columns']),external_squad_rows=known+unknown,known_external_minute_rows=known,unknown_external_minute_rows=unknown,external_physical_matches=minutes['physical_fixtures_with_FPL_or_PL_club'],historical_PL_origins=verified['historical_PL_origins'],fresh_PL_origins=sum(int(r['PL_calendar_fresh_origins']) for r in coverage),historical_announced_cup_fixtures=sum(1 for _ in read(P/'historical_announced_club_fixtures.csv')),verification=verified,all_competitions_complete=False,model_changed=False)
 dump(P/'release_summary.json',release)
 (P/'RESULTATER.txt').write_text('SAMLET MASTER OPPDATERT FOR ALLE ÅTTE SESONGER\n\n'+f'190 124 PL-rader er bevart med alle opprinnelige felt.\n{len(summary["context_columns"])} nye kontekstfelt er koblet på.\n{known} eksterne minuttregistreringer er kontrollert; {unknown} er ukjente.\n272 historiske PL-prognosetidspunkter har datert oppsett, 241 er høyst 14 dager gamle.\nHistoriske cupkunngjøringer er delvis dekket.\n\n'+json.dumps(release,indent=2)+'\n')
 ctxmanifest=dict(version=P.name,role='all_season_external_workload_and_historical_calendar',created_at=datetime.now(timezone.utc).isoformat(),master_dataset=OUT.name,seasons=list(verified['season_rows']),all_competitions_complete=False,historical_deadline_qualified=False,model_enabled=False,raw_sources_in_archive=False,source_inventory='source_inventory.json',source_files=len(sources),files={})
 for path in sorted(P.iterdir()):
  if path.is_file() and path.name!='manifest.json':ctxmanifest['files'][path.name]=sha(path)
 dump(P/'manifest.json',ctxmanifest)
 shutil.copy2(P/'verification.json',OUT/'verification.json');shutil.copy2(P/'context_coverage.csv',OUT/'season_coverage.csv')
 mastermanifest=dict(version=OUT.name,role='combined_all_season_FPL_observation_master',rows=190124,fixtures=2730,seasons=list(verified['season_rows']),completed_current_round=7,history_eligible_rows=159881,history_excluded_rows=30243,previous_master=MASTER.name,previous_master_sha256=sha(MASTER/'player_matches.csv.xz'),context_dataset=P.name,context_manifest_sha256=sha(P/'manifest.json'),source_inventory_sha256=sha(P/'source_inventory.json'),weather_is_retrospective=True,all_competitions_complete=False,historical_deadline_qualified=False,model_changed=False,context_columns=summary['context_columns'],files={})
 for path in sorted(OUT.iterdir()):
  if path.is_file() and path.name!='manifest.json':mastermanifest['files'][path.name]=sha(path)
 dump(OUT/'manifest.json',mastermanifest)
 spec=importlib.util.spec_from_file_location('new_master_loader',OUT/'loader.py');loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
 assert sum(1 for _ in loader.iter_records())==190124
 assert sum(1 for _ in loader.iter_records('history'))==159881
 masterzip=archive(OUT);contextzip=archive(P)
 context=dict(id=P.name,seasons=list(verified['season_rows']),directory=P.name,manifest=P.name+'/manifest.json',loader=P.name+'/loader.py',player_match_context=P.name+'/player_match_context.csv.xz',player_round_context=P.name+'/player_round_context.csv.xz',joined_master=OUT.name+'/player_matches.csv.xz',player_match_rows=190124,player_round_rows=verified['player_round_rows'],model_enabled=False,historical_deadline_qualified=False,all_competitions_complete=False,archive=contextzip.name,archive_sha256=sha(contextzip))
 oldpointer=json.loads((R/'datasets/MASTER_ACTIVE.json').read_text());previous=dict(version=oldpointer['version'],master_table=oldpointer['master_table'],archive=oldpointer['archive']);pointer=dict(oldpointer)
 pointer.update(version=OUT.name,release_directory=OUT.name,role='combined_all_season_observations_weather_loan_workload_calendar',master_table=OUT.name+'/player_matches.csv.xz',loader=OUT.name+'/loader.py',manifest=OUT.name+'/manifest.json',archive=masterzip.name,archive_sha256=sha(masterzip),workload_context=context,external_competitions=dict(dataset=P.name,matches=P.name+'/matches.csv.gz',player_minutes=P.name+'/player_minutes.csv.gz',FPL_only=True,is_fpl_fixture=False,data_role='workload_context'),previous_master=previous,competition_data_contract='COMPETITION_DATA_CONTRACT_V4.json')
 pointer['cup_pilot_is_previous_release']=True
 contract=json.loads((R/'datasets/COMPETITION_DATA_CONTRACT_V3.json').read_text());contract['version']=4;contract['master']['dataset']=OUT.name;contract['external_competitions']['dataset']=P.name;contract['external_competitions']['international_supplement']=P.name;contract['external_competitions']['cup_qualifier_supplement']=P.name+'/matches.csv.gz';contract['integration'].update(current_state='One physically combined master for all eight seasons; PL rows unchanged; external matches separate; no model enabled.',workload_context_dataset=P.name,workload_seasons=list(verified['season_rows']),joined_master=pointer['master_table'],all_competitions_complete=False)
 contract['integration'].pop('joined_season_master',None);contract['integration'].pop('workload_season',None)
 dump(R/'datasets/COMPETITION_DATA_CONTRACT_V4.json',contract);dump(R/'datasets/WORKLOAD_ACTIVE.json',context);dump(R/'datasets/MASTER_ACTIVE.json',pointer)
 projectpath=R/'overview/PROJECT.json';project=json.loads(projectpath.read_text());project['observation_master'].update(id=OUT.name,directory='datasets/'+OUT.name,master_table='datasets/'+pointer['master_table'],loader='datasets/'+pointer['loader'],updated_date='2026-10-25',all_season_context_in_master=True,context_columns=len(summary['context_columns']),previous_master=previous)
 project['workload_context']=dict(context,active_pointer='datasets/WORKLOAD_ACTIVE.json',updated_date='2026-10-25');project['competition_data_contract']='datasets/COMPETITION_DATA_CONTRACT_V4.json';project['all_season_external_context']=release
 project['external_competition_pilot']['status']='previous_frozen_pilot_superseded_by_all_season_context';project['external_competition_pilot']['workload_context_dataset']=P.name
 dump(projectpath,project)
 print(json.dumps(dict(published=True,master_table=pointer['master_table'],rows=190124,master_archive_bytes=masterzip.stat().st_size,context_archive_bytes=contextzip.stat().st_size,loader_observation_and_history_checks=True),indent=2),flush=True)
if __name__=='__main__':main()
