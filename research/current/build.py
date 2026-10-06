from pathlib import Path
import sys,pickle,json,time,warnings
warnings.filterwarnings("ignore",category=UserWarning)
import numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge,BayesianRidge
from sklearn.ensemble import ExtraTreesRegressor,HistGradientBoostingRegressor
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'project'));sys.path.insert(0,str(ROOT/'project/tuning_v3'))
import research
from build_inputs import design,BASE,FX,STATS
SEASONS=[f'{y}-{str(y+1)[-2:]}' for y in range(2020,2026)]
NEW=['team_ga','opp_gf','xgf','xga','opp_xgf','opp_xga','lambda_for','lambda_against','p_clean','expected_goals_m6','expected_assists_m6','starts_m6','saves_m6','bonus_m6','minutes_trend']
def augment(p):
 p=design(p)
 # Smoothed goal-rate matchup features. These are NOT a fitted Dixon-Coles model.
 p['lambda_for']=np.clip(p.team_gf*p.opp_ga/1.35*np.where(p.home==1,1.12,.90),.15,5)
 p['lambda_against']=np.clip(p.opp_gf*p.team_ga/1.35*np.where(p.home==1,.90,1.12),.15,5)
 p['p_clean']=np.exp(-p.lambda_against)
 for i in range(1,5):
  for c in ['opp_gf','team_ga','p_clean','lambda_for','xgf','opp_xga']:
   p[f'{c}_pos_{i}']=p[c]*(p.pos==i)*p.minutes_m12.fillna(60).clip(0,90)/90
 return p
EXT=BASE+FX+NEW+[f'{c}_pos_{i}' for i in range(1,5) for c in ['opp_gf','team_ga','p_clean','lambda_for','xgf','opp_xga']]

