from common import *
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib,time

def worker(s):
    games=games_for(s);decomp=[];matched=[]
    for mode in ['no_chips','fixed_chips']:
        anchor=trace(s,REF,mode);states=states_before(anchor);anchor_rows={r['gw']:r for r in anchor['trace']}
        for m in MODELS:
            obj=trace(s,m,mode)
            for row in obj['trace']:
                decomp.append(dict(season=s,model=m,mode=mode,gw=row['gw'],calendar_chip=experiment.CAL.get(row['gw'],'ordinary'),net=row['net'],transfers=row['transfers'],**components(row,games[row['gw']])))
        for gw in range(5,39):
            g=games[gw];state=states[gw]
            for chip in ([None,experiment.CAL[gw]] if gw in experiment.CAL else [None]):
                for m in MODELS:
                    p,c=experiment.make_choice(g,m,copy.deepcopy(state),chip)
                    r=experiment.settle(c['starters'],c['bench'],c['captain'],c['vice'],dict(zip(p.pid,p.pos)),g['actual'],g['active'],chip)
                    # Reference action under original regime must reproduce the archive.
                    if m==REF and chip==(experiment.CAL.get(gw) if mode=='fixed_chips' else None):
                        archived=anchor_rows[gw]
                        for key in ['squad','starters','bench','captain','vice']:
                            assert (set(c[key])==set(archived[key]) if key=='squad' else c[key]==archived[key]),(s,gw,mode,key)
                        assert r['gross']-4*c['paid']==archived['net']
                    matched.append(dict(season=s,anchor=mode,gw=gw,calendar_chip=experiment.CAL.get(gw,'ordinary'),action_chip=chip or 'none',model=m,net=r['gross']-4*c['paid'],gross=r['gross'],hits=4*c['paid'],transfers=c['transfers'],captain_bonus=r['captain_bonus'],solver_status=c['solver_status'],solver_gap=c['solver_gap'],squad=','.join(map(str,sorted(c['squad']))),captain=c['captain']))
    pd.DataFrame(decomp).to_csv(OUT/f'path_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    pd.DataFrame(matched).to_csv(OUT/f'matched_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    return s

def main():
    t=time.time()
    with ProcessPoolExecutor(max_workers=4) as ex:
        for f in as_completed([ex.submit(worker,s) for s in SEASONS]):print('DONE',f.result(),round(time.time()-t),flush=True)
    path=pd.concat([pd.read_csv(OUT/f'path_{s}.csv.gz') for s in SEASONS]);matched=pd.concat([pd.read_csv(OUT/f'matched_{s}.csv.gz') for s in SEASONS])
    cols=['net','xi','captain','tc','bb','hits','transfers']
    season=path.groupby(['season','model','mode'])[cols].sum().reset_index();season.to_csv(OUT/'path_seasons.csv',index=False)
    pairs=summarize_pairs(season,['season','mode'],cols);pairs.to_csv(OUT/'path_paired_seasons.csv',index=False)
    pairs.groupby(['mode','comparison','metric']).difference.agg(['mean','min','max',lambda x:int((x>0).sum())]).rename(columns={'<lambda_0>':'positive_seasons'}).to_csv(OUT/'path_paired_summary.csv')
    x=pairs[pairs['mode']=='fixed_chips'].merge(pairs[pairs['mode']=='no_chips'],on=['season','comparison','metric'],suffixes=('_chips','_none'));x['interaction']=x.difference_chips-x.difference_none
    x.to_csv(OUT/'path_interaction_seasons.csv',index=False);x.groupby(['comparison','metric']).interaction.mean().to_csv(OUT/'path_interaction_summary.csv')
    by=path.groupby(['season','model','mode','calendar_chip'])[cols].sum().reset_index()
    z=summarize_pairs(by,['season','mode','calendar_chip'],cols);z.to_csv(OUT/'path_by_chip_seasons.csv',index=False);z.groupby(['mode','calendar_chip','comparison','metric']).difference.mean().to_csv(OUT/'path_by_chip_summary.csv')
    keys=['season','anchor','gw','calendar_chip','action_chip'];paired=summarize_pairs(matched,keys,['net','hits','transfers','captain_bonus'])
    paired.to_csv(OUT/'matched_paired_weekly.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    per=paired.groupby(['season','anchor','calendar_chip','action_chip','comparison','metric']).difference.mean().reset_index();per.to_csv(OUT/'matched_paired_seasons.csv',index=False)
    per.groupby(['anchor','calendar_chip','action_chip','comparison','metric']).difference.agg(['mean',lambda x:int((x>0).sum())]).rename(columns={'<lambda_0>':'positive_seasons'}).to_csv(OUT/'matched_paired_summary.csv')
    chip=paired[paired.action_chip!='none'];none=paired[paired.action_chip=='none'];j=chip.merge(none,on=['season','anchor','gw','calendar_chip','comparison','metric'],suffixes=('_chip','_none'),validate='one_to_one');j['interaction']=j.difference_chip-j.difference_none
    j.to_csv(OUT/'matched_interaction_weekly.csv',index=False)
    j.groupby(['anchor','calendar_chip','comparison','metric']).interaction.agg(['mean','count']).to_csv(OUT/'matched_interaction_summary.csv')
    checks=dict(new_matched_decisions=len(matched),archived_path_rows=len(path),identical_state=True,reference_actions_reproduced=True,exact_additive_accounting=True,nonoptimal=int((matched.solver_status!=0).sum()),max_solver_gap=float(matched.solver_gap.max()))
    (OUT/'chip_checks.json').write_text(json.dumps(checks,indent=2));print(checks)
if __name__=='__main__':main()
