# Prioritert avklaringskø etter poengbetydning

> **Superseded as the current work queue:** see [FPL-authoritative ledger](../fpl_authority/README.md). Historical diagnostics and approved evidence below are retained; provider differences do not override compatible FPL values.

7. oktober 2026. Videreført fra `2aded7f` på eksisterende PR #1.
Dette er en separat analyse og et lite bevist datatillegg. Den tidligere
restlisten, godkjente keeperverdier og låste poeng/BPS/bonus/modeller er uendret.

## Hva eksisterende data avklarer

| Tiltak | Felt–spillerkamper | Hva er avklart? |
|---|---:|---|
| Laget spilte uavgjort eller tapte | 272 | `winning_goal=0`, dokumentert fra offisielt sluttresultat |
| Straffemålsfordeling for GK/DEF | 922 | Fordelingen trengs ikke til poeng: begge måltyper gir 12 BPS |
| **Avklarte poengbehov** | **1 194** | Fordelt på **1 146 unike spillerkamper** |

De 272 nullene ligger i `documented_zero_supplement.csv`, med kamp, spiller,
begge lags score og bevisgrunn. Alle eksplisitte kampvinnertellere er først
kontrollert mot regelen; ingen motsigelser finnes. Det gjøres ingen generell
slutning fra blank teller til null.

De 922 straffemålstellerne **forblir ukjente**. For keepere og forsvarere er
BPS-bidraget `12 × ordinære mål + 12 × straffemål = 12 × alle mål`.
Grunnpoeng for mål avhenger heller ikke av straffestatus. Totalt antall mål,
posisjon og andre komponenter må fortsatt være avklart. Dette gjelder ikke
MID/FWD, hvor straffemål har en annen BPS-vekt enn øvrige mål.

Utgangspunktet var 881 908 åpne feltbehov. Etter nulltillegget er **881 636
råstatistikk-/regelbehov** fortsatt åpne. Når også de 922 irrelevante
fordelingene tas ut av poengavhengigheten, er det **880 714 gjenstående
poengbehov**, fortsatt fordelt på **77 280 unike spillerkamper**.
Dette er ingen påstand om like mange poengfeil eller nødvendige datatrekk.

## Konflikter med og uten utslag i de registrerte alternativene

- **Minutter:** 16 649 av 17 360 konfliktobservasjoner gir identiske
  minuttpoeng og minutt-BPS for alle registrerte kildeverdier. **711** krysser
  minst én grense. Grunnpoeng bruker 60+ minutter; den eksisterende
  kvalifiserte BPS-kandidaten bruker mer enn 60. Deltakelse ved null minutter
  holdes også atskilt. Resultatene er per minuttkomponent, ikke hele scoringen.
- **Pasninger:** 120 spillerkamper har konflikt i forsøk eller fullførte
  pasninger. For **81** er BPS-båndet identisk for alle gyldige kombinasjoner
  av de registrerte verdiene. Dette gjelder 132 feltbehov. Forsøk under 30 og
  fullføringsgrenser på 70/80/90 prosent håndteres eksplisitt; ugyldige
  kombinasjoner med flere fullførte enn forsøkte pasninger brukes ikke.
- **Øvrige konflikter:** 962 felt i **793 unike spillerkamper** har konflikt
  utenom minutter. `other_stat_conflicts.csv.gz` viser alle kildeverdier og
  spenn i enkeltkomponentens grunnpoeng/BPS. CBI, taklinger og gjenvinninger
  vurderes også mot terskelen for defensive bidrag.

**Kildealternativer er ikke beviste grenser for den sanne verdien.** Derfor
er verken de 16 649 minuttkonfliktene eller de 132 pasningsfeltene fjernet
fra restlisten. Lik poengverdi for registrerte alternativer begrunner lavere
prioritet, ikke automatisk godkjenning. Spennene kan ikke summeres til et
gyldig totalpoeng- eller bonusintervall: komponentene kan være avhengige, og
andre tellere mangler fortsatt.

## Anbefalt arbeidsrekkefølge

Tier 0 er de lokale avklaringene over. De øvrige nivåene er en eksplisitt
arbeidsprioritering, ikke en estimert gevinst-/kostnadsmodell.

### 1. Fire måltilordninger med direkte poengbetydning

| Spiller | Kamp | Historisk FPL | FotMob/arkiv |
|---|---|---:|---:|
| Scott McTominay | Man Utd–Brighton, 10.11.2019 | 0 | 1 |
| Solly March | Leeds–Brighton, 11.03.2023 | 0 | 1 |
| Gabriel | Arsenal–Crystal Palace, 20.01.2024 | 1 | 2 |
| Yoane Wissa | Brentford–Ipswich, 26.10.2024 | 1 | 2 |

Hent offisiell dokumentasjon av måltilordning og eventuelle senere revisjoner.
Avklar hva som var original FPL-avgjørelse og hva som er senere
hendelsesstatistikk. Kontroller tilhørende selvmåls- og assisttilordninger før
en kildepolitikk for historisk omregning vedtas. Ingen kilde er valgt her.

### 2. Poenggrenseavvik og øvrige eksplisitte konflikter

Prioriter de 711 minuttobservasjonene som krysser poengbånd, samt øvrige
konflikter som ikke er nedprioritert gjennom pasningskontrollen. Sammen med
de fire måltilordningene gjelder denne køen **1 442 unike spillerkamper**;
overlapp mellom felter og tiltak er fjernet. Etterprøv rårespons, definisjon
og revisjonstidspunkt før verdier godkjennes.

