"""Match identity guards, exact fill invariants, and independent team totals."""
from copy import deepcopy
import json
import pandas as pd
from fetch import P,parse

def run():
    f=pd.read_csv(P/'results/fixture_manifest.csv').set_index('id').loc[222].to_dict();f['id']=222
    d=json.loads((P/'raw/fotmob_3610151.json').read_text())
    rows=parse(d,f)
    for section,key,value in [('general','matchId','0'),('general','matchTimeUTCDate','2021-01-22T15:00:00Z')]:
        bad=deepcopy(d);bad[section][key]=value
        try:parse(bad,f)
        except AssertionError:pass
        else:raise AssertionError('invalid match accepted')
    counts=pd.DataFrame(rows)
    pl=json.loads((P/'raw/pl_match_66563.json').read_text())
    assert pl['entity']['id']==66563 and pl['entity']['gameweek']['compSeason']['id']==418
    assert pd.to_datetime(pl['entity']['kickoff']['millis'],unit='ms',utc=True)==pd.Timestamp('2022-01-22T15:00:00Z')
    assert [x['score'] for x in pl['entity']['teams']]==[1,2]
    result=[]
    for name,tid in [('Brentford','130'),('Wolves','38')]:
        official={x['name']:x['value'] for x in pl['data'][tid]['M']}
        for source,reference in [('tackles','total_tackle'),('blocks','outfielder_block'),('clearances','total_clearance'),('interceptions','interception'),('recoveries','ball_recovery')]:
            observed=counts.loc[counts.source_team==name,source].sum()
            assert observed==official[reference],(name,source)
            result.append({'team':name,'stat':source,'fotmob_player_sum':observed,'official_team_total':official[reference]})
    pd.DataFrame(result).to_csv(P/'results/official_team_check.csv',index=False)
    gaps=pd.read_csv(P/'results/gap_fill_audit.csv')
    resolved=gaps[gaps.defcon_v3.notna()]
    assert resolved.identity_ok.all()
    assert resolved.defcon_v3.isin([0,2]).all()
    for stat in ['Tkl_Tackles','Sh_Blocks','Int','Clr','Recov']:
        known=gaps[stat+'_before'].notna()
        assert gaps.loc[known,stat].equals(gaps.loc[known,stat+'_before'])
    print('Match rejection guards, ten official team totals, identity gates and known-count preservation passed.')

if __name__=='__main__':run()
