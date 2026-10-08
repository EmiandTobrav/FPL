# Treningsdatasett etter 2026/27-reglene — arbeid pågår

Arbeidsgren: `codex/training-dataset-2026-27`, fra GitHub-commit
`3365c6cb5b3f827c88378e8349bfa7492af91361`. Rå FPL, godkjente historiske
rekonstruksjoner, gamle modeller og benchmark er bevart. Ingen modelltrening.

## Gjeldende leveranse

Den offisielle kilden markerte GW1–GW5 i 2026/27 som avsluttet ved innhenting
8. oktober 2026. Bootstrap, kamper, fem live-runder og alle 667 spillerhistorikker
er lagret som 674 råsvar med SHA-256. Spillerhistorikkene har individuelle
innhentingstidspunkter. For øvrige råsvar oppgis lokal filskrivetid.

| Område | Status |
|---|---|
| 2026/27 spillerkamper | 1 538 observasjoner, 50 avsluttede hele kamper |
| 2026/27 spiller–runde | 3 216 offisielle rader, inkludert ikke-deltakelse |
| Kvalitetskontroll | 16 918 sammenligninger av kampstatistikk; bonus for alle 1 538 deltakere; poengsum mot offisiell komponentforklaring |
| Historisk datarest | 14 907 feltkrav i 13 745 spillerkamper; 326 nye keeperlokasjoner avklart |
| Historisk inputdekning | 63 535 spillerkamper og 752 kamper inputkomplette |
| Historisk omregning | Fortsatt ikke kvalifisert; ingen nye historiske poengetiketter |
| Modellinput/treningspipeline | Ikke ferdigstilt eller koblet om |
| Historiske kampstarter | Alle 185 573 kanoniske rader; 22 startere i hver av 2 660 kamper |
| 2022/23 forventede statistikker | 26 505 kvalifiserte xG/xA/xGI/xGC-rader i 380 kamper; tilgjengelighet før frist uavklart |

Den [fulle startversjonen](lineups/conservation/README.md) avklarer de siste
32 672 null-minutt-rolleverdiene fra eksakte, komplette startellevere.
[Kvalifisert 2022/23-statistikkversjon](fpl_history_2022/reconciliation/README.md)
dekker alle 26 505 kanoniske rader. GW16-versjoner er dokumentert med arkiv-
og Git-objektbevis; GW29-xGI er rettet fra kompatibel xG+xA. Første mislykkede
kontroll beholdes med uendrede gater. 72 fokuserte tester består. Samlet
offline-replay dekker 94 byteidentiske resultatfiler.

## Ny dataavklaring: direkte keeperlokasjon

[Lokasjonsavstemming](../scoring_2026_27/bulk_reconciliation/followup_2026_10_08/fotmob_keeper_location/README.md)
lukker 326 krav med eksplisitt skuddopphav og entydig keeper-ID. Hele rednings-
inventaret må stemme med FPL og primære lag-/keeperankre. 40 kontrollkeepere
stemmer uten avvik; ti nye tester og elleve byteidentiske replayresultater består.
244 nye kamper er inputkomplette. 2025/26 har nå 363 slike kamper; disse trenger
sesongrelevante kilde-/regelgater og helkampbonus før poengetiketter godkjennes.
De siste 16 lokasjonskravene er sperret av redningsantall. Ingen differanseberegning
av lokasjon brukes. CBI-V1 feilet og er bevart med null nye avklaringer.

Den tidligere beregningsversjonen med 489 kandidatkamper er et bevart snapshot;
den er ikke den oppdaterte inputdekningen. Samlet historisk replay bruker fortsatt
den opprinnelige ledgerpekeren og endrer ikke fryste kontroller eller labels.

## Ny dataavklaring: alle skuddkrav lukket

[Skuddavstemming](../scoring_2026_27/bulk_reconciliation/followup_2026_10_08/fotmob_shot_conservation/README.md)
lukker 994 krav med eksplisitte lagtotaler og eksakt fordeling. 919 flere
spillerkamper og 18 flere hele kamper har komplette poenginput. 25 kontrollkamper
og 95 aktuelle kamper gir 710 samsvarende kildekontroller. Den tidligere
beregningsversjonen med 489 kandidatkamper bevares og reproduseres mot sitt
opprinnelige snapshot; 508 kamper i gjeldende ledger har nå komplette input.
Poengetiketter, features før frist og aktiv treningsintegrasjon gjenstår.

