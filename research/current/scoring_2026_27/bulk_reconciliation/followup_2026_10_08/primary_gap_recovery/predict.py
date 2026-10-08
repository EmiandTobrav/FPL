from pathlib import Path
import pandas as pd,json,gzip,hashlib
from conservation import exhausts,cbi,legacy_net
P=Path(__file__).resolve().parent;S=P.parent;K=['season','fixture','code'];T=['season','fixture','primary_team_id']
MAP={'times_tackled':'times_tackled','saved_obox':'saves_outside_box','was_fouled':'fouls_won','ontarget_scoring_att':'shots_on_target','won_tackle':'won_tackles','total_tackle':'total_tackles','att_pen_goal':'penalty_goals','clearance_off_line':'goal_line_clearances'}
COMP=['total_clearance','outfielder_block','interception']
def save(d,n):(P/n).write_bytes(gzip.compress(d.to_csv(index=False).encode(),mtime=0) if n.endswith('.gz') else d.to_csv(index=False).encode())
def main():
 p=pd.DataFrame(json.loads((P/'players.json').read_text()));roster=pd.read_csv(P/'roster.csv');assert len(p)==len(roster) and not p.duplicated(K).any()
 for n in list(MAP)+COMP:
  if n not in p:p[n]=float('nan')
  a=p[n].dropna();assert a.ge(0).all() and a.mod(1).eq(0).all()
 before=pd.read_csv(S/'bulk_followup/results/requirements.csv.gz',low_memory=False);teams=pd.read_csv(S/'season_conservation/inputs/full_team_totals.csv');season=pd.read_csv(S/'season_conservation/combined/season_proofs.csv');teams=teams.merge(season[['season','primary_team_id','tier2_qualified']],on=['season','primary_team_id'],validate='many_to_one')
 known=before[(before.field=='goal_line_clearances')&~before.is_open&before.value.gt(0)].merge(roster[K+['primary_team_id']],on=K,validate='one_to_one');veto=set(map(tuple,known[T].to_numpy()));veto.update(map(tuple,p.loc[p.clearance_off_line.gt(0),T].to_numpy()))
 teams['line_zero_qualified']=[bool(r.tier2_qualified and (pd.isna(r.clearance_off_line) or r.clearance_off_line==0) and (r.season,r.fixture,r.primary_team_id) not in veto) for r in teams.itertuples()]
 teams.loc[teams.line_zero_qualified,'clearance_off_line']=0
 parents=teams.set_index(T);q=p.copy();proof=[];methods={}
 for col in list(MAP)+COMP:
  parent='fk_foul_won' if col=='was_fouled' else col
  for key,group in p.groupby(T):
   total=parents.loc[key,parent] if parent in parents else float('nan');vals=group[col];lower=vals.sum();valid=pd.notna(total) and total>=0 and total%1==0;qual=exhausts(total,vals)
   proof.append(dict(zip(T,key),counter=col,parent_counter=parent,total=total,known_sum=lower,active_players=len(group),explicit_players=int(vals.notna().sum()),missing_players=int(vals.isna().sum()),qualified=qual,reason='exact_exhaustion' if qual else 'missing_parent' if not valid else 'positive_residual' if lower<total else 'conflict'))
   if qual:q.loc[group.index[vals.isna()],col]=0
  for i in q.index:methods[(i,col)]='explicit_primary_player' if pd.notna(p.loc[i,col]) else 'exact_primary_team_conservation'
 q['clearances_blocks_interceptions']=[cbi(v) for v in q[COMP].to_numpy()];q['legacy_net_tackles']=[legacy_net(a,b) for a,b in zip(q.won_tackle,q.total_tackle)]
 rows=[]
 for i,r in q.iterrows():
  for col,field in {**MAP,'clearances_blocks_interceptions':'clearances_blocks_interceptions','legacy_net_tackles':'legacy_net_tackles'}.items():
   if pd.isna(r[col]):continue
   rows.append({**{k:r[k] for k in K+['primary_team_id','pl_player_id','pulse_id','scope']},'field':field,'value':r[col],'method':methods.get((i,col),'complete_component_arithmetic')})
 save(pd.DataFrame(rows),'predictions.csv.gz');save(pd.DataFrame(proof),'conservation.csv');save(q,'qualified_components.csv.gz')
 files=[P/n for n in ['predict.py','conservation.py','protocol.json','players.json','roster.csv','sources.json','fixture_plan.csv']]+[S/'bulk_followup/results/requirements.csv.gz',S/'season_conservation/inputs/full_team_totals.csv',S/'season_conservation/combined/season_proofs.csv']
 freeze={'inputs':{str(f.relative_to(S)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'predictions_sha256':hashlib.sha256((P/'predictions.csv.gz').read_bytes()).hexdigest()}
 if (P/'freeze.json').exists():assert json.loads((P/'freeze.json').read_text())==freeze
 (P/'freeze.json').write_text(json.dumps(freeze,indent=2)+'\n');print(pd.DataFrame(rows).groupby(['scope','field']).size().to_string())
if __name__=='__main__':main()
