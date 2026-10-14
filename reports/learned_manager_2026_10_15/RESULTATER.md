# Lært managerpolicy: kontrollert sammenligning

Lært TC/BB-reserve ga +47.0 netto poeng i snitt i de to lærte evalueringssesongene; begge sesonger positive. Pilotkravet bestått; behold benchmark inntil separat vurdering.

Prognosene er identiske. Bare verdien av å spare Triple Captain og Bench Boost er lært. Kandidaten styrer lovlige, hele sesongforløp gjennom den eksisterende planleggeren. Dette er en liten lært beslutningskomponent, ikke en full manager lært med reinforcement learning.

| Sesong | Rolle | Benchmark | Lært policy | Forskjell | Endrede rundebeslutninger |
|---|---|---:|---:|---:|---:|
| 2022-23 | Kontroll uten læring | 2429 | 2429 | +0 | 0 |
| 2023-24 | Lært evaluering | 2413 | 2466 | +53 | 37 |
| 2024-25 | Lært evaluering | 2344 | 2385 | +41 | 38 |

Primært snitt for 2023/24 og 2024/25: **+47.0 poeng per sesong**. Snitt over alle tre, inkludert kontrollen: +31.3. Poeng er etter overgangskostnader. Den kalde kontrollen inngår ikke som bevis for læring.

## Hva ble lært?

To små Ridge-modeller lærer diskontert chipbonus fra benchmarkens faktiske senere chipbruk i tidligere sesonger. Det velges ikke en optimal fremtidig runde med fasit. Modellen for 2023/24 bruker bare 2022/23; modellen for 2024/25 bruker 2022/23 og 2023/24. Modeller og skalering fryses før første frist.

| Evalueringssesong | Chip | Treningsrader | Ulike observerte chipbruk |
|---|---|---:|---:|
| 2022-23 | triple_captain | 0 | 0 |
| 2022-23 | bench_boost | 0 | 0 |
| 2023-24 | triple_captain | 11 | 2 |
| 2023-24 | bench_boost | 12 | 2 |
| 2024-25 | triple_captain | 22 | 4 |
| 2024-25 | bench_boost | 28 | 4 |

Flere treningsrader deler samme senere chiputfall. De er derfor ikke uavhengige treningseksempler. Datagrunnlaget er lite og følger én eksisterende managers atferd. Modellen lærer ikke en identifisert kontrafaktisk verdi av å vente og deretter velge andre lag.

## Hvilke valg ble endret?

| Sesong | Policy | Triple Captain, runder | Bench Boost, runder | Overgangskostnad |
|---|---|---|---|---:|
| 2022-23 | Benchmark | 10, 22 | 6, 27 | 32 |
| 2022-23 | Lært policy | 10, 22 | 6, 27 | 32 |
| 2023-24 | Benchmark | 10, 22 | 13, 24 | 36 |
| 2023-24 | Lært policy | 2, 20 | 1, 38 | 28 |
| 2024-25 | Benchmark | 9, 24 | 7, 22 | 8 |
| 2024-25 | Lært policy | 2, 20 | 1, 24 | 32 |

Sesongforskjellen inkluderer alle senere følger av endrede handlinger. Den kan ikke tilskrives chipbonus alene; tropp, kaptein og bytter kan også avvike etter første forskjell. [Rundetabellen](rounds.csv) og [chiploggen](chips.csv) viser forløpet.

## Ressurser og kontroller

Begge bruker samme datasett, 114 fryste prognosetidspunkter, lovlighetsmotor, startregler, planlegger og grenser: én tråd/arbeider, samme frø, 16 noder per løserkall og høyst 40 kall per beslutning. Ingen prognosemodell trenes på nytt. Begge har en tildelt grense på fem CPU-sekunder til policytilpasning per sesong. Lik ressursramme innebærer ikke lik faktisk bruk. Tilpasningstiden måler selve Ridge/skalering; uttrekk av treningsrader og verifisering av arkivfiler er forarbeid uten separat tidsmåling.

| Sesong | Løserkall benchmark / lært | Løsersekunder benchmark / lært | Tilpasning lært, CPU-s |
|---|---:|---:|---:|
| 2022-23 | 355 / 355 | 147.6 / 148.8 | 0.0000 |
| 2023-24 | 446 / 405 | 157.8 / 116.9 | 0.0031 |
| 2024-25 | 396 / 358 | 233.2 / 153.2 | 0.0010 |

Faktisk CPU og veggklokketid per sesong finnes i sesongkvitteringene. For benchmark 2022/23 gikk totalmålingen tapt ved en mekanisk oppsummeringsfeil. De 38 fullførte rundene ble bevart og validert uten nye løserkall. Per-kall-tid er bevart. Se [metodikk og retting](README.md).

Etterkontrollen består: 228 oppgjør og tilstandsoverganger er beregnet på nytt; alle 114 referanserunder gjenskaper arkivert benchmarkhandling og poeng; kontrollen uten læring er identisk; inputhash, uendrede prognoser, treningsdatoer, koeffisienter og løsergrenser er kontrollert. Ukjente valgte utfall ble ikke gjort om til nuller. Dette er en maskinell etterkontroll som gjenbruker den samme regelmotoren, ikke en ekstern validering av reglene.

## Tolkning og videre arbeid

Pilotkravet er bestått, men benchmark oppgraderes ikke automatisk. Neste vurdering bør undersøke om gevinsten tåler et bredere, tidsriktig treningsgrunnlag og en på forhånd fastlagt ny evaluering.

Bare to sesonger tester faktisk læring. Alle evalueringsårene er allerede studerte utviklingsdata. Ingen påstand om statistisk signifikans, generell overlegenhet eller vinnsannsynlighet følger av dette. 2025/26 er ikke brukt i dette forsøket. Det eksisterende best-effort-poengmålet og dets kvalitetsbegrensninger gjelder fortsatt.

## Sporbarhet

- [Fryst protokoll](protocol.json), [registrering](registration.json) og [etterkontroll](audit.json).
- [Sesongresultater og ressurser](results.csv), [rundepoeng](rounds.csv), [chipvalg](chips.csv), [treningsomfang](training_summary.csv).
- `training/`: treningsrader og koeffisienter. `runs/`: låste avgjørelser, oppgjør og kvitteringer.
- `failure.json` og `mechanical_resume_v002.*`: bevart feil og eksplisitt mekanisk retting. `complete.json`: faktisk fullføring.
