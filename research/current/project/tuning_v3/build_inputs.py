"""Point-in-time opening forecasts. No outcomes are passed to the optimizer.
Future fixtures are the final historical schedule: an explicit proxy, not archived
announcement snapshots. New registrations are delayed until observed before cutoff.
"""
from pathlib import Path
import sys,pickle,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge,BayesianRidge
from sklearn.ensemble import ExtraTreesRegressor
ROOT=Path(__file__).resolve().parents[1]; OUT=Path(__file__).resolve().parent
SEASONS=[f'{y}-{str(y+1)[-2:]}' for y in range(2020,2026)]
STATS=['historic','minutes','goals_scored','assists','clean_sheets','played','long_play']
LAG=[f'{v}_m{w}' for w in [6,12,38] for v in STATS]
BASE=LAG+['last_price','n_history']+[f'pos_{i}' for i in range(1,5)]+[f'price_pos_{i}' for i in range(1,5)]
FX=[f'{v}_pos_{i}' for v in ['home','elo_diff','opp_ga','team_gf'] for i in range(1,5)]
def design(p):
 p=p.copy()
 for i in range(1,5):
  p[f'pos_{i}']=(p.pos==i).astype(int);p[f'price_pos_{i}']=p.last_price*p[f'pos_{i}']
  for v in ['home','elo_diff','opp_ga','team_gf']:
   p[f'{v}_pos_{i}']=p[v]*p[f'pos_{i}']*p.minutes_m12.fillna(60).clip(0,90)/90
 return p

