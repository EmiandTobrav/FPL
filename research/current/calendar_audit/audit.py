from pathlib import Path
import json,gzip,hashlib,pickle
import pandas as pd,numpy as np
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent
CALENDAR_COLUMNS=['id','event','kickoff_time','team_h','team_a','provisional_start_time']

def main():
    old=HERE/'snapshot_manifest.json'
    provenance=json.loads(old.read_text()) if old.exists() and not list((HERE/'snapshots').glob('*.csv')) else []
    for p in sorted((HERE/'snapshots').glob('*.csv')):
        raw=p.read_bytes();d=pd.read_csv(p,usecols=CALENDAR_COLUMNS)
        assert len(d)==380 and d.id.nunique()==380,p
        assert sorted(set(d.team_h)|set(d.team_a))==list(range(1,21)),p
        assert (pd.concat([d.team_h,d.team_a]).value_counts()==38).all(),p
        b=d.to_csv(index=False).encode();packed=gzip.compress(b,mtime=0);target=p.with_suffix('.csv.gz');target.write_bytes(packed)
        provenance.append(dict(path=str(target.relative_to(HERE)),source_sha256=hashlib.sha256(raw).hexdigest(),stored_sha256=hashlib.sha256(packed).hexdigest(),rows=len(d),columns=CALENDAR_COLUMNS))
    (HERE/'snapshot_manifest.json').write_text(json.dumps(provenance,indent=2))
    selection=pd.read_csv(HERE/'selection.csv');rows=[]
    for s,q in selection.groupby('season'):
        final=pd.read_csv(CURRENT/f'project/data/{s}_fixtures.csv')
        for r in q.itertuples():
            d=pd.read_csv(HERE/f'snapshots/{s}_{r.sha}.csv.gz')
            for target in range(r.gw,min(39,r.gw+3)):
                a=d[d.event==target];b=final[final.event==target]
                for club in range(1,21):
                    snapshot=set(a.loc[(a.team_h==club)|(a.team_a==club),'id']);actual=set(b.loc[(b.team_h==club)|(b.team_a==club),'id'])
                    rows.append(dict(season=s,gw=r.gw,target_gw=target,club_id=club,age_days=r.age_days,within14days=r.age_days<=14,snapshot_count=len(snapshot),final_count=len(actual),same_fixtures=snapshot==actual))
    audit=pd.DataFrame(rows);audit.to_csv(HERE/'schedule_audit.csv',index=False)
    summary=[]
    for s,q in selection.groupby('season'):
        a=audit[(audit.season==s)&(audit.target_gw>audit.gw)];fresh=a[a.within14days]
        summary.append(dict(season=s,decision_rounds=len(q),distinct_snapshots=q.sha.nunique(),median_age_days=q.age_days.median(),max_age_days=q.age_days.max(),rounds_within14days=int((q.age_days<=14).sum()),future_team_rounds=len(a),fresh_future_team_rounds=len(fresh),fresh_count_diff_from_one=int((fresh.snapshot_count!=1).sum()),fresh_counts_changed_later=int((fresh.snapshot_count!=fresh.final_count).sum()),fresh_fixtures_changed_later=int((~fresh.same_fixtures).sum())))
    pd.DataFrame(summary).to_csv(HERE/'coverage.csv',index=False);print(pd.DataFrame(summary).to_string(index=False))
if __name__=='__main__':main()
