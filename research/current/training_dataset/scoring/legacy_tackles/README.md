# Gammel netto-taklingsregel: ny primærkontroll, ikke kvalifisert

Kontrollert 8. oktober 2026 på `codex/training-dataset-2026-27`.
291 faste spillerkamper fra alle seks sesonger 2019/20–2024/25 har nå egne
hashkontrollerte Premier League-svar. Utvalg og primærkontroller ble laget
før den numeriske avlesningen av publisert historisk FPL-BPS. Dette er en
retrospektiv komponentkontroll, ikke en urørt holdout. Ingen datarest lukkes,
ingen gamle tellerverdier overskrives og ingen treningslabels godkjennes.

## Utfall

| Sesong | Planlagte | Primæravstemte beregninger | Over signert beregning | Over klippet beregning | Mellom beregningene |
|---|---:|---:|---:|---:|---:|
| 2019/20 | 52 | 46 | 27 | 1 | 26 |
| 2020/21 | 53 | 48 | 39 | 1 | 38 |
| 2021/22 | 51 | 45 | 37 | 5 | 32 |
| 2022/23 | 49 | 46 | 37 | 3 | 34 |
| 2023/24 | 66 | 61 | 49 | 4 | 45 |
| 2024/25 | 20 | 18 | 11 | 1 | 10 |
| **Sum** | **291** | **264** | **200** | **15** | **185** |

**Den foreslåtte øvre-grensekontrollen består ikke.** 185 rader skiller de to
beregningene, men 15 publiserte BPS-verdier overskrider også den klippede
beregningen. Dette gjør samsvaret mellom historisk BPS, komponentdefinisjoner,
avrunding og kilderevisjoner til en konkret ny avklaringsoppgave. Kontrollene
beviser verken korrekt klipping for hele historikken eller en full BPS-formel.
De må ikke omtales som endelig forkastelse av en regelhypotese når andre
forutsetninger i kontrollen fortsatt motsies av fasit.

Fire eksplisitte kildeavvik gjelder to spillerkamper:

- 2019/20, fixture 104, code 66242: `won_contest` 3 mot 4 og `total_pass` 68 mot 69.
- 2023/24, fixture 276, code 232413: `ball_recovery` 5 mot 6 og `total_pass` 43 mot 42.

25 andre kontroller mangler tilstrekkelig primærbelegg for CBI. Disse 27 radene
ble holdt utenfor BPS-beregningene før fasit ble lest, men bevares i planen og
`source_eligibility.csv`. Ingen kontroll ble fjernet etter BPS-utfallet.

De opprinnelige tallgatene er uendret: minst 20 skillende rader og minst to i
hver av seks sesonger, ingen overskridelser av klippet grense og ingen
primære kildeavvik. De to siste gatene feiler. `validation_summary.json`
setter `legacy_clipping_qualified=false` og `training_labels_enabled=false`.
Signerte råtellere og begge gamle omregningskandidater beholdes.

## Bevis og begrensninger

`raw_inputs.tar.gz` inneholder alle 291 primærsvar. `source_manifest.json`
bevarer URL, bytehash, omfang og opprinnelig innsamlingsplan per svar.
2024/25-lagtotal for mållinjeklareringer er hentet separat og lagret med
kildehash; den har 19 eksplisitte lagrader. Et utelatt lag antas aldri å ha null.

3 983 feltkontroller sammenligner tilgjengelige positive komponenter og kjente
negative komponenter. 761 nullsertifikater gjelder konkrete kontrollkomponenter:
741 eksakte lag-/kampsummer og 20 eksakte 2024/25-lag-/sesongsummer. De er
belegg innen denne kontrollen, ikke 761 nye ledgerkrav eller en global
kvalifisering av de eksterne statistikkene. Sesong, kamp og klubbidentitet
kontrolleres også for hele kildepopulasjonen som brukes i sumbevisene.
Manglende total, positiv rest, overrun eller ugyldig teller gir ingen null.

Beregningen inkluderer alle deklarerte positive BPS-komponenter og bruker
maksimalt minuttbidrag og maksimalt vinnermålbidrag. Ukjente negative tellere
bevares som ukjente; de trekkes ikke fra bare ved beregning av en foreslått
øvre grense. Dette er ikke observert null og er ikke en rekonstruert fasit.
De 15 moteksemplene viser at den samlede historiske beregnings-/kilde-
forutsetningen trenger mer kvalifisering. Uendrede FPL-BPS-komponenter skal
fortsatt beholdes i den endelige deltaomregningen.

Premier League og arkivet deler Opta-opphav. Primæravstemming er derfor ikke
uavhengig leverandørvalidering eller bevis for uendret historisk kildeversjon.
`rule_corroboration.json` dokumenterer bare en datert tredjepartskopi av
2024/25-regelteksten om fravær av negativt taklingsbidrag. Den er ikke en
autentisert offisiell arkivrespons og kan ikke alene kvalifisere regelen.

`initial_plan/`, `direct_primary_plan/` og `preflight_v3/` bevarer tidligere
oppsett. Alle revisjoner skjedde før numerisk FPL-BPS-avlesning: feil tidlig
2024-feltvalg, tillegg av eksisterende konservasjonsbevis og til slutt streng
avvisning av ugyldige tellere med full kildeidentitetskontroll. Siste V4 har
samme 291 rader som innsamlingen og uendrede akseptgrenser. Den opprinnelige
innsamlingsmanifesten er fortsatt bundet til `direct_primary_plan/freeze.json`.

## Reproduksjon og neste arbeid

Fra repositoryroten, Python 3.12 / pandas 2.2.3:

```sh
python research/current/training_dataset/scoring/legacy_tackles/prepare.py
python research/current/training_dataset/scoring/legacy_tackles/primary_predict.py
python research/current/training_dataset/scoring/legacy_tackles/validate.py
python -m unittest discover -s research/current/training_dataset/scoring/legacy_tackles -p 'test_*.py' -v
python research/current/training_dataset/reproduce.py
```

Dette bruker fryste lokale innganger uten nettverk. Innlesning av BPS nekter
endrede innganger, primærsvar, kildemanifest, kode, plan og fryste beregninger.
17 nye tester dekker manglende/ugyldige tellere, grenser, konservasjon,
kildeidentitet og kvalifiseringsgatene. Hele leveransens offline-replay skal
gjenskape 94 filer, inklusive de 12 nye kontrollutgangene.

Undersøk de 15 konkrete radene i `bps_bound_checks.csv` med
`clipped_bound_violated=true` og de fire radene i `primary_disagreements.csv`.
Skill dokumentert kildeversjon, komponentdefinisjon og avrunding fra en
antatt taklingsregel. Nye hypoteser må få ny erklært protokoll og egnet nytt
kontrollbelegg; samme 291 utfall kan brukes til feilsøking/regresjon, men ikke
markedsføres som urørt fasit. Ikke kjør innsamlingen eller samme kontroll på
nytt uten nytt grunnlag. De øvrige globale regelgatene, 16 227 feltkrav,
historiske treningslabels, friststyrte features og aktiv innlesing gjenstår.
