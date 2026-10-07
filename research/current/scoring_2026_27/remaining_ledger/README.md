# Samlet restliste for historisk 2026/27-harmonisering

> **Superseded as the current work queue:** see [FPL-authoritative ledger](../fpl_authority/README.md). Historical diagnostics and approved evidence below are retained; provider differences do not override compatible FPL values.

7. oktober 2026. Videreført på PR #1 fra `f799229dfbecaa11baf5d2a86b431eff6368a6ab`.
Dette er en **sammenkoblet kilde- og behovsoversikt**, ikke nye poengetiketter.
Alle godkjente keeperverdier, låste poeng/BPS/bonus, modeller og benchmark er bevart.

## Resultat uten dobbelttelling

Populasjonen er **77 280 unike spillerkamper i 2 660 kamper**, 2019/20–2025/26.
Nøkkelen er `(season, fixture, code)`, med FPLs stabile spillerkode. Alle har
en FPL-rad. Ingen aktive historiske FPL-rader faller utenfor populasjonen.
Én leverandøraktiv rad har null historiske FPL-minutter: Evan Ferguson,
2024/25, kamp 239, kode 487117. Den beholdes og må avklares før sluttberegning.

| Status for nødvendige felt etter sammenkobling | Felt–spillerkamper |
|---|---:|
| Dokumentert verdi større enn null | 673 347 |
| Dokumentert null, inkludert eksplisitte nullbevis | 800 612 |
| Manglende data i alle anvendelige, gjennomgåtte kilder | 806 298 |
| Motstridende eksplisitte kildeverdier | 18 322 |
| Uavklart assistberegning etter målreglene | 57 288 |
| **Sum nødvendige felt** | **2 355 867** |

**881 908 felt–spillerkamper står åpne**, fordelt på **77 280 unike
spillerkamper**. Alle spillerkampene har minst ett fortsatt sparsomt felt uten
dokumentert null. 18 016 har minst én kildekonflikt; 57 288 har uavklart
assistberegning. Disse kategoriene overlapper og skal **ikke summeres**.
`findings.json` viser de fire disjunkte overlappgruppene; spiller- og
kampoversiktene bruker samme entydige nøkler.

Dette er ikke de 3 003 033 tomme arkivfeltene, og heller ikke antallet nye
datatrekk som trengs. Mange hull er utelatte sjeldne tellere. En dokumentert
nullkonvensjon, en komplett hendelsesrekonstruksjon eller et tilstrekkelig
poengintervall kan senere løse flere uten ny spillerstatistikk. Ingen slik
generell nullkonvensjon er godkjent her. Oversikten angir tilgjengelige eksakte
tellinger; den påstår ikke at hvert ukjent felt vil endre poeng eller bonus.

17 360 minuttfelt har kildeavvik. Dette er statistikk-/revisjonsavvik, ikke
17 360 dokumenterte poengfeil. Uten minuttfeltet har **793 unike spillerkamper**
en konflikt i et nødvendig felt. Historiske FPL-minutter overskrives ikke.

## Rest per nødvendig felt

De to første tallkolonnene er databehov; regelkolonnen er separat.
Dokumenterte verdier/nuller per felt og sesong finnes i `field_summary*.csv`.
Hvert felt forekommer høyst én gang per spillerkamp.

