"""Three fixed, public-outlet probes; stop on authorization/rate refusal."""
from pathlib import Path
import hashlib,json,time,urllib.request,urllib.error
P=Path(__file__).resolve().parent
OUTLET='1mjq6w6ezkxe611ykkj8rgz7f1'
def main():
    records=[]
    for row in json.loads((P/'plan.json').read_text())['fixtures']:
        uid=row['match_id'];url=f'https://api.performfeeds.com/soccerdata/matchexpectedgoals/{OUTLET}?fx={uid}&_rt=b&_fmt=json'
        name=f"inputs/{row['season']}_{row['fixture']}.json";f=P/name
        if f.exists():raw=f.read_bytes();status=200
        else:
            try:
                request=urllib.request.Request(url,headers={'Origin':'https://theanalyst.com','Referer':'https://theanalyst.com/','User-Agent':'FPL-data-research/1.0'})
                with urllib.request.urlopen(request,timeout=30) as response:raw=response.read();status=response.status
                json.loads(raw);f.write_bytes(raw)
            except urllib.error.HTTPError as error:
                status=error.code;raw=error.read();name=name.removesuffix('.json')+'_http_error.txt';(P/name).write_bytes(raw)
        records.append(dict(**row,url=url,status=status,file=name,sha256=hashlib.sha256(raw).hexdigest()))
        print(row['season'],row['fixture'],status,len(raw),flush=True)
        (P/'sources.json').write_text(json.dumps(records,indent=2)+'\n')
        if status in [401,403,429]:break
        time.sleep(.5)
if __name__=='__main__':main()
