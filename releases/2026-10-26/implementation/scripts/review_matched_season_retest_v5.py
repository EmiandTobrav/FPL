"""Independent input/prediction checks and human-readable publication, no new fits."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,pickle,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import matched_season_retest_v5 as m
P=m.P;KEY=m.KEY

def table(d,index=False):
    d=d.reset_index() if index else d
    def cell(x):
        if pd.isna(x):return '–'
        if isinstance(x,(float,np.floating)):return f'{x:.3f}'.rstrip('0').rstrip('.')
        return str(x).replace('|','\\|')
    return '\n'.join(['| '+' | '.join(map(str,d.columns))+' |','| '+' | '.join(['---']*len(d.columns))+' |']+['| '+' | '.join(cell(x) for x in row)+' |' for row in d.itertuples(index=False,name=None)])

def verify():
    m.check_inputs();m.verify_files(P,m.common.read(P/'prediction_lock.json')['files']);d=m.load('head_data.pkl');train=m.load('training.pkl');view=m.load('pool_features.pkl');origins=m.load('origins.pkl');cols=m.common.read(m.D/'schema.json')['features'];checks=values=0
    for s in m.SEASONS:
        saved=pd.read_pickle(P/f'component_{s}.pkl').set_index(KEY)
        for a in pd.read_csv(P/f'component_audit_{s}.csv').itertuples():
            at=origins[(s,a.round)];h=a.horizon;ts=[f'target_{v}_{h}' for v in ['points','minutes','starts','attack','appearance','residual']];tr=train[train.train_eligible&train.forecast_at.lt(at)&train[f'label_at_{h}'].lt(at)&train[ts].notna().all(axis=1)]
            assert len(tr)==a.rows and m.common.keys_hash(tr)==a.keys_sha256 and tr[f'label_at_{h}'].max()<at
            q=view[view.season.eq(s)&view['round'].between(a.round,min(a.round+3,38))];assert m.sha(P/a.file)==a.sha256
            with (P/a.file).open('rb') as f:b=pickle.load(f)
            assert b['columns']==cols;v,_,_=m.common.predict_arm(b,q);z=saved.reindex(pd.MultiIndex.from_frame(q[KEY]));np.testing.assert_allclose(v,z[[f'component_p{h}',f'component_m{h}']],atol=1e-9,rtol=1e-10);values+=len(q);checks+=1
    assert checks==80
    for j in range(8):np.testing.assert_allclose(d[f'u_count_{j}'],d[f'count_{j}'],equal_nan=True,rtol=0,atol=0)
    complete=d[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=d[[f'y_at_{j}' for j in range(3)]].max(axis=1);transforms=0
    for a in pd.read_csv(P/'head_audit.csv').itertuples():
        j=a.offset;at=pd.Timestamp(a.cutoff);tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&h3.lt(at)];raw,_,_=m.method.design(tr,'component',j);_,expected=m.method.transform(raw);model=m.common.read(P/f'heads/component_{a.season}_gw{a.round:02d}_j{j}.json')
        for k in ['median','mean','std']:np.testing.assert_allclose(expected[k],model['transform'][k],atol=1e-10,rtol=1e-10)
        transforms+=1
    # Historical points have the same meaning in both architecture inputs.
    master=pd.read_csv(m.common.MASTER,usecols=['season','fixture','code','history_eligible','target_total_points']);raw=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=['season','fixture','code','target_total_points']);z=master[master.season.between('2020-21','2025-26')&master.history_eligible].merge(raw,on=['season','fixture','code'],validate='one_to_one',suffixes=('_common','_raw'));np.testing.assert_allclose(z.target_total_points_common,z.target_total_points_raw,equal_nan=True,atol=0,rtol=0)
    # No completed fixture may remain a phantom future fixture after repair.
    events=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=['season','fixture','fixture_kickoff_time','kickoff_time']).drop_duplicates(['season','fixture']);events['available']=pd.to_datetime(events.fixture_kickoff_time.fillna(events.kickoff_time),utc=True)+pd.Timedelta(hours=24)
    for (s,g),ca in m.load('calendars.pkl').items():
        if s not in m.SEASONS:continue
        past=events[events.season.eq(s)&events.available.lt(origins[(s,g)])];f=ca['frame'];assert not (f.id.isin(past.fixture)&f.event.ge(g)).any()
    a=pd.read_csv(P/'head_audit.csv');update=[]
    for s in m.EVAL:
        q=a[a.season.eq(s)&a.offset.eq(0)];assert len(q)==10 and q['round'].tolist()==m.REFITS and int(q.current_season_rows.max())>0;assert q.current_season_rows.iloc[0]==0
        unique={arm:len({m.sha(P/f'heads/{arm}_{s}_gw{g:02d}_j0.json') for g in m.REFITS}) for arm in m.ARMS};assert min(unique.values())>1
        update.append(dict(season=s,updates=10,first_current_rows=int(q.current_season_rows.iloc[0]),last_current_rows=int(q.current_season_rows.iloc[-1]),component_unique_H1_heads=unique['component'],reference_unique_H1_heads=unique['operational_matched']))
    pd.DataFrame(update).to_csv(P/'rolling_update_summary.csv',index=False);m.atomic_json(P/'independent_forecast_verification.json',dict(passed=True,base_component_fits_checked=checks,base_values_replayed=values,training_only_transforms_recomputed=transforms,same_fixture_exposures_both_models=True,harmonized_input_points_checked=len(z),no_completed_ghost_future_fixtures=True,all_three_seasons_learn_current_year=True));print('INDEPENDENT VERIFICATION PASSED',flush=True)

def metrics():
    d=m.load('head_data.pkl');pred={a:pd.read_csv(P/f'{a}.csv.gz').set_index(KEY) for a in m.ARMS};rows=[]
    for s in m.EVAL:
        q=d[d.season.eq(s)&d.can_buy].copy();reference=pred['operational_matched'].reindex(pd.MultiIndex.from_frame(q[KEY]));q['candidate_rank_value']=reference.xp_0.to_numpy();selected=[]
        for (_,pos),g in q.groupby(['round','position']):selected.extend(g.sort_values(['candidate_rank_value','code'],ascending=[False,True]).head(dict(GK=5,DEF=20,MID=20,FWD=10)[pos]).index)
        for scope in ['all_buyable','same_reference_top_candidates']:
            z=q if scope=='all_buyable' else q[q.index.isin(selected)]
            for h in [1,3]:
                v=z[z[[f'y_{j}' for j in range(h)]].notna().all(axis=1)&(z['round']+h<=39)];y=v[[f'y_{j}' for j in range(h)]].sum(axis=1).to_numpy()
                for arm in m.ARMS:
                    xp=pred[arm].reindex(pd.MultiIndex.from_frame(v[KEY]))[[f'xp_{j}' for j in range(h)]].sum(axis=1).to_numpy();e=xp-y;rows.append(dict(season=s,scope=scope,horizon=h,arm=arm,n=len(y),mse=float(np.mean(e*e)),mae=float(np.mean(abs(e))),bias=float(np.mean(e))))
    pd.DataFrame(rows).to_csv(P/'forecast_metrics.csv',index=False)

def publish():
    assert m.common.read(P/'independent_forecast_verification.json')['passed']
    # Formatting adapter only: no optional third-party report dependency needed.
    pd.DataFrame.to_markdown=lambda self,index=True,**kw:table(self,index=index)
    m.report();metrics();score=pd.read_csv(P/'scores.csv');wide=score.pivot(index='season',columns='arm',values='net');wide['Forskjell']=wide.component-wide.operational_matched;wide=wide.rename(columns={'component':'Komponentmodell','operational_matched':'Dagens modelloppskrift'});mean=wide.mean(axis=0);wide.loc['Snitt']=mean;cover=pd.read_csv(P/'comparability.csv');cover=cover[cover.season.isin(m.EVAL)][['season','rounds','strict_calendar_snapshots','calendar_h1_known','calendar_h3_known']].copy()
    for c in ['calendar_h1_known','calendar_h3_known']:cover[c]=cover[c].map(lambda v:f'{100*v:.1f} %')
    cover.columns=['Sesong','Runder','Kalenderkilder før frist','Dekning neste runde','Dekning neste tre runder'];up=pd.read_csv(P/'rolling_update_summary.csv');up=up[['season','updates','last_current_rows']];up.columns=['Sesong','Rekalibreringer per modell','Egne sesongobservasjoner ved siste H1-oppdatering'];all_complete=bool(score.complete.all());gate=bool(all_complete and (wide.loc[m.EVAL,'Forskjell']>0).all());verification=m.common.read(P/'verification.json');verdict='Komponentmodellen slår den felles referansen i alle tre sesongene og består den forhåndsdefinerte forskningsporten.' if gate else 'Komponentmodellen består ikke den forhåndsdefinerte porten om å slå referansen i hver av de tre sesongene.'
    if not all_complete:verdict='Minst ett forsøk stoppet teknisk. Ufullførte forsøk har ingen sesongsum og sammenligningen kan ikke godkjennes.'
    output=R/'overview/MATCHED_MODEL_RESULTS_2026_10_25.md';text=['# Ny sammenligning på felles kalender og løpende kalibrering','',verdict,'','## Netto sesongpoeng','',table(wide,index=True),'','Poengene er etter trekk for betalte bytter. Referansen er dagens modelloppskrift trent på det rettede, felles datagrunnlaget og med samme oppdateringsmuligheter. Den aktive modellen er ikke byttet ut.','', '## Hva datasettet inneholder','', 'Én prognoserad per spiller og runde. Komponentmodellen bruker325 historiske innganger: spillerprestasjon og minutter, start-/innbytterroller, tilgjengelighet, dødballroller, belastning fra tidligere klubb- og landskamper, kalender, motstanderstyrke og tidligere observert vær. Grunnprognosene gjelder én og tre runder; manageren får åtte separate rundeprognoser.','', '2022/23 brukes til å lære den innledende kalibreringen. De tre testsesongene er2023/24,2024/25 og2025/26.2026/27 inngår ikke i trening eller evaluering. Ufullstendige målverdier blir utelatt, ikke satt til null.','', '## Samme regler i alle sesongene','', '- Offisiell frist hentes fra et lagret førfristøyeblikksbilde. Treningsrader med udokumentert eller for sen opprinnelig prognosefrist utelates.','- Kalenderen bruker siste fysisk arkiverte Git-versjon fra før fristen, med kontroll av både forfatter- og lagringstid. Bekreftede kamper beholdes selv om andre kamper mangler runde. Slike kampantall er nedre grenser. Null regnes som en sikker blankrunde i kilden bare når klubbens kalender er komplett.','- Allerede spilte kamper avstemmes først når kampstart pluss24 timer er passert. Det hindrer at en gammel kalender får modellen til å planlegge for en kamp som allerede er spilt.','- Samme kvalifiserte kamphistorikk og harmoniserte poengdefinisjon brukes for begge modellene. Reelle nullminutter beholdes; dokumenterte opphold utenfor Premier League gir ikke kunstige nullkamper.','- Nye grunnmodeller og kalibrering kommer i runde1,5,9,…,37 i alle tre sesongene. Begge kalibreringene bruker identiske kvalifiserte spiller-/rundenøkler per målvindu. Prognoseopphav og hele målvinduet må være tilgjengelige før oppdateringsfristen.','- Samme spillerutvalg, priser, startbudsjett£100m, manager, åtte prognoserunder, tre planleggingsrunder og felles spilleregler brukes i alle kjøringer. Reglene har fem bankede gratisbytter og to sett chips; dette er en sammenligning under ett felles regelsett.','',table(cover),'',table(up),'','## Kontroller og begrensninger','',f'{verification["decisions_replayed"]} lagbeslutninger er kontrollert på nytt mot lagreglene, og alle lagrede oppgjør er poengberegnet på nytt.80 komponentpakker og de lagrede grunnprognosene er kontrollert, og begge modellene får samme kampeksponering.240 kalibreringsvinduer har identiske lærernøkler, med uavhengig kontroll av tidsgrenser, treningsnormalisering og de lineære løsningene.','', 'Kildealder er fortsatt ulik: kalenderarkivene i2025/26 er ofte eldre. Ny kalenderpolitikk gjør tilgjengelige bekreftede kamper brukbare i alle årene, men kan ikke gjenskape en kunngjøring som ikke finnes i det historiske arkivet. Uversjonerte nettsider hentet senere og faktisk fremtidig vær er utelatt. Historiske kampdata følger den dokumenterte tilgjengelighetsregelen kampstart pluss24 timer; full dokumentasjon av alle tidligere statistikkversjoner finnes ikke.','', 'Dette er en retrospektiv utviklingstest på kjente sesonger. En bestått forskningsport er grunnlag for videre innføring og kontroll av ferske innganger, ikke automatisk aktivering.','', '## Detaljer','',f'- [Prognosefeil, samme rader]({P}/forecast_metrics.csv)',f'- [Dekning per inngang og sesong]({P}/feature_coverage.csv)',f'- [Kalenderkilde og alder per frist]({P}/calendar.csv)',f'- [Løpende oppdateringer]({P}/head_audit.csv)',f'- [Kontroll av prognosene]({P}/independent_forecast_verification.json)',f'- [Kontroll av lagbeslutningene]({P}/verification.json)']
    output.write_text('\n'.join(text)+'\n');m.atomic_json(P/'delivery.json',dict(research_gate_passed=gate,complete=all_complete,overview=str(output.relative_to(R)),input_manifest_sha256=m.sha(P/'inputs.json'),criteria_sha256=m.sha(P/'review_criteria.json'),files={str(p.relative_to(R)):m.sha(p) for p in [output,Path(__file__),P/'evidence_manifest.json',P/'scores.csv',P/'forecast_metrics.csv',P/'rolling_update_summary.csv',P/'independent_forecast_verification.json',P/'verification.json']}));print(wide.to_string(),flush=True);print('RESEARCH GATE',gate,flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
