"""Bounded public participant-stat acquisition with reuse of pinned summaries."""
import importlib.util,json,urllib.request
import pandas as pd
from prepare import P,R,K,digest,save

spec=importlib.util.spec_from_file_location('identity',R/'scoring_2026_27/keeper_recovery/recover.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def main():
    raw=P/'inputs/raw';raw.mkdir(exist_ok=True);sources=[];bridges=[]
    old=P.parent/'espn_gap_acquisition';cache={s['url']:old/s['file'] for s in json.loads((old/'inputs/sources.json').read_text())}
    aliases=pd.read_csv(P/'inputs/primary_identities.csv').groupby('code').name.agg(lambda a:set(a.map(m.norm))).to_dict()
    def get(url,name):
        f=raw/name
        if not f.exists():
            if url in cache:f.write_bytes(cache[url].read_bytes())
            else:
                with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FPL-dataset-data-acquisition'}),timeout=30) as response:f.write_bytes(response.read())
        sources.append(dict(file=str(f.relative_to(P)),url=url,sha256=digest(f)));return json.loads(f.read_bytes())
    native=pd.read_csv(P/'inputs/native_players.csv.gz')
    for r in pd.read_csv(P/'inputs/fixture_plan.csv').itertuples():
        board=get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates={r.date.replace("-","")}',f'scoreboard_{r.date}.json');hits=[]
        for e in board.get('events',[]):
            c=e['competitions'][0];s={x['homeAway']:x for x in c['competitors']}
            if m.team(s['home']['team']['displayName'])==m.team(r.home) and m.team(s['away']['team']['displayName'])==m.team(r.away):
                assert c['status']['type']['completed'] and c['date'][:10]==r.date and int(s['home']['score'])==r.home_score and int(s['away']['score'])==r.away_score;hits.append(str(e['id']))
        assert len(hits)==1;eid=hits[0];d=get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event={eid}',f'summary_{eid}.json')
        n=native[native.season.eq(r.season)&native.fixture.eq(r.fixture)]
        for club in d['rosters']:
            pool=n[n.historical_team.map(m.team).eq(m.team(club['team']['displayName']))]
            for a in club['roster']:
                athlete=a['athlete'];pn=athlete.get('fullName',athlete.get('displayName',''));provider=dict(player_name=pn,first_name=pn.rsplit(' ',1)[0],last_name=athlete.get('lastName',pn.rsplit(' ',1)[-1]))
                ranks=[(int(x.code),3 if m.norm(pn) in aliases.get(int(x.code),set()) else m.name_match(x._asdict(),provider)) for x in pool.itertuples()];best=max([v for _,v in ranks],default=0);codes=[code for code,v in ranks if best>0 and v==best]
                if len(codes)!=1:continue
                code=codes[0];pid=str(athlete['id']);tid=str(club['team']['id']);u=f'https://sports.core.api.espn.com/v2/sports/soccer/leagues/eng.1/events/{eid}/competitions/{eid}/competitors/{tid}/roster/{pid}/statistics/0?lang=en&region=us';get(u,f'stats_{eid}_{pid}.json')
                bridges.append(dict(season=r.season,fixture=r.fixture,code=code,espn_event_id=eid,espn_player_id=pid,espn_team_id=tid,name=pn))
        print(r.season,r.fixture,'collected',flush=True)
    save(pd.DataFrame(bridges),P/'inputs/player_bridge.csv');unique={s['file']:s for s in sources};assert len(unique)==len({s['url'] for s in sources})
    (P/'inputs/sources.json').write_text(json.dumps(list(unique.values()),indent=2)+'\n')

if __name__=='__main__':main()
