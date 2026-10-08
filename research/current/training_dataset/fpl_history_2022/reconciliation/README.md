# Kvalifisert 2022/23-versjon av forventede statistikker

Versjon `same_fpl_final_2022_snapshot_reconciliation_v2`, 8. oktober 2026.
Alle **26 505 kanoniske rader i 380 kamper** har kvalifiserte xG/xA/xGI/xGC-
verdier i en separat avledet visning. Historisk tilgjengelighet før frist,
poeng/BPS/bonus og samlet treningsleveranse er fortsatt ikke godkjent.

## Kildeversjoner og myndighet

Begge statistikkversjoner er arkiverte uttrekk fra FPL, med samme identiteter og
hendelsesankre. Ingen ekstern leverandør erstatter kompatibel FPL-statistikk.

- Ukentlig GW16-fil er fra commit
  [`92f81c3`](https://github.com/vaastav/Fantasy-Premier-League/commit/92f81c3063ae2ae361daecc81fa51f909dd109a9),
  publisert 23. november 2022. Alle 667 kanoniske GW16-rader gjenskapes eksakt:
  identitet, kamp, minutter, hendelsesankre og fire forventede statistikker.
- Sesongens avsluttende historikk er dokumentert i commit
  [`7009d35`](https://github.com/vaastav/Fantasy-Premier-League/commit/7009d351b6077cc3f3ae5bdc3a7e23f58f6817e6),
  publisert 29. mai 2023. Alle 778 spillerkatalogers Git-treidentiteter er
  uendret mellom dette tidspunktet og den allerede innhentede kilden.
  Dessuten samsvarer SHA-1 for **hver faktisk CSV-bytefil** med Git-bloben fra
  mai 2023. Kontrollen avviser manglende, ekstra eller dupliserte filer.
- Kildekode fra mai 2023 i `provenance/` viser direkte innhenting av FPL
  element-summary og eksport av history-rader. Tekstkopiene er referanser,
  ikke kode som kjøres i reproduksjonen.
- FPLs [offisielle forklaring](https://www.premierleague.com/en/news/3118332)
  definerer xGI som xG+xA. De publiserte Haaland-sesongtotalene 28,54 xG,
  3,11 xA og 31,65 xGI stemmer også med det fryste FPL-registeret.

Git-dato dokumenterer eksistensen av arkivversjonen, ikke den eksakte
publiseringsdatoen hos FPL for hver historisk verdi. De ulike GW16-verdiene er
reelle tidligere/senere FPL-versjoner, ikke bare avrundingsavvik. Arkivbeviset
fastsetter ikke hvorfor FPL reviderte dem.

## Avgrensede endringer

| Omfang | Behandling | Rader |
|---|---|---:|
| Før GW16 | Direkte slutt-FPL-backfill for den strukturelle rånullblokken | 8 491 |
| GW16 | Dokumentert senere FPL-versjon; tidligere verdier beholdes | 667 |
| GW29 | Kun ugyldig xGI repareres fra kompatibel original xG+xA | 296 |
| Øvrige rader/felt | Kompatible originalverdier beholdes numerisk uendret | Full populasjon |

Samlet endres **12 571 feltverdier**, med original, ny verdi og begrunnelse
registrert enkeltvis. Rader i backfill-/versjonsgruppene kan ha uendrede
numeriske nuller; gruppens radtall er derfor ikke antall endrede felt.
GW29 endrer verken xG, xA eller xGC. Ingen minutter, hendelsestellere,
historiske poeng, assists, BPS eller bonus overskrives.

## Kontroller og begrensninger

V1s mislykkede likhetskontroll mot ukesuttrekk beholdes: **482 kontrollfeil**.
Ingen terskler er senket og ingen feilkamper ekskludert. V2 er en dokumentert
avstemming av faktiske kildeversjoner og matematisk xGI-definisjon. Den er
utviklet etter diagnostikk og utgjør ikke en ny fasituavhengig prediktor eller
uavhengig leverandørholdout. Plan, innganger og senere innhentede bevis har egne
lås-/fingeravtrykkfiler med eksplisitt kontrollstadium.

Alle 778 kildeobjekter og 18 eksakte GW16-feltsammenligninger består. Den
faktiske avledede visningens **3 112 spiller-/feltsummer** stemmer med
sesongregisteret innen de opprinnelige summerings-/avrundingstoleransene.
xGI-additivitet og de 244 kampene / 775 ikke-pilotspillerne stemmer etter
dokumentert versjonsavstemming, med de opprinnelige numeriske toleransene.
Disse er integritets-/referansekontroller; de viser ikke når feltene var kjent
før historiske beslutninger.

## Datakort og bruk

`expected_statistics_qualified.csv.xz` har eksakt én rad per
`season, fixture, code`, uten tap av kanoniske observasjoner. For hvert av de
fire forventede feltene finnes:

- originalfeltnavnet og `*_original`: uendrede kanoniske råverdier;
- `*_final`: kildeverdien fra avsluttende FPL-historikk;
- `*_qualified`: verdien i denne separate statistikkversjonen;
- `*_quality`: `native_compatible_fpl`, `direct_final_fpl_backfill`,
  `documented_later_fpl_snapshot_revision` eller `exact_native_xg_plus_xa_repair`.

`source_file` og `source_sha256` peker på den avsluttende kildefilen som
backfill/revisjon og referansekontroll bruker. For beholdte råverdier gjelder
også den kanoniske FPL-kildelinjen i inventaret. Matematisk xGI-reparasjon
bygger på original xG/xA, selv om sluttkilden også finnes ved siden av.
`historical_feature_availability_qualified` er false på **alle rader**.
Dette feltet må respekteres av den senere featurebyggingen; sluttverdiene skal
ikke automatisk tilordnes historiske før-frist-snapshots.

`manifest.json` oppgir kvalitet, datadekning og fingeravtrykk. Åpne poengkrav
er fortsatt **16 227** og kvalifiserte hele historiske poengkamper fortsatt **0**.
Pre-2022-kompatibel xG, poeng-/kildegater, tidsriktige features og faktisk
treningsintegrasjon gjenstår.

## Reproduksjon

Fra repositoryroten, Python 3.12 / pandas 2.2.3:

```sh
python research/current/training_dataset/reproduce.py
python -m unittest discover -s research/current/training_dataset/fpl_history_2022/reconciliation -p 'test_*.py' -v
```

Den samlede reproduksjonen bruker bare lokale, fryste innganger i en separat
kopi og gjenskaper **82 byteidentiske resultatfiler**. Tretten nye tester
dekker feil Git-identitet, endret katalog, duplisert inventar, manglende eller
ugyldig backfill, sesongavgrensing, bevaring av kompatible verdier og poeng,
eksakt xGI-reparasjon og kontroll av den faktiske visningens sesongsummer.
Samlet fokuserte testsamling: **55 tester**, uten modelltrening.
