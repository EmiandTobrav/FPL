# 2025/26 omregnet til 2026/27 — kvalifisert delvis poengversjon

**363 hele kamper og 10 971 spillerkamper har kvalifisert BPS, ny helkampbonus
og totalpoeng etter 2026/27-reglene.** Bonus og totalpoeng endres for 435 rader.
Alle totaler er avstemt mot et separat grunnpoengregnskap, med null avvik.
Dette er en poengleveranse; tidsriktige features og treningsinnlesing gjenstår.

| Leveranse | Omfang |
|---|---:|
| Hele kanoniske spillerkampuniverset | 29 747 rader |
| Spillerkamper med minutter eller poenghendelser | 11 493 |
| Kvalifiserte hele kamper | 363 av 380 |
| Kvalifiserte poengetiketter | 10 971 |
| Sperrede hele kamper | 17 |
| Åpne numeriske krav i 2025/26 | 17 |
| Samlet historisk datarest, uendret i dette scoringtrinnet | 14 907 |
| Treningsklare rader med features og loader | 0 |

## Regel- og kildegrunnlag

[Offisielle endringer for 2026/27](https://www.premierleague.com/en/news/4679946/)
fjerner trekket for å bli taklet, endrer CBI fra ett BPS per to til ett per tre,
og erstatter keeperens redningsbidrag. Historisk FPL-BPS bærer alle uendrede
komponenter. For keeperen brukes nye `2*saves + inside + big_chance_saves +
7*penalties_saved`, og gamle `3*inside + 2*outside + 8*penalties_saved` trekkes ut.
[2025/26-reglene](https://www.premierleague.com/en/news/4362127/whats-new-in-202526-fantasy-changes-to-bonus-points-system)
bekrefter den gamle vektingen. FPLs native antall redninger brukes; summen av
lokasjonstellerne antas ikke lik dette antallet.

Grunnpoeng, assistdefinisjon og defensive awards er uendret mellom disse to
sesongene. Native 2025/26-CBI, assists, BPS, redninger, strafferedninger og
defensive tellinger avstemmes mot kanoniske FPL-verdier før beregning. Allerede
tildelte defensive poeng legges ikke til på nytt. Netto-taklingsklipping for
eldre sesonger gjelder ikke her; alle mislykkede eldre kontroller bevares.

Kildekvalifiseringen gjenbruker fryste kontroller: 68 eksplisitte times-tackled-
avstemminger, 543 komplette skuddinventarer for inside-box, 40 outside-box-
kontrollkeepere og 52 eksplisitte 2026/27-big-chance-save-verdier. Alle stemmer.
Kontrollene har delt Opta-opphav og er ikke en uavhengig leverandørholdout.
Resultatfilene og inngangene er låst med SHA-256. Gamle gater er ikke senket.

## Ny kilderevisjon — isolert og sperret

Offisiell Kelleher-sesongtotal er 27 storsjanseredninger; den godkjente
rekonstruksjonen summerer til 26. Ny primærinnhenting av alle 37 spilte kamper
og én sesongrespons lokaliserer forskjellen: kamp 337 har nå eksplisitt 1,
mens godkjent arkiv har 0. De andre 36 kampene stemmer. Primærsvarenes
eksplisitte tellinger summerer til sesongtotalen 27, og dermed kan utelatte
tellinger i akkurat dette komplette spillerinventaret bevises som nuller.
Utvalg og identitet avstemmes med FPL-minutter og kamp-/Pulse-ID.

Tidligere godkjente keeperverdier og rå FPL er bevart. Kamp 337 får ingen ny
poengetikett; den var allerede sperret av motstanderkeeperens lokasjonsteller.
Dokus dokumenterte times-tackled-konflikt i kamp 356 er også sperret.
De øvrige åpne lokasjonskravene har inkompatible redningsinventarer. Ashley
Barnes' null-minutt-kort i kamp 215 inngår i full poengrelevant deltakerliste;
kampen sperres fordi denne observasjonen mangler i gammel ledger.

## Filer og reproduksjon

- `results/qualified_player_matches.csv.xz`: kvalifiserte deltakere, originale
  FPL-verdier, harmoniserte poeng/BPS/bonus/assists, times-tackled, keeperens
  inside-/outside-/big-chance-saves med kildebelegg og eksplisitt labelstatus.
- `results/player_matches.csv.xz`: alle 29 747 kanoniske rader. Harmoniserte
  felter for sperrede kamper og ikke-poengrelevante null-minutt-rader er tomme.
- `results/fixture_status.csv`: samtlige 380 kamper og deres sperrer.
- `results/changed_bps_components.csv.xz`, `results/basic_components.csv.xz`:
  komponentregnskap, herunder native defcon og residual.
- `results/*controls.csv`, `results/keeper_primary_comparisons.csv`:
  kontrollavstemminger og bevart gammel verdi mot fersk primærkilde.
- `results/qualification.json`, `results/summary.json`, `results/manifest.json`:
  avgrensning, dekning, kvalifisering, kilder og fingeravtrykk.
- `input_lock.json`, `inputs/ledger_CURRENT.json`, `inputs/primary/`:
  separat låst ledger og 38 rå primærsvar med URL-/fil-/innholdsfingeravtrykk.

Fra repositoryroten, med Python 3.12 og pandas 2.2.3:

```sh
python research/current/training_dataset/scoring/season_2025/reproduce.py
python -m unittest discover -s research/current/training_dataset/scoring/season_2025 -p 'test_*.py' -v
python research/current/training_dataset/reproduce.py
```

Separat offline-replay gjenskaper 12 resultatfiler byteidentisk. Ni tester
kontrollerer blant annet manglende inventarer, ubegrunnede nuller, hele
kampsperrer, null-minutt-kort, uavhengig bonusrangering og defcon-regnskap.
Den gamle historiske beregningen bruker sitt opprinnelige snapshot under
samlet replay; denne nye versjonen bruker sin egen arkiverte ledgerpeker.

Ingen modeller trenes eller endres. Spiller–runde-totaler, ikke-deltakelses-
labels, fristsikre features, eldre sesonglabels og aktiv treningsloader gjenstår.
