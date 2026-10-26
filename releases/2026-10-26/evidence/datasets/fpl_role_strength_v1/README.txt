START-/INNBYTTERMØNSTRE OG DYNAMISK MOTSTANDERSTYRKE
25. oktober 2026

INNE I MASTER V5
101 nye felt er fysisk koblet til alle 190 124 opprinnelige PL-rader:
69 pr_-felt for spillerens rollehistorikk og 32 ds_-felt for lagstyrke.
Alle tidligere masterfelt, vær/sol, utlånsmarkeringer, belastning,
kalender, tilgjengelighet og dødballroller er bevart uendret.
Åtte sesonger 2019/20–2026/27; inneværende sesong fortsatt gjennom GW7.
Bare PL-kamper inngår i disse to nye historikklagene. Cup og landskamper
beholdes i de separate belastningsfeltene, ikke som nye FPL-observasjoner.

TID OG KVALITET
pr_forecast_at og ds_forecast_at følger av_forecast_at, inklusive de to
tidligere faktiske fristene i 2021/22 GW18 og 2024/25 GW15.
Bare observation_available_after_proxy strengt før fristen brukes.
Dette viderefører avspark+24t som tilgjengelighetsproxy; det er ikke
dokumentert faktisk mottakstid eller bevis for hvilken versjon av en
senere korrigert statistikk som forelå historisk. Begge nye lag har
strict_historical_qualified=False. Ingen senere resultater fyller hull.
Dobbeltrundens kamper får samme førfrist-rollehistorikk; første delkamp
kan ikke sive inn i egenskapene til andre delkamp i samme runde.

ROLLEHISTORIKK: pr_
Kilden er native_starts og native_minutes med eksisterende kvalifiserte
startetiketter. For 2026/27 er begge kontrollert mot den arkiverte,
komplette offisielle GW1–7-filen og dens låste revisjonskontroll.
Alle 5 460 lag-/kampgrupper har nøyaktig elleve registrerte starter.
Start bestemmes aldri av om spilleren nådde 60 minutter.
- start: kvalifisert start=1, også korte starter.
- sub: kvalifisert start=0 og minutter>0, også lange innhopp.
- none: start=0 og null registrerte minutter. Ubrukt benk, skade og
  annen utelatelse kan ikke skilles med denne etiketten.
- unknown: manglende/ukvalifisert start eller ugyldige minutter/etikett.

Alle 190 124 kildeetikettene passerer definisjonskontrollen i utgivelsen.
Dette betyr ikke at alle rader har tidligere historikk før første frist.
Bare history_eligible=True kan bli spillerhistorikk. De 30 243 markerte
utlåns-/utenfor-PL-nullene blir ikke negative rolleobservasjoner.

Vinduer er siste 3, 5 og 10 registrerte, historikkegnede spillerKAMPER i
samme sesong. De er ikke runder eller alle klubbens kamper før spilleren
kom inn i datasettet. Reelle nullobservasjoner inngår. Telling, kjent/
ukjent rolle og om vinduet er fullt følger hvert gjennomsnitt.
Start-, innhopp- og nullandel har kjente rolleobservasjoner som nevner.
Minuttsnitt ved start og innhopp har separate nevnere; fravær av slike
observasjoner gir tomt felt, aldri kunstig null eller et lagsnitt.
Betinget andel minst 60 minutter beholdes separat fra startandel.

Andre felt: påfølgende starter/innhopp/nuller, dager siden siste registrerte
rolle, siste rolleovergang og endring siste 3 mot 10 kamper.
pr_latest_appearance_preceded_by_no_minutes vurderes bare når siste
observasjon er en opptreden og den foregående har kjent rolle. Ellers
er feltet tomt. En foregående null beviser ikke skaderetur.
Historikken følger stabil spillerkode over klubbytte; siste klubb
og avvik fra målradens klubb er merket. Den er ikke en ren nåværende-
klubb-historikk. Forrige umiddelbart foregående sesong oppsummeres
separat; den fyller aldri korte inneværende-sesongvinduer.

