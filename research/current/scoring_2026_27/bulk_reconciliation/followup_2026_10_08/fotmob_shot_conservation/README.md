# Skudd på mål: hele restgruppen avklart

8. oktober 2026, arbeidsgren `codex/training-dataset-2026-27`.

**994 krav lukket. 15 233 krav gjenstår i 14 071 spillerkamper.**
63 209 spillerkamper og 508 hele kamper har komplette poenginput: 919 og 18
flere enn forrige snapshot. Ingen historiske omregnede poengetiketter er godkjent.

Den tidligere FotMob-projeksjonen hentet defensive spillerfelt, men ikke eksplisitte
lagtotaler for `ShotsOnTarget`. Disse totalene er hentet for alle 95 kamper med
åpne skuddkrav og 25 kontrollkamper, valgt før sammenligning: de fem første
ikke-berørte kampene per relevant sesong. Dette bruker kampdata som den tidligere
projeksjonen ikke tok med, uten å gjenta den mislykkede BPS-kontrollen.

Alle 994 nye nuller har et eksakt bevis: summen av alle eksplisitte skuddverdier
for klubbens spillere, inklusive spillere uten FPL-rad, uttømmer en eksplisitt
fullkamptotal. Det finnes dermed ingen skudd igjen å tildele spillerne med utelatt
felt. Manglende lagtotal eller positiv rest ville gitt avståelse. Kjente positive
hendelser, uenige primærverdier, klubbsider, historisk FPL og allerede avklarte
verdier vetoer hele laggruppen ved motstrid. Ingen slik motstrid ble funnet.

Kontrollene gir 161 eksplisitte spiller- og 50 primære lagtotal-sammenligninger
uten avvik, over alle fem sesonger. De aktuelle kampene gir ytterligere 404
spiller- og 95 lagtotal-sammenligninger uten avvik. Alle 240 laggrupper avstemmes.
FotMob og primærdata deler Opta-grunnlag; dette kvalifiserer feltdefinisjon og
konservering, og skal ikke beskrives som uavhengig leverandørvalidering.

| Sesong | Nye verdier |
|---|---:|
| 2019/20 | 297 |
| 2020/21 | 174 |
| 2021/22 | 202 |
| 2022/23 | 256 |
| 2023/24 | 65 |

[Protokoll](protocol.json), [fast kildeplan](plan.csv),
[kildebelegg med bytehash](inputs/source_manifest.csv),
[kontrollsammenligninger](results/source_comparisons.csv),
[lagavstemming](results/team_conservation.csv) og
[avklarte krav](results/derived_values.csv) er bevart sammen med 120 råsvar.
De 774 254 andre ledger-radene er kontrollert uendret, inklusive alle konflikter,
FPL-verdier og tidligere kvalifiserte rekonstruksjoner. Rå FPL er uendret.

[Ny restliste](results/remaining_fields.csv.xz),
[full ledger](results/requirements.csv.xz),
[kampdekning](results/match_readiness.csv) og [funn](results/findings.json)
er gjeldende via [CURRENT](../../CURRENT.json). Kvalitetsflagg og åpne regelgater
for BPS, bonus og poeng beholdes; inputkomplett er ikke treningsklart.

Reproduksjon uten nettverk fra repositoryets rot:

```bash
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/fotmob_shot_conservation/reproduce.py
python -m unittest discover -s research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/fotmob_shot_conservation -p 'test_*.py' -v
```

Ni sikkerhets-/identitetstester består. [Reproduksjonsrapporten](reproduction_verification.json)
verifiserer avledede filer i separat kopi. Den eldre historiske beregningen og
legacy-kontrollen reproduseres fortsatt med deres opprinnelige, arkiverte CURRENT-
peker. Kontrollutvalg, gamle utfall og modeller endres ikke når restlisten går videre.
Neste arbeid må tilføre nye fakta eller kvalifiserte regler til de resterende
kravene; denne skuddgruppen skal ikke samles inn igjen.
