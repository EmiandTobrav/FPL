"""Publish one Norwegian overview from the sealed common-data comparison."""
import sys,json
from pathlib import Path
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json
from scripts import common_model_retest as run
D=run.D;P=run.P
NAMES={'ridge':'Ridge','extra_trees':'Extra Trees','ridge_extra_50':'50/50 Ridge + Extra Trees','hgb':'HGB','catboost':'CatBoost, alle felt','lightgbm':'LightGBM','two_part':'Todelt deltakelsesmodell','role_conditional':'Start/innhopp/ingen minutter','component':'Komponentmodell','point_distribution':'Poengfordeling med lærte forventninger','fixed_history':'Fast sesongvektet historikk','catboost_history':'CatBoost, bare grunnhistorikk','catboost_without_availability':'Uten tilgjengelighet/fravær','catboost_without_set_piece':'Uten dødballroller','catboost_without_workload':'Uten kampbelastning/hvile','catboost_without_role':'Uten rollemønstre','catboost_without_strength':'Uten dynamisk styrke','catboost_without_lagged_weather':'Uten tidligere kampvær'}

def main():
    verification=run.read(P/'verification.json');assert verification['passed'];assert run.read(D/'verification.json')['passed']
    m=pd.read_csv(P/'metrics.csv');summary=pd.read_csv(P/'summary.csv');coverage=pd.read_csv(D/'coverage.csv');manifest=run.read(D/'manifest.json');score=run.read(P/'score.json');schema=run.read(D/'schema.json')
    lines=['# Felles modelltest på beriket FPL-grunnlag','', '25. oktober 2026. Alle modellene er kjørt på den samme fryste spiller–runde-tabellen. Tidligere resultater er bevart; de er ikke brukt som nye kontrollresultater.','',
      '**Dette er en sammenligning av prognoser. Ingen nye sesongsimuleringer eller dokumentert forbedring av managerens netto sesongpoeng inngår. Dagens operative modell er beholdt.**','',
      '## Datagrunnlag','',f"Master v5 har 190 124 spiller–kamp-rader. Den nye tabellen har {manifest['rows']:,} spiller–runde-rader og {manifest['features']} eksplisitt tillatte prognosefelt. Komplette kilder og sjekksummer følger [manifestet](../../datasets/fpl_common_training_v1/manifest.json).",'',
      '| Sesong | Lagrede rader | Historikk-/treningskvalifiserte rader | Kjente H1-poengmål | Kjente H3-poengmål |','|---|---:|---:|---:|---:|']
    for row in coverage.itertuples():lines.append(f'| {row.season} | {row.rows:,} | {row.train_eligible:,} | {row.known_H1:,} | {row.known_H3:,} |')
    lines+=['','Tellingene over beskriver tabellen; faktisk treningsutvalg avhenger også av prognosetidspunktet og når hele målperiodens fasit var tilgjengelig. 2019/20 bidrar med historikk, men har ikke harmoniserte poengmål. 2026/27 lagres som nåtidsdel og brukes ikke til trening eller scoring i dette forsøket.','',
      'Spilleruniverset er observerte spiller–runde-rader. Det er ikke en fullt rekonstruert liste over alle kjøpbare spillere ved hver historiske frist. Ingen modeller får bruke rundens faktiske lag, posisjon, pris, motstander eller kampantall som input fra utfallsraden. Tidligere observert posisjon/pris/klubb og arkiverte kalendere brukes.','',
      'Ekte nullminutter og negative poeng beholdes. Dokumenterte strukturelle nuller utenfor PL inngår ikke som kvalifisert historikk eller treningsmål. Ukjente mål og manglende fremtidige rader blir ikke oppdiktede nuller. H3 summerer tre nøyaktige FPL-rundenumre; en ufullstendig målperiode er ukjent.','',
      '| Datagruppe | Felt |','|---|---:|']
    for name,cols in schema['feature_groups'].items():lines.append(f'| {name} | {len(cols)} |')
    lines+=['','Værfelt gjelder gjennomsnitt fra de tre siste tilgjengelige spillerkampene, ikke faktisk vær i målkampen. Ingen tidskvalifiserte historiske værvarsler er lagt til. Dødballer er rapporterte roller/scenarioer, ikke bekreftede takere. Cup og landslag er belastningskontekst med ufullstendig dekning; mangler betyr ikke at spilleren ikke spilte.','',
      '## Felles testoppsett','',
      '- Trening fra 2020/21 og fremover, med ekspanderende historikk. Oppdatering før GW1, 9, 17, 25 og 33 i hver evalueringssesong. Samme rader per treningsfold og horisont for alle modeller; betingede modellhoder bruker naturlig sine kategorier innen denne felles treningsdelen.',
      '- H1 og H3 trenes separat. Hele målperiodens statistikk må være tilgjengelig strengt før oppdateringen. H3-prognoser er direkte rundesummer, ikke åtte fremtidige enkeltprognoser til en manager.',
      '- 2022/23–2024/25 er tidligere undersøkte utviklingssesonger. 2025/26 rapporteres separat som en tidligere undersøkt senere kontroll, ikke en urørt holdout.',
      '- Prognosegrensen er den felles operasjonelle tidsproxyen. 2021/22 GW18 og 2024/25 GW15 utelates helt fordi den opprinnelige grensen var etter faktisk frist. Ingen sen prognose får bare et tidligere tidsstempel.',
      '- Imputering og eventuell skalering læres bare på treningsdelen. Alle numeriske felt har eksplisitte mangelflagg. Kildeidentiteter, fritekst og kvalitets-/utfallsflagg er ikke modellfeatures.',
      '- Fabrikkparametre er låst før kjøring. Ingen søk etter beste innstillinger eller resultatstyrte gjentakelser. Tidligere forkastede familier testes i nye, navngitte konfigurasjoner med de nye opplysningene.',
      '- Ridge trent på de samme nye dataene er den felles modellreferansen. Den aktive operative modellen `fixed_season_h8_adaptive_v1` er også scoret som fryst ekstern referanse på identiske evalueringsrader i de to sesongene med arkiverte prognoser. Den beholder sin opprinnelige trening og er ikke en nytrenet arm i den kontrollerte arkitektursammenligningen. Ingen operativ oppgradering er dokumentert av dette alene.','',
      '## Resultater for forventede poeng','',
      'Lavere MSE er bedre. Utviklingssnittet gir hver sesong lik vekt. Prosenten sammenligner med den nytrente felles Ridge-referansen. «Alle 3» krever lavere MSE i hver av de tre utviklingssesongene.','']
    family=[n for n in run.ARMS if not n.startswith('catboost_')]
    for h in [1,3]:
        z=summary[(summary.period=='development')&(summary.horizon==h)].set_index('arm');later=summary[(summary.period=='later_2025_26')&(summary.horizon==h)].set_index('arm');gates={g['arm']:g for g in score['gates'] if g['horizon']==h};base=z.loc['ridge','point_mse']
        lines += [f'### H{h}','', '| Modell | Utviklings-MSE | Mot Ridge | Bedre i alle 3? | MSE 2025/26 |','|---|---:|---:|:---:|---:|']
        for name in sorted(family,key=lambda n:z.loc[n,'point_mse']):
            value=z.loc[name,'point_mse'];gain=(base-value)/base*100;gate='Referanse' if name=='ridge' else ('Ja' if gates[name]['point_pass_all_development_seasons'] else 'Nei')
            lines.append(f'| {NAMES[name]} | {value:.4f} | {gain:+.2f} % | {gate} | {later.loc[name,"point_mse"]:.4f} |')
        lines+=['']
    anchor=pd.read_csv(P/'operational_anchor_metrics.csv');assert run.read(P/'operational_anchor_verification.json')['passed']
    lines+=['## Sammenligning med dagens operative modell','',
      'Her scores dagens fryste operative prognoser og samtlige nye varianter mot de samme nye masterfasitene, på nøyaktig de samme kjente og arkivert kjøpbare radene. Bare 2023/24 og 2024/25 har denne operative prognosepakken. Dette er et annet og mindre evalueringsutvalg enn hovedtabellene over.','',
      'Den operative modellens historiske trening er bevart. Forskjellene her kan derfor skyldes både trening, modell og informasjon. Tabellen dokumenterer felles evaluering, ikke at dagens modell er trent om på alle nye felt. Lavere MSE er bedre.','']
    for h in [1,3]:
        z=anchor[anchor.horizon.eq(h)].pivot(index='arm',columns='season',values='point_mse');z['mean']=z.mean(axis=1)
        lines += [f'### H{h}, felles operativt utvalg','', '| Modell | 2023/24 MSE | 2024/25 MSE |','|---|---:|---:|']
        for name in z.sort_values('mean').index:
            label='Dagens fryste operative modell' if name=='frozen_operational' else NAMES[name]
            lines.append(f'| {label} | {z.loc[name,"2023-24"]:.4f} | {z.loc[name,"2024-25"]:.4f} |')
        lines+=['']
    lines+=['## Bidrag fra de nye datagruppene','',
      'Samme CatBoost-oppsett brukes i alle disse armene. Positiv prosent betyr at fullpakken har lavere feil enn varianten uten datagruppen. Effektene kan overlappe og skal ikke summeres. Dette måler disse faste modellkonfigurasjonene, ikke informasjonens maksimale mulige verdi.','',
      '| Gruppe tatt bort | H1: gevinst av å beholde gruppen | H3: gevinst av å beholde gruppen | H1 bedre i alle 3 utviklingsår? |','|---|---:|---:|:---:|']
    dev=summary[summary.period.eq('development')].set_index(['horizon','arm']);allmetric=m[m.scope.eq('all')&~m.season.eq('2025-26')]
    for name in [n for n in run.ARMS if n.startswith('catboost_without_')]:
        values=[]
        for h in [1,3]:values.append((dev.loc[(h,name),'point_mse']-dev.loc[(h,'catboost'),'point_mse'])/dev.loc[(h,name),'point_mse']*100)
        z=allmetric[allmetric.horizon.eq(1)].pivot(index='season',columns='arm',values='point_mse');passed=(z.catboost<z[name]).all()
        lines.append(f'| {NAMES[name]} | {values[0]:+.2f} % | {values[1]:+.2f} % | {"Ja" if passed else "Nei"} |')
    for h in [1,3]:
        old=dev.loc[(h,'catboost_history'),'point_mse'];new=dev.loc[(h,'catboost'),'point_mse'];lines += ['',f'Hele utvidelsen mot CatBoost med bare grunnhistorikk, H{h}: {(old-new)/old*100:+.2f} % lavere MSE.']
    lines+=['','## Forventede minutter og sannsynligheter','',
      'Minutter vurderes separat fra poeng. Poengmodellene får dermed ikke en samlet karakter som skjuler en forverring i minutter.','',
      '| Modell | H1 minutt-MSE, utviklingssnitt | H1 minutt-MSE 2025/26 |','|---|---:|---:|']
    z=summary[(summary.period=='development')&(summary.horizon==1)].set_index('arm');late=summary[(summary.period=='later_2025_26')&(summary.horizon==1)].set_index('arm')
    for name in sorted(family,key=lambda n:z.loc[n,'minute_mse']):lines.append(f'| {NAMES[name]} | {z.loc[name,"minute_mse"]:.2f} | {late.loc[name,"minute_mse"]:.2f} |')
    lines+=['','Deltakelsessannsynligheter fra todelt modell og rollemodell vurderes med Brier, og poengkategoriene med normalisert RPS. Tabellen under gjelder H1; lavere er bedre. Disse målene sammenlignes innen samme hendelse, ikke med MSE.','',
      '| Sesong | Todelt: Brier deltakelse | Rollemodell: Brier deltakelse | Poengfordeling: RPS |','|---|---:|---:|---:|']
    for s in run.SEASONS:
        z=m[m.scope.eq('all')&m.horizon.eq(1)&m.season.eq(s)].set_index('arm')
        lines.append(f'| {s} | {z.loc["two_part","participation_brier"]:.5f} | {z.loc["role_conditional","participation_brier"]:.5f} | {z.loc["point_distribution","rps"]:.5f} |')
    lines+=['','## Hvordan resultatene skal tolkes','',
      'Alle modellfamiliene er testet på nytt på felles grunnlag, inklusive tidligere forkastede todelte, rolle- og komponentvarianter. En ny konfigurasjon som vinner her opphever ikke konklusjonen fra et eldre forsøk. Fast sesongvektet historikk i denne testen er en enkel nytreningsreferanse og er ikke den operative kalibreringspakken med samme ord i navnet.','',
      'Resultatene er utviklingsevidens fra flere allerede undersøkte perioder. Fire-runders blokkintervaller er lagret i intervals.csv. Mange modeller og overlappende tremålshorisonter gir usikkerhet; intervallene er beskrivende, uten korreksjon for alle sammenligningene. Små forskjeller bør ikke brukes som grunnlag for modellbytte alene.','',
      'Den faste topp60-gruppen i metrics.csv velges fra tidligere sesongvektet poenghistorikk, før utfall. Den er felles for alle armer og er en diagnostisk spillergruppe, ikke en lovlig tropp eller en modellspesifikk liste over de beste kjøpene. «Unflagged» er kun en sensitivitetsvisning.','',
      'For å avgjøre om en kandidat gir flere FPL-poeng må den få egne tidskontrollerte fremtidige enkeltprognoser og testes mot dagens operative modell med samme lovlige spillerpool, priser, åpningslag, manager, chips og ressursgrenser. H1-prognoser gjentas ikke kunstig over H8, og H3-summer fordeles ikke vilkårlig på fremtidige runder. Dette forsøket gjør ingen slik sesongpoengpåstand.','',
      '## Kontrollspor','',f"- {run.read(P/'prediction_lock.json')['fits']} primitive modelltilpasninger; 40 felles treningsfolder og {len(run.ARMS)} modell-/featurevarianter.",
      f"- Alle {verification['all_prediction_files_replayed']} prognosefiler er gjenspilt mot de lagrede modellene og kontrollert med sjekksummer.",
      '- Samme treningsnøkler og prognosenøkler er kontrollert i hver fold. Alle imputeringers medianer er gjenberegnet fra den respektive treningsdelen.',
      '- Masterens H1-poeng og minutter er kontrollsummert uavhengig. Tidligere historikk og H3-mål er etterregnet på et fast tilfeldig utvalg.',
      '- Både prognoseopprinnelse og hele målets tilgjengelighet er kontrollert før hvert fit. Historiske statistikkversjoner og faktisk mottakstid er fortsatt dokumenterte proxybegrensninger.',
      '- Kildedata, eldre resultater, aktiv modell og forseglede prospektive prognoser er bevart.','',
      '[Alle resultater per sesong og spillergruppe](metrics.csv) · [Felles resultatsammendrag](summary.csv) · [Parvise usikkerhetsintervaller](intervals.csv) · [Etterkontroll](verification.json) · [Låst forsøkskontrakt](proposal.json) · [Datakort](../../datasets/fpl_common_training_v1/README.md)','']
    (P/'RESULTATER.md').write_text('\n'.join(lines))
    (D/'README.md').write_text('\n'.join(['# Felles FPL-treningstabell v1','',f"{manifest['rows']:,} spiller–runde-rader, {manifest['features']} tillatte features. Bygget fra master v5; originalene er bevart.",'',
      'Bruk training.pkl for effektiv lokal innlesing eller training.csv.gz for portabel tilgang. schema.json har nøkkel, tillatte features og datagrupper. Velg kun schema["features"] som input; target_*, label_at_*, flagg, forecast_at og kjente klubber er metadata/utfall.',
      '', 'Filtrer train_eligible, forecast_at < prognosegrense og label_at_H < prognosegrense. Målet target_points_H og øvrige nødvendige mål må være kjente. Lær imputering og skalering bare på disse treningsradene. Bruk en ny fit ved hver forhåndsvalgt oppdatering.',
      '', 'H1/H3 er observerte poeng- og minuttsummer; native_starts skiller starter fra innhopp. Strukturelle utenfor-PL-rader brukes ikke som historikk. Ekte nullminutter og negative poeng beholdes. Manglende fremtidig runde eller ukjent utfall gir ikke null.',
      '', '2021/22 GW18 og 2024/25 GW15 er merket excluded_origin og utelates fra trening og scoring. Dette unngår sammenblanding av kontekstlag som ble beregnet ved forskjellige prognosegrenser. Faktisk historisk publiseringstid og kjøpbar roster er ikke fullt rekonstruert.',
      '', 'Vær gjelder bare tidligere tilgjengelige kamper. Avspark+24t er også her en tilgjengelighetsproxy; senere værrevisjoner er ikke dokumentert som sanntidsmottak. Aktuelt/fremtidig faktisk kampvær er aldri en feature.',
      '', 'Se coverage.csv, manifest.json og verification.json. Ny dataversjon eller endret utvalg krever nye kontroller og en ny sammenligningsrunde. Ingen operativ datape ker eller modell er automatisk erstattet.',
      '', '[Samlet modellrapport](../../reports/common_model_retest_2026_10_25/RESULTATER.md)','']).replace('datape ker','datapeker'))
    deps=[P/n for n in ['RESULTATER.md','metrics.csv','summary.csv','intervals.csv','verification.json','prediction_lock.json','fit_audit.csv','cohorts.csv','operational_anchor_metrics.csv','operational_anchor_verification.json']]+[D/'manifest.json',D/'verification.json']
    result=dict(conclusion='18 modell-/featurevarianter er sammenlignet på én felles, tidskontrollert spiller–runde-tabell. Resultater gjelder prognoser, ikke sesongpoeng eller operativ promotering.',decision='retain_for_research',results=summary.to_dict('records'),evidence_hashes={str(p.relative_to(R)):sha(p) for p in deps},production_changed=False,manager_run=False)
    atomic_json(P/'result.json',result)
    print('PUBLISHED',P/'RESULTATER.md',flush=True)

if __name__=='__main__':main()