DYNAMISK STYRKE: ds_
Målbasert, motstandsjustert og beskrivende indeks. Ikke en trent modell,
kalibrert målfrekvens eller sannsynlighet for scoring/clean sheet.
Faktiske lagresultater dedupliseres til 2 730 fysiske kamper; de tusenvis
av gjentatte spillerlinjene teller ikke som flere kamper.

Hvert lag starter med angrepsindeks=1 og innslippsindeks=1 i hver sesong.
Før første tilgjengelige kamp er prior_only=True og rå målsnitt tomt.
Høy angrepsindeks betyr sterkere angrep. Høy innslippsindeks betyr
svakere forsvar. Dette fortegnet er viktig ved bruk av variablene.

For hver historiske kamp låses motstanderindeks og ligabaseline strengt
før kampens eget avspark, også når tidligere kampresultater fortsatt
venter på 24-timersgrensen. Resultatet legges inn først ved tilgjengelighet.
Samtidige avspark/frister leser tilstanden før samtidige resultatoppdateringer.

Justert mål-for-ratio = faktiske mål / (ligabaseline for arenaen ×
motstanderens innslippsindeks før kampen).
Justert mål-mot-ratio = faktiske innslupne / (motstanderens arena-baseline ×
motstanderens angrepsindeks før kampen).
Indeks = (5 + summen av vektede ratioer) / (5 + summen av vektene).
Siste maksimalt 10 tilgjengelige kamper brukes med vekt 0,9^alder,
nyeste kamp alder=0. Nøytral priorvekt er fast 5, ikke lært fra resultater.
Ligaens hjemme-/bortebaseline bruker tidligere tilgjengelige resultater
med 20 faste pseudokamper på henholdsvis 1,5 og 1,2 mål.
Parametrene ble dokumentert før byggingen; ingen hyperparametersøk.

Lag og motstander har hver sin angreps-/innslippsindeks, historikktelling,
rå målsnitt og siste tilgjengelige kamp. Hjemme-/bortesnitt har egne
tellinger. Match attack index er lagangrep × motstanderinnslipp;
match concession index er laginnslipp × motstanderangrep.
Sesongstart, nyopprykkede lag og få kamper er eksplisitt merket via
prior_only og tellinger. Vi trekker ikke inn fremtidige tabeller eller
forrige sesongs styrke automatisk.

XG OG GRENSER
ds_xg_used=False. Flere historiske xG-felt er merket med ukvalifisert
FPL-definisjon, og fullstendige lagtotaler er ikke dokumentert for hele
perioden. Spiller-xGC kan heller ikke summeres til lagets xGC. Vi lager
derfor ikke skjulte xG-estimater eller bytter mellom xG og mål i indeksen.
Eksisterende xG-felt og usikkerhet er bevart til senere kvalifisering.
Kampkoblingen følger eksisterende master og er kontrollert mot klubb-
koder, motstander, arena, resultat og avspark. Dette rekonstruerer ikke
en ny historisk kunngjøringslogg for kampoppsettet.

FILER OG KONTROLLER
contract.json: metode/parametre og avgrensning låst før bygging.
player_history_audit.csv.gz: kompakt rågrunnlag, rolle og kvalitetsgrunnlag.
fixture_strength_audit.csv: én fysisk kamp, resultat og låste nevnerverdier.
player_match_context.csv.xz: 190 124 rader, season/fixture/code, begge lag.
player_round_role_context.csv.xz: 182 939 rader, season/round/code, kun pr_.
Styrken er kampbasert, siden to kamper i samme runde har ulike motstandere.
coverage.csv: sesongvis antall rader med tilgjengelig historikk.
summary.json: feltliste og dekning. verification.json: kontrollresultater.
build.py beregner; verify.py sammenligner uavhengige aggregater, historiske
styrkenivåer, kildebevaring, tidsgrenser og syntetiske grensetilfeller.
Fremtidige resultater endres i en test uten at tidligere felt får endres.
input_hashes.json og manifest.json låser kilder og resultater med SHA256.

loader.py iter_context() gir begge lag per kamp. by_round=True gir bare
rollelaget. strict=True gir ingen rader, siden historisk mottakstid er
proxy. masterens loader tilbyr alle felt i én tabell og beholder
history-visningen som utelater strukturelle nuller og retrospektivt vær.
Tidligere dataversjoner, ACTIVE.json og modeller er ikke endret.