def main():
 d=pd.read_pickle(ROOT/'results/features.pkl').sort_values('available');fixtures=[]
 for y in range(2019,2026):
  s=f'{y}-{str(y+1)[-2:]}'
  t=pd.read_csv(ROOT/f'data/{s}_teams.csv').set_index('id').code
  f=pd.read_csv(ROOT/f'data/{s}_fixtures.csv');f['season']=s
  f['homeclub']=f.team_h.map(t);f['awayclub']=f.team_a.map(t)
  f['available']=pd.to_datetime(f.kickoff_time,utc=True)+pd.Timedelta(hours=3)
  fixtures.append(f)
 fixtures=pd.concat(fixtures).sort_values('available')
 states={};hist=[]
 for r in fixtures.itertuples():
  if pd.isna(r.team_h_score):continue
  for k in [r.homeclub,r.awayclub]:states.setdefault(k,{'elo':1500.,'gf':1.35,'ga':1.35})
  h,a=states[r.homeclub],states[r.awayclub]
  win=1/(1+10**((a['elo']-h['elo']-60)/400));delta=20*((r.team_h_score>r.team_a_score)+.5*(r.team_h_score==r.team_a_score)-win)
  h['elo']+=delta;a['elo']-=delta
  for k,gf,ga in [(r.homeclub,r.team_h_score,r.team_a_score),(r.awayclub,r.team_a_score,r.team_h_score)]:
   st=states[k];st['gf']=.85*st['gf']+.15*gf;st['ga']=.85*st['ga']+.15*ga
   hist.append({'club':k,'time':r.available,**st})
 hist=pd.DataFrame(hist)
 # Every feature in training is lagged; outcomes only used as training labels.
 train_design=design(d)
 preseason=pd.read_csv(ROOT/'simulation/preseason_predictions.csv').set_index(['season','pid'])
 audits=[]
 for s in SEASONS:
  with open(ROOT/f'simulation/cache_{s}.pkl','rb') as f:old=pickle.load(f)
  cutoff=pd.Timestamp(old[1]['cutoff']);tr=train_design[(train_design.season<s)&(train_design.available<cutoff)]
  models={}
  for name,cols,est in [('basic',BASE,Ridge(alpha=100)),('ridge',BASE+FX,Ridge(alpha=100)),('bayes',BASE+FX,BayesianRidge()),('extra',BASE+FX,ExtraTreesRegressor(n_estimators=48,max_depth=12,min_samples_leaf=40,max_features=.8,n_jobs=2,random_state=173))]:
   model=make_pipeline(SimpleImputer(add_indicator=True),StandardScaler(),est);model.fit(tr[cols],tr.historic)
   models[name]=(model,cols)
  initial=old[1]['frame'].set_index('pid');currentseason=d[d.season==s];games={};eligible=set(initial.index)
  sf=fixtures[fixtures.season==s]
  for gw in range(1,20):
   cut=pd.Timestamp(old[gw]['cutoff']);past=d[d.available<cut]
   thispast=currentseason[currentseason.available<cut]
   eligible.update(thispast.pid.astype(int));last=past.drop_duplicates('pid',keep='last').set_index('pid')
   # Current-season club updates only from already observed rows.
   cur=thispast.drop_duplicates('pid',keep='last').set_index('pid')
   p=pd.DataFrame(index=pd.Index(sorted(eligible),name='pid'))
   for c in ['pos','club','name','initial_price']:
    p[c]=initial[c].reindex(p.index)
   p['club']=cur.club.reindex(p.index).fillna(p.club)
   p['pos']=cur.pos.reindex(p.index).fillna(p.pos).astype(int)
   p['name']=p.name.fillna(cur['name'].reindex(p.index))
   p['market']=np.rint(cur.price.reindex(p.index)*10).fillna(p.initial_price).fillna(last.price.reindex(p.index)*10).astype(int)
   p['can_buy']=True # Absence from the current outcome file cannot forbid a purchase.
   p['last_price']=p.market/10
   p['n_history']=past.groupby('pid').size().reindex(p.index).fillna(0)
   for w in [6,12,38]:
    means=past.groupby('pid').tail(w).groupby('pid')[STATS].mean()
    for c in STATS:p[f'{c}_m{w}']=means[c].reindex(p.index)
   team=hist[hist.time<cut].drop_duplicates('club',keep='last').set_index('club')
   p['elo']=p.club.map(team.elo).fillna(1500);p['team_gf']=p.club.map(team.gf).fillna(1.35)
   forecasts={name:np.zeros((len(p),19-gw+1)) for name in models}
   batch=[];counts=np.zeros((len(p),19-gw+1));index_map={pid:i for i,pid in enumerate(p.index)}
   for future in range(gw,20):
    schedule=sf[sf.event==future]
    for r in schedule.itertuples():
     for club,opp,home in [(r.homeclub,r.awayclub,1),(r.awayclub,r.homeclub,0)]:
      mask=p.club==club
      if not mask.any():continue
      x=p.loc[mask].copy();x['home']=home
      x['elo_diff']=x.elo-(team.loc[opp,'elo'] if opp in team.index else 1500)
      x['opp_ga']=team.loc[opp,'ga'] if opp in team.index else 1.35
      x['_row']=[index_map[i] for i in x.index];x['_col']=future-gw
      batch.append(x);counts[mask.to_numpy(),future-gw]+=1
   x=design(pd.concat(batch))
   for name,(model,cols) in models.items():
    np.add.at(forecasts[name],(x._row.to_numpy(),x._col.to_numpy()),np.maximum(0,model.predict(x[cols])))
   neutral_x=p.copy();neutral_x['home']=.5
   league=set(sf.homeclub)|set(sf.awayclub)
   rating=team.reindex(list(league));neutral_x['elo_diff']=neutral_x.elo-rating.elo.fillna(1500).mean();neutral_x['opp_ga']=rating.ga.fillna(1.35).mean()
   neutral_x=design(neutral_x)
   neutral={name:np.maximum(0,model.predict(neutral_x[cols])).astype(np.float32) for name,(model,cols) in models.items()}
   pp=preseason.loc[s].preseason_ridge.reindex(p.index)
   pp=pp.fillna(pd.Series(forecasts['ridge'][:,0],index=p.index))
   # Prior affects only registered preseason players; fades by GW7.
   weight=max(0,.75*(7-gw)/6)
   forecasts['prior']=weight*(pp.to_numpy()[:,None]*counts)+(1-weight)*forecasts['ridge']
   neutral['prior']=(weight*pp.to_numpy()+(1-weight)*neutral['ridge']).astype(np.float32)
   games[gw]={'neutral':neutral,'fixture_count':counts[:,0].astype(np.float32),'frame':p.reset_index()[['pid','pos','club','name','market','can_buy']],
              'forecast':{k:v.astype(np.float32) for k,v in forecasts.items()},
              'actual':old[gw]['actual'],'active':old[gw]['active'],'cutoff':str(cut)}
   assert not len(past) or past.available.max()<cut
  with open(OUT/f'inputs_{s}.pkl','wb') as f:pickle.dump(games,f)
  audits.append({'season':s,'training_rows':len(tr),'training_max_available':str(tr.available.max()),'first_cutoff':str(cutoff),'gw1_players':len(initial),'gw19_players':len(games[19]['frame'])})
  print('Prepared neutral forecasts',s,len(tr),flush=True)
 pd.DataFrame(audits).to_csv(OUT/'input_audit.csv',index=False)
 (OUT/'feature_spec.json').write_text(json.dumps({'base':BASE,'fixture':FX,'elo_K':20,'home_elo_advantage':60,'training':'expanding prior seasons only','forecast_horizon':19,'schedule':'final historical event assignment; not timestamped announcements','eligibility':'GW1 archive roster then observed before deadline only','excluded':['current outcome row eligibility','current actual availability','future Elo','future model outputs','elite ownership not available pre-deadline']},indent=2))
if __name__=='__main__':main()
