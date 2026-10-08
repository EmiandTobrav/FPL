# Felles tabeller og innlesing — fortsatt ikke treningsklart

**187 111 spillerkamper og 181 604 spiller–runde-rader** dekker alle åtte
sesonger 2019/20–2026/27. Original FPL bevares, kvalifiserte omregnede verdier
ligger i egne felter, og uklare poengetiketter forblir tomme.

| Område | Omfang |
|---|---:|
| Kvalifiserte spillerkamp-poeng | 12 509: 10 971 fra 2025/26 og 1 538 native 2026/27 |
| Kvalifiserte spiller–runde-poeng | 14 023 |
| Kvalifiserte hele kamper | 363 historiske og 50 native |
| Historiske spiller–runde-rader med flere kamper | 7 146 |
| Native rader med eksplisitt ikke-deltakelse | 1 678 |
| Neste-runde-target med kvalifisert poengsum | 12 905 |
| Neste tre runder, komplett kvalifisert sum | 7 884 |
| Neste seks runder, komplett kvalifisert sum | 3 945 |
| Treningsklare rader med tidsriktige features | 0 |

## Tabeller og definisjoner

- `results/player_matches.csv.xz`: hele kampuniverset med originaler, egne
  target-poeng, historisk posisjon, stabile spiller-/klubbkoder, kildehenvisninger
  og kvalitetsstatus. Kvalifiserte starter og 2022/23-xG/xA/xGI/xGC er slått inn
  med bevarte originaler. Klubb kobles fra faktisk kamp, også ved klubbskifte.
- `results/player_rounds.csv.xz`: summer fra observerte historiske rader og
  native 2026/27-rundeutfall. Dobbeltrunder får ingen delsum som target: alle
  nødvendige spillerkampverdier må være kvalifisert. Kalenderens endelige
  rundeplassering er outcome-metadata, ikke modellens fremtidige kalender.
- `results/next_round_targets.csv.xz`: H1 er runde `r+1` etter en fullført
  ankerrunde, H3 er `r+1..r+3`, H6 er `r+1..r+6`. Horisonter krysser ikke
  sesonggrenser. Ukjente runder gjøres ikke til blanke nullrunder.
- `results/input_counters.csv.xz`: alle 775 248 krav med status og proveniens.
  De 14 907 åpne verdiene er tomme, selv om en sekundær råkolonne har et tall.
  Scoringkvalifisering gjelder allerede kvalifiserte 2025/26-deltakere.
- `results/statistic_coverage.csv`, `results/summary.json`, `results/manifest.json`:
  dekning, gjenværende gater og SHA-256 for kode, innganger og resultater.

2026/27s live-rundeoversikt gir eksplisitte ikke-deltakelsesutfall. Disse er
kvalifiserte utfall, men innhentet live-univers dokumenterer ikke hvem som var
kjøpbar før tidligere frister. Roster-/før-frist-flagg er fortsatt falske.
Historiske inaktive rader får ikke omregnede poeng uten egen kvalifisering.

## Faktisk innlesing og reproduksjon

[ACTIVE.json](../ACTIVE.json) velger `fpl_2026_27_canonical_v1_partial`.
[pipeline.py](../pipeline.py) leser tabellene fra denne konfigurasjonen og
kontrollerer poeng-/dataversjon, fingeravtrykk, identiteter og tomme uavklarte
targets. Ingen gamle FPL-poeng erstatter manglende target-poeng. Benchmarkens
gamle innlesing og modeller er bevart; ingen modelltrening utføres.

```sh
python research/current/training_dataset/pipeline.py --inspect
python research/current/training_dataset/reproduce.py
python -m unittest discover -s research/current/training_dataset/canonical -p 'test_*.py' -v
```

Inspeksjonen leser alle åtte sesonger med `training_ready=false`. Uten
`--inspect` stanser innlesingen med `DatasetNotReady`/exit 2, fordi features
før frist og ferdig datakvalifisering mangler. Samlet replay dekker 113
resultatfiler. Ni nye tester dekker delvis dobbeltrunde, manglende runde,
sesong-/spillergrenser, feil poengversjon og bevarte nuller/datakonflikter.

## Gjenstående arbeid

Historiske ikke-deltakelses-/blankrundelabels må kvalifiseres med null-minutt-
kort bevart. Faktiske frister, før-frist-rosters og statistikkversjoner må
skaffes før features bygges og trening åpnes. Benchmarkens `kickoff+3h`-
tilgjengelighet og `kickoff-36h`-frist er proxyer; de godkjenner ingen features
her. Hele den eldre felt-/regelkvalifiseringen fortsetter. Null-/lavpoengutfall
alene skal ikke bli en skjev eldre treningskohort.
