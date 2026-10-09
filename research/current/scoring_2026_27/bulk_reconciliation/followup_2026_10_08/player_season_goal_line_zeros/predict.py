"""Freeze explicit season-counter-zero predictions, never omitted zeros."""
from pathlib import Path
import json,hashlib,gzip
import pandas as pd
P=Path(__file__).resolve().parent;B=P.parents[1];R=B.parents[1];K=['season','fixture','code']
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def save(frame,name):
 raw=frame.to_csv(index=False).encode();(P/name).write_bytes(gzip.compress(raw,mtime=0) if name.endswith('.gz') else raw)
def main():
 for n,h in json.loads((P/'selection_freeze.json').read_text()).items():assert digest(P/n)==h,n
 for freeze_name in ['control_extension_freeze.json','reference_selection_freeze.json','league_selection_freeze.json']:
  for n,h in json.loads((P/freeze_name).read_text()).items():assert digest(P/n)==h,n
 parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());assert digest(B/parent['requirements'])==parent['requirements_sha256']
 ledger=pd.read_csv(B/parent['requirements'],low_memory=False);population=ledger[ledger.field.eq('goal_line_clearances')][K].copy()
 refs=json.loads((P/'reference_selection_plan.json').read_text())
 for name,sha in refs['reference_files'].items():
  path=P.parent/name;assert digest(path)==sha,name
 reference=pd.read_csv(P.parent/'goal_line_events/predictions.csv.gz',usecols=K);reference=reference[reference.season.eq('2025-26')]
 population=pd.concat([population,reference],ignore_index=True);assert not population.duplicated(K).any()
 sources=json.loads((P/'sources.json').read_text());deps={str((B/parent['requirements']).relative_to(R)):parent['requirements_sha256']}
 for name,sha in refs['reference_files'].items():deps[str((P.parent/name).relative_to(R))]=sha
 ranked_ids=json.loads((P/'plan.json').read_text())['seasons'];ranked_ids.update(json.loads((P/'control_extension_plan.json').read_text())['additional_control_seasons'])
 primary_sources_path=R/'scoring_2026_27/delta_input_audit/primary_sources.json';deps[str(primary_sources_path.relative_to(R))]=digest(primary_sources_path);primary_sources=json.loads(primary_sources_path.read_text())
 rows=[];summary=[]
 for source in sources:
  season=source['season'];path=P/source['file'];assert digest(path)==source['sha256'];body=json.loads(path.read_text())
  assert body['entity']=='clearance_off_line' and body['stats']['pageInfo']['numPages']==1
  records=body['stats']['content'];assert len(records)==body['stats']['pageInfo']['numEntries'];codes={}
  for v in records:
   assert v['name']=='clearance_off_line' and v['value']>=0 and int(v['value'])==v['value'];code=int(v['owner']['altIds']['opta'].lstrip('p'));assert code not in codes;codes[code]=(int(v['value']),int(v['owner']['id']))
  rosterfile='inputs/primary/players_'+season+'.json';frozen=next(x for x in primary_sources if x['file']==rosterfile);assert 'compSeasons='+str(ranked_ids[season])+'&' in frozen['url']
  roster_path=R/'scoring_2026_27/delta_input_audit'/rosterfile;assert digest(roster_path)==frozen['sha256'];deps[str(roster_path.relative_to(R))]=digest(roster_path)
  rosterbody=json.loads(roster_path.read_text());assert rosterbody['entity']=='appearances' and rosterbody['stats']['pageInfo']['numPages']==1
  active={}
  for v in rosterbody['stats']['content']:
   assert v['name']=='appearances' and v['value']>=0 and int(v['value'])==v['value'];code=int(v['owner']['altIds']['opta'].lstrip('p'))
   if v['value']>0:assert code not in active;active[code]=int(v['owner']['id'])
  zeros={code for code,(count,owner) in codes.items() if count==0 and code in active}
  assert all(codes[code][1]==active[code] for code in zeros)
  selected=population[population.season.eq(season)&population.code.isin(zeros)].copy();selected['value']=0;selected['proof']='explicit_nonnegative_player_season_goal_line_counter_zero';rows.append(selected[K+['value','proof']]);summary.append(dict(season=season,ranked_players=len(codes),explicit_zero_players=len(zeros),predicted_player_matches=len(selected)))
 predictions=pd.concat(rows,ignore_index=True);assert not predictions.duplicated(K).any();save(predictions,'predictions.csv.gz');save(pd.DataFrame(summary),'source_scope.csv');write(P/'dependencies.json',deps)
 write(P/'prediction_freeze.json',{n:digest(P/n) for n in ['predict.py','reference_selection_plan.json','reference_selection_freeze.json','plan.json','selection_freeze.json','control_extension_plan.json','control_extension_freeze.json','inputs/parent_CURRENT.json','sources.json','predictions.csv.gz','source_scope.csv','dependencies.json']})
 print(pd.DataFrame(summary).to_string(index=False));print('Frozen predictions',len(predictions))
if __name__=='__main__':main()