## Ny regelkontroll: mislykket kvalifisering bevart

[Legacy-taklingskontrollen](scoring/legacy_tackles/README.md) har 291 fryste
primærsvar fra alle seks gamle regelsesonger, med 264 feltavstemte beregninger.
185 rader skiller signert og klippet beregning, men 15 publiserte BPS-verdier
overskrider også den klippede beregningen. Fire kildeavvik gjelder to spillere.
De opprinnelige null-feil-gatene består ikke; ingen klipping eller historisk
poenglabel godkjennes. 25 ytterligere kontroller mangler CBI-belegg. Alle
kontroller, versjoner, uavklarte tellere og avvik er bevart. Ikke gjenta samme
kontroll uten nytt komponent-/kildebelegg. 17 nye tester dekker blant annet
feil nullsertifikater og kildeidentitet; samlet replay gjenskaper 94 filer.

## Historikk: tidligere delvise dataversjoner

[Ny startleveranse](lineups/README.md) har 152 901 kvalifiserte verdier på
185 573 kanoniske rader. Råverdiene beholdes. Offisielle lagoppstillinger
dokumenterer 2 992 feilaktige rånuller før GW16 i 2022/23. Samme periode har
uniforme xG/xA/xGI/xGC-nuller; semantisk dekning av disse feltene er uavklart.
Startleveransen godkjenner ingen historiske poenglabels. Samlet offline-replay
dekker nå 50 byteidentiske resultatfiler; 33 fokuserte tester består.

Historisk beregningsmotor er etablert med 185 573 kanoniske originalrader og
avstemt grunnpoengregnskap. Separate omregningskandidater finnes for 489 hele
kamper; **ingen historiske kandidater er godkjent for trening**. Kontrollen fant
også 12 null-minutt-rader med kort utenfor gammel ledger og to kildekonflikter.
Se [beregning, sensitivitet og sperrer](scoring/README.md).

Tabellene ligger i `snapshots/2026_10_08/derived/`:

- `player_matches.csv.gz`: historisk kampidentitet og klubbside fra FPL-historikk,
  alle offisielle kampstatistikker, egne target-poeng/BPS/bonus/assists,
  defcon-count og offisielt tildelte defcon-poeng, kildehenvisninger.
- `player_rounds.csv.gz`: offisielle rundetotaler og eksplisitte nuller for
  ikke-deltakere som finnes i den aktuelle rundeoversikten.
- `point_components.csv.gz`: hele den offisielle poengforklaringen per spillerkamp.
- `manifest.json`: kilde- og resultatfingeravtrykk, regel-/datasettversjon,
  omfang og begrensninger.

Bonus kontrolleres mot hele deltakerlisten, også spillere med nøyaktig null BPS.
FPLs separate kampoversikt utelater slike nuller. Rå spillerhistorikk gir eksplisitt
verdi og deltakelse; fravær i kampoversikten gjøres aldri til en observasjon.
GW1s 310 aktive rader stemmer med det tidligere fryste FPL-uttrekket på minutter,
mål, assists, BPS, bonus, totalpoeng og posisjon.

Dette er kvalifiserte offisielle utfall fra selve målsesongen, ikke en ferdig
historisk treningsleveranse. Ingen nåværende klubber, priser eller spillerstatus
er tilbakedatert. Kampstatistikk er sammenlignet mellom spillerhistorikk,
rundeoversikt og kampoversikt. Kontrollene er innen samme offisielle FPL-kilde,
ikke uavhengig leverandørvalidering. Pris/eierskap i historikken er metadata med
uavklart før-frist-tidspunkt og må ikke brukes direkte som beslutningsfeatures.
Posisjon/navn kommer fra målsesongens register; gamle GW1-posisjoner er avstemt.
Nye hendelsesdata hentes bare i en ny snapshotmappe, så gammel fasit ikke erstattes.

## Reproduksjon og tester

Bruk Python 3.12 og pandas 2.2.3. Fra repositoryroten:

```sh
python research/current/training_dataset/reproduce.py
python -m unittest discover -s research/current/training_dataset -p 'test_*.py' -v
python -m unittest discover -s research/current/training_dataset/penalty_controls -p 'test_*.py' -v
python -m unittest discover -s research/current/training_dataset/lineups -p 'test_*.py' -v
```

