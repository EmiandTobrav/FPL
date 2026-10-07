"""Positive event evidence only; absent events never prove zero."""
from pathlib import Path
import hashlib,json
import pandas as pd
import pyarrow.parquet as pq
P=Path(__file__).resolve().parent
path=Path('/private/tmp/fpl_events_EPL.parquet')
digest=hashlib.sha256(path.read_bytes()).hexdigest()
if digest!='a69184e1c0d35ed39e1146b748f0ff3b649750bb1d52624286406e0cacd4b6f2':raise ValueError('Event source drift')
e=pq.read_table(path,columns=['match_id','event_id','player_id','type_id','outcome','qualifier_json'],filters=[('season','in',[f'{y}-{y+1}' for y in range(2019,2025)]),('type_id','in',[4,15,16])]).to_pandas()
if e.duplicated(['match_id','event_id']).any():raise ValueError('Duplicate event')
q=e.qualifier_json.map(lambda v:json.loads(v) if isinstance(v,str) and v else {})
e['positive_foul_won']=e.type_id.eq(4)&e.outcome.eq(1)
e['positive_on_target']=e.type_id.eq(16)&q.map(lambda d:'28' not in d)|e.type_id.eq(15)&q.map(lambda d:'82' not in d)
d=e.groupby(['match_id','player_id'])[['positive_foul_won','positive_on_target']].sum().reset_index()
d=d[(d.positive_foul_won>0)|(d.positive_on_target>0)]
d.to_csv(P/'inputs/positive_event_evidence.csv.gz',index=False,compression={'method':'gzip','mtime':0})
(P/'inputs/positive_event_source.json').write_text(json.dumps(dict(sha256=digest,scope='Positive contradiction screen only. No source count or zero inferred from event absence.',type_4_outcome_1='foul won candidate',type_16_without_28='non-own goal; necessarily on target',type_15_without_82='saved attempt excluding explicit blocked qualifier; conservative contradiction veto'),indent=2)+'\n')
print('positive-only event rows',len(d))
