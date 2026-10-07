# Historiske storsjanseredninger: 5 343 av 5 381 avklart

Kontrollert 7. oktober 2026. **99,29 % av de historiske keeperobservasjonene har
nå en kontrollert telling. 38 observasjoner i 22 kamper er
fortsatt uløste.** Dette er et separat datatillegg. Låste poeng, BPS, bonus,
modelltrening og benchmark er ikke endret. Kostnad: 0 kroner.

## Oppfølging av restlisten

[18 nye avklaringer og konkrete sperrer](followup/README.md): 57 primærresponser
er hentet og kontrollert. Seks eksplisitte primærtall, fem dokumenterte
null-redningsgrenser, tre komplette redningsinventarer og fire tellinger fra
skudd- og skytterstatistikk løser 18 observasjoner. Alle keeperobservasjoner
i 2024/25 er nå dekket. `resolution_method` angir bevismetoden.

## Ny kontroll av kampstatistikk

[Én ny avklaring og 16 strammere usikkerhetsgrenser](resumption/README.md):
23 offisielle kampsvar er hentet. Sánchez er avklart til én storsjanseredning
via eksplisitt lagstatistikk og entydig keepertilordning. Hele 2025/26 er nå dekket.
38 observasjoner i 22 kamper gjenstår.

[Videre kontroll av restlisten](remaining_audit/README.md): 2 295 offisielle
hendelseskommentarer fra alle 22 kamper er kontrollert, sammen med nyere
kampstatistikk og fire nye arkivkandidater. Ingen nye eksakte tellinger ble
funnet. En konkret liste med alle 38 databehov og kilde-ID-er er lagret.

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
| 2019/20 | 770 | 761 | 9 |
| 2020/21 | 765 | 752 | 13 |
| 2021/22 | 763 | 763 | 0 |
| 2022/23 | 770 | 754 | 16 |
| 2023/24 | 776 | 776 | 0 |
| 2024/25 | 770 | 770 | 0 |
| 2025/26 | 767 | 767 | 0 |
| **Sum** | **5 381** | **5 343** | **38** |

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
- Første rekonstruksjon avviser tellinger over historiske FPL-redninger.
  Motstridende eksplisitte storsjanseredningstall krever kildeavklaring.
  Oppfølgingen dokumenterer ett revidert FPL-redningsavvik (Ward).
- **2026/27-kontroll:** 100 keeperobservasjoner i 50 kamper. Alle 52 eksplisitte
  storsjanseredningstall stemmer. De øvrige 48 manglende eksplisitte feltene
  regnes ikke som verifiserte nuller. Ingen av de 100 rekonstruksjonene bryter
  kontrollene. Dette er samsvar mellom to Opta-baserte datatyper, ikke en
  uavhengig dataleverandør eller en ny kontroll av hele FPL-BPS-formelen.
- Blant den historiske populasjonen og 19 tilgjengelige FPL-observasjoner fra
  2026/27 fant første kontroll 343 eksplisitte sammenligninger: 341 like, to
  konflikter. Oppfølgingen avklarer Dúbravka med offisielt primærtall tre;
  Sánchez-konflikten ble senere avklart med eksplisitt primærtall på lagnivå.
- Tjuefem fokuserte tester kontrollerer blokkeringer, manglende verdier, skudddekning,
  duplikater, periodekobling, keeperbytte, retursekvenser og identitetsnormalisering.

## Hva gjenstår konkret?

**37 keeperobservasjoner i 21 kamper mangler hendelsesgrunnlag.** De fem
øvrige keeperne i disse kampene er avklart med eksplisitt null redninger.
`missing_source_matches.csv` er fortsatt den konkrete listen over kildekampene.

**Én annen observasjon mangler skuddgrunnlag:** Ramsdale mot Aston Villa
1. februar 2020. Sánchez-konflikten er avklart i [den nye kontrollen](resumption/README.md).
De tidligere 18 vedtakene finnes i [oppfølgingsrapporten](followup/README.md).

Ingen av de 38 manglende verdiene er erstattet med null eller et xG-anslag.
En supplerende kilde må levere eksplisitte storsjansemerker og skille mellom
keeperredninger og utespillerblokker.

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
python research/current/scoring_2026_27/keeper_recovery/reconcile_followup.py
python research/current/scoring_2026_27/keeper_recovery/reconcile_match_totals.py
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
