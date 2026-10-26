"""Cross-check selected publication proxies against independent metadata files."""
from common import *
def main():
 commits={};hashes={}
 for row in json.loads((OLD/'full_selected_snapshots.json').read_text()):
  if 'author_at' in row:commits[row['commit']]=max(dt(row['author_at']),dt(row['committer_at']))
 for file in list((P/'raw').glob('*commits_*.json'))+list((OLD/'raw').glob('commits_*.json')):
  if file.name.endswith('.source.json'):
   hashes[str(file.relative_to(R))]=sha(file);continue
  data=json.loads(file.read_text());assert isinstance(data,list)
  for c in data:
   if 'commit' in c:commits[c['sha']]=max(dt(c['commit']['author']['date']),dt(c['commit']['committer']['date']))
  hashes[str(file.relative_to(R))]=sha(file)
 hashes[str((OLD/'full_selected_snapshots.json').relative_to(R))]=sha(OLD/'full_selected_snapshots.json')
 checked=0
 for row in json.loads((P/'selected_sources.json').read_text()):
  if row['format']=='none':continue
  assert row['commit'] in commits,row
  assert commits[row['commit']]==dt(row['source_time']),row
  assert dt(row['source_time'])<dt(row['selection_cutoff']),row
  checked+=1
 result=dict(passed=True,selected_source_commit_times_checked=checked,metadata_files=len(hashes),source_time_rule='max(author_time,committer_time) strictly before effective cutoff',metadata_hashes=hashes)
 (P/'metadata_verification.json').write_text(json.dumps(result,indent=2));print('Metadata verified',checked,'sources',len(hashes),'files',flush=True)
if __name__=='__main__':main()
