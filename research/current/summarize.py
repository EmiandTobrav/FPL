from pathlib import Path
import sys,json,gzip,pickle,copy,re,ast,hashlib,zipfile,html
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));from experiment import MODELS,SEASONS,opening,make_choice
NAMES={'ridge':'Ridge','bayes':'Bayesian Ridge','extra':'Extra Trees','hgb':'Boosting – grunnvariabler','hgb_extended':'Boosting – utvidede variabler','mix_ridge_extra_50':'50 % Ridge + 50 % Extra Trees','mix_ridge_hgb_25':'75 % Ridge + 25 % utvidet boosting','mix_ridge_hgb_50':'50 % Ridge + 50 % utvidet boosting','mix_ridge_hgb_75':'25 % Ridge + 75 % utvidet boosting','mix_three':'Ridge + Extra Trees + utvidet boosting (⅓ hver)'}
def main():
 rows=[];v=[];initials={}
 for path in (ROOT/'results').glob('trace_*.json.gz'):
  obj=json.loads(gzip.decompress(path.read_bytes()));r=obj['summary'];rows.append(r);s=r['season'];tr=obj['trace']
  assert len(tr)==34 and [x['gw'] for x in tr]==list(range(5,39))
  signature=json.dumps(obj['handoff'],sort_keys=True)
  if s in initials:assert initials[s]==signature
  initials[s]=signature
  assert r['points38']==r['opening_points']+sum(x['gross']-x['hits'] for x in tr)
  for x in tr:
   assert len(x['squad'])==15 and len(set(x['squad']))==15 and len(x['starters'])==11
   assert x['bank']>=0 and 1<=x['ft']<=5
   assert x['gross']==sum(x['contributions'].values())+x['captain_bonus']
  chips=[x['chip'] for x in tr if x['chip']]
  assert len(chips)==(8 if r['mode']=='fixed_chips' else 0)
  v.append(dict(season=s,model=r['model'],mode=r['mode'],rows=len(tr),reconciled=True,nonoptimal=r['nonoptimal']))
 results=pd.DataFrame(rows).sort_values(['season','mode','model']);assert len(results)==120
 results.to_csv(ROOT/'results/season_results.csv',index=False)
 pd.DataFrame(v).to_csv(ROOT/'results/verification.csv',index=False)
 # Recover audit records from initial build and resumed build, without depending on cache rebuild.
 audits=pd.DataFrame([json.loads(p.read_text()) for p in (ROOT/'results').glob('audit_*.json')]);assert len(audits)==6
 assert (pd.to_datetime(audits.training_max,utc=True)<pd.to_datetime(audits.first_cutoff,utc=True)).all()
 assert audits.old_forecast_max_difference.max()<1e-4
 audits.to_csv(ROOT/'results/input_audit.csv',index=False)
 baseline=results[results.model=='ridge'][['season','mode','points38']].rename(columns={'points38':'ridge_points'})
 results=results.merge(baseline,on=['season','mode']);results['gain']=results.points38-results.ridge_points
 summary=results.groupby(['mode','model']).agg(mean_points=('points38','mean'),mean_gain=('gain','mean'),min_gain=('gain','min'),max_gain=('gain','max'),wins=('gain',lambda x:(x>0).sum()),mean_hits=('hits','mean'),mean_transfers=('transfers','mean')).reset_index()
 summary.to_csv(ROOT/'results/model_summary.csv',index=False)
 selections=[]
 def pick(past,candidates,mode):
  z=past[(past['mode']==mode)&past.model.isin(candidates)].groupby('model').gain.agg(['mean','std'])
  z['score']=z['mean']-.25*z['std'].fillna(0)
  best=z.score.max()
  if 'ridge' in z.index and z.loc['ridge','score']>=best-2:return 'ridge'
  return z.sort_values(['score'],ascending=False).index[0]
 for mode in ['no_chips','fixed_chips']:
  for s in SEASONS[2:]:
   past=results[results.season<s];current=results[(results.season==s)&(results['mode']==mode)].set_index('model')
   allmodel=pick(past,MODELS,mode);single=pick(past,MODELS[:5],mode);ensemble=pick(past,MODELS[5:],mode)
   selections.append(dict(season=s,mode=mode,selected=allmodel,points=current.loc[allmodel,'points38'],gain_vs_ridge=current.loc[allmodel,'gain'],selected_single=single,single_points=current.loc[single,'points38'],selected_ensemble=ensemble,ensemble_points=current.loc[ensemble,'points38'],ensemble_vs_single=current.loc[ensemble,'points38']-current.loc[single,'points38'],all_vs_single=current.loc[allmodel,'points38']-current.loc[single,'points38']))
 select=pd.DataFrame(selections);select.to_csv(ROOT/'results/chronological_selection.csv',index=False)
 intervals=[];rng=np.random.default_rng(173)
 for mode,g in select.groupby('mode'):
  for metric in ['gain_vs_ridge','ensemble_vs_single','all_vs_single']:
   a=g[metric].to_numpy();boot=rng.choice(a,size=(10000,len(a)),replace=True).mean(axis=1)
   intervals.append(dict(mode=mode,metric=metric,mean=float(a.mean()),low95=float(np.quantile(boot,.025)),high95=float(np.quantile(boot,.975)),seasons=len(a)))
 pd.DataFrame(intervals).to_csv(ROOT/'results/selection_intervals.csv',index=False)
 # Prediction diagnostics on same eligible pools, all GW5-38; not outcome-filtered starters.
 diag=[]
 for s in SEASONS:
  with open(ROOT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
  from experiment import xp_for
  for m in MODELS:
   squared=[];absolute=[];toperrors=[]
   for gw in range(5,39):
    g=games[gw];y=np.array([g['actual'].get(i,0) for i in g['frame'].pid]);pred=xp_for(g,m);err=pred-y
    squared.extend(err**2);absolute.extend(np.abs(err));toperrors.extend((err[g['pred']['ridge']>=2])**2)
   diag.append(dict(season=s,model=m,rmse=np.sqrt(np.mean(squared)),mae=np.mean(absolute),ridge_2plus_rmse=np.sqrt(np.mean(toperrors))))
 pd.DataFrame(diag).to_csv(ROOT/'results/prediction_metrics.csv',index=False)
 # A material guard: changing same-round outcomes cannot change the choices.
 state,_=opening('2020-21')
 with open(ROOT/'results/games_2020-21.pkl','rb') as f:game=pickle.load(f)[5]
 fake=copy.deepcopy(game);fake['actual']={int(i):99999 for i in game['frame'].pid};fake['active']={int(i):True for i in game['frame'].pid}
 _,a=make_choice(game,'mix_three',state,None);_,b=make_choice(fake,'mix_three',state,None)
 for k in ['squad','starters','bench','captain','vice','incoming','outgoing']:assert a[k]==b[k]
 checks=dict(simulations=len(results),seasons=6,decision_rounds=120*34,identical_handoff_per_season=True,point_accounting=True,nonoptimal_decisions=int(results.nonoptimal.sum()),largest_solver_gap=float(results.max_solver_gap.max()),outcome_blind_decisions=True,original_forecast_max_difference=float(audits.old_forecast_max_difference.max()),temporal_training=True)
 (ROOT/'results/checks.json').write_text(json.dumps(checks,indent=2))
 def table(df):return df.to_html(index=False,float_format=lambda x:f'{x:.1f}',border=0,escape=True)
 def named(df):
  df=df.copy()
  for c in ['model','selected','selected_single','selected_ensemble']:
   if c in df:df[c]=df[c].map(NAMES)
  return df
 pieces=['''<!doctype html><html lang="nb"><meta charset="utf-8"><title>FPL – hovedmodell, første kombinasjonstest</title><style>body{font:16px/1.6 system-ui,sans-serif;color:#172d36;background:#f5f8fa;margin:0}main{max-width:1180px;margin:auto;padding:38px 24px}h1{font-size:34px;line-height:1.15}h2{margin-top:34px}table{border-collapse:collapse;font-size:13px;background:white;width:100%;margin:18px 0}th,td{padding:9px;border-bottom:1px solid #dce3e7;text-align:right}th:first-child,td:first-child{text-align:left}.scroll{overflow-x:auto}.note{padding:18px;background:#fff1d9;border-left:5px solid #b47710}.ok{padding:18px;background:#e2f2eb;border-left:5px solid #267554}code{background:#e7ecf0}li{margin:7px 0}</style><main><p>5. oktober 2026 · Retrospektiv forskningspilot</p><h1>Hovedmodellen: enkeltmodeller og kombinasjoner til GW38</h1><p>120 nye sesongforløp: seks sesonger, ti prognosemodeller og to chipregimer. Alle mottar nøyaktig samme tropp, bank, kjøpspriser og gratisbytter fra den vedlagte standard-startmodellen etter GW4. Ingen produksjonsparameter er endret.</p><div class="note"><b>Dette er ikke en ny, urørt sluttprøve.</b> Sesongene 2020/21–2025/26 er tidligere undersøkt i prosjektet. Historiske poeng kombineres med fem lagrede bytter og to sett chips. Prisene er historiske proxyer; komplett fristinformasjon og full omregning til årets poengregler mangler. Resultatene er verken faktiske historiske rangeringer eller dokumentert topp-5 %-sannsynlighet.</div><h2>Hva ble faktisk kjørt?</h2><p>Ridge, Bayesian Ridge og Extra Trees bygger videre på de eksisterende mottakerne. To nye HistGradientBoosting-modeller tester grunnvariablene og en utvidet variabelpakke. Kombinasjonene er aritmetiske gjennomsnitt av spillernes poengprognoser, før én felles optimizer velger tropp, ellever og kaptein. Ingen modell gir egne stemmer direkte til spillerkjøp.</p>''']
 spec=pd.DataFrame([dict(Modell=NAMES[m],Innhold=('Tidligere modellfamilie, uendrede parametere' if m in MODELS[:3] else 'Ny boostingmodell, samme grunnvariabler' if m=='hgb' else 'Boosting + angrep/forsvar, xG og spillerhistorikk' if m=='hgb_extended' else 'Faste vekter; ingen vekt er valgt med testsesongens fasit')) for m in MODELS]);pieces.append('<div class="ok"><b>Første funn:</b> 50/50 Ridge + Extra Trees ga i gjennomsnitt +37,2 poeng uten chips og +55,7 med felles chipkalender mot Ridge over seks sesonger. Den slo Ridge i henholdsvis fem og fire av seks sesonger. Dette er en beskrivende kandidat, ikke et forhåndsbekreftet vinneroppsett.</div><p>Når én modell ble valgt blant alle ti kun fra fortiden, var gjennomsnittlig gevinst i de fire evalueringssesongene bare +3,8 uten chips og +2,3 med felles chipkalender. Separate valg innen kombinasjonsfamilien ga større utslag, men familien er del av denne retrospektive undersøkelsen. Vi beholder derfor referansen og prioriterer 50/50-kombinasjonen for videre testing.</p>')
 pieces.append(table(spec))
 pieces.append('''<h2>Variabler og tidsgrenser</h2><p>Grunnvariablene omfatter tidligere poeng, minutter, mål, assists, clean sheets, spilletidsfrekvens, pris, posisjon, hjemmebane, Elo-forskjell, eget lags målrate og motstanderens baklengsrate. Utvidelsen tilføyer eget lags baklengsrate og motstanderens målrate, tidsvektet lag-xG for/mot, spillerens historiske xG/xA, redninger, bonus og minuttendring. Enkle målrateprodukter og exp(−forventede baklengsmål) brukes som matchup-variabler, ikke som en ferdig kalibrert Dixon–Coles-modell. Startfrekvensvariabelen er her en 60+-minuttersproxy.</p><p>Modellene trenes én gang før hver sesong, kun på eldre sesonger. Spiller- og laghistorikken oppdateres løpende før hver runde. Kampdata regnes tilgjengelige tre timer etter avspark; beslutningstidspunktet er den tidligere motorens konservative proxy, normalt 36 timer før rundens første kamp. Ingen xP-kolonne brukes. Alle kamper i en dobbelrunde har samme informasjonsgrense. xG mangler i eldre sesonger; en modell kan ikke lære av xG før slike historiske treningsdata finnes. Hele variabelpakken testes samlet, så et utslag beviser ikke at xG alene hjelper.</p><h2>Samlet beskrivende sammenligning</h2><p>Alle tall er nettopoeng etter hits. Gevinst sammenlignes med Ridge i samme sesong og chipregime. Gjennomsnittene nedenfor brukes ikke som bevis for et forhåndsvalgt beste alternativ.</p>''')
 for mode,title in [('no_chips','Uten chips'),('fixed_chips','Felles chipkalender')]:
  ss=summary[summary['mode']==mode].drop(columns='mode').sort_values('mean_points',ascending=False)
  pieces.append('<h3>'+title+'</h3><div class="scroll">'+table(named(ss))+'</div>')
 pieces.append('''<h2>Tidsordnet modellvalg</h2><p>For hver av 2022/23–2025/26 velges modell bare fra tidligere sesongers resultater. Valgskåren er gjennomsnittlig merpoeng mot Ridge minus 0,25 × sesongstandardavvik. Ridge beholdes dersom den ligger innenfor to poeng fra beste skår. Vi velger også beste enkeltmodell og beste kombinasjon separat på samme fortid. To innledende sesonger brukes før første evaluering. Dette er en tidsordnet retrospektiv utvelgelse, ikke et stort nestet hyperparametersøk.</p>''')
 for mode,title in [('no_chips','Uten chips'),('fixed_chips','Felles chipkalender')]:
  z=select[select['mode']==mode].drop(columns='mode')
  pieces.append('<h3>'+title+'</h3><div class="scroll">'+table(named(z))+'</div>')
 pieces.append('<p><code>ensemble_vs_single</code> sammenligner kombinasjonen valgt på fortiden med enkeltmodellen valgt på fortiden. <code>all_vs_single</code> sammenligner fritt valg blant alle ti med valg blant bare enkeltmodellene.</p>'+table(pd.DataFrame(intervals)))
 pieces.append('''<p>95 %-intervallene er en enkel paret bootstrap over fire sesonger. Fire sesonger er svært lite; intervallene beskriver historisk variasjon og dekker ikke all usikkerhet, utvalgsoptimisme eller fremtidige regimeskifter.</p><h2>Hva isolerer denne testen?</h2><p>Alle bruker samme én-rundes optimizer, med 0,10 benkvekt, 0,5 poeng byttefriksjon og lik kandidatfiltrering. Automatisk benk, kaptein/visekaptein, bank, kjøpspris, salgspris og byttetrekk følger tilstanden. Den faste chipkalenderen er WC6, TC15, FH18, BB19, WC24, FH33, BB36, TC37. Den er en kontroll med likt ressursbudsjett, ikke en optimal chipstrategi. Blanke runder, dobbeltrunder og historiske kampflyttinger følger endelig rundetildeling for den aktuelle runden; kunngjøringstidspunktene er ikke rekonstruert.</p><p>Det er ikke kjørt en ny minuttmodell, full hierarkisk hendelsesmodell, oddsmodell, stacking eller flerstegs bytteoptimalisering. Den nye boostingpakken og enkle prognosekombinasjoner er første avgrensede test. Startstrategiens eksisterende fremtidsverdi er beholdt i GW1–4, mens mottakerens planleggingshorisont holdes fast for å isolere prognoseendringer.</p><h2>Kontroller</h2>''')
 pieces.append(table(pd.DataFrame([checks])))
 pieces.append('''<p>Ingen samme-rundes fasit sendes til optimeringen. En kontroll med manipulerte poeng og tilgjengelighet gir identiske valg. Alle 120 forløp kontrolleres for felles overlevering, lagstørrelser, budsjett, bytter og poengregnskap. Prognosene i GW1–19 gjenskaper de eksisterende mottakerne innen avrunding. Eventuelle løsninger uten optimal solverstatus rapporteres over; optimalitet gjelder bare det prognosebaserte kandidatutvalget.</p><h2>Videre beslutning</h2><p>Resultatene skal brukes til å avgrense neste test, ikke til å automatisk erstatte referansen. Neste naturlige eksperiment er å holde prognosemodellen fast og teste flerukers bytteplanlegging. Separate ablasjoner og en dedikert minuttmodell trengs for å identifisere hvilke nye variabler som faktisk tilfører verdi. Prospektive før-frist-snapshots er nødvendig for en uavhengig bekreftelse.</p><h2>Kilder og reproduksjon</h2><p>Primære innganger er brukerens vedlagte FPL_modellpakke og FPL_parametertuning_v3. Offentlig supplerende datakilde: <a href="https://github.com/vaastav/Fantasy-Premier-League">Vaastav FPL Historical Dataset</a>. Metoder og begrensninger i kildekoden er bevart. Den pakkede LES_MEG.txt beskriver kjøring, og kontrollsummer følger med. Ingen nettverkskall kreves for å spille av de fryste inngangene.</p></main></html>''')
 (ROOT/'FPL_hovedmodell_test.html').write_text(''.join(pieces))
 print('MODEL SUMMARY\n',summary.to_string(index=False))
 print('CHRONOLOGICAL\n',select.to_string(index=False))
 print('INTERVALS\n',pd.DataFrame(intervals).to_string(index=False))
 print('CHECKS',checks)
if __name__=='__main__':main()
