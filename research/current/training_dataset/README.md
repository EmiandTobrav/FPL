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
| Historisk datarest | 16 227 feltkrav i 14 990 spillerkamper; uendret |
| Historisk inputdekning | 62 290 spillerkamper og 490 kamper inputkomplette |
| Historisk omregning | Fortsatt ikke kvalifisert; ingen nye historiske poengetiketter |
| Modellinput/treningspipeline | Ikke ferdigstilt eller koblet om |

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
```

Reproduksjonen bruker bare fryste, lokale innganger i en separat kopi og
sammenligner SHA-256 for alle avledede resultatfiler. Den henter ikke nye data.
De tidligere åtte testene inkluderer feil poengforklaring, uferdig kamp, endret BPS,
null-BPS-deltakere, bonus ved delt plass og negative BPS, fasituavhengig
kontrollutvelgelse, endret inngang og feil assistfasit som skal sperre godkjenning.
Fjorten nye historiske transformasjons-/sperretester er også lagt til.
Ingen full repository-/CI-test påstås. Samlet replay gjenskaper nå også den
historiske beregningen fra fryste FPL- og ledgerinnganger: 25 identiske filer.

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
5. Fullfør sammenlignbar eldre xG/xA/xGI/xGC, starter og defensive tellinger.
6. Bygg hele det historiske spillerkamp-/rundeuniverset, tidsriktige features,
   horisont-targets og faktisk innlesing i den aktive treningspipelinen.
7. Frys samlet datakort, dekning, manifest og reproduksjon for hele leveransen.

Den opprinnelige gjennomføringskartleggingen gjelder fortsatt, med ett
oppdatert punkt: dagens FPL-uttrekk dekker nå GW1–GW5 i den nye snapshotversjonen.
