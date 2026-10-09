"""Freeze qualification guards from previously approved source exceptions."""
import json
import pandas as pd
from prepare import P,B,R,K,digest,save

T=['season','primary_team_id']
def main():
    for n,h in json.loads((P/'selection_freeze.json').read_text()).items():assert digest(P/n)==h,n
    for n,h in json.loads((P/'dependencies.json').read_text()).items():assert digest(R/n)==h,n
    old=P.parent/'big_chance_zero_bounds'
    for n,h in json.loads((old/'prediction_freeze.json').read_text()).items():assert digest(old/n)==h,n
    counts=pd.read_csv(R/'scoring_2026_27/keeper_recovery/keeper_counts.csv.gz',low_memory=False)
    evidence=pd.read_csv(R/'scoring_2026_27/keeper_recovery/save_evidence.csv.gz',low_memory=False)
    exceptions=counts[counts.original_reason.fillna('').str.contains('big_chance_missed_conflict') & counts.status.eq('reconstructed') & counts.big_chance_saves.gt(0) & counts.resolution_method.isin(['complete_paired_save_inventory','explicit_primary_counter'])]
    matches=pd.read_csv(old/'match_bounds.csv.gz');guards=[];proof=[]
    for r in exceptions.itertuples():
        hits=evidence[evidence.season.eq(r.season)&evidence.fixture.eq(r.fixture)&evidence.keeper_id.eq(r.player_id)&evidence.blocked.eq(False)]
        hits=hits[hits.qualifier_json.map(lambda q:'214' in json.loads(q))]
        if hits.empty:continue
        side='away' if r.side=='h' else 'home';group=matches[matches.season.eq(r.season)&matches.fixture.eq(r.fixture)&matches.side.eq(side)]
        if group.empty:continue
        assert len(group)==1
        # A documented event conflicts with this zero source bound: invalidate
        # every match in the source team-season, including unobserved targets.
        if not bool(group.iloc[0].zero_bound):continue
        tid=int(group.iloc[0].primary_team_id)
        guards.append(dict(season=r.season,primary_team_id=tid,exception_fixture=r.fixture,exception_code=r.code,exception_name=r.name,approved_big_chance_saves=r.big_chance_saves,reason=r.original_reason,resolution_method=r.resolution_method))
        for e in hits.to_dict('records'):proof.append(dict(**e,primary_team_id=tid,exception_code=r.code))
    guards=pd.DataFrame(guards);assert not guards.empty and not guards.duplicated(T).any()
    bounds=pd.read_csv(old/'all_counter_bounds.csv.gz')
    bounds['source_guarded']=pd.MultiIndex.from_frame(bounds[T]).isin(pd.MultiIndex.from_frame(guards[T]))
    bounds['emitted_value']=bounds.value.where(~bounds.source_guarded)
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());req=pd.read_csv(B/parent['requirements'],low_memory=False)
    pending=req[req.is_open & req.status.eq('missing_data') & req.value.isna()][K]
    pred=bounds[~bounds.source_guarded].merge(pending,on=K,validate='one_to_one')
    save(guards,P/'source_guards.csv.gz');save(pd.DataFrame(proof),P/'guard_event_evidence.csv.gz');save(bounds,P/'all_counter_bounds.csv.gz');save(pred,P/'predictions.csv.gz')
    record={n:digest(P/n) for n in ['prepare.py','predict.py','selection_freeze.json','protocol.json','dependencies.json','source_guards.csv.gz','guard_event_evidence.csv.gz','all_counter_bounds.csv.gz','predictions.csv.gz']}
    f=P/'prediction_freeze.json'
    if f.exists():assert json.loads(f.read_text())==record
    f.write_text(json.dumps(record,indent=2)+'\n')
    print(guards.to_string(index=False));print('Guarded keeper rows',int(bounds.source_guarded.sum()),'missing candidates',len(pred))
if __name__=='__main__':main()
