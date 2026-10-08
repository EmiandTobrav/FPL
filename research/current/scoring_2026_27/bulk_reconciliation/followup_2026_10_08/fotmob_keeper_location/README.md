# Direkte keeperlokasjon: 326 krav lukket, 244 nye hele kamper

8. oktober 2026. **14 907 krav gjenstår i 13 745 spillerkamper.**
**63 535 spillerkamper og 752 hele kamper** har komplette poenginput.
Dette er inputdekning; historiske poengetiketter er fortsatt ikke kvalifisert.

Skuddinventaret fra FotMob har eksplisitt skuddopphav og keeper-ID. Vi teller
keeperens faktiske, ublokkerte redningsskudd med `isFromInsideBox=false`.
Utespillerblokker, mållinjeredninger og selvmål holdes utenfor. Metoden bruker
ikke totalredninger minus innenfor-redninger og anslår ingen lokasjoner.

Anvendelse krever at inventaret stemmer med begge lagenes eksplisitte antall
skudd, at hver keeperredning har eksplisitte klassifiserings-/lokasjonsflagg og
entydig keeperidentitet på motstanderlaget, og at keeperens komplette telling
stemmer med både historisk FPL-redninger og eksplisitt FotMob-redningstall.
Ukjent identitet, manglende skudd/total/klassifisering, positive kildemotsetninger
eller uenige redningsantall gir avståelse. Manglende felt blir aldri automatisk null.

Alle 261 kamper med de 342 åpne lokasjonskravene ble valgt, pluss de første 20
andre kampene i 2025/26 som kontroll. Fem tidligere råsvar ble gjenbrukt; 276 nye
public kampresponser ble hentet. [Plan](plan.csv) og [protokoll](protocol.json)
var fastlagt før lokasjonssammenligning. Dette er kildemapping mot allerede
kvalifiserte Opta/FPL-grunnlag; det er ingen uavhengig leverandør- eller modellholdout.

Alle 40 kontrollkeepere er kvalifisert for sammenligning og stemmer med de
allerede godkjente outside-tallene, uten avvik. 543 av 569 keeperobservasjoner i
kontroll-/målutvalget har komplette, avstemte redningsinventarer; 26 avstår på
redningsantall. Det er ingen lokasjonsavvik blant sammenlignbare, avklarte rader.
**326 nye outside-tall er dokumenterte nuller.** 16 av de 342 opprinnelige kravene
står igjen, alle med redningsantall som ikke stemmer. Ingen tidligere verdi endres.

[Keeperprediksjoner og avståelser](results/keeper_predictions.csv),
[redningsbelegg](results/save_evidence.csv), [kontroller](results/control_comparisons.csv)
og [avklarte krav](results/derived_values.csv) gjør hver telling etterprøvbar.
De 774 922 øvrige ledger-radene er kontrollert uendret, inklusive rå FPL,
konflikter og tidligere keeperrekonstruksjoner.

[Restliste](results/remaining_fields.csv.xz), [full ledger](results/requirements.csv.xz),
[kampdekning](results/match_readiness.csv), [funn](results/findings.json) og
[filmanifest](results/manifest.json) er gjeldende via [CURRENT](../../CURRENT.json).
2025/26 har nå 363 av 380 kamper med komplette input. Neste arbeid bør kvalifisere
poeng og helkampbonus for denne sesongen med reglene som faktisk gjelder der,
samt fortsette de øvrige historiske feltkravene og treningsintegrasjonen.

Ti sikkerhetstester består. Elleve resultater gjenskapes byteidentisk fra fryste
råsvar og innganger i separat kopi uten nettverk:

```bash
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/fotmob_keeper_location/reproduce.py
python -m unittest discover -s research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/fotmob_keeper_location -p 'test_*.py' -v
```

[Reproduksjonsrapport](reproduction_verification.json). Eldre beregninger og
kontrollutvalg bevares med sin opprinnelige ledgerpeker. [CBI-V1](../fotmob_cbi_conservation/README.md)
feilet og har ikke kvalifisert nye felt. Begge studier og alle råsvar er bevart.
