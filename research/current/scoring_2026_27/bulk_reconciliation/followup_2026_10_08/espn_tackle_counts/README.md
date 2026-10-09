# ESPN core-tellere: avsluttet uten utfylling

Den fryste direkte mappingen totalTackles → total_tackles og effectiveTackles →
won_tackles feiler mot native FPL/arkiv og tidligere godkjente verdier.
Signert netto er 2 × won − total; ingen klipping eller BPS-kvalifisering.
**Ingen feltkrav lukkes. Ingen ledger eller poengversjon endres.**

Planen velger alle 16 manglende won_tackles-rader og fem aktive DEF/MID etter
spillerkode fra hver av 30 tidligere kontrollkamper, før innhenting av disse
tellernes utfall. 166 deltakere undersøkes; 55 har avvik i minutter og avstår.
100 kontrollrader og 11 målrader består identitet, eksplisitte heltall,
én opptreden, won ≤ total og eksakte native FPL-minutter.

47 referanseavvik for total, 30 for won og 12 for signert netto stopper alle
mappinger. Referanser overlapper; dette er ikke 89 unike spilleravvik.
Minstekravene beholdes. Kilden deler mulig Opta-opphav og kontrollene er ikke
uavhengig holdout. Ingen ny mapping tilpasses fasiten i dette forsøket.
Gjenbruk råsvarene, men ikke gjenta ruten uten konkret kilde-/definisjonsbevis.

`python reproduce.py` gjenoppretter nøyaktige råsvar og gjenskaper koblinger,
prediksjoner og kontrollutfall i en separat kopi med nettverk eksplisitt sperret.
`python test_acquisition.py` kontrollerer manglendeverdier, signert netto,
minuttvetoer og at feilede mappinger ikke gir utfyllinger.
