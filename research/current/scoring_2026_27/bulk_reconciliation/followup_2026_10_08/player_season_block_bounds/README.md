# Fire mållinjeverdier fra eksakte spiller-sesonggrenser

9. oktober 2026: **fire åpne krav lukkes**, fra 11 219 til **11 215**.
Jesse Lingard, Andreas Pereira, Marcus Rashford og Mason Greenwood får
dokumentert null mållinjeklareringer i Man Utd–Aston Villa, kamp 135 i 2019/20.
Ingen ny spillerkamp eller hel kamp blir inputkomplett: dekningen er fortsatt
66 478 spillerkamper og 824 hele kamper. Mållinjeresten går fra 48 til 44.

Den nye innhentingen gjelder spillernes sesongvise `outfielder_block`.
2019/20 har én komplett side med 357 entydige Opta-spillerkoder. Summen
**2 521** er nøyaktig lik summen av eksplisitte sesongtotaler for alle 20 lag,
som tidligere ble avstemt mot 380 kamper. Alle telleverdier er ikke-negative
heltall. Nulltotaler og utelatte tellere er derfor eksakt avklart for aktive
utespillere i den hashkontrollerte sesongrosteren. En spillers mållinje-
klareringer er en delmengde av spillerens blokkerte skudd. Null blokkerte
skudd i hele sesongen gir null i hver kamp, uten individuell minuttjustering.
Keepere inngår ikke i denne utfyllingen.

Kildedata for 2020/21 feiler avstemmingen: spillersummen er **2 471**, lag-
summen **2 472**. Hele den sesongen avstår, og videre innhenting stoppes
etter den fryste planen. Ingen ukjent teller i en gruppe med positiv residual
blir null. De planlagte 2021/22- og 2024/25-responsene er ikke hentet.
Ingen kontrollutfall brukes til å velge den avstemte kildegruppen.

Prediksjonene ble fryst før kontroll mot kjente mållinjeverdier. **1 513
kontroller i 378 kamper har null avvik**, og ingen eksplisitte positive
arkivtellinger motsier nullgrensen. Dette gjenbruker godkjente Opta-verdier;
det er ikke uavhengig holdout eller samlet kvalitetsgodkjenning.
Kontrollkravet på minst 1 000 observasjoner og null feil er bevart.

Alle **775 244 øvrige ledgerrader**, native kildekolonner, godkjente verdier,
beskyttede konflikter, assistpekere og native rettelser beholdes.
Poengversjoner, kanoniske tabeller og modeller er ikke bygd på nytt.

Tre tester kontrollerer blant annet at én manglende blokkering sperrer hele
sesongen, og at ett kjent positivt moteksempel sperrer utfyllingen.
Isolert offline-replay gjenskaper **16 filer byteidentisk**:

```sh
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/player_season_block_bounds/test_bounds.py
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/player_season_block_bounds/reproduce.py
```

De to nye råresponsene, den mislykkede residualen og alle kildefingeravtrykk
er bevart. Normal replay henter ingen data. Resterende mållinjeverdier og
alle andre krav er fortsatt åpne; dette er en datagapbatch, ikke treningsklarhet.
