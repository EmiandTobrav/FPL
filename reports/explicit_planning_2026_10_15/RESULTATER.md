# Resultat: eksplisitt planlegging uten reserve

H2 uten reserve: -69.3 mot samme planlegger med reserve og -55.7 mot historisk benchmark i sesongsnitt. Pilotkrav ikke bestått; benchmark beholdes.

| Sesong | Uten reserve | Samme planlegger med reserve | Forskjell | Tidligere benchmark | Tidligere TC/BB-policy |
|---|---:|---:|---:|---:|---:|
| 2022-23 | 2380 | 2417 | -37 | 2429 | 2429 |
| 2023-24 | 2265 | 2330 | -65 | 2413 | 2466 |
| 2024-25 | 2374 | 2480 | -106 | 2344 | 2385 |

Den parede kontrollen isolerer reservekostnaden: samme prognoser, samme planlegger og samme ressursgrenser. De to tidligere referansene er etterkontrollerte, gjenbrukte sesongresultater med andre beslutningsmetoder. Dette er utviklingsdata som allerede er undersøkt; ingen generalisering til usette sesonger er dokumentert.

## Hva som faktisk er endret

Planleggeren sammenligner lovlige planer for to runder med forventede netto poeng som eneste poengmål. Chips kan brukes nå, senere eller ikke brukes. Utløp håndteres som manglende fremtidig valgmulighet. Reservekostnader, kunstig benkbonus, friksjon per bytte, diskontering og lærte scorekorreksjoner er fjernet fra kandidaten. Alle tidligere forsøk er bevart.

To runder er en begrenset test av mekanismen. Kandidaten er ikke en ny trent manager og planlegger ikke eksplisitt hele gjenværende sesong. Den har ingen lært sluttverdi etter de to rundene. Begrenset optimering og sekvensielle Free Hit-segmenter gir heller ingen garanti for globalt beste plan. Se [metoden](README.md) og [fryst protokoll](protocol.json).

## Chips og ressurser

| Sesong | Policy | Wildcard | Free Hit | Bench Boost | Triple Captain | Optimeringer | Solversekunder |
|---|---|---|---|---|---|---:|---:|
| 2022-23 | med reserve | [6, 20] | [19, 25] | [9, 27] | [10, 23] | 381 | 58.8 |
| 2022-23 | uten reserve | [2, 20] | [4, 22] | [1, 24] | [3, 21] | 149 | 20.3 |
| 2023-24 | med reserve | [6, 23] | [18, 29] | [7, 24] | [11, 22] | 416 | 50.4 |
| 2023-24 | uten reserve | [2, 20] | [7, 23] | [1, 21] | [3, 22] | 162 | 16.1 |
| 2024-25 | med reserve | [6, 32] | [29] | [7, 20] | [13, 24] | 460 | 59.3 |
| 2024-25 | uten reserve | [2, 20] | [3, 24] | [1, 21] | [5, 22] | 154 | 27.0 |

Ressursgrensen er én tråd, 16 noder per optimering og 40 optimeringer per beslutning for begge. Like grenser betyr ikke lik faktisk tid eller likt antall optimeringer. Seks nye sesongforløp, 228 runder, ingen modelltilpasninger. Den samme offisielt tomme GW7 i 2022/23 behandles som vent uten optimering.

## Kontroller og konklusjon

52 rammeverkstester og seks registertester bestod. De seks nye planleggingstestene dekker å vente til en bedre runde, positiv chip ved utløp, chipsett ved halvårsskifte, gratis åpningslag, Free Hit-restaurering og at kandidaten aldri kaller reservefunksjonen. Fem utfallsblinde integrasjonsprøver på reelle input bestod før registrering.

Etterkontrollen validerte alle lagrede plansekvenser og tilstandsoverganger, regnet poengmål og valg på nytt, kontrollerte ressurslogger og avregnet alle 228 faktiske runder på nytt. Beslutninger er lagret før utfall. [Etterkontroll](audit.json).

Det langsiktige målet er fortsatt netto sesongpoeng. Neste mekanisme bør gi lengre fremtidsforløp eller en validert verdi av gjenværende tilstand, lært fra fremtidige netto poeng. Reservekonstanter skal ikke gjeninnføres under et nytt navn. Ingen automatisk parameterjakt eller benchmarkendring er gjort.
