# Mållinjeklarering fra uttrykkelig spiller-sesongnull

Denne ferdigstilte innhentingsbatchen lukker **ett krav**, fra **11 188 til
11 187**. Reece James (kode 225796) i **2021/22 kamp 23** får dokumentert
mållinjeklarering **0**. Én ny spillerkamp blir inputkomplett: **66 479
spillerkamper og 824 hele kamper**. **16 mållinjekrav gjenstår**.

## Kildebevis og uendrede gater

Syv offentlige Premier League-rangeringer for `clearance_off_line` dekker
alle historiske sesonger 2019/20–2025/26. Bare en uttrykkelig ikke-negativ
heltallsverdi på null for den aktive spilleren brukes. Kode og kilde-ID
avstemmes mot allerede innhentede, hashkontrollerte sesongvise
appearance-lister. En spiller som mangler i rangeringen blir ikke null.
Positive sesongtotaler fordeles ikke på enkeltkamper. Hele sesongens null
beviser null i denne statistikken også i kampen; FPL-minuttene beholdes.

De første fire mål-sesongene ga 547 mulige spillerkamper. Før GL-utfall ble
sammenlignet ble kontrollomfanget utvidet til alle syv historiske sesonger,
uten å fjerne kontroller eller endre nullregelen. 2025/26 trenger ikke eget
GL-deltakrav i ledgeren, og denne sesongens 52 kontroller bruker alle
berørte nøkler fra den tidligere kvalifiserte v1-hendelsesversjonen.
Begge utvidelser er dokumentert før sammenligning. Opprinnelige 977
prediksjoner og før-utvidelsesfrys er bevart byte for byte i egne snapshots.

**1 028 kontroller i 818 kamper har null avvik**: 976 tidligere lukkede
ledgerverdier og 52 tidligere kvalifiserte hendelsesverdier fra 2025/26.
Ingen positiv arkivtelling motsier noen prediksjon. Den opprinnelige gaten
på minst 1 000 kontroller og null feil/motsetninger beholdes.
Dette er regresjon på godkjente kilder med felles Opta-opphav, ikke native
FPL-mållinjefasit, uavhengig holdout eller samlet kvalitetsgodkjenning.

## Den separate lagprøven er forkastet

Ett offentlig 2019/20-lagsvar gir bare **19 uttrykkelige lag** og sum **61**,
mot spillersum **51**. Det kan ikke sertifisere alle aktive lag eller
uttømme lagtotalene. Ruten forkastes; flere lagsvar hentes ikke, og ingen
utelatt spiller eller lag blir null. Opprinnelig plan, frys, råsvar og
[avslutningsbevis](league_findings.json) beholdes. Uendrede kilder skal ikke
gjenprøves. Den direkte uttrykkelige spiller-nullen er et separat bevis.

## Bevaring og reproduksjon

**775 247 øvrige ledger-rader og alle opprinnelige kilde-/tidligere-verdi-
kolonner for 775 248 rader er bevart.** Assists, native rettelser,
keeper-CBI-/frisparkavklaringer og gamle labels/modeller/benchmark endres
ikke. Kollektiv QA-flagg beholdes. Ingen ny BPS, bonus, poeng eller features.
Åtte responser ble innhentet. Fra første fryste kildeplan til vellykket
isolert replay tok batchen **14 minutter 31 sekunder**, eksklusive senere
publisering; [tidsmålingen](elapsed_report.json) bygger på lokale filstempler.

Fra denne mappen, med prosjektets Python-miljø og pandas:

```bash
python -m unittest -v test_bounds.py
python finalize_sources.py
python reproduce.py
```

Tre tester består: feil kilde-ID sperrer prediksjon, utelatt spiller blir
ikke null, og positiv godkjent motsetning sperrer anvendelse. **16 filer
reproduseres byteidentisk offline**. Snapshotkontrollen verifiserer også
de opprinnelige ett-/firesesongskildelistene og 977-prediksjonsfrysen.
Ingen ny nettinnhenting eller parquet er nødvendig.

[Kildeprotokoll](plan.json), [kontrollutvidelse](control_extension_plan.json),
[2025-referansevalg](reference_selection_plan.json),
[prediksjonsfrys](prediction_freeze.json), [kildehashverdier](sources.json),
[resultat](results/findings.json) og [replay](replay_report.json) dokumenterer
arbeidet. [CURRENT.json](../../CURRENT.json) velger gjeldende restliste.
Inputkompletthet er fortsatt ikke treningsklarhet.
