# Trinn B – verdi etter planhorisonten

Trinn B: ikke bestått. Benchmark beholdes.

| Sesong | A: kontroll | B: sluttverdi | Forskjell |
|---|---:|---:|---:|
| 2023-24 | 2457 | 2381 | -76 |
| 2024-25 | 2463 | 2414 | -49 |

Én låst variant. Samme prognoser, H3, to grener, forslag, videreføringspolicy og chipreserver. En standardisert Ridge (alpha 50) anslår diskontert verdi etter horisonten fra tropp, bank, gratisbytter og gjenværende chips. Sluttverdi ved GW38 er null. Bare tidligere avsluttede sesonger brukes ved trening.

Tidsordnet verdi-diagnose på 2023/24: MSE 2834.75, mot 6606.75 med bare sesongtid og 231705.35 med null sluttverdi. Dette er overlappende avkastninger fra én lærerbane, ikke uavhengige prøver eller dokumentasjon av kontrafaktisk verdi.

Alle 152 kontroll- og kandidatrunder er avregnet på nytt. Lovlige overganger, grenvalg, sluttverdier, prognosehash, treningsgrenser og løsergrenser er kontrollert. Treningens koeffisienter er gjenskapt med en separat lukket Ridge-beregning. Kontrollen fra A gjenbrukes; tre nye utfallsblinde prøver gjenskapte grenene eksakt.

Begrensninger: tidligere undersøkte utviklingsår, én lærerbane per treningsår (36 overlappende rader), læreren er benchmark og ikke rollout, og hypotetiske sluttlag kan avvike fra treningsfordelingen. Historiske priser og tilgjengelighet har eksisterende proxyer. Prognosene er uendret og to runder gamle ved terminaltidspunktet. Ingen automatisk oppgradering.

## Ressurser og beslutninger

2023-24: endret valg mot A på samme tilstand i 17 av 38 runder. Kandidat 812 løserkall / 123.5 sekunder; kontroll 784 / 128.1. Hits: 24 mot 20.
Chipbruk kandidat: {'wildcard': [5, 23], 'free_hit': [37], 'bench_boost': [7, 24], 'triple_captain': [9, 28]}. Kontroll: {'wildcard': [7, 23], 'free_hit': [29], 'bench_boost': [13, 24], 'triple_captain': [11, 25]}.
Ubrukte chips kandidat: {'1': ['free_hit'], '2': []}. Kontroll: {'1': ['free_hit'], '2': []}.

2024-25: endret valg mot A på samme tilstand i 7 av 38 runder. Kandidat 753 løserkall / 110.5 sekunder; kontroll 728 / 119.8. Hits: 12 mot 4.
Chipbruk kandidat: {'wildcard': [6, 21], 'free_hit': [33], 'bench_boost': [7, 20], 'triple_captain': [11, 24]}. Kontroll: {'wildcard': [6, 21], 'free_hit': [29], 'bench_boost': [7, 22], 'triple_captain': [9, 24]}.
Ubrukte chips kandidat: {'1': ['free_hit'], '2': []}. Kontroll: {'1': ['free_hit'], '2': []}.

Resultatet gjelder denne sluttverdimodellen. En negativ prøve er ikke en generell avvisning av planlegging med sluttverdi. Ingen nye prognoser eller endringer i den fryste GW7–38-pakken.

[Protokoll](protocol.json) · [Kontroll og fulle detaljer](audit.json) · [Runder](rounds.csv)
