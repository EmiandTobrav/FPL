# Historiske storsjanseredninger: 5 324 av 5 381 rekonstruert

Kontrollert 7. oktober 2026. **98,94 % av de historiske keeperobservasjonene har
nå en kontrollert, hendelsesbasert telling. 57 observasjoner i 32 kamper er
fortsatt uløste.** Dette er et separat datatillegg. Låste poeng, BPS, bonus,
modelltrening og benchmark er ikke endret. Kostnad: 0 kroner.

## Løsningen

Det offentlige [pannadata-arkivet](https://github.com/peteowen1/pannadata)
publiserer Opta-baserte skudd og hendelser i GitHub Releases. Arkivet inneholder
det eksplisitte storsjansemerket som mangler i FotMob-råfilene våre. Vi har hentet
og SHA-256-kontrollert fire publiserte filer; kilder, versjoner og hashverdier
står i `source_manifest.json`. Dette bruker en offentlig eksport, uten å omgå
tilgangssperren som tidligere ble møtt hos Optas datatjeneste.

En storsjanseredning rekonstrueres fra et skudd med **Opta-type 15,
storsjansekvalifikator 214 og uten blokkeringskvalifikator 82**. Utespilleres
blokkerte skudd holdes utenfor. Ved keeperbytte kobles skuddet til keeperens
redningshendelse med kamp, lag, periode og tidspunkt. En tett retursekvens kan
aksepteres når alle aktuelle redningshendelser peker på samme keeper. Uavklart
keeperidentitet gir manglende verdi. xG brukes ikke.

`bigChanceSaves` forekommer også på utespillere i dette arkivet. Sesongsummer
over alle spillere er derfor ikke rene keepersummer. Historisk fravær av dette
feltet tolkes fortsatt ikke som null.

## Dekning i det låste datasettets keeperpopulasjon

| Sesong | Keeperobservasjoner | Rekonstruert | Uløst |
|---|---:|---:|---:|
| 2019/20 | 770 | 759 | 11 |
| 2020/21 | 765 | 751 | 14 |
| 2021/22 | 763 | 763 | 0 |
| 2022/23 | 770 | 749 | 21 |
| 2023/24 | 776 | 776 | 0 |
| 2024/25 | 770 | 763 | 7 |
| 2025/26 | 767 | 763 | 4 |
| **Sum** | **5 381** | **5 324** | **57** |

Historisk populasjon kommer fra de 42 allerede låste FotMob-partisjonene.
FPLs BPS-lister alene er ikke en fullstendig deltakerliste; enkelte keepere
med null BPS mangler der. Alle 5 381 opprinnelige nøkler er derfor beholdt.
Kampkobling krever sesong, dato, normaliserte lagnavn, hjemme/borte og identisk
sluttresultat. Spillerkobling bruker entydige navn innen den konkrete kampen,
med FPL-kode bevart. 5 339 observasjoner har kildekamp og spillerkobling;
minuttene er identiske mot FotMob for alle unntatt Robin Olsen mot Chelsea
1. desember 2024 (45 mot 46). Den observasjonen er allerede uløst.

## Kontroll og begrensninger

- Skuddmengde og scorede storsjanser kontrolleres mot kampens spillerstatistikk.
  Tapte storsjanser uten avslutning finnes også i Opta; tellingen for tapte
  storsjanser brukes derfor som øvre grense for slike skudd.
- Null krever komplett skudddekning og ingen kvalifiserende redninger. Et
  manglende keeperfelt blir aldri automatisk null.
- Rekonstruert telling må ikke overstige keeperens registrerte FPL-redninger.
  Motstridende eksplisitte storsjanseredningstall gir uløst verdi.
- **2026/27-kontroll:** 100 keeperobservasjoner i 50 kamper. Alle 52 eksplisitte
  storsjanseredningstall stemmer. De øvrige 48 manglende eksplisitte feltene
  regnes ikke som verifiserte nuller. Ingen av de 100 rekonstruksjonene bryter
  kontrollene. Dette er samsvar mellom to Opta-baserte datatyper, ikke en
  uavhengig dataleverandør eller en ny kontroll av hele FPL-BPS-formelen.
- Blant den historiske populasjonen og 19 tilgjengelige FPL-observasjoner fra
  2026/27 finnes 343 eksplisitte sammenligninger: 341 like, to konflikter.
- Ti fokuserte tester kontrollerer blokkeringer, manglende verdier, skudddekning,
  duplikater, periodekobling, keeperbytte, retursekvenser og identitetsnormalisering.

## Hva gjenstår konkret?

**42 observasjoner / 21 kamper mangler i kildearkivet:** fire kamper 1. desember
2019, sju kamper 5.–6. desember 2020 og ti kamper 1.–3. april 2023. Se
`missing_source_matches.csv`. Dette er en avgrenset bestillingsliste for en
supplerende hendelseseksport, ikke behov for å hente hele historikken igjen.

**15 observasjoner / 11 andre kamper har datakonflikter eller manglende merker:**
åtte mangler nødvendige skuddmerker, to har motstridende skuddantall, to har
motstridende tapte storsjanser, to har motstridende eksplisitt keeperfelt, og
én overstiger historisk FPL-redningstall. `unresolved_keepers.csv` angir nøyaktig
kamp, spiller, foreslått telling og sperregrunn.

De to eksplisitte konfliktene er Dúbravka mot Manchester City 22. april 2026
(tre merkede skuddredninger, eksplisitt telling to) og Sánchez mot Tottenham
19. mai 2026 (null fra skuddrekonstruksjonen, eksplisitt telling én). De velges
ikke bort fra kontrollrapporten, og ingen av tellingene er godkjent automatisk.
Danny Ward mot Chelsea 27. august 2022 har to rekonstruerte storsjanseredninger
og to redninger hos Opta/FotMob, men én redning i historiske FPL-data.

En supplerende eksport må inneholde eksplisitt storsjansemerke, skuddtype,
blokkeringsmerke og keeperidentitet/keeperbytter for restlisten. Sesongsummer,
xG-grenser og videoanslag kan ikke erstatte dette som eksakt Opta-grunnlag.
Dribble360s offentlige dokumentasjon viser en mulig kommersiell datakilde,
men faktisk dekning av disse kampene og nødvendige kvalifikatorer er ikke
verifisert. Ingen abonnement er opprettet og ingen forespørsel er sendt.

## Filer og gjenkjøring

- `keeper_counts.csv.gz`: godkjent felt `big_chance_saves`, separat
  `candidate_big_chance_saves`, status, sperregrunn og koblingsnøkler. Bruk kun
  rader med `status == reconstructed` som tellinger. Uløste rader har tomt
  godkjent felt.
- `save_evidence.csv.gz`: de merkede storsjanseskuddene, inkludert ekskluderte
  blokkeringer, keeperkobling og tilgjengelig original kvalifikator-JSON.
- `inputs/`: kompakte, versjonerte kildeuttrekk, delt per sesong.
- `fotmob_keepers.csv.gz`: hele den opprinnelige keeperpopulasjonen, med kode,
  kamp, minutter og redninger.
- `fixture_mapping.csv.gz`, `coverage.csv`, `findings.json`: koblinger og kontroll.
- `current_season_validation.csv`, `current_validation.json`: nyere kontroll.

Rutinekjøring krever bare pandas og de innlagte filene:

```sh
python research/current/scoring_2026_27/keeper_recovery/recover.py
python research/current/scoring_2026_27/keeper_recovery/validate_current.py
python -m unittest discover -s research/current/scoring_2026_27/keeper_recovery -p 'test_*.py'
```

`prepare_inputs.py` kan gjenskape kildeuttrekkene fra de fire publiserte
arkivfilene og repoets FPL-snapshot; dette krever i tillegg pyarrow. Den stopper
hvis den eksterne, mutable release-filen ikke lenger har den lagrede hashen.
Vanlig gjenkjøring bruker de versjonerte uttrekkene og trenger ikke nedlasting.

**Full historisk keeperdekning er fortsatt falsk.** Assists og resten av
BPS-innhentingen gjenstår separat. De nye tellingene må inngå i en samlet,
kontrollert omberegning før datasettet kan kalles fullt harmonisert til 2026/27.