Reproduksjonen bruker bare fryste, lokale innganger i en separat kopi og
sammenligner SHA-256 for alle avledede resultatfiler. Den henter ikke nye data.
De tidligere åtte testene inkluderer feil poengforklaring, uferdig kamp, endret BPS,
null-BPS-deltakere, bonus ved delt plass og negative BPS, fasituavhengig
kontrollutvelgelse, endret inngang og feil assistfasit som skal sperre godkjenning.
Fjorten nye historiske transformasjons-/sperretester er også lagt til.
Ingen full repository-/CI-test påstås. Samlet replay gjenskaper historisk
beregning, startroller og den separate 2022/23-statistikkversjonen fra fryste
innganger: 94 identiske filer. De 72 fokuserte testene kjøres med separate
oppdagelser i `training_dataset`, `penalty_controls`, `lineups`,
`lineups/conservation`, `fpl_history_2022`, `fpl_history_2022/reconciliation`
og `scoring/legacy_tackles`.

Den eldre batch 3 er også gjenskapt: alle 63 resultatfiler ble identiske.
`replay_batch3.py` tilpasser kun gzip-headerens OS-byte for Linux-produserte
filer på macOS. CSV-innhold, prediksjoner, kildefingeravtrykk og forventede
resultatfingeravtrykk endres ikke. Den opprinnelige replay-rapporten bevares;
ny verifikasjon ligger i `batch3_replay_verification.json`.

## Straffekontroll: nytt kontrollbelegg, ingen nye verdier

`penalty_controls/` har en ny fryst kontrollplan for den eksisterende, strenge
prediktoren. I flermålskamper isoleres assistmottakerens straffebidrag bare når
alle andre bidrag til denne spilleren er kjente eller utelukket med allerede
kvalifiserte kandidatgrenser. FPL-assisttotaler leses først etter at planen er fryst.

30 kontroller i 27 kamper stemte: seks enmålskontroller og 24 isolerte bidrag fra
flermålskamper. Ingen konflikter med godkjente avgjørelser eller kandidatutelukkelser.
Kravet om minst 20 kontroller er beholdt; det nye oppsettet krever også minst
20 ulike kamper. Selvvunne straffer er fortsatt ikke kvalifisert. Dette er
tidsordnet regresjon på tidligere sette 2025/26-utfall og delt Opta-kilde,
ikke ny holdout eller full lagvektorkontroll for flermålskampene.

**Pilotens anvendelse ga null nye målavgjørelser og null nye assisttotaler.**
Alle relevante historiske prediksjoner var allerede beskyttede avgjørelser.
Ikke kjør denne ruten igjen i håp om å redusere dagens rest. De uavklarte
straffemålene trenger andre årsaksbevis; samme strenge prediktor dekker dem ikke.
Første valideringsforsøk stoppet på feil antatt koblingskardinalitet før noen
sammenligning ble beregnet. Bare kardinaliteten ble rettet, fra én-til-én til
mange-til-én for to straffer til samme mottaker i én kamp. Kode/lock fra første
forsøk er bevart; utvalg og kvalitetsgrenser ble ikke endret.

## Gjenstående arbeid før målet er oppnådd

1. Lukk faktiske gjenværende årsaksgap og øvrige numeriske gap fra
   `scoring_2026_27/bulk_reconciliation/CURRENT.json`. Straffepilotens nye
   kontrollstøtte endrer ikke denne restlisten eller de betingede prioriteringene.
2. Kvalifiser alle historiske BPS-deltaer, inklusive netto-taklingsklipping,
   gamle komponent-/revisjonsdefinisjoner og samlede godkjente målrettelser.
3. Kontroller de 73 eksterne felt-/sesonggruppene og dokumenterte unntak.
4. Beregn ny historisk BPS og helkampbonus, deretter komponentavstemte totaler;
   ingen uavklart kamp skal få kopierte historiske poeng som harmonisert label.
5. Fullfør sammenlignbar pre-2022 xG/xA/xGI/xGC og defensive tellinger.
   Historiske starter og en separat 2022/23-xG-versjon er nå kvalifisert;
   historisk før-frist-tilgjengelighet for statistikkene gjenstår.
6. Bygg hele det historiske spillerkamp-/rundeuniverset, tidsriktige features,
   horisont-targets og faktisk innlesing i den aktive treningspipelinen.
7. Frys samlet datakort, dekning, manifest og reproduksjon for hele leveransen.

Den opprinnelige gjennomføringskartleggingen gjelder fortsatt, med ett
oppdatert punkt: dagens FPL-uttrekk dekker nå GW1–GW5 i den nye snapshotversjonen.
