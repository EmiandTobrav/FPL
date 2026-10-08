# Keeper-CBI: kort pilot, mislykket kvalifisering bevart

640 allerede lagrede fullkamper er gjenbrukt. En egen keeperkontroll ble fryst
før nye sammenligninger: minst 100 native keeperverdier, 50 native kamper og
20 positive native kontroller, samt 30 historiske/5 positive kontroller per
sesong og null feil. Generisk CBI-V1 og alle historiske lag-/primærvetoer beholdes.

569 2025/26-keeperrader i 281 kamper ble kontrollert direkte mot FPL. 392 har
positiv native CBI. Seks avvik stopper hele ruten:

| Kamp | Spillerkode | FPL | FotMob-komponenter |
|---:|---:|---:|---:|
| 41 | 204936 | 4 | 5 |
| 289 | 184254 | 1 | 3 |
| 307 | 172649 | 0 | 2 |
| 310 | 149065 | 3 | 4 |
| 317 | 59735 | 3 | 2 |
| 346 | 204936 | 1 | 2 |

388 lukkede historiske keeperkontroller stemmer, men det overstyrer ikke de
seks native moteksemplene. Ingen av de potensielt 334 lagavstemte targetradene
anvendes. Alle 341 manglende keeper-CBI-krav og alle beskyttede konflikter
forblir åpne. Nåværende ledgerpekere og kvalifiserte 2025/26-labels endres ikke.
Ingen nye kildenettforespørsler var nødvendige.

Dette er gjenbrukt regresjonsbelegg fra felles Opta/FotMob-linje, ikke en ny
uavhengig holdout. Ikke gjenta samme rute uten fakta som forklarer de konkrete
native avvikene eller en annen kompatibel kilde. Fravær av komponent er ikke
null; pilotens nullsertifikater krevde eksakt eksplisitt lagtotal.

```sh
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/fotmob_keeper_cbi/reproduce.py
python -m unittest discover -s research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/fotmob_keeper_cbi -p 'test_*.py' -v
```

Resultater, plan, protokoll, inngangsfingeravtrykk og avvik ligger i denne
mappen. Ingen mislykket gate senkes, og ingen nuller eller målpoeng oppfinnes.
