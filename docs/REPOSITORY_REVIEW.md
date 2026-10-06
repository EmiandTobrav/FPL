# Gjennomgang av mai-repositoryet, 6. oktober 2026

Utgangspunkt: `EmiandTobrav/FPL`, commit `568075f40905fdc42234c401b8918cc0c9e632fc` (14. mai 2026). Gjennomgått kode, modell-/ensemble-/variabelrapporter, databygging, ukentlige prognoser og testpakken.

## Beslutning

Behold eldre kildekode og rapporter som forskningsgrunnlag. La `research/current` være inngangen til videre start-/hovedmodellarbeid. Det gamle prosjektet er nyttig, men resultatene gir ikke grunnlag for å erstatte sesongreferansen. Git-historikken beholdes uten omskriving.

| Del | Vurdering | Videre bruk |
|---|---|---|
| FPL API-henting, normalisering og prediksjonsrader | Nyttig infrastruktur med egne tester | Behold `src/data`; bruk som utgangspunkt for tidsstemplede før-frist-snapshots |
| Lagform og Elo | Har egne angreps- og forsvarsmål, ikke bare samlet styrke | Behold; test isolerte angrep/forsvar-ablasjoner i dagens simulator |
| Residual-CatBoost / XGBoost | Lovende gamle RMSE-resultater; ikke FPL-sluttscore | Behold implementasjon og rapporter. Residualideen er nå prøvd med HGB i dagens featureformat |
| Enkle og lærte ensemblevekter | Nyttig eksperimentkode; vektene lærer fra eldre sesonger | Behold som kandidat. Sammenlign senere med faste vekter på samme sesongprotokoll |
| Minuttjustert gjennomsnitt | Lav MAE, men skalerer allerede observerte poeng med minutter igjen | Behandle som shrinkage-baseline, ikke som kalibrert minuttmodell |
| Tostegs minutter/poeng | Gammel rapport viser ingen MAE-forbedring | Lavere prioritet; ingen automatisk overgang |
| Aktiv-spillerfilter | Reduserer mange nullrader, men overser noen reelle poenggivere | Bruk til diagnostikk, ikke ukritisk som hardt kjøpsfilter |
| Gamle Parquet-innganger | Git LFS-pekerfiler i Git-treet | Aktiv forskning leveres med egne kontrollerte data og trenger ikke disse |

## Metodeproblemer som begrenser gamle modellrangeringer

1. **Horisonten er ikke konsistent med dagens oppgave.** `rolling_features.py` bygger historikk til og med t−1 på rad t. `target_builder.py` setter målet til rad t+1. Dagens modell bruker historikk før rundens frist til å predikere den aktuelle runden. Gamle ukentlige prognoser beregnes på kommende rader, som heller ikke matcher treningsmålets ekstra forskyvning.
2. **Neste observerte rad er ikke nødvendigvis neste GW.** `groupby(...).shift(-1)` i målbyggeren hopper over manglende runder. Tre-rundersmålet summerer de neste tre observerte radene. Dette må erstattes med eksplisitt GW-indeksering før gjenbruk av denne treningspipelinen. Manglende rader må ikke automatisk tolkes som null uten å skille blanke runder fra manglende data.
3. **Kampkontekst og mål må peke på samme kamp.** Gamle `was_home`/motstanderfeatures beskriver rad t mens målet er t+1. Dette er først og fremst feiltilpasning av horisont, ikke i seg selv bevis for fremtidslekkasje.
4. **Runderekkefølge er ikke alltid tilgjengelighetstid.** Lagget etter GW-nummer beviser ikke før-frist-tilgjengelighet ved omberammede kamper. Dagens pipeline bruker kampens tilgjengelighetstid og én felles cutoff for dobbeltrunden, men har fortsatt dokumentert kalenderproxy.
5. **Gamle top-k-tall er over sesongens rader.** `evaluate_predictions` sender en hel sesong til top-k-funksjonene uten GW-gruppering. De måler ikke ukentlige lagvalg eller nettosesongpoeng.
6. **Gamle rapporter tilhører ulike kjøringer.** Eksempelvis endres også baseline-MAE i lagformrapporten. Den tabellen alene isolerer derfor ikke verdien av nye lagfeatures på et uendret testutvalg. Noen oppsummeringer inneholder dessuten residualmodeller som ikke står i den innledende modellisten.

Disse funnene tilsier nye sammenligninger på felles tidsgrenser, spillerpool, starttilstand, chips og poengregler. De innebærer ikke at hver eldre rapport er ugyldig. Koden beholdes, men gamle rangeringer brukes som hypoteser.

## Ny, faktisk kjørt residualtest

`research/current/test_legacy_candidates.py` sammenligner en minutt-shrinkage-baseline, direkte HGB og residual-HGB over seks sesonger (2020/21–2025/26), GW5–38. Hver modell trenes kun på eldre sesonger tilgjengelige før åpningstidspunktet. Direkte og residual HGB bruker samme grunnfeatures og hyperparametere. Residualvarianten predikerer korreksjonen til lagget seks-observasjons gjennomsnitt × lagget minuttandel. Dette er en tilpasning av ideen, ikke reproduksjon av den gamle fem-GW-CatBoost-modellen.

Se [alle måltall](../research/current/results/legacy_review/prediction_probe.csv) og [protokoll](../research/current/results/legacy_review/protocol.json). Residual-HGB forbedret RMSE i bare én av seks sesonger. Det gir ikke grunnlag for å prioritere akkurat denne varianten over direkte HGB. CatBoost/XGBoost er ikke trent på nytt i denne gjennomgangen.

Testen gjelder prediksjonsfeil på observerte spiller-kamprader, ikke komplett tilgjengelig spillerpool eller nye lag-/byttevalg. Den dokumenterer derfor ingen ny gevinst i FPL-sluttscore. Alle sesongene var allerede undersøkt.

## Verifikasjon

Det eldre prosjektets første testkjøring: 152 bestått, én feil fordi tomme arbeidsmapper ikke finnes i Git. `scripts/prepare_data.py` oppretter disse. Nye tester kontrollerer residualens treningsmål/tilbakelegging, uavhengighet av aktuell fasit og poengregnskap/felles overlevering i alle 120 lagrede sesongforløp. Se STATUS for endelig teststatus.
