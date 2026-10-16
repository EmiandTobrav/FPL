# Parvis sluttverdi – forskjell mellom handlinger fra samme tilstand

Parvis sluttverdi: ikke bestått. Benchmark beholdes.

| Sesong | A: kontroll | B2: parvis sluttverdi | Forskjell |
|---|---:|---:|---:|
| 2023-24 | 2457 | 2476 | +19 |
| 2024-25 | 2463 | 2374 | -89 |

Én låst variant. Samme prognoser, H3, to grener, forslag, videreføringspolicy og chipreserver. En Ridge uten konstantledd (alpha 50) lærer forskjellen i diskontert avkastning etter horisonten mellom to handlinger fra samme tilstand. Egenskapene er forskjeller i tropp, bank, gratisbytter og chips. Samme sluttverdiegenskaper som B1; RMS-skalering uten sentrering sikrer antisymmetri. Sluttverdi ved GW38 er null. Bare tidligere avsluttede sesonger brukes ved trening.

Tidsordnet par-diagnose på 2023/24: MSE 333.416, mot 363.593 ved alltid å anslå null forskjell. Riktig fortegn i 81.8% av 11 par med ikke-null faktisk forskjell. Tolv forhåndsvalgte par; overlappende videreføringer. Ingen tuning.

Alle 152 kontroll- og kandidatrunder er avregnet på nytt. Lovlige overganger, grenvalg, sluttverdier, prognosehash, treningsgrenser og løsergrenser er kontrollert. Treningens koeffisienter er gjenskapt med en separat lukket Ridge-beregning. Kontrollen fra A gjenbrukes; tre nye utfallsblinde prøver gjenskapte grenene eksakt.

Begrensninger: tidligere undersøkte utviklingsår, tolv forhåndsvalgte benchmark-starttilstander per treningsår, to H3-grener per tilstand og overlappende videreføringer. Begge grener fortsetter med samme uendrede forslagspolicy uten sluttverdilæring. Fremtidige arkivprognoser leses bare ved egne historiske frister under trening. Sluttlagene ved H3 bruker frosne priser som i A. Hypotetiske fotballutfall påvirkes ikke av fantasy-handlinger. Begrenset tilstandsdekning og forskjell mellom videreføringspolicy og endelig manager begrenser overføringen. Historiske priser og tilgjengelighet har eksisterende proxyer. Prognosene er uendret og to runder gamle ved terminaltidspunktet. Ingen automatisk oppgradering.

## Ressurser og beslutninger

Teknisk v2: første forsøk stoppet ved17 rapporterte noder mot grense16 etter81 treningsrunder, før modellfit/evaluering. V2 har grense64 bare for treningsvidereføring; root og evaluering beholder16. Ingen prognose eller læringsregel endret. De81 gamle treningsrundene gjenbrukes ikke og kommer i tillegg til v2-arbeidet.

Treningskontroll: 884 videreførte og etterkontrollerte treningsrunder; 24 par. To parvise modellfit, null prognosefit.

2023-24: endret valg mot A på samme tilstand i 3 av 38 runder. Kandidat 772 løserkall / 113.1 sekunder; kontroll 784 / 128.1. Hits: 16 mot 20.
Chipbruk kandidat: {'wildcard': [6, 23], 'free_hit': [29], 'bench_boost': [7, 24], 'triple_captain': [12, 25]}. Kontroll: {'wildcard': [7, 23], 'free_hit': [29], 'bench_boost': [13, 24], 'triple_captain': [11, 25]}.
Ubrukte chips kandidat: {'1': ['free_hit'], '2': []}. Kontroll: {'1': ['free_hit'], '2': []}.

2024-25: endret valg mot A på samme tilstand i 3 av 38 runder. Kandidat 754 løserkall / 108.7 sekunder; kontroll 728 / 119.8. Hits: 12 mot 4.
Chipbruk kandidat: {'wildcard': [6, 21], 'free_hit': [33], 'bench_boost': [7, 22], 'triple_captain': [9, 24]}. Kontroll: {'wildcard': [6, 21], 'free_hit': [29], 'bench_boost': [7, 22], 'triple_captain': [9, 24]}.
Ubrukte chips kandidat: {'1': ['free_hit'], '2': []}. Kontroll: {'1': ['free_hit'], '2': []}.

Resultatet gjelder denne sluttverdimodellen. En negativ prøve er ikke en generell avvisning av planlegging med sluttverdi. Ingen nye prognoser eller endringer i den fryste GW7–38-pakken.

[Protokoll](protocol.json) · [Kontroll og fulle detaljer](audit.json) · [Runder](rounds.csv)