### 3. Kildedefinisjoner, assists og avgrenset innhenting

To mulige nullgrenser er undersøkt, men **ingen er godkjent**:

| Kandidatregel | Eksplisitte sammenligninger | Moteksempler | Mulige nullfelt å undersøke |
|---|---:|---:|---:|
| Vunne taklinger ≤ totale taklinger | 32 344 | 0 | 28 522 |
| Store sjanser skapt ≤ sjanser skapt | 7 612 | 42 | 41 582 |

Den første er et konkret spor med stort dekningspotensial, men fravær av
moteksempler beviser ikke at definisjonen gjelder alle kildeversjoner og
sesonger. Den andre kan **ikke brukes som generell nullregel**: det finnes
allerede 42 moteksempler i de eksplisitte dataene. Undersøk definisjoner og
revisjoner fremfor å gjøre disse kandidatene til nye nuller.

For sjeldne tellerfelt kreves dokumentert utelatelsessemantikk for det
konkrete feltet/kilden/sesongen eller et komplett hendelsesinventar. To
samtidig utelatte felt er ikke validering. Dekningstallene i tiltakstabellene
er berørte populasjoner, **ikke forventet antall vellykkede avklaringer**.

Assists trenger fortsatt uttømmende mål-/kandidatvalg, verifiserte fakta og
støttede regelruter før kampene kan godkjennes. De tidligere
utviklingseksemplene brukes ikke som ny holdout. Innhenting avgrenses av de
eksisterende køene for 21 arkivløse kamper, tre ytterligere hendelsesløse
kamper og 38 keeperobservasjoner. Dokumenterte tidligere kildeforsøk skal
ikke gjentas uten nytt grunnlag.

### 4. Konflikter med samme registrerte poengbånd

Behold og dokumenter minutt-/pasningskonfliktene, men ta dem etter sakene
over. En feil i definisjon eller alle tilgjengelige kildeverdier kan fortsatt
endre konklusjonen. Globale BPS-/assistkvalifiseringer er heller ikke løst.

## Terskler og bonus

Den separate defensive terskelkontrollen gir samme nedre og øvre poengutfall for
76 739 observasjoner, inkludert keepere som ikke kan få defensive bidrag. **19 utespillerobservasjoner**
har et tilstrekkelig kjent subtotal selv om noen tellere mangler. Dette er
en kontroll under historisk FPL-posisjon og målreglenes terskler, **ikke 19
nye godkjente etiketter** eller en erstatning for det tidligere låste
defensive datasettet. Ved uavklart deltakelse godkjennes ikke terskelresultatet.

Ingen komplett BPS eller bonus produseres. De mange tellere uten dokumentert
øvre grense gjør at sammenligning av registrerte kildeverdier alene ikke kan
bevise slutt-BPS. Bonus krever et komplett, konsistent kamppopulasjonsgrunnlag
og tilstrekkelige BPS-grenser for alle relevante spillere. Sikre tellergrenser,
eventuelle sikre enkeltpoeng og full harmonisering må fortsatt skilles.

## Leveranser og reproduksjon

- `resolution_queue.csv.gz`: én rad per opprinnelig åpent felt, med navn,
  kamp, tiltak, prioritet, bevisomfang og separate flagg for ukjent råstatistikk
  og avklart poengavhengighet.
- `prioritized_player_matches.csv.gz`: deduplisert spillerkampkø.
- `action_summary.csv`, `action_field_summary.csv`: berørte felt,
  spillerkamper og kamper per tiltak. Tiltaksgrupper kan overlappe i
  spillerkampantall; ikke summer disse til en unik total.
- `action_catalog.json`: beviskrav og begrunnelse for prioriteringen.
- `documented_zero_supplement.csv`: de 272 nye dokumenterte nullene.
- `minute_conflicts.csv.gz`, `pass_conflicts.csv.gz`,
  `other_stat_conflicts.csv.gz`: etterprøvbare kandidat-/komponentkontroller.
- `subset_bound_screen.csv`, `subset_bound_evidence.csv.gz`: kandidatregler
  med avståelse, konkrete mulige nuller og moteksempler.
- `defensive_thresholds.csv.gz`: delvise tellinger og terskelgrenser.
- `acquisition_scope.csv`: overlappende kildeflagg, ikke ekstra restbehov.
- `findings.json`, `manifest.json`, `validation.json`: funn og fingeravtrykk.

Kjør offline med Python/pandas fra repositoryroten:

```sh
python research/current/scoring_2026_27/resolution_priority/build.py
python -m unittest discover -s research/current/scoring_2026_27/resolution_priority -p 'test_*.py'
```

Koden leser den frosne restlisten og offisielle kampscorer. Den verifiserer
restlistens resultatfingeravtrykk før bruk. Ingen nye nettverksdata eller
betalte kilder inngår. Kostnad: 0 NOK. Full harmonisering er fortsatt uferdig.

**15 nye tester, 13 eksisterende restlistetester og seks BPS-tester består**
(34 totalt i denne runden). To komplette kjøringer gir identiske fingeravtrykk
for alle 16 resultatfiler. Testene dekker blant annet ulike minuttgrenser,
pasningsgrenser, ukjente defensive tellere, delvise terskelbevis, posisjonsavhengig
straffemålsvekt, nulltillegget, kandidatavståelse og deduplisering. Hele
repositoryets testsuite og GitHub CI er ikke verifisert her.
