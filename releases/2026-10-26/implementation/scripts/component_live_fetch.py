"""Capture official FPL responses with actual retrieval receipts; never backdate."""
import concurrent.futures, datetime, hashlib, json, time, urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'reports/component_operational_activation_2026_10_26/raw'
def fetch(path, endpoint):
    url='https://fantasy.premierleague.com/api/'+endpoint
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url,timeout=40) as response: raw=response.read()
            data=json.loads(raw); at=datetime.datetime.now(datetime.timezone.utc).isoformat()
            path.write_bytes(raw)
            return dict(file=str(path.relative_to(R)),url=url,retrieved_at=at,sha256=hashlib.sha256(raw).hexdigest())
        except Exception:
            if attempt==2: raise
            time.sleep(1+attempt)
def main():
    P.mkdir(parents=True,exist_ok=True)
    receipts=[fetch(P/'bootstrap.json','bootstrap-static/'),fetch(P/'fixtures.json','fixtures/')]
    boot=json.loads((P/'bootstrap.json').read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        receipts+=list(executor.map(lambda e:fetch(P/f'element_{e["id"]}.json',f'element-summary/{e["id"]}/'),boot['elements']))
    (P/'receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    print('Captured',len(receipts),'official responses; completed',receipts[-1]['retrieved_at'],flush=True)
if __name__=='__main__':main()
