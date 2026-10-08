from pathlib import Path
import pandas as pd,json,gzip
P=Path(__file__).resolve().parent;S=P.parent
r=pd.read_csv(P/'results/remaining_fields.csv.gz',low_memory=False);p=pd.read_csv(S/'tackle_event_recovery_v2/inputs/players.csv.gz');lookup=p.set_index(['match_id','player_id']).to_dict('index');g=pd.read_csv(S/'tackle_event_recovery_v2/team_gates.csv').dropna(subset=['match_id','recipient_team_id']);team=g.set_index(['match_id','recipient_team_id']).complete.to_dict();e=pd.read_csv(S/'tackle_event_recovery_v2/inputs/duels.csv.gz',low_memory=False);pairs=pd.read_csv(S/'tackle_event_recovery_v2/paired_events.csv.gz',low_memory=False);paired=set(zip(pairs.match_id,pairs.event_id_v));lost=e[e.type_id.eq(50)|(e.type_id.eq(3)&~e.outcome.eq(1))];blocked=set((x.match_id,x.player_id) for x in lost.itertuples() if (x.match_id,x.event_id) not in paired);smother=set(zip(pairs.loc[pairs.type_id_t.eq(54),'match_id'],pairs.loc[pairs.type_id_t.eq(54),'player_id_v']));out=[]
for x in r[r.field.eq('times_tackled')].itertuples():
 key=(x.match_id,x.player_id);person=lookup.get(key)
 if x.status!='missing_data':reason='protected_explicit_conflict'
 elif person is None:reason='missing_archive_or_player_identity'
 elif not team.get((x.match_id,person['team_id']),False):reason='opponent_whole_tackle_inventory_unqualified'
 elif key in blocked:reason='unpaired_failed_takeon_or_dispossession'
 elif key in smother:reason='smother_subtype_not_qualified'
 else:reason='individual_inventory_not_proven'
 out.append(dict(season=x.season,fixture=x.fixture,code=x.code,reason=reason))
out=pd.DataFrame(out);out.to_csv(P/'results/tackle_remaining_reasons.csv',index=False);s=out.groupby('reason').size().to_dict();assert sum(s.values())==1693;(P/'results/tackle_remaining_summary.json').write_text(json.dumps(s,indent=2)+'\n');print(s)
