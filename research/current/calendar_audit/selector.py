from pathlib import Path
import json,pickle
import pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent

def select_before(commits,cutoff):
    cutoff=pd.Timestamp(cutoff)
    candidates=[c for c in commits if max(pd.Timestamp(c['author_time']),pd.Timestamp(c['committer_time']))<cutoff]
    return max(candidates,key=lambda c:max(pd.Timestamp(c['author_time']),pd.Timestamp(c['committer_time']))) if candidates else None

def main():
    sources=json.loads((HERE/'source_commits.json').read_text());rows=[];needed={}
    for s,commits in sources.items():
        with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
        for gw in range(5,39):
            cutoff=pd.Timestamp(games[gw]['cutoff']);c=select_before(commits,cutoff)
            assert c is not None
            available=max(pd.Timestamp(c['author_time']),pd.Timestamp(c['committer_time']))
            rows.append(dict(season=s,gw=gw,cutoff=str(cutoff),sha=c['sha'],snapshot_time=str(available),age_days=(cutoff-available).total_seconds()/86400))
            needed[(s,c['sha'])]=dict(season=s,sha=c['sha'],author_time=c['author_time'],committer_time=c['committer_time'],url=f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/{c['sha']}/data/{s}/fixtures.csv")
    d=pd.DataFrame(rows);d.to_csv(HERE/'selection.csv',index=False);(HERE/'downloads.json').write_text(json.dumps(list(needed.values()),indent=2))
    print(d.groupby('season').age_days.agg(['count','median','max']).to_string());print('Distinct snapshots',len(needed))
if __name__=='__main__':main()
