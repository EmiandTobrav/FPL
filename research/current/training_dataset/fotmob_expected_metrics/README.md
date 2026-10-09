# FotMob xG/xA: avsluttet, feilet kompatibilitetsprøve

120 allerede lagrede kampresponser er undersøkt. 2 702 eksplisitte xG-/xA-
verdier har entydige spillerkoder; 1 987 oppfyller kravet om identiske native
minutter. Manglende nøkler blir ikke null. Kampidentitet, dato, klubber og
sluttresultat er kontrollert med den eksisterende kvalifiserte dekoderen.
Prediksjoner og gater er fryst før sammenligning.

Kontrollen mot kvalifisert 2022/23-FPL og native 2023/24 gir **101 avvik
blant 312 xG-verdier** og **34 avvik blant 526 xA-verdier**, fordelt på 38
kamper. Den korrigerte 2022/23-versjonen brukes, slik at de gamle strukturelle
rånullene ikke blir feil fasit. Avrunding er på to desimaler med HALF_UP;
ingen toleranse eller kalibrering er tilpasset avvikene.

**Ingen verdier fylles og ingen feltkrav lukkes.** Ruten er avsluttet med
bevart mislykket kontroll. Publisert modellopphav og kompatibilitet med
2026/27 er heller ikke kvalifisert. Ikke masseinnhent eller gjenåpne denne
ruten uten konkrete nye definisjons-/versjonsfakta som kan forklare avvikene.
xGI-/xGC-imputering og bruk av xGOT som xGC er ikke godkjent.

`python research/current/training_dataset/fotmob_expected_metrics/reproduce.py`
gjenskaper syv resultat-/prediksjonsfiler byteidentisk offline fra de
hashkontrollerte råsvarene. Ledger, kanoniske tabeller, features og poeng
endres ikke. Dette er en kildeprøve, ikke samlet datakvalifisering.
