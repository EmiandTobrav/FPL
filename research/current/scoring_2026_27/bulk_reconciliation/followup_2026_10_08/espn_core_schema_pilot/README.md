# ESPN core-skjema: felt funnet, keeper-CBI feiler

Seks nøyaktige offentlige responser er lagret i inputs med URL og bytehash i
inputs/sources.json. Norwich–Liverpool 2019/20 viser eksplisitte total/effective
Tackles, clearances, blockedShots og interceptions; det er faktiske positive
utespillertellere, ikke bare standardnuller. Skjemaet har ikke nødvendige
mottakertaklinger, keeperlokasjon, storsjanseredninger eller mållinjemarkører.

Alle seks tidligere native keepervetoer ble valgt i keeper_veto_plan.csv før
kildekontrollen. Første Donnarumma-rad, 2025/26 FPL-kamp 41, gir totalClearance
5 og eksplisitte interceptions/blockedShots 0, mot FPL-CBI 4.
**Ruten stopper her; de fem andre vetokampene innhentes ikke. Ingen utfylling.**
FPL er autoritativt; kildeavstemning eller kildestemming kan ikke overstyre det.

`python verify.py` kontrollerer råhashene og gjenskaper det konkrete vetoet
mot den fryste planen. Den er ikke en full keeper-CBI-studie. Taklingsfeltene
undersøkes separat i ../espn_tackle_counts og feiler også der.
