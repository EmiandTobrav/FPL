"""Publish the audit and its single-intervention diagnostic without promotion."""
import sys,json,re,shutil
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import atomic_json,sha,verify_files
from scripts.audit_season_comparability import P,OLD,NEW,SEASONS,ARMS
T=P/'rolling_reference_v2';LABEL={'component':'Komponentmodellen','operational_fixed':'Dagens operative referanse'}
def read(p):return json.loads(p.read_text())
def f(x,d=0):return format(x,'.'+str(d)+'f').replace('.',',')
def main():
    verify_files(R,read(P/'input_manifest.json')['files']);a=read(P/'audit.json');assert a['passed'];cal=read(P/'calendar_policy_audit.json');assert cal['passed'];verify_files(R,cal['files']);tv=read(T/'manager_verification.json');assert tv['passed'];verify_files(R,read(T/'proposal.json')['input_hashes']);league=pd.read_csv(P/'league.csv').set_index('season');terms=pd.read_csv(P/'score_decomposition.csv');calendar=pd.read_csv(P/'calendar.csv');markets=pd.read_csv(P/'markets.csv');updates=pd.read_csv(P/'calibration_updates.csv');q=pd.read_csv(P/'feature_coverage.csv').pivot(index='group',columns='season',values='known_share');players=pd.read_csv(P/'player_contributions.csv');new_results=pd.DataFrame(tv['scores']).set_index('setting');old_results=pd.read_csv(NEW/'scores.csv');old_results=old_results[old_results.arm.eq('operational_fixed')].set_index('setting')
    lines=['# Hvorfor falt begge modellene i 2025/26?','',
      '**Kontrollen finner ingen manglende kamper, feil poengsummering eller bytte av målstandard. De seks opprinnelige sesongtotalene gjenskapes nøyaktig. Kalenderdekningen og referansens løpende kalibreringsgrunnlag er derimot ikke likeverdige mellom sesongene.**','',
      'Fallet er reelt for de lagrede valgene under de lagrede kildene. Det dokumenterer ikke at 2025/26 i seg selv hadde færre FPL-poeng tilgjengelig: det samlede harmoniserte poenggrunnlaget er litt høyere. De beste poengsankerne, deres priser, modellenes eierskap og kapteinsuttelling endres betydelig. Den eksakte poengvirkningen av kalenderpolitikken er ikke isolert av denne revisjonen.','',
      '## Kort sammenlignbarhetskontroll','',
      '| Kontroll | Funn | Vurdering |','|---|---|---|',
      '| Kamper og mål-runder | 380 kamper og 38 runder i alle tre sesonger; komplett kampinventar, 38 kamper per klubb, samsvar i kamp-ID, runde og avspark | Sammenlignbart på dekning |',
      '| Poengstandard og summering | Samme harmoniserte 2026/27-mål, samme bonusrangering, kaptein, benk og fire poeng per betalt bytte | Ingen regnefeil funnet |',
      '| Manager, regler og start | Samme programkode, tom tropp, £100 millioner, én gratisovergang, åtte chipbruk over to halvparter, samme søkegrenser | Sammenlignbart under det felles fryste regelsettet |',
      '| Priser og spillerutvalg | Samme enhet og tidsregel, ingen fremtidige metadata. Første 2025/26-liste er betydelig eldre | Ulik kildeferskhet; historiske markedsproxyer |',
      '| Kalender og fremtidig motstander | 2025/26 bruker langt flere ukjente/foreldede opplysninger; komplett rekonstruksjon finnes, men streng friskhetsregel maskerer mye | Ikke likeverdig informasjonsdekning |',
      '| Referansens sesongkalibrering | Nye nåsesong-rader i 2023/24 og 2024/25, ingen i den opprinnelige 2025/26-testen | Oppdateringsgrunnlaget var forskjellig |','',
      'Regelsettet er det samme kontrafaktiske regelsettet i alle år, med fem oppsparte gratisbytter og fire chiptyper i hver halvdel. Det er en sammenligning av historiske kamputfall under dette regelsettet, ikke en gjengivelse av alle reglene som opprinnelig gjaldt i hver sesong. Tidsstempler og historiske kjøpslister er fortsatt proxyer.','',
      '## 1. Fasit og poengregning holder','',
      f'Alle {a["player_match_point_and_bonus_rows_recalculated"]:,} spiller–kamp-rader fra de tre årene er kontrollert: poeng er regnet på nytt fra native poeng, bonusendring, assistendring, defensive bidrag og de allerede dokumenterte hendelsesrevisjonene. Bonus er uavhengig rangert fra de lagrede mål-BPS-verdiene. Spiller–runde-summene er kontrollert mot kampene. Alle 228 valg og oppgjør fra de seks hovedsesongene er deretter gjenspilt fra kampfasit, priser og regelmotor.','',
      '| Sesong | Kamper | Harmoniserte poeng, hele spillergrunnlaget | Poeng til sesongens topp ti | Defensive bidrag i harmonisert fasit |','|---|---:|---:|---:|---:|']
    for s in SEASONS:
        z=league.loc[s];lines.append(f'| {s} | 380 | {f(z.target_points)} | {f(z.top10_points)} | {f(z.defcon_points)} |')
    lines+=['',
      'Forsvarspoengene ble lagt til eldre native sesonger ved omregning. I 2025/26 ligger de allerede i native poeng og blir derfor ikke lagt til en gang til. Den lille nettoendringen fra native til målpoeng i 2025/26 betyr dermed ikke at forsvarspoengene mangler.',
      'Fire avvik fra den enkle standardformelen i 2023/24–2024/25 skyldes tidligere registrerte mål-/selvmålsrevisjoner. Disse er eksplisitt inkludert i kontrollen. Ingen uavklarte aritmetiske avvik står igjen. Dette kontrollerer regningen på de lagrede kildene; eldre forsvars-/BPS-tilnærminger og uavklart kildesikkerhet blir ikke gjort til uavhengig verifiserte hendelser av denne kontrollen.','',
      '## 2. Hva består poengfallet av?','',
      'Poengregnskapet kan deles nøyaktig i tellende lag etter benkeinnhopp/bench boost, ekstra kapteinspoeng inkludert triple captain og byttekostnader. Direkte chipspoeng inngår allerede i de to første delene og skal ikke legges til en gang til.','',
      '| Modell | Del | Snitt 2023/24–2024/25 | 2025/26 | Endring |','|---|---|---:|---:|---:|']
    for arm in ARMS:
        z=terms[terms.arm.eq(arm)].set_index('season');old=z.loc[SEASONS[:2]].mean(numeric_only=True);new=z.loc['2025-26']
        for col,label in [('base','Tellende lag, uten ekstra kapteinspoeng'),('captain_bonus','Ekstra kapteinspoeng'),('hits','Byttekostnader'),('net','Netto sesongpoeng')]:lines.append(f'| {LABEL[arm]} | {label} | {f(old[col],1)} | {f(new[col],1)} | {f(new[col]-old[col],1)} |')
    lines+=['',
      'Komponentmodellens fall på 437,5 poeng består av 363 færre lagpoeng og 76,5 færre ekstra kapteinspoeng, delvis motvirket av to poeng lavere byttekostnader. Referansens fall på 333 består av 234 færre lagpoeng og 101 færre ekstra kapteinspoeng, også med to poeng spart på bytter. Manglende runder eller større hitkostnader forklarer altså ikke fallet.','',
      'Dette er en eksakt regnskapsdeling, ikke en kausal fordeling mellom kalender, spillerform og modell. Begge modeller brukte alle åtte tilgjengelige chips.','',
      '### Spillere og prisnivå endres','',
      'Salahs harmoniserte sesongpoeng faller fra 350 til 126 fra 2024/25 til 2025/26, Palmer fra 218 til 116 og Mbeumo fra 246 til 150. Haaland stiger samtidig fra 179 til 239. De ti beste spillernes samlede uttelling går ned, selv om totalen i hele ligaen stiger. Poengene er med andre ord fordelt annerledes.','',
      '| Modell | Spiller | Bidrag til laget 2024/25 | Bidrag 2025/26 | Endring |','|---|---|---:|---:|---:|']
    for arm in ARMS:
        z=players[players.arm.eq(arm)].pivot(index='code',columns='season',values='contribution').fillna(0)
        for code,label in [(118748,'Salah'),(223094,'Haaland'),(244851,'Palmer')]:
            if code in z.index:lines.append(f'| {LABEL[arm]} | {label} | {f(z.loc[code,"2024-25"])} | {f(z.loc[code,"2025-26"])} | {f(z.loc[code,"2025-26"]-z.loc[code,"2024-25"])} |')
    lines+=['',
      'Spillerbidragene inkluderer faktisk eierskap, tellende kamper og kapteinsmultiplikatorer i loggene. De isolerer ikke spillerform fra modellens kjøp/salg eller kapteinsvalg. En stor nedgang for én spiller kan bli delvis erstattet av økt uttelling fra andre.','',
      '## 3. Kalenderen: eksisterende rekonstruksjon ble for det meste maskert','',
      '| Sesong | H8-rader med kvalifisert kampantall | Referanse: ferske runder | Referanse: foreldede runder | Referanse: manglende runder |','|---|---:|---:|---:|---:|']
    for s in SEASONS:
        z=calendar[calendar.season.eq(s)];counts=z.reference_calendar_status.value_counts();lines.append(f'| {s} | {f(league.loc[s,"calendar_known_share"]*100,1)} % | {int(counts.get("archived",0))} | {int(counts.get("stale_future_no_adjustment",0))} | {int(counts.get("missing_neutral_h1",0))} |')
    lines+=['',
      '**Prosjektet har en separat, komplett rekonstruert kalender ved alle 38 fristene i 2025/26.** Den viderefører siste dokumenterte oppsett og bruker daterte kunngjøringer om flyttinger. Denne revisjonen har kontrollert 14 440 rekonstruksjonsrader, 380 kamper per tidspunkt, kildehashene og at alle oppgitte kilde-/hendelsesproxyer ligger før prognosetidspunktet.',
      'Den felles modelltesten brukte likevel et strengt spor: dersom grunnsnapshotet var eldre enn 14 dager, ble H8-kampantall, hjemmeandel og fremtidig motstanderkontekst satt til ukjent. Samme terskel ble brukt i alle tre år, men langt flere 2025/26-snapshots falt utenfor. Et likt regelverk ga derfor ulik faktisk informasjonsdekning.',
      f'Det strenge flagget skjuler også {cal["newly_announced_fixture_origin_rows_masked_by_base_freshness"]} kamp–opprinnelsesrader med daterte flyttemeldinger fordi grunnsnapshotet var gammelt. Dette gjelder blant annet de sene dobbel-/blankrundene. Den rekonstruerte eventplasseringen var til stede i filen, men ble ikke tatt i bruk gjennom friskhetsporten.',
      'Numerisk dekning for styrkefeltene faller samtidig fra omtrent 98–99 % til 69 %, fordi fremtidig motstander avhenger av kalenderen. Fraværskildene og dødballkildene ligger rundt 99 % kjent i alle tre sesonger. Vanlig historikk og belastningsfelt har heller ikke et tilsvarende dekningsfall.',
      'Ingen av de kjente null-kampantallene i disse testene ble feilaktig blanke sett mot gjennomførte kamper. Kalenderavvik i de to eldre årene ligger ved kamper som ble avbrutt eller utsatt etter kalenderens kildetidspunkt. Ukjent kalender ble ikke gjort til faktisk null eller fylt med den endelige kalenderfasiten.',
      'En videreført/kunngjøringsreparert kalender er en annen informasjons- og kildepolicy enn et ferskt arkivsnapshot. Den er ikke 38 nye historiske API-kvitteringer, og de videreførte avsparkstidene er ikke fullt tidskvalifisert. Den kan testes som et eget felles spor for kampantall, hjemme/borte og motstander; den skal ikke uten videre brukes som presis fasit for fremtidig hvile og klokkeslett. **Hvor mange sesongpoeng dette ville endret, er ikke målt her.**','',
      '## 4. Priser, spillerutvalg og innganger','',
      '| Sesong | Spillere i første arkivutvalg | Alder på første registreringssnapshot | Salahs registrerte startpris |','|---|---:|---:|---:|']
    for s in SEASONS:
        z=markets[markets.season.eq(s)&markets['round'].eq(1)].iloc[0];lines.append(f'| {s} | {int(z.players)} | {f(z.preseason_source_age_days,2)} døgn | £{f(z.salah_price/10,1)} |')
    lines+=['',
      'Alle 114 rundeutvalg har samme prisformat i pund/tideler; market = price_tenths = price × 10. Alle lagrede pris-, posisjons- og klubbtidspunkter er før den brukte prognosegrensen. Ingen faktor-ti-feil, ekstra åpningsbudsjett eller arvet tropp er funnet. Historiske priser og kjøpbarhet er fortsatt rekonstruerte proxyer, og første 2025/26-liste er eldre.',
      'De to inngangsbyggerne er identiske bortsett fra sesongvalg og fil-/cacheplassering. Samme 325 grunnfelt, kvalifisert historikk, ekte nullminutter og tidsfiltrering brukes. Ekspanderende utvalg av naturlig eldre sesonger og ulike kildedekninger betyr likevel at årgangene ikke er identiske datasett.','',
      '## 5. Referansen fikk ikke nye kalibreringsrader i 2025/26','',
      'I de to første sesongene fikk den faste sesongkalibreringen gradvis nye ferdigspilte nåsesong-observasjoner i treningsarkivet. I 2025/26 brukte den aktive oppskriften det fryste arkivet fra 2022/23–2024/25. Alle ti nye tilpasninger ga derfor samme kalibreringskoeffisienter, med null nåsesong-rader. I de to eldre årene finnes ti forskjellige koeffisientpakker.',
      '**Dette gjelder det ekstra sesongkalibreringslaget.** Den underliggende prognosemodellen og dens historikk ble fortsatt oppdatert; alle referanseprognoser var ikke konstante.',
      'For å måle denne ene forskjellen er det opprettet et nytt, tydelig diagnostisk arkiv med 2025/26-rader. Samme opprinnelige features, parametre, refitrytme, kalender, priser og manager er bevart. Bare lærerobservasjoner med både opprinnelse og full måltilgjengelighet før hver refit er tillatt. Prognosene i de fire første rundene gjenskaper den opprinnelige referansen før nye rader får virkning. Ingen live-fil eller gammel test er endret.','',
      '| 2025/26-oppsett | Opprinnelig referanse | Referanse med nåsesong-oppdateringer | Endring | Uendret komponentmodell |','|---|---:|---:|---:|---:|']
    for setting,label in [('adaptive_chips','Med chips'),('no_chips','Uten chips')]:
        z=new_results.loc[setting];old=old_results.loc[setting,'net'];comp=read(NEW/'manager'/f'component_{setting}/summary.json')['net'];val='Ufullført' if not z.complete else f(z.net);delta='—' if not z.complete else f(z.net-old);lines.append(f'| {label} | {f(old)} | {val} | {delta} | {f(comp)} |')
    lines+=['',
      'Med chips endrer denne kontrollen referansen med bare to poeng. Manglende nåsesong-oppdatering forklarer derfor nesten ingenting av det store fallet i hovedoppsettet i denne konkrete kontrollen. Uten chips er virkningen større. Den metodiske forskjellen skal fortsatt være synlig; det diagnostiske sporet er ikke den aktive modellen og er ingen ny uavhengig bekreftelse.',
      f'De 320 kalibreringshodene og alle {tv["decisions_replayed"]} nye lagrede valg/oppgjør er gjenspilt. Ingen modellinnstillinger ble søkt frem etter resultatene.','',
      '## Konklusjon og betydning for modellvalget','',
      '1. **Poengfallet er ikke en regne- eller kampdekningsfeil.** De lagrede poengsummene 2 565/2 604/2 147 og 2 468/2 498/2 150 er gjenskapt uavhengig.',
      '2. **Det tellende laget og kapteinene gir mindre uttelling.** Toppspillernes poengfordeling, priser og faktiske modellvalg endres betydelig. Dette er den direkte regnskapsforklaringen, men skiller ikke i seg selv mellom kalenderkvalitet, spillerutvikling og prediksjonsfeil.',
      '3. **2025/26 har svakere planleggingsinformasjon i det valgte strenge kalendersporet.** En separat rekonstruksjon finnes. Den tidligere beskrivelsen av «manglende kalender» var derfor for grov: mye informasjon var til stede, men satt til ukjent av kildepolicyen.',
      '4. **Referansens oppdateringsgrunnlag var annerledes.** Den isolerte kontrollen viser at dette ikke forklarer hovedfallet, selv om det endrer enkelte beslutninger.',
      '5. **−3-resultatet skal leses som utfallet av det konkrete fryste oppsettet.** Det er ingen ren bekreftelse på at modellene er like gode med ferske komplette innganger. Komponentmodellen ble valgt blant mange varianter på de to første utviklingssesongene; disse snittene kan også være optimistiske utvelgelsesresultater.',
      'Før vi bruker den nye sesongen som avgjørende modellvalg, må en ny sammenligning velge én eksplisitt kalenderpolicy for både trening og evaluering og én regel for løpende lærerarkiv. Ferske faktiske førfristinnganger eller et separat, tydelig merket rekonstruksjonsspor må brukes likt. Presise fremtidige avspark trenger egen kvalifisering. En ren etterutfylling med endelig kampfasit ville ikke være en gyldig reparasjon. Dagens operative modell er bevart.','',
      '## Underlag','',f'[Uavhengig audit]({P}/audit.json) · [Liga- og poengdekning]({P}/league.csv) · [Poengregnskap]({P}/score_decomposition.csv) · [Spillerbidrag]({P}/player_contributions.csv) · [Kalender per frist]({P}/calendar.csv) · [Kalenderpolicy]({P}/calendar_policy_audit.json) · [Priser og snapshotalder]({P}/markets.csv) · [Koeffisienter og læreroppdateringer]({P}/calibration_updates.csv) · [Kontrollert arkivoppdatering]({T}/manager_verification.json)','']
    report=P/'RESULTATER.md';report.write_text('\n'.join(lines));overview=R/'overview/SEASON_COMPARABILITY_AUDIT_2026_10_25.md';overview.write_text(report.read_text())
    trialdeps=[T/n for n in ['proposal.json','prediction_lock.json','forecast_verification.json','manager_verification.json','scores.csv','fit_audit.csv','diagnostic_archive.pkl']];result=dict(conclusion='Same-season reference calibration update isolated with unchanged other inputs. Adaptive-chips reference2150→2152; no-chip2024→2075. This does not explain the main cross-season fall. Diagnostic only; active files unchanged.',decision='retain_for_research',results=tv['scores'],evidence_hashes={str(x.relative_to(R)):sha(x) for x in trialdeps},production_changed=False);atomic_json(T/'result.json',result)
    # Revise navigation while retaining the exact previously delivered text.
    prior=R/'overview/COMPONENT_ADOPTION_READINESS_2026_10_25.md';previous=prior.read_bytes();(P/'prior_readiness_overview.md').write_bytes(previous);prior.write_text('# Komponentmodell – vurderingen er presisert etter datakontroll\n\n[Les den nye revisjonen av datagrunnlag, kalender og poengberegning](SEASON_COMPARABILITY_AUDIT_2026_10_25.md).\n\nDe tidligere poengtallene er riktige under det fryste oppsettet. Kalenderdekning og referansens læreroppdateringer gjør likevel 2025/26 til en mindre ren bekreftelsestest enn den forrige vurderingen ga inntrykk av. Aktiv modell er bevart.\n\n[Den opprinnelige vurderingen er arkivert uendret]('+str(P/'prior_readiness_overview.md')+').\n')
    candidate_path=R/'overview/COMPONENT_CANDIDATE.json';candidate=read(candidate_path);candidate.update(comparability_audit=str(overview.relative_to(R)),comparison_scope='original2025 result preserved; calendar coverage and calibration-update differences identified',next_gate='matched explicit calendar policy and teacher update policy, or genuine before-deadline paired trial',prior_overview_archive=str((P/'prior_readiness_overview.md').relative_to(R)));candidate_path.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n')
    root=R/'README.md';root.write_text(root.read_text().replace('# FPL prosjektoversikt\n','# FPL prosjektoversikt\n\n**Revisjon av 2025/26-fallet:** [Datagrunnlag, kalender og poengberegning](overview/SEASON_COMPARABILITY_AUDIT_2026_10_25.md). Poengsummene er gjenskapt; kalenderdekningen og kalibreringsarkivet var ikke likeverdige mellom sesongene.\n',1));nextfile=R/'overview/NEXT.md';nextfile.write_text('# Ny revisjon av sesongsammenligningen\n\n[Revisjonen av2025/26](SEASON_COMPARABILITY_AUDIT_2026_10_25.md) presiserer den forrige bekreftelsestesten. Bevar målstandard og manager; gjør kalenderpolicy og løpende kalibreringsarkiv eksplisitt like før ny konklusjon om modellvalg. Ikke fyll historiske innganger med sluttfasit. Den aktive modellen er ikke endret.\n\n'+nextfile.read_text())
    sources={str(x.relative_to(R)):sha(x) for x in P.rglob('*') if x.is_file() and x.name not in ['delivery.json','evidence_manifest.json']};atomic_json(P/'evidence_manifest.json',dict(files=sources,prior_readiness_overview_sha256=sha(P/'prior_readiness_overview.md')));verify_files(R,read(P/'input_manifest.json')['files']);links=0
    for target in re.findall(r'\]\(([^)]+)\)',overview.read_text()):
        if target.startswith('/'):assert Path(target).exists();links+=1
    atomic_json(P/'delivery.json',dict(passed=True,overview_sha256=sha(overview),audit_matches=1140,original_manager_decisions=228,diagnostic_manager_decisions=tv['decisions_replayed'],old_overview_sha256=hashlib_of(previous),old_readiness_bytes_preserved=True,evidence_sha256=sha(P/'evidence_manifest.json'),local_links_checked=links,production_changed=False));print('SEASON COMPARABILITY AUDIT DELIVERED',flush=True)
def hashlib_of(value):
    import hashlib
    return hashlib.sha256(value).hexdigest()
if __name__=='__main__':main()
