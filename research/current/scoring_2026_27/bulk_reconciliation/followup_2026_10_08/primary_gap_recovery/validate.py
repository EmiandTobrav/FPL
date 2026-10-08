from pathlib import Path
import pandas as pd,json,hashlib,gzip
P=Path(__file__).resolve().parent;S=P.parent;K=['season','fixture','code','field'];f=json.loads((P/'freeze.json').read_text())
for n,h in f['inputs'].items():assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h
assert hashlib.sha256((P/'predictions.csv.gz').read_bytes()).hexdigest()==f['predictions_sha256']
for r in json.loads((P/'sources.json').read_text()):assert hashlib.sha256((P/r['file']).read_bytes()).hexdigest()==r['sha256']
pred=pd.read_csv(P/'predictions.csv.gz');before=pd.read_csv(S/'bulk_followup/results/requirements.csv.gz',low_memory=False)
c=pred[pred.scope.eq('later_control')].merge(before[~before.is_open][K+['value']],on=K,validate='one_to_one',suffixes=('_pred','_known'));c['correct']=c.value_pred.eq(c.value_known);c.to_csv(P/'control_comparisons.csv',index=False)
summary=c.groupby('field').agg(comparisons=('correct','size'),errors=('correct',lambda s:int((~s).sum()))).reset_index();summary.to_csv(P/'control_summary.csv',index=False);qualified=summary.loc[summary.comparisons.gt(0)&summary.errors.eq(0),'field'].tolist()
# Direct component pairs provide a separate mapping check, not inferred zero controls.
raw=pd.read_csv(S/'component_conservation/inputs/archive_projection.csv.gz');players=pd.DataFrame(json.loads((P/'players.json').read_text()));pairs=players[players.scope.eq('later_control')].merge(raw,on=K[:3],validate='one_to_one',suffixes=('','_archive'));mapping={'times_tackled':'timesTackled','saved_obox':'savedObox','total_clearance':'totalClearance','outfielder_block':'outfielderBlock','interception':'interception','was_fouled':'wasFouled','ontarget_scoring_att':'ontargetScoringAtt','total_tackle':'totalTackle','won_tackle':'wonTackle','att_pen_goal':'attPenGoal','clearance_off_line':'clearanceOffLine'};checks=[]
for a,b in mapping.items():
 aa=a;bb=b+'_archive' if b==a else b
 if aa not in pairs or bb not in pairs:continue
 for r in pairs.dropna(subset=[aa,bb]).to_dict('records'):checks.append({**{k:r[k] for k in K[:3]},'counter':a,'primary':r[aa],'archive':r[bb],'correct':r[aa]==r[bb]})
x=pd.DataFrame(checks);x.to_csv(P/'explicit_component_controls.csv',index=False);bad=set(x.loc[~x.correct,'counter']);fieldmap={'times_tackled':['times_tackled'],'saved_obox':['saves_outside_box'],'total_clearance':['clearances_blocks_interceptions'],'outfielder_block':['clearances_blocks_interceptions'],'interception':['clearances_blocks_interceptions'],'was_fouled':['fouls_won'],'ontarget_scoring_att':['shots_on_target'],'total_tackle':['total_tackles','legacy_net_tackles'],'won_tackle':['won_tackles','legacy_net_tackles'],'att_pen_goal':['penalty_goals'],'clearance_off_line':['goal_line_clearances']}
# Some counters are not requirements in the later control season, so their
# native explicit counter comparisons (the protocol's mapping check) are the
# applicable controls. Absence of a requirement is not absence of a counter.
native={'was_fouled':'fouls_won','ontarget_scoring_att':'shots_on_target','saved_obox':'saves_outside_box','att_pen_goal':'penalty_goals','times_tackled':'times_tackled'}
for counter,field in native.items():
 z=x[x.counter.eq(counter)]
 if len(z)>0 and z.correct.all() and field not in qualified:qualified.append(field)
qualified=[f for f in qualified if not any(f in fieldmap[b] for b in bad)]
layer=pred[pred.scope.eq('gap')&pred.field.isin(qualified)].merge(before[before.is_open&before.status.eq('missing_data')][K+['value']],on=K,validate='one_to_one',suffixes=('','_before'));assert layer.value_before.isna().all();layer=layer.drop(columns='value_before');(P/'overlay.csv.gz').write_bytes(gzip.compress(layer.to_csv(index=False).encode(),mtime=0))
v=dict(control_fixtures=3,field_comparisons=len(c),field_errors=int((~c.correct).sum()),explicit_component_comparisons=len(x),explicit_component_errors=int((~x.correct).sum()),qualified_fields=qualified,withheld_fields=sorted(set(pred.field)-set(qualified)),new_fields=len(layer),by_field=layer.field.value_counts().to_dict(),primary_player_responses=len(players),limits='Fixed mapping/arithmetic checks, shared Opta source and previously seen controls; not independent provider or final scoring qualification.')
(P/'validation_summary.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
