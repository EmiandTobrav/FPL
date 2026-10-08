# Aktiv kanonisk dataversjon v3 – fortsatt delvis

`ACTIVE.json` peker til denne versjonen. Den bevarer hele v1-inventaret:
**187 111 spillerkamper og 181 604 spiller–runde-rader** fra 2019/20–2026/27.
374 historiske kamper og 50 native 2026/27-kamper har kvalifiserte poeng.
Det gir **12 853 kvalifiserte kampetiketter og 14 365 rundepoeng**.
Kamp 365 er ny karantene etter et ferskt BCS-avvik. Alle fortsatt kvalifiserte
poeng er identiske; originalverdier og den publiserte v1 bevares.

| Fil i results/ | Innhold |
|---|---|
| player_matches.csv.xz | Originale og omregnede verdier, identiteter, faktisk historisk klubb/posisjon og kvalitetsstatus |
| player_rounds.csv.xz | Streng helrundeaggregering; ukvalifiserte delkamper gir ukjent target |
| next_round_targets.csv.xz | 13 203 H1-, 8 387 H3- og 4 522 H6-targets med komplett kvalifisert sum |
| input_counters.csv.xz | Hele 775 248-felts ledgeren; 14 893 åpne krav er maskert som ukjente |
| statistic_coverage.csv | Dekning per felt/sesong; kilde-/featurekvalifisering er adskilt |
| manifest.json og summary.json | Versjon, SHA-256, tellinger og uavklarte gater |

Horisontene er de neste rundene etter ankerrunden. Ukjente runder blir ikke
blanke nuller. Native 1 678 eksplisitte ikke-deltakelsesrader bevares; det hevdes
ikke at disse spillerne var i universet før hver historiske frist. Inaktive
historiske observasjoner og seks sperrede 2025/26-kamper har ukjente targets.

**Treningsklare rader: 0.** Historiske ikke-deltakelses-/blankrundelabels,
faktiske frister, før-frist-spilleruniverser og kvalifiserte statistikkversjoner
for modellinput gjenstår. Eldre sesongers poenggater står også åpne. Verken
tidsstempel for innhenting av en senere sesongfasit eller kampstart pluss tre
timer brukes som bevis for historisk informasjonstilgjengelighet.

Fra repositoryroten:

```sh
python research/current/training_dataset/pipeline.py --inspect
python research/current/training_dataset/canonical_extension/reproduce.py
python research/current/training_dataset/reproduce.py
```

Innlesingen leser faktisk alle åtte sesonger og denne poengversjonen.
Standardinnlesing for trening sperres inntil features og treningsrader er
kvalifisert; originalpoeng er ingen fallback. Bevarte modeller og benchmark
bruker fortsatt sine frosne versjoner. Ingen modeller er trent.