| Felt | Manglende data | Kildekonflikt | Uavklart regel |
|---|---:|---:|---:|
| Minutter | 0 | 17 360 | 0 |
| Mål | 0 | 4 | 0 |
| Straffemål | 6 066 | 0 | 0 |
| Clean sheets | 0 | 0 | 0 |
| Baklengsmål for poeng | 0 | 0 | 0 |
| Redninger | 0 | 41 | 0 |
| Redninger innenfor boksen | 0 | 0 | 0 |
| Storsjanseredninger | 38 | 0 | 0 |
| Straffer reddet | 0 | 0 | 0 |
| Straffer bommet | 0 | 0 | 0 |
| Gule kort | 0 | 26 | 0 |
| Røde kort | 0 | 0 | 0 |
| Selvmål | 0 | 0 | 0 |
| Klareringer + skuddblokker + brytninger (CBI) | 4 614 | 420 | 0 |
| Gjenvinninger | 0 | 140 | 0 |
| Totale taklinger, utespillere | 0 | 93 | 0 |
| Vunne taklinger | 44 778 | 0 | 0 |
| Vellykkede innlegg uten cornere | 65 599 | 0 | 0 |
| Store sjanser skapt | 69 658 | 10 | 0 |
| Sjanser skapt | 5 230 | 0 | 0 |
| Vellykkede driblinger | 38 589 | 14 | 0 |
| Kampvinnende mål | 803 | 0 | 0 |
| Klareringer på mållinjen | 76 697 | 0 | 0 |
| Frispark vunnet | 42 880 | 1 | 0 |
| Skudd på mål | 40 951 | 0 | 0 |
| Pasningsforsøk | 0 | 111 | 0 |
| Vellykkede pasninger | 0 | 97 | 0 |
| Straffer forårsaket | 76 582 | 0 | 0 |
| Store sjanser brent | 71 237 | 2 | 0 |
| Feil som førte til mål | 76 382 | 0 | 0 |
| Feil som førte til skudd | 75 421 | 0 | 0 |
| Frispark imot | 0 | 3 | 0 |
| Offside | 69 822 | 0 | 0 |
| Skudd utenfor | 40 951 | 0 | 0 |
| Assists etter 2026/27-reglene | 0 | 0 | 57 288 |

CBI er ett poengbehov: en eksplisitt FPL-sum eller tre avklarte delverdier er
tilstrekkelig. Delkomponentene beholdes i feltloggen med
`required_for_scoring=False`; de inngår ikke igjen i resttall eller totalsum.
En sum av to kjente felt og ett utelatt felt godtas aldri som komplett CBI.
Totale taklinger og vunne taklinger holdes atskilt. Alle vellykkede innlegg
brukes ikke som erstatning for innlegg uten cornere. FotMob-/PL-clean sheets
erstatter ikke FPLs poengbetingede clean-sheet-felt.

## Keeper-, kamp- og assistbehov

- **5 343/5 381 godkjente keeperverdier beholdes nøyaktig**, med 38 blanke
  verdier. Resten er 37 observasjoner i de 21 manglende kildekampene og
  Ramsdale mot Villa 1. februar 2020. Opprinnelig sperre, kandidatverdi og
  godkjenningsmetode bevares i spilleroversikten og keeperkildene. En gammel
  kandidat overstyrer aldri et godkjent vedtak. Ingen xG-imputering.
- **593 spillerkamper i 21 kamper** mangler det supplerende arkivet. Dette
  er en kildeflagggruppe, ikke 593 komplette datatap: FPL, FotMob og
  primærkontroller kan allerede dekke enkeltfelt i disse kampene.
- **Tre ytterligere kamper, 95 spillerkamper og ni mål**, har arkivstatistikk,
  men mangler hendelser. De markeres separat i spiller- og kampoversiktene.
  De skal ikke legges oppå feltsummen som nye spillerkamper.
- **19 992 assistnuller kan bevises fra lagets offisielle null mål**. Dette
  er et nytt, separat nullbevis i behovsoversikten, ikke en endring i låste
  labels. De øvrige 57 288 spillerkampene trenger fortsatt komplett
  assistvurdering eller annet tilstrekkelig bevis. Dette er en konservativ
  vurderingspopulasjon, ikke 57 288 positive assistkandidater.
- De **fire offisielle assisttilleggene** er markert og bevart, men avgjør
  bare ett mål hver. De beviser ikke hele spillerens moderne kamptotal.
  De fire rådatabaserte avslagene av ti utviklingseksempler brukes heller
  ikke som komplette kampnuller. Seks eksempler er fortsatt ukjente;
  ingen ny uavhengig holdout eller historisk assistmodell er etablert.

Detaljerte keeperbestillinger finnes fortsatt i
[`required_observations.csv`](../keeper_recovery/remaining_audit/required_observations.csv).
Den målbaserte assistkøen og kodebegrensningene gjenbrukes fra
[`bps_recovery`](../bps_recovery/README.md),
[`assist_rules`](../assist_rules/README.md) og
[`assist_schema`](../assist_schema/README.md).
Måltall som stemmer med sluttresultatet beviser ikke komplett berøringsforløp.

## Filer og metode

- `remaining_fields.csv.gz`: samlet restliste med navn, sesong, kamp, dato,
  lag, FPL-/Opta-/FotMob-ID-er, nødvendig felt, alle tilgjengelige
  kildeverdier, status og grunn. Direkte brukbar uten å slå opp navn separat.
