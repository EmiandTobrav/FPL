"""Acquire one pinned event response; reuse an already captured date scoreboard."""
import json,urllib.request
from prepare import P,digest

def main():
    old=P.parents[1]/'espn_primary_identity';raw=P/'inputs/raw';raw.mkdir(exist_ok=True);sources=[]
    for name,url in [('scoreboard_2023-04-02.json','https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates=20230402'),('summary_638101.json','https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event=638101')]:
        f=raw/name
        if not f.exists():
            cache=old/'inputs/raw'/name
            if cache.exists():f.write_bytes(cache.read_bytes())
            else:
                with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FPL-goal-inventory-acquisition'}),timeout=40) as response:f.write_bytes(response.read())
        sources.append(dict(file=str(f.relative_to(P)),url=url,sha256=digest(f)))
    (P/'inputs/sources.json').write_text(json.dumps(sources,indent=2)+'\n')
    board=json.loads((raw/'scoreboard_2023-04-02.json').read_text());hits=[e for e in board['events'] if str(e['id'])=='638101'];assert len(hits)==1
    print('One event summary acquired; pinned scoreboard event found')
if __name__=='__main__':main()
