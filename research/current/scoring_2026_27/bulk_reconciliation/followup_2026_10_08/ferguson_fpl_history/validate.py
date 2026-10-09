"""Qualify one native FPL source-version correction, preserving raw snapshots."""
import json
import pandas as pd
from prepare import P,K,digest,save

def main():
    for name,h in json.loads((P/'selection_freeze.json').read_text()).items():assert digest(P/name)==h,name
    for src in json.loads((P/'inputs/sources.json').read_text()):assert digest(P/src['file'])==src['sha256']
    out=P/'results';out.mkdir(exist_ok=True)
    native=pd.read_csv(P/'inputs/native_player_season.csv.gz');history=pd.read_csv(P/'inputs/player_history.csv');roster=pd.read_csv(P/'inputs/players_raw.csv')
    person=roster[roster.id.eq(123)];assert len(person)==1
    person=person.iloc[0];assert int(person.code)==487117 and person.first_name=='Evan' and person.second_name=='Ferguson'
    assert len(native)==len(history)==38 and not history.fixture.duplicated().any() and history.element.eq(123).all()
    assert set(history.fixture)==set(native.fixture)
    mutable=json.loads((P/'protocol.json').read_text())['mutable_factual_fields']
    fields=[f for f in native if f not in ['season','code','fixture']]
    comparisons=[];corrections=[]
    joined=native.merge(history,on='fixture',validate='one_to_one',suffixes=('_native','_history'))
    for row in joined.to_dict('records'):
        for field in fields:
            old,new=row[field+'_native'],row[field+'_history'];equal=(pd.isna(old) and pd.isna(new)) or old==new
            comparisons.append(dict(fixture=row['fixture'],field=field,original=old,history=new,equal=bool(equal)))
            if not equal:
                assert row['fixture']==239 and field in mutable,(row['fixture'],field,old,new)
                corrections.append(dict(season='2024-25',fixture=239,code=487117,field=field,original=old,value=new,source='inputs/player_history.csv'))
    assert len(corrections)==6 and {c['field'] for c in corrections}==set(mutable)
    target=history[history.fixture.eq(239)].iloc[0];old=native[native.fixture.eq(239)].iloc[0]
    assert target.minutes==17 and target.bps==old.bps==4 and target.total_points==1 and target['round']==24
    gw=pd.read_csv(P/'inputs/gw24.csv');gw=gw[gw.fixture.eq(239)&gw.element.eq(123)];assert len(gw)==1
    for field in fields:assert gw.iloc[0][field]==old[field],field
    integers=['minutes','bps','total_points','goals_conceded','assists','bonus','goals_scored','own_goals','clean_sheets','yellow_cards','red_cards','saves','penalties_saved','penalties_missed','starts']
    decimals=['expected_goals','expected_assists','expected_goal_involvements','expected_goals_conceded'];totals=[]
    for field in integers+decimals:
        actual=float(history[field].sum());expected=float(person[field]);tol=0 if field in integers else 1e-8
        assert abs(actual-expected)<=tol,(field,actual,expected)
        totals.append(dict(field=field,history_sum=actual,roster_total=expected,difference=actual-expected))
    corrected=native.copy()
    for c in corrections:corrected.loc[corrected.fixture.eq(c['fixture']),c['field']]=c['value']
    pd.testing.assert_frame_equal(native[~native.fixture.eq(239)],corrected[~corrected.fixture.eq(239)])
    save(pd.DataFrame(corrections),out/'native_fpl_corrections.csv.gz');save(corrected,out/'native_player_season_corrected.csv.gz');save(pd.DataFrame(comparisons),out/'source_comparisons.csv.gz');save(pd.DataFrame(totals),out/'season_total_checks.csv.gz')
    overlay=pd.DataFrame([dict(season='2024-25',fixture=239,code=487117,field='historical_bps',value=4)]);save(overlay,out/'overlay.csv.gz')
    report=dict(qualified_fields=['historical_bps'],new_fields=1,by_field={'historical_bps':1},factual_corrections=6,season_rows=38,unchanged_player_season_rows=37,source_comparisons=len(comparisons),unchanged_factual_values=sum(c['equal'] for c in comparisons),exact_season_totals=len(totals),bps_value_unchanged=True,point_rescoring=False,limits='Native FPL mirror source-version reconciliation and regression, not independent holdout or final collective quality. Original GW and native data remain intact.')
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
