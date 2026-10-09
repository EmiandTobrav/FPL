"""Four fixed season totals; exact small source trial, no omitted zeros."""
from pathlib import Path
import json,hashlib,urllib.request
P=Path(__file__).resolve().parent
PLAN={'2019-20':274,'2020-21':363,'2022-23':489,'2024-25':719}
def main():
    assert json.loads((P/'plan.json').read_text())['seasons']==PLAN
    sources=[]
    for season,cid in PLAN.items():
        url=f'https://footballapi.pulselive.com/football/stats/ranked/teams/big_chance_missed?comps=1&compSeasons={cid}&page=0&pageSize=100&altIds=true'
        f=P/'inputs'/f'{season}.json'
        if not f.exists():
            raw=urllib.request.urlopen(urllib.request.Request(url,headers={'Origin':'https://www.premierleague.com','User-Agent':'FPL-research/1.0'}),timeout=30).read();json.loads(raw);f.write_bytes(raw)
        raw=f.read_bytes();sources.append(dict(season=season,url=url,file=str(f.relative_to(P)),sha256=hashlib.sha256(raw).hexdigest()))
        print(season,len(raw),flush=True)
    (P/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
if __name__=='__main__':main()
