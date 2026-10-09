"""Freeze exact-exhaustion candidates and all independent complete controls."""
from pathlib import Path
import pandas as pd,json,gzip,hashlib
P=Path(__file__).resolve().parent;B=P.parents[1];R=B.parents[1];K=['season','fixture','code'];G=['season','code']
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def save(d,n):
 raw=d.to_csv(index=False).encode();(P/n).write_bytes(gzip.compress(raw,mtime=0) if n.endswith('.gz') else raw)
def main():
 for n,h in json.loads((P/'selection_freeze.json').read_text()).items():assert digest(P/n)==h,n
 plan=json.loads((P/'plan.json').read_text());parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());before_path=B/parent['requirements'];assert digest(before_path)==parent['requirements_sha256']
 before=pd.read_csv(before_path,low_memory=False);native_path=R/'training_dataset/scoring/results/historical_inventory.csv.xz';native=pd.read_csv(native_path,usecols=K+['minutes'])
 deps={str(before_path.relative_to(R)):digest(before_path),str(native_path.relative_to(R)):digest(native_path)}
 correction_path=B/parent['native_fpl_corrections'];assert digest(correction_path)==parent['native_fpl_corrections_sha256'];corrections=pd.read_csv(correction_path);deps[str(correction_path.relative_to(R))]=digest(correction_path)
 # Identity-only positive-minute population uses the approved native correction.
 for row in corrections[corrections.field.eq('minutes')].itertuples():
  mask=native.season.eq(row.season)&native.fixture.eq(row.fixture)&native.code.eq(row.code);assert mask.sum()==1;native.loc[mask,'minutes']=row.value
 pop=before[before.field.eq('goal_line_clearances')&before.position.isin(['DEF','MID','FWD'])].merge(native,on=K,validate='one_to_one');pop=pop[pop.minutes.gt(0)]
 known=pop[~pop.is_open];assert known.value.notna().all() and known.value.ge(0).all() and known.value.mod(1).eq(0).all()
 counts=pop.groupby(G).agg(inventory_matches=('fixture','size'),open_matches=('is_open','sum'));sums=known.groupby(G).value.sum().to_dict()
 old=P.parent/plan['source_stage']
 for n,h in plan['sources_sha256'].items():assert digest(old/n)==h,n;deps[str((old/n).relative_to(R))]=h
 raw_sources=json.loads((old/'sources.json').read_text());group_rows=[];predictions=[]
 for src in raw_sources:
  season=src['season']
  path=old/src['file'];assert digest(path)==src['sha256'];deps[str(path.relative_to(R))]=digest(path)
  if season=='2025-26':continue
  data=json.loads(path.read_text());assert data['entity']=='clearance_off_line' and data['stats']['pageInfo']['numPages']==1
  roster_path=R/'scoring_2026_27/delta_input_audit/inputs/primary'/('players_'+season+'.json');deps[str(roster_path.relative_to(R))]=digest(roster_path);body=json.loads(roster_path.read_text());assert body['entity']=='appearances' and body['stats']['pageInfo']['numPages']==1
  appearances={int(x['owner']['altIds']['opta'][1:]):(int(x['value']),int(x['owner']['id'])) for x in body['stats']['content']};assert len(appearances)==len(body['stats']['content'])
  codes=set()
  for item in data['stats']['content']:
   code=int(item['owner']['altIds']['opta'][1:]);assert code not in codes;codes.add(code);total=item['value'];assert total>=0 and total%1==0
   if total==0 or (season,code) not in counts.index:continue
   assert code in appearances and int(item['owner']['id'])==appearances[code][1]
   n,open_count=map(int,counts.loc[(season,code)].to_numpy());expected=appearances[code][0];inventory_complete=n==expected and expected>0
   known_sum=float(sums.get((season,code),0));row=dict(season=season,code=code,source_total=int(total),primary_appearances=expected,inventory_matches=n,open_matches=open_count,known_sum=known_sum,inventory_complete=inventory_complete,all_values_complete=inventory_complete and open_count==0)
   group_rows.append(row)
   if inventory_complete and open_count>0 and known_sum==total:
    selected=pop[pop.season.eq(season)&pop.code.eq(code)&pop.is_open&pop.status.eq('missing_data')];assert selected.value.isna().all()
    for target in selected.itertuples():predictions.append(dict(season=season,fixture=target.fixture,code=code,field='goal_line_clearances',value=0,proof='known_approved_whole_season_gl_exhausts_explicit_primary_positive_player_total'))
 groups=pd.DataFrame(group_rows);pred=pd.DataFrame(predictions,columns=K+['field','value','proof']);assert not pred.duplicated(K).any();save(groups,'season_groups.csv');save(pred,'predictions.csv.gz');write(P/'dependencies.json',deps)
 write(P/'prediction_freeze.json',{n:digest(P/n) for n in ['plan.json','predict.py','selection_freeze.json','inputs/parent_CURRENT.json','season_groups.csv','predictions.csv.gz','dependencies.json']})
 print('Frozen explicit positive source groups',len(groups),'candidate fields',len(pred),'with complete controls retained irrespective of agreement')
if __name__=='__main__':main()
