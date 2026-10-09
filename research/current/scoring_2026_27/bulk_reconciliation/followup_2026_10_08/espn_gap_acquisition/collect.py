"""Bounded public collection; stop on access/rate refusals, no authentication."""
import json, urllib.request
import pandas as pd
from prepare import P, R, digest
import importlib.util

spec=importlib.util.spec_from_file_location('native_identity',R/'scoring_2026_27/keeper_recovery/recover.py')
identity=importlib.util.module_from_spec(spec);spec.loader.exec_module(identity)

def main():
    rawdir=P/'inputs/raw';rawdir.mkdir(exist_ok=True)
    plan=pd.read_csv(P/'plan.csv',dtype={'date':str});sources=[];rows=[]
    def get(url,name):
        p=rawdir/name
        if not p.exists():
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FPL-dataset-source-acquisition'}),timeout=30) as response:
                p.write_bytes(response.read())
        sources.append(dict(file=str(p.relative_to(P)),url=url,sha256=digest(p)))
        return json.loads(p.read_bytes())
    boards={date:get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates={date.replace("-", "")}',f'scoreboard_{date}.json') for date in sorted(plan.date.unique())}
    for r in plan.itertuples():
        hits=[]
        for e in boards[r.date].get('events',[]):
            c=e['competitions'][0];sides={x['homeAway']:x for x in c['competitors']}
            if identity.team(sides['home']['team']['displayName'])==identity.team(r.home) and identity.team(sides['away']['team']['displayName'])==identity.team(r.away):
                assert c['date'][:10]==r.date and c['status']['type']['completed']
                assert int(sides['home']['score'])==r.home_score and int(sides['away']['score'])==r.away_score
                hits.append(str(e['id']))
        if len(hits)!=1: raise ValueError(f'Fixture identity unresolved: {r.season}/{r.fixture}')
        eid=hits[0];get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event={eid}',f'summary_{eid}.json')
        rows.append(dict(season=r.season,fixture=r.fixture,espn_event_id=eid))
        print(r.season,r.fixture,eid,flush=True)
    pd.DataFrame(rows).to_csv(P/'inputs/fixture_bridge.csv',index=False)
    (P/'inputs/sources.json').write_text(json.dumps(sources,indent=2)+'\n')

if __name__=='__main__':main()
