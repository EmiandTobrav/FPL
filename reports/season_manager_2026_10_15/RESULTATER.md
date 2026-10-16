# Lært manager gjennom hele sesongen

Episodisk manager ga -243.0 netto poeng mot benchmark, -290.0 mot chip-policyen og -297.5 mot samme forslag uten læring i sesongsnitt. Pilotkravet ikke bestått; dagens benchmark beholdes.

Policyen velger en komplett handling runde for runde. Bytter, å spare gratisbytter, tropp, startellever, benkerekkefølge, kaptein/visekaptein og Wildcard, Free Hit, Bench Boost og Triple Captain inngår i valgene. Valgene er avgrenset til lovlige forslag fra den eksisterende planleggeren og faste alternativer. Dette dekker beslutningstypene, ikke alle mulige kombinasjoner av spillere og handlinger.

| Sesong | Benchmark | Første lærte chip-policy | Samme forslag uten læring | Episodisk lært manager |
|---|---:|---:|---:|---:|
| 2023-24 | 2413 | 2466 | 2391 | 1838 |
| 2024-25 | 2344 | 2385 | 2475 | 2433 |

| Sesong | Mot benchmark | Mot chip-policy | Læringens tillegg mot samme forslag |
|---|---:|---:|---:|
| 2023-24 | -575 | -628 | -553 |
| 2024-25 | +89 | +48 | -42 |

Alle poeng er etter overgangskostnader. Siste kolonne isolerer effekten av den lærte rangeringen innenfor de samme forslagsreglene. Selve forslagene kan avvike når managernes egne lag har utviklet seg forskjellig.

## Slik foregår læringen

En enkel verdi-/handlingsmodell lærer fra hele historiske sesongforløp. Hver treningsrad får faktisk poengsum fra den valgte runden til og med GW38 som mål, fratrukket en felles kortsiktig forventningsverdi. Dermed kan et valg belønnes eller straffes gjennom senere følger for tropp, bank, gratisbytter og chips. Den lærte justeringen legges til den samme kortsiktige verdien ved valg av handling.

Modellen er StandardScaler og Ridge med alpha 50. Den får 40 før-frist-felt om handlingen, laget, bank, bytter, chipbeholdning, gjenværende tid, uendrede poengprognoser og noen eksisterende historikkfelt for spilletid. Ingen spiller-ID brukes som feature. Ingen prognosemodell trenes på nytt.

For 2023/24 brukes eksisterende 2022/23-forløp og to nye treningsforløp gjennom 2022/23. For 2024/25 gjenbrukes disse og suppleres med to eksisterende 2023/24-forløp og to nye treningsforløp gjennom 2023/24. De nye treningsforløpene prøver alternative lovlige handlinger med fast utforskingsandel 30 og 15 prosent. Modellen oppdateres etter et helt forløp og fryses før hvert evalueringsår. Alle treningsmål må være tilgjengelige før første frist i evalueringsåret.

Dette er avgrenset episodisk Monte Carlo-læring fra historisk simulator, med en enkel modell for rangering. Gjentatte forløp gjennom samme fotballsesong er korrelerte og gir ikke nye uavhengige sesonger. Modellen optimaliserer netto poeng; et konkurrentfelt og vinnsannsynlighet er ikke modellert.

## Sammenligning og ressurser

Prognoser, poengmål, før-frist-data, startregler og regelmotor er felles. Benchmark og første chip-policy gjenbrukes fra det foregående fullførte og kontrollerte forsøket med nøyaktig samme input og grenser; deres løserarbeid gjentas ikke. Kontrollen uten læring og den episodiske policyen kjøres på nytt for begge år. Begge nye policyer har samme forslagssystem, én tråd og grenser på 16 noder per kall og 40 kall per beslutning.

Læring krever ekstra arbeid: fire nye komplette treningsforløp, 152 treningsbeslutninger og seks små modelltilpasninger. I tillegg er det fire evalueringsforløp med 152 beslutninger. Samlet er 304 nye runder kjørt. Tildelt treningsramme er felles, men faktisk arbeid er ikke identisk med en kontroll som ikke trener. Tilpasningstiden måler modelltilpasning; forarbeid/uttrekk av lærerdata har ikke separat CPU-måling. Detaljer per forløp finnes i [ressurstabellen](resources.csv).

## Kontroller og konklusjon

Etterkontrollen beregner alle 304 oppgjør på nytt fra fryste utfall, validerer samtlige lagrede forslag og tilstandsoverganger, kontrollerer alle tilgjengelige chipfamilier, gjenskaper utvalg og utforsking, sesonglange treningsmål, seks modelltilpasninger, frister, prognosehash og løsergrenser. Avgjørelser og hele forslagssettet er lagret før rundens utfall leses. Ukjente valgte utfall blir ikke nuller. Kontrollen bruker den eksisterende regelmotoren; den er ikke en ekstern kvalifisering av FPL-regler eller dataproxyer.

Denne kandidatversjonen oppfyller ikke oppgraderingskravet. Behold det dokumenterte utfallet og unngå å gjenta samme variant eller bruke evalueringsresultatene til ubundet parameterjakt.

Begge evalueringsår er tidligere studerte utviklingsdata. To år og et lite antall fotballsesonger gir begrenset bevis for generalisering. 2025/26 er ikke brukt. Best-effort-poengmål, estimater og historiske tilgjengelighetsproxyer følger det uendrede datasettet.

- [Fryst protokoll](protocol.json), [konfigurasjon](config.json), [registrering](registration.json), [etterkontroll](audit.json).
- [Resultater](results.csv), [rundebeslutninger](rounds.csv), [alle chips](chips.csv), [ressurser](resources.csv).
- `models/` og `training/`: fryste evalueringsmodeller, treningsrader og tilpasninger. `episodes/`: alle låste forslag og oppgjør.
