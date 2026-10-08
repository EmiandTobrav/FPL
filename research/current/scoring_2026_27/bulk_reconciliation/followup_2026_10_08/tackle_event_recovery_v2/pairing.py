"""Count only actual tackle events with uniquely identified opposing duel actors."""
import json
import pandas as pd
KEY=['match_id','period_id']
def q(v):return json.loads(v) if isinstance(v,str) and v.strip() else {}
def pair(events):
 e=events.copy();e['clock']=e.minute*60+e.second
 e['opposite_ref']=e.qualifier_json.map(lambda s:q(s).get('233'))
 e['valid_ref']=e.opposite_ref.map(lambda s:isinstance(s,str) and s.isdigit())
 t=e[e.type_id.isin([7,54])].copy();v=e[(e.type_id.eq(50)|(e.type_id.eq(3)&e.outcome.eq(0)))&e.valid_ref].copy()
 t['px']=(t.x*10).round().astype('Int64');t['py']=(t.y*10).round().astype('Int64');v['px']=((100-v.x)*10).round().astype('Int64');v['py']=((100-v.y)*10).round().astype('Int64')
 pairs=t[t.valid_ref].dropna(subset=['px','py','player_id','team_id']).merge(v.dropna(subset=['px','py','player_id','team_id']),on=KEY+['px','py'],suffixes=('_t','_v'))
 pairs=pairs[pairs.team_id_t.ne(pairs.team_id_v)&pairs.clock_t.sub(pairs.clock_v).abs().le(3)&(pairs.type_id_t.eq(7)|pairs.type_id_v.eq(3))]
 nt=pairs.groupby(['match_id','event_id_t']).size();nv=pairs.groupby(['match_id','event_id_v']).size()
 pairs=pairs[[nt[(r.match_id,r.event_id_t)]==1 and nv[(r.match_id,r.event_id_v)]==1 for r in pairs.itertuples()]].copy()
 # Reciprocal source references define local IDs; they must remain unique per team.
 bad_t=pairs.duplicated(['match_id','team_id_t','opposite_ref_v'],keep=False)
 bad_v=pairs.duplicated(['match_id','team_id_v','opposite_ref_t'],keep=False)
 pairs=pairs[~(bad_t|bad_v)]
 return t,pairs
