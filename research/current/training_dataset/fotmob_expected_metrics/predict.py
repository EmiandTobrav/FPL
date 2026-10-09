"""Freeze explicit expected-statistic candidates before native comparison."""
import gzip,json,math
import pandas as pd
from prepare import P,R,K,digest,save
SOURCE=R/'scoring_2026_27/bulk_reconciliation/followup_2026_10_08/fotmob_shot_conservation'
def main():
    for n,h in json.loads((P/'selection_freeze.json').read_text()).items():assert digest(P/n)==h,n
    manifest=pd.read_csv(SOURCE/'inputs/source_manifest.csv');plan=pd.read_csv(SOURCE/'plan.csv');native=pd.read_csv(R/'training_dataset/scoring/results/historical_inventory.csv.xz',low_memory=False)
    native=native[K+['minutes']];assert not native.duplicated(K).any();metadata=manifest.merge(plan,on=['season','fixture'],validate='one_to_one',suffixes=('','_plan'))
    rows=[];sources={};eligibility=[]
    for s in metadata.itertuples():
        f=SOURCE/s.path;assert digest(f)==s.file_sha256;raw=gzip.decompress(f.read_bytes());assert __import__('hashlib').sha256(raw).hexdigest()==s.raw_sha256;sources[str(f.relative_to(R))]=s.file_sha256
        d=json.loads(raw);g=d['general'];header=d['header'];assert int(g['matchId'])==int(s.fotmob_match_id) and g['finished'] and int(g['leagueId'])==47
        assert pd.to_datetime(g['matchTimeUTCDate']).strftime('%Y-%m-%d')==s.date
        assert int(header['teams'][0]['score'])==s.team_h_score and int(header['teams'][1]['score'])==s.team_a_score
        for fm_id,person in d['content']['playerStats'].items():
            opta=person.get('optaId');code=int(str(opta).lstrip('p')) if opta is not None else None
            stats={}
            for group in person['stats']:
                for x in group['stats'].values():
                    if x.get('key') in ['minutes_played','expected_goals','expected_assists']:
                        assert x['key'] not in stats;stats[x['key']]=x['stat'].get('value')
            if code is None:continue
            eligibility.append(dict(season=s.season,fixture=s.fixture,code=code,fotmob_player_id=fm_id,source_minutes=stats.get('minutes_played'),source_file=str(f.relative_to(R))))
            for field in ['expected_goals','expected_assists']:
                value=stats.get(field)
                if value is None:continue
                assert isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value>=0
                rows.append(dict(season=s.season,fixture=s.fixture,code=code,field=field,value=value,fotmob_player_id=fm_id,source_minutes=stats.get('minutes_played'),source_file=str(f.relative_to(R))))
    candidates=pd.DataFrame(rows).merge(native,on=K,validate='many_to_one');assert not candidates.duplicated(K+['field']).any()
    candidates['eligible']=candidates.source_minutes.eq(candidates.minutes)&candidates.minutes.gt(0)
    save(candidates,P/'predictions.csv.gz');save(pd.DataFrame(eligibility),P/'identity_inventory.csv.gz')
    (P/'source_files.json').write_text(json.dumps(sources,indent=2)+'\n')
    freeze={n:digest(P/n) for n in ['predict.py','prepare.py','protocol.json','dependencies.json','selection_freeze.json','predictions.csv.gz','identity_inventory.csv.gz','source_files.json']}
    f=P/'prediction_freeze.json'
    if f.exists():assert json.loads(f.read_text())==freeze
    f.write_text(json.dumps(freeze,indent=2)+'\n');print('Explicit candidates',len(candidates),'eligible',int(candidates.eligible.sum()),'reference fixtures',candidates[candidates.season.isin(['2022-23','2023-24'])][K[:2]].drop_duplicates().shape[0])
if __name__=='__main__':main()
