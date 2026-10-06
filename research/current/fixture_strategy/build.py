from pathlib import Path
import sys,json,pickle,hashlib
import numpy as np,pandas as pd
from sklearn.linear_model import Ridge
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from fixture_strategy.features import design,effect,assemble
from upside.features import load_history
from decision_specialist.models import future_proxy
from calendar_audit.selector import select_before
OUT=HERE/'results';SEASONS=[f'{y}-{str(y+1)[-2:]}' for y in range(2022,2026)]

def main():
    d,fixtures,th=load_history();selection=pd.read_csv(CURRENT/'calendar_audit/selection.csv');audits=[];fits={}
    sources=json.loads((CURRENT/'calendar_audit/source_commits.json').read_text())
    for s in SEASONS:
        games=pickle.load(open(CURRENT/f'results/games_{s}.pkl','rb'));cut=pd.Timestamp(games[1]['cutoff'])
        train=d[(d.season<s)&(d.available<cut)&d.pos.isin([1,2,3,4])].copy()
        coeff={}
        for pos,q in train.groupby('pos'):
            x=design(q.historic_m6,q.minutes_m6,q.team_gf,q.team_ga,q.home,q.opp_ga,q.opp_gf)
            m=Ridge(alpha=100,fit_intercept=False).fit(x,q.historic)
            coeff[int(pos)]=m.coef_.tolist()
        fits[s]=dict(coefficients=coeff,training_rows=len(train),max_available=str(train.available.max()),season_cutoff=str(cut))
        gate=pd.read_csv(CURRENT/f'decision_specialist/results/gate_{s}.csv.gz');old=pd.read_csv(CURRENT/f'decision_specialist/results/horizon_{s}.csv.gz')
        codes=pd.read_csv(CURRENT/f'project/data/{s}_teams.csv').set_index('id').code;rows=[]
        for r in selection[selection.season==s].itertuples():
            g=games[r.gw];p=g['frame'];cut=pd.Timestamp(g['cutoff']);assert select_before(sources[s],cut)['sha']==r.sha
            assert pd.Timestamp(r.snapshot_time)<cut and r.age_days>=0
            past=d[d.available<cut].sort_values('available');minutes=p.pid.map(past.groupby('pid').tail(6).groupby('pid').minutes.mean()).fillna(45).to_numpy()
            team=th[th.time<cut].sort_values('time').drop_duplicates('club',keep='last').set_index('club')
            def strength(opp,col):return float(team.loc[opp,col]) if opp in team.index else 1.35
            h=old[old.gw==r.gw];q=gate[gate.gw==r.gw];assert np.array_equal(q.pid,p.pid) and np.array_equal(h.pid,p.pid)
            ref=.5*g['pred']['ridge']+.5*g['pred']['extra'];base=future_proxy(q.constant.to_numpy(),ref,g['count'],h.reference_1.to_numpy(),8)
            snap=pd.read_csv(CURRENT/f'calendar_audit/snapshots/{s}_{r.sha}.csv.gz',usecols=['id','event','team_h','team_a'])
            snap['home']=snap.team_h.map(codes);snap['away']=snap.team_a.map(codes);assert snap[['home','away']].notna().all().all()
            cur=fixtures[(fixtures.season==s)&(fixtures.event==r.gw)]
            row=q[['season','gw','pid','cutoff']].copy()
            for name in ['count','venue','opponent','full']:
                current=np.zeros(len(p));counts=np.zeros(len(p))
                for f in cur.itertuples():
                    for club,opp,home in [(f.home,f.away,1),(f.away,f.home,0)]:
                        mask=p.club.to_numpy()==club
                        current[mask]+=effect(p.pos,minutes,home,strength(opp,'ga'),strength(opp,'gf'),coeff,name)[mask];counts[mask]+=1
                current/=np.maximum(counts,1)
                fx={}
                for j in range(1,min(8,39-r.gw)):
                    fx[j]=[]
                    for f in snap[snap.event==r.gw+j].itertuples():
                        e=np.full(len(p),np.nan)
                        for club,opp,home in [(f.home,f.away,1),(f.away,f.home,0)]:
                            mask=p.club.to_numpy()==club
                            e[mask]=effect(p.pos,minutes,home,strength(opp,'ga'),strength(opp,'gf'),coeff,name)[mask]
                        fx[j].append(e)
                forecast=assemble(base,current,fx,r.age_days)
                np.testing.assert_array_equal(forecast[:,0],base[:,0])
                for j in range(8):row[f'{name}_{j}']=forecast[:,j]
            archived=pd.read_csv(CURRENT/f'calendar_counts/results/horizon_{s}.csv.gz');a=archived[archived.gw==r.gw]
            np.testing.assert_allclose(row[[f'count_{j}' for j in range(3)]],a[[f'calendar_count_{j}' for j in range(3)]],rtol=0,atol=1e-12)
            rows.append(row);audits.append(dict(season=s,gw=r.gw,age_days=r.age_days,calendar_used=r.age_days<=14,cutoff=str(cut),max_team_time=str(team.time.max()),max_player_time=str(past.available.max()),changed_cells=int(np.count_nonzero(row.full_1-row.count_1))))
        pd.concat(rows,ignore_index=True).to_csv(OUT/f'forecast_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0});print('BUILT',s,flush=True)
    (OUT/'coefficients.json').write_text(json.dumps(fits,indent=2));pd.DataFrame(audits).to_csv(OUT/'forecast_audit.csv',index=False)
if __name__=='__main__':main()