def main():
 t0=time.time()
 d,fixtures=research.load_data()
 # Preserve explicit starts only where available. Derive missing historic starts from 60+ as a stated proxy.
 d['starts']=d['starts'].fillna(d.long_play)
 if not (ROOT/'project/results/features.pkl').exists():
  d,_=research.features(d,fixtures)
 else:d=pd.read_pickle(ROOT/'project/results/features.pkl')
 # lagged team xG reconstructed from sum of player xG, only for seasons with actual xG coverage.
 tx=d.groupby(['season','fixture','club','opponent','available'],as_index=False).agg(xgf=('expected_goals',lambda x:x.sum(min_count=1)))
 inv=tx[['season','fixture','club','xgf']].rename(columns={'club':'opponent','xgf':'xga'})
 tx=tx.merge(inv,on=['season','fixture','opponent'],validate='one_to_one').sort_values('available')
 tx['xgf_sm']=tx.groupby('club').xgf.transform(lambda x:x.ewm(alpha=.15,adjust=False).mean())
 tx['xga_sm']=tx.groupby('club').xga.transform(lambda x:x.ewm(alpha=.15,adjust=False).mean())
 for side,key in [('', 'club'),('opp_','opponent')]:
  h=tx[['club','available','xgf_sm','xga_sm']].rename(columns={'club':key,'available':side+'xgtime','xgf_sm':side+'xgf','xga_sm':side+'xga'}).sort_values(side+'xgtime')
  d=pd.merge_asof(d.sort_values('cutoff'),h,left_on='cutoff',right_on=side+'xgtime',by=key,allow_exact_matches=False)
  assert (d[side+'xgtime'].dropna()<d.loc[d[side+'xgtime'].notna(),'cutoff']).all()
 d['minutes_trend']=d.minutes_m6-d.minutes_m12
 # starts absent in saved feature expansion; played/long_play used as pre-match proxy.
 d['starts_m6']=d.long_play_m6
 train=augment(d)
 # Recreate team histories, including all seasons, using only past available outcomes.
 history=[];states={}
 for r in fixtures.sort_values('available').itertuples():
  if pd.isna(r.team_h_score):continue
  for k in [r.home,r.away]:states.setdefault(k,dict(elo=1500.,gf=1.35,ga=1.35))
  h,a=states[r.home],states[r.away];delta=20*(float(r.team_h_score>r.team_a_score)+.5*float(r.team_h_score==r.team_a_score)-1/(1+10**((a['elo']-h['elo']-60)/400)))
  h['elo']+=delta;a['elo']-=delta
  for k,gf,ga in [(r.home,r.team_h_score,r.team_a_score),(r.away,r.team_a_score,r.team_h_score)]:
   states[k]['gf']=.85*states[k]['gf']+.15*gf;states[k]['ga']=.85*states[k]['ga']+.15*ga
   history.append(dict(club=k,time=r.available,**states[k]))
 th=pd.DataFrame(history);audit=[]
 for s in SEASONS:
  if (ROOT/f'results/games_{s}.pkl').exists():
   print('EXISTING',s,flush=True);continue
  with open(ROOT/f'project/tuning_v3/inputs_{s}.pkl','rb') as f:old=pickle.load(f)
  tr=train[(train.season<s)&(train.available<pd.Timestamp(old[1]['cutoff']))]
  models={}
  configs=[('ridge',BASE+FX,Ridge(alpha=100)),('bayes',BASE+FX,BayesianRidge()),('extra',BASE+FX,ExtraTreesRegressor(n_estimators=48,max_depth=12,min_samples_leaf=40,max_features=.8,n_jobs=1,random_state=173)),('hgb',BASE+FX,HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=15,min_samples_leaf=60,l2_regularization=20,early_stopping=False,random_state=173)),('hgb_extended',EXT,HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=15,min_samples_leaf=60,l2_regularization=20,early_stopping=False,random_state=173))]
  for name,cols,est in configs:
   m=make_pipeline(SimpleImputer(add_indicator=True),StandardScaler(),est);m.fit(tr[cols],tr.historic);models[name]=(m,cols)
  initial=old[1]['frame'].set_index('pid');eligible=set(initial.index);sf=fixtures[fixtures.season==s];games={};checks=[]
  for gw in range(1,39):
   schedule=sf[sf.event==gw];cut=pd.to_datetime(schedule.kickoff_time,utc=True).min()-pd.Timedelta(hours=36)
   if gw<=19:cut=pd.Timestamp(old[gw]['cutoff'])
   if pd.isna(cut):raise ValueError((s,gw,'missing cutoff'))
   past=d[d.available<cut];cur=past[past.season==s].sort_values('available').drop_duplicates('pid',keep='last').set_index('pid')
   eligible.update(cur.index.astype(int));p=pd.DataFrame(index=pd.Index(sorted(eligible),name='pid'))
   for c in ['pos','club','name','market']:p[c]=initial[c].reindex(p.index)
   p['club']=cur.club.reindex(p.index).fillna(p.club);p['pos']=cur.pos.reindex(p.index).fillna(p.pos).astype(int)
   p['name']=p.name.fillna(cur['name'].reindex(p.index));p['market']=np.rint(cur.price.reindex(p.index)*10).fillna(p.market).astype(int)
   p['can_buy']=True;p['last_price']=p.market/10;p['n_history']=past.groupby('pid').size().reindex(p.index).fillna(0)
   for w in [6,12,38]:
    cols=list(dict.fromkeys(STATS+['expected_goals','expected_assists','saves','bonus']))
    means=past.sort_values('available').groupby('pid').tail(w).groupby('pid')[cols].mean()
    for c in cols:p[f'{c}_m{w}']=means[c].reindex(p.index)
   p['starts_m6']=p.long_play_m6;p['minutes_trend']=p.minutes_m6-p.minutes_m12
   team=th[th.time<cut].sort_values('time').drop_duplicates('club',keep='last').set_index('club')
   xteam=tx[tx.available<cut].sort_values('available').drop_duplicates('club',keep='last').set_index('club')
   for c in ['gf','ga']:p['team_'+c]=p.club.map(team[c]).fillna(1.35)
   p['elo']=p.club.map(team.elo).fillna(1500)
   for c in ['xgf','xga']:p[c]=p.club.map(xteam[c+'_sm'])
   xp={k:np.zeros(len(p)) for k in models};counts=np.zeros(len(p));positions={pid:i for i,pid in enumerate(p.index)};batch=[]
   for r in schedule.itertuples():
    for club,opp,home in [(r.home,r.away,1),(r.away,r.home,0)]:
     x=p[p.club==club].copy()
     if not len(x):continue
     x['home']=home;x['elo_diff']=x.elo-(team.loc[opp,'elo'] if opp in team.index else 1500)
     for c in ['gf','ga']:x['opp_'+c]=team.loc[opp,c] if opp in team.index else 1.35
     for c in ['xgf','xga']:x['opp_'+c]=xteam.loc[opp,c+'_sm'] if opp in xteam.index else np.nan
     x['_row']=[positions[i] for i in x.index];counts[x._row]+=1;batch.append(x)
   if batch:
    batch=augment(pd.concat(batch))
    for name,(m,cols) in models.items():np.add.at(xp[name],batch._row,np.maximum(0,m.predict(batch[cols])))
   if gw<=19:
    orig=old[gw];assert np.array_equal(orig['frame'].pid,p.index)
    for name in ['ridge','bayes','extra']:
     checks.append(float(np.max(np.abs(xp[name]-orig['forecast'][name][:,0]))))
     # Existing opening inputs are authoritative, keep original receiver projections in GW1-19.
     xp[name]=orig['forecast'][name][:,0]
   actual=d[(d.season==s)&(d.event==gw)]
   active=actual.assign(active=(actual.minutes>0)|(actual.yellow_cards>0)|(actual.red_cards>0)).groupby('pid').active.max().to_dict()
   games[gw]=dict(frame=p.reset_index()[['pid','pos','club','name','market','can_buy']],pred=xp,actual=actual.groupby('pid').historic.sum().to_dict(),active=active,cutoff=str(cut),count=counts)
  with open(ROOT/f'results/games_{s}.pkl','wb') as f:pickle.dump(games,f)
  audit.append(dict(season=s,training_rows=len(tr),training_max=str(tr.available.max()),first_cutoff=old[1]['cutoff'],old_forecast_max_difference=max(checks),rounds=len(games),players_last=len(p)))
  (ROOT/f'results/audit_{s}.json').write_text(json.dumps(audit[-1]))
  print('BUILT',s,audit[-1],'seconds',round(time.time()-t0),flush=True)
 pd.DataFrame(audit).to_csv(ROOT/'results/input_audit.csv',index=False)
 (ROOT/'results/feature_spec.json').write_text(json.dumps(dict(base=BASE+FX,extended=EXT),indent=2))
if __name__=='__main__':main()