- `field_ledger.csv.gz`: også alle dokumenterte verdier/nuller og CBI-delbevis.
  Filtrer `required_for_scoring=True` ved opptelling av poengbehov.
- `player_matches.csv.gz`: én rad per spillerkamp, med feltliste,
  overlappende kategoriflagg, kildemangler og keeper-/assistkontekst.
- `player_summary.csv`, `match_summary.csv`: dedupliserte oversikter per
  spiller/sesong og kamp. Kategorikolonnene er overlappende;
  `affected_unique` er unionen.
- `field_summary.csv`, `field_summary_by_season.csv`: feltvis opptelling med
  eksplisitte positive verdier, nuller, mangler, konflikter og regelbehov.
- `field_definitions.csv`: kildefelter og posisjonsavgrensninger.
- `rule_gates.json`: globale formel-/valideringssperrer. Disse kopieres ikke
  kunstig til alle spillerkamper og telles ikke som manglende rådata.
- `manifest.json`: SHA-256 for hver lest inngang og hvert dataresultat.

Kildene er de eksisterende versjonerte FPL-GW-/spiller-/kampfilene, alle 42
FotMob-partisjoner, de sju historiske BPS-arkivuttrekkene, primærkontrollene,
keepersporets ytterligere 57 primærrader, harmoniserte defensive telleruttrekk,
godkjente keepervedtak og de offisielle assisttilleggene. FPLs dokumenterte
GW/kickoff-metode løser dupliserte kampregistreringer; alle andre
dupliserte eller manglende identitetsnøkler avvises.

Eksplisitte like tellinger kan fylle hverandres hull. Motstridende tall gir
blank sammenslått verdi og `source_conflict`, med unntak for allerede godkjente
keepervedtak. Null kan komme fra et eksplisitt tellerfelt, tidligere bevist
keeperverdi, null scorede mål som grense for straffe-/vinnermål, eller lagets
null mål som grense for assists. Vanlig fravær i arkivet er aldri nullbevis.
Kildene har delvis samme Opta-opphav: samsvar er ikke uavhengig validering.

Tidligere dokumenterte kildeforsøk i keeperoppfølgingen, restkontrollen og
innhentingsrapportene er lest. Ingen sperrede endepunkter er forsøkt igjen,
og ingen nye nettverksdata, kjøp eller leverandørhenvendelser inngår her.

## Gjenkjøring og neste arbeid

Krever Python og pandas; ingen stor rå-Parquet-cache eller nettverk trengs:

```sh
python research/current/scoring_2026_27/remaining_ledger/build.py
python -m unittest discover -s research/current/scoring_2026_27/remaining_ledger -p 'test_*.py'
```

**13 nye tester og 72 relevante eksisterende tester består**. To komplette
offline-kjøringer gir byte-identiske resultater for alle 12 datafiler;
122 inngangsfingeravtrykk er kontrollert. Testene kontrollerer blant annet
blank/null, konflikter, identitetsduplikater, CBI uten dobbelttelling,
assistnullgrensen, kategoriunionen og nøyaktig likhet med alle 5 381
historiske keeperverdier, inkludert de 38 blanke. `validation.json` dokumenterer
omfanget. Hele repositoryets testsuite og GitHub CI er ikke verifisert her.

Prioriter restlisten etter felt og kildeflagg: avklar først kildenes
utelatelsessemantikk for de mange sjeldne tellerne, undersøk de 793
spillerkampene med andre konflikter enn minutter, og bruk den konkrete
kampkøen for manglende arkiv/hendelser. Assistsporet trenger komplett
kandidatvalg og regelbevis før hele kamper kan godkjennes. Gjeldende
ikke-corner-/pasningsdefinisjoner og de to resterende primære BPS-avvikene
trenger fortsatt kvalifisering; tidligere brukte GW1/GW2 er ikke ny holdout.

Til slutt må grunnpoeng, defensive bidrag, BPS og bonus beregnes samlet.
Bonus avhenger av alle relevante spillere i samme kamp; det er en avledet
sperre, ikke enda et rådatahull som skal dobbelttelles. **Full historisk
harmonisering er fortsatt ikke ferdig.** Kostnad: 0 NOK.
