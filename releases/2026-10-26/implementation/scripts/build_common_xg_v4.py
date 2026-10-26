"""Extend frozen common rows with genuinely archived predeadline FPL xG/xA.

Uses reported season totals and changes between dated bootstrap snapshots.
Never substitutes end-season revised match xG into an earlier decision.
"""
import sys,json,lzma,hashlib,collections,os
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json,verify_files
OLD=R/'datasets/fpl_common_training_v3';D=R/'datasets/fpl_common_training_v4';P=R/'reports/xg_adaptation_2026_10_26'
FEATURES=['xg_current_total','xa_current_total','xg_current_per90','xa_current_per90','xg_previous_total','xa_previous_total','xg_previous_per90','xa_previous_per90']+[f'{kind}_{name}_{w}' for w in [3,10] for name in ['reported_change','change_per90'] for kind in ['xg','xa']]

def read(p):return json.loads(Path(p).read_text())
def rate(x,m):return 90*x/m if m>0 else np.nan
def number(v):
    try:
        n=float(v);return n if np.isfinite(n) and n>=0 else np.nan
    except (ValueError,TypeError):return np.nan

def main():
    D.mkdir(exist_ok=True);assert not (D/'manifest.json').exists(),'Do not overwrite a sealed release';verify_files(OLD,read(OLD/'manifest.json')['files']);training=pd.read_pickle(OLD/'training.pkl');view=pd.read_pickle(OLD/'pool_features.pkl');schema=read(OLD/'schema.json');masterpath=R/'datasets/fpl_master_enriched_v5/player_matches.csv.xz'
    master=pd.read_csv(masterpath,usecols=['season','code','native_minutes','history_eligible','observation_available_after_proxy']);master=master[master.history_eligible].copy();master['at']=pd.to_datetime(master.observation_available_after_proxy,utc=True,format='mixed');history={(s,int(c)):q.sort_values('at') for (s,c),q in master.groupby(['season','code'])};empty=master.iloc[:0]
    selections=read(R/'datasets/fpl_availability_all_seasons_v1/selected_sources.json');selection={(r['season'],int(r['round'])):r for r in selections};requests=pd.concat([training[['season','round','forecast_at']],view[['season','round','forecast_at']]]).drop_duplicates();assert not requests.duplicated(['season','round']).any();requested={(s,int(g)):at for s,g,at in requests.itertuples(index=False,name=None)}
    # Current and prior samples remain separate. Preseason bootstrap statistics
    # refer to the PREVIOUS season; current cumulative exposure is known empty.
    snapshots={};audit=[];deps={};status=[];sources=[]
    for (s,g),at in sorted(requested.items()):
        r=selection.get((s,g));frame={};valid=False;source=None
        if r and r['format']=='bootstrap':
            path=R/r['source_file'];raw=path.read_bytes();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==r['blob_sha'];deps[r['source_file']]=sha(path);boot=json.loads(lzma.decompress(raw));ev=next(e for e in boot['events'] if e['id']==g);source=pd.Timestamp(r['source_time']);actual=pd.Timestamp(ev['deadline_time']);valid=source<at and at-source<=pd.Timedelta(hours=24) and actual==at and (ev['is_next'] or ev['is_current'])
            sources.append(dict(season=s,round=g,file=r['source_file'],source_time=str(source),actual_deadline=str(actual),forecast_at=str(at),source_url=r['source_url'],commit=r['commit'],blob_sha=r['blob_sha'],sha256=sha(path),valid=bool(valid)))
            if valid:
                assert len({e['code'] for e in boot['elements']})==len(boot['elements'])
                for e in boot['elements']:
                    if e['element_type'] not in [1,2,3,4]:continue
                    code=int(e['code']);xg=number(e.get('expected_goals'));xa=number(e.get('expected_assists'));minutes=number(e.get('minutes'));has=np.isfinite(xg) and np.isfinite(xa) and np.isfinite(minutes)
                    hs=history.get((s,code),empty);native=float(hs.loc[hs['at'].lt(at),'native_minutes'].sum());previous=f'{int(s[:4])-1}-{s[2:4]}';ph=history.get((previous,code),empty);prior_minutes=float(ph.loc[ph['at'].lt(at),'native_minutes'].sum());bound=has and abs(minutes-(prior_minutes if g==1 else native))<1e-6
                    # A non-playing player cannot have accumulated xG/xA.
                    consistent=not has or minutes>0 or (xg==0 and xa==0)
                    if has and not consistent:bound=False
                    frame[code]=dict(xg=xg if bound else np.nan,xa=xa if bound else np.nan,minutes=minutes if bound else np.nan,known=bool(bound),source=source)
                    status.append(dict(season=s,round=g,code=code,snapshot_has_fields=bool(has),qualified=bool(bound),source_minutes=minutes,expected_native_minutes=prior_minutes if g==1 else native,preseason_previous_season=g==1,reason='qualified_reported_fpl_snapshot' if bound else 'fields_not_yet_available' if not has else 'exposure_or_semantics_mismatch',source_time=str(source),forecast_at=str(at)))
        snapshots[(s,g)]=frame
        audit.append(dict(season=s,round=g,forecast_at=str(at),source_qualified=bool(valid),source_players=len(frame),known=sum(v['known'] for v in frame.values())))
    rows=[];timing=[]
    # Include only the exact original training and inference keys. Registering
    # a player in a later snapshot never fabricates an earlier training row.
    keys=pd.concat([training[['season','round','code','forecast_at']],view[['season','round','code','forecast_at']]]).drop_duplicates();assert not keys.duplicated(['season','round','code']).any()
    for s,g,code,at in keys.itertuples(index=False,name=None):
        g=int(g);code=int(code);x={k:np.nan for k in FEATURES};own=snapshots.get((s,g),{}).get(code);prior=snapshots.get((s,1),{}).get(code);cur=None;latest=[]
        if prior and prior['known']:
            for kind in ['xg','xa']:x[f'{kind}_previous_total']=prior[kind];x[f'{kind}_previous_per90']=rate(prior[kind],prior['minutes'])
            latest.append(prior['source'])
        if g==1 and own and own['known']:
            # Verified original deadline precedes all current season releases.
            hs=history.get((s,code),empty);assert not hs['at'].lt(at).any();cur=dict(xg=0.,xa=0.,minutes=0.,known=True,source=own['source']);latest.append(own['source'])
        elif g>1 and own and own['known']:cur=own;latest.append(own['source'])
        if cur:
            for kind in ['xg','xa']:x[f'{kind}_current_total']=cur[kind];x[f'{kind}_current_per90']=rate(cur[kind],cur['minutes'])
            for w in [3,10]:
                g0=max(1,g-w);old=snapshots.get((s,g0),{}).get(code)
                if g0==1:old=dict(xg=0.,xa=0.,minutes=0.,known=True,source=old['source']) if old and old['known'] else None
                if old and old['known']:
                    minutes=cur['minutes']-old['minutes']
                    if minutes>=0:
                        for kind in ['xg','xa']:
                            delta=cur[kind]-old[kind];x[f'{kind}_reported_change_{w}']=delta;x[f'{kind}_change_per90_{w}']=rate(delta,minutes)
                        if g0>1:latest.append(old['source'])
        assert not latest or max(latest)<at
        rows.append(dict(season=s,round=g,code=code,**x));timing.append(dict(season=s,round=g,code=code,forecast_at=str(at),latest_xg_source=str(max(latest)) if latest else None,known_current=cur is not None,known_previous=bool(prior and prior['known'])))
    extra=pd.DataFrame(rows);extra[FEATURES]=extra[FEATURES].astype('float32');extra.to_pickle(D/'xg_features.pkl');timing=pd.DataFrame(timing);timing.to_csv(D/'xg_timing.csv.gz',index=False);pd.DataFrame(status).to_csv(D/'xg_qualification.csv.gz',index=False);pd.DataFrame(audit).to_csv(D/'xg_origin_coverage.csv',index=False);atomic_json(D/'xg_sources.json',sources)
    for name,base in [('training.pkl',training),('pool_features.pkl',view)]:
        enriched=base.merge(extra,on=['season','round','code'],how='left',validate='one_to_one');assert len(enriched)==len(base);pd.testing.assert_frame_equal(enriched[base.columns],base.reset_index(drop=True));enriched.to_pickle(D/name)
    for name in ['availability.csv.gz','calendar.csv','calendars.pkl','comparability.csv','feature_coverage.csv','metadata.pkl','observed_calendar_reconciliations.csv','origins.csv','origins.pkl','policy_backend_hashes.json']:os.link(OLD/name,D/name)
    schema['features']+=FEATURES;schema['feature_groups']['expected_attack']=FEATURES;schema['expected_attack_contract']='Archived predeadline FPL reported cumulative totals, correctly separate previous season preseason values; increments over up to3/10 deadline intervals including recorded revisions; per90 denominator is reported minutes; missing is NaN, never unknown0. No final-history xG backfill.';atomic_json(D/'schema.json',schema)
    cov=[]
    enriched=pd.read_pickle(D/'pool_features.pkl')
    for s,q in enriched.groupby('season'):
        for c in FEATURES:cov.append(dict(season=s,feature=c,known_share=float(q[c].notna().mean())))
    pd.DataFrame(cov).to_csv(D/'xg_feature_coverage.csv',index=False)
    atomic_json(D/'qualification.json',dict(passed=True,feature_count=len(schema['features']),new_features=len(FEATURES),all_old_values_and_keys_identical=True,all_sources_predeadline=True,git_time_proxy_not_push_receipt=True,unknowns_remain_missing=True,negative_reported_changes_preserved=True,preseason_statistics_are_previous_season=True,no_final_statistical_vintages_used=True,field_definition='FPL reported xG is shot scoring probability sum; xA is completed-pass goal-assist likelihood, not Fantasy-assist award probability',official_definition='https://www.premierleague.com/en/news/3118332',collector_lineage='https://github.com/Randdalf/fplcache/blob/4aaec38e6b5f5ade8b63162a3678ce67148adb67/cache.py',qualification_scope='Archived FPL-reported predictors with recorded Git/source clock; not independent Opta model version validation or every API publication receipt',rows=len(training),pool_rows=len(view)))
    deps.update({str(p.relative_to(R)):sha(p) for p in [Path(__file__),OLD/'manifest.json',OLD/'training.pkl',OLD/'pool_features.pkl',masterpath,R/'datasets/fpl_availability_all_seasons_v1/selected_sources.json',P/'source_cache.py.txt',P/'source_README.md.txt']});files={p.name:sha(p) for p in D.iterdir() if p.is_file()};atomic_json(D/'manifest.json',dict(id='fpl_common_training_v4',parent='fpl_common_training_v3',rows=len(training),pool_rows=len(view),features=len(schema['features']),new_feature_group='expected_attack',evaluation_seasons=['2023-24','2024-25','2025-26'],input_hashes=deps,files=files,production_model_changed=False,qualification='xg snapshot archived FPL-reported qualification; same old statistical/calendar/market limitations retained'))
    print('COMMON XG BUILT',len(training),len(view),len(schema['features']),flush=True)
    print(pd.DataFrame(cov).pivot(index='feature',columns='season',values='known_share').round(3).to_string(),flush=True)
if __name__=='__main__':main()
