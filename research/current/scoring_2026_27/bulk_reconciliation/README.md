# Gjeldende datagaparbeid og restliste

Oppdatert 9. oktober 2026: **11 949 åpne feltkrav i 11 444 spillerkamper**.
**65 836 spillerkamper og 812 hele kamper** har komplette input. Siste batch
lukker **527 mållinjekrav**, med **390 nye komplette spillerkamper og 44 nye
hele kamper**. Syv tester består; ti resultater og fryste prediksjoner
gjenskapes byteidentisk i separat offline-replay.

Start med [CURRENT.json](CURRENT.json), [arbeidsrekkefølgen](WORK_ORDER.md)
og [nytt identitets-/inventarbevis](followup_2026_10_08/goal_line_identity_v2/README.md).
[Restliste](followup_2026_10_08/goal_line_identity_v2/results/remaining_fields.csv.xz),
[full ledger](followup_2026_10_08/goal_line_identity_v2/results/requirements.csv.xz)
og [assistavhengigheter](priority/assist_groups.csv) er oppdatert sammen.

| Feltgruppe | Åpne krav |
|---|---:|
| Assists etter målreglene | 9 926 |
| Times tackled | 1 238 |
| CBI | 545 |
| Mållinjeklareringer | 48 |
| Øvrige felt | 192 |
| **Totalt** | **11 949** |

48 mållinjekrav gjenstår: 39 arkiv-/identitetsgap og ni større minuttavvik.
Det nye ettminuttsunntaket gjelder bare denne tellerens kvalifiserte inventar
og identitet. FPL-minutter og alle tidligere keeper-/BPS-gater bevares.
Effektiv datainnhenting fortsetter før samlet kvalitet, scoring og features.
De tidligere 374 kvalifiserte 2025/26-poengkampene utvides ikke her.

## Historikk: 303 krav fra sesongblokktotaler

Oppdatert 9. oktober 2026: **12 476 åpne feltkrav i 11 834 spillerkamper**.
**65 446 spillerkamper og 768 hele kamper** har komplette input. Siste batch
lukker **303 mållinjekrav** med eksplisitte primære sesongblokktotaler, og gjør
241 flere spillerkamper inputkomplette. Fem tester består; elleve resultater
og fryst prediksjon gjenskapes identisk i separat offline kopi.

Start med [CURRENT.json](CURRENT.json), [arbeidsrekkefølgen](WORK_ORDER.md)
og [sesongbevisene](followup_2026_10_08/goal_line_season_blocks/README.md).
[Restliste](followup_2026_10_08/goal_line_season_blocks/results/remaining_fields.csv.xz),
[full ledger](followup_2026_10_08/goal_line_season_blocks/results/requirements.csv.xz)
og [assistavhengigheter](priority/assist_groups.csv) er oppdatert sammen.

Førsteprioritet er fortsatt effektiv lukking av datagap. Samlet kvalitet,
poengomregning og fristsikre treningsvisninger følger etterpå. Ingen ny scoring
eller trening utføres; tidligere 374 kvalifiserte poengkamper bevares.

| Feltgruppe | Åpne krav |
|---|---:|
| Assists etter målreglene | 9 926 |
| Times tackled | 1 238 |
| Mållinjeklareringer | 575 |
| CBI | 545 |
| Øvrige felt | 192 |
| **Totalt** | **12 476** |

575 mållinjekrav gjenstår: 536 spiller-minuttilfeller og 39 arkiv-/identitetsgap.
Feltspesifikk identitet og komplette hendelser er neste kildebehov;
FPL-minutter og tidligere fryste kontrollgater bevares.

## Historikk: 2 114 hendelseslukkinger før sesongavstemmingen

Oppdatert 9. oktober 2026: **12 779 åpne feltkrav i 12 075 spillerkamper**.
**65 205 spillerkamper og 768 hele kamper** har komplette input.
Siste batch lukker **2 114 mållinjekrav**, med 1 656 nye komplette spillerkamper
og to hele kamper. Fem tester består; ti resultater og de fryste prediksjonene
gjenskapes byteidentisk uten nettverk i separat kopi.

Førsteprioritet er effektiv lukking av datagap. Samlet kvalitetssikring,
poengomregning og treningsvisninger følger etterpå; se [arbeidsrekkefølgen](WORK_ORDER.md).
Nye utfyllinger beholder kvalitetsflagg. Tidligere poengversjoner og rå FPL bevares.
De 374 poengkvalifiserte 2025/26-kampene utvides ikke i denne innhentingsbatchen.

Start med [CURRENT.json](CURRENT.json) og [hendelsesbevisene](followup_2026_10_08/goal_line_events/README.md).
[Restliste](followup_2026_10_08/goal_line_events/results/remaining_fields.csv.xz),
[full ledger](followup_2026_10_08/goal_line_events/results/requirements.csv.xz),
[dekning](followup_2026_10_08/goal_line_events/results/match_readiness.csv)
og [assistavhengigheter](priority/assist_groups.csv) er oppdatert sammen.

| Feltgruppe | Åpne krav |
|---|---:|
| Assists etter målreglene | 9 926 |
| Times tackled | 1 238 |
| Mållinjeklareringer | 878 |
| CBI | 545 |
| Øvrige felt | 192 |
| **Totalt** | **12 779** |

For de 878 mållinjekravene gjenstår 590 minuttavvik, 249 ukvalifiserte
blokkinventarer og 39 arkiv-/identitetsgap. Neste mulige kilde er eksplisitte
sesongtotaler for blokkeringer og eksakt sesongavstemming. Den nye
[straffe-par-piloten](followup_2026_10_08/penalty_pair_recovery/README.md)
ga ingen nye prediksjoner og mangler tilstrekkelige selvtatte kontroller;
den legges til side uten å endre krav eller kontrollgater.

## Historikk: keeperlokasjon før siste mållinjebatch

Oppdatert 8. oktober 2026, keeperlokasjon: **14 907 åpne feltkrav i 13 745
spillerkamper**. **63 535 spillerkamper og 752 hele kamper** har komplette input.
Siste batch lukker **326 keeperlokasjonskrav** og gir **244 nye hele kamper**.
363 av 380 kamper i 2025/26 har nå også kvalifiserte poeng/BPS/bonus i
[en egen sesongversjon](../../training_dataset/scoring/season_2025/README.md):
10 971 spillerkamper, null komponentavvik og 435 endrede poengsummer.
`CURRENT.json` her gjelder fortsatt datakrav og full historisk kvalifisering;
eldre sesonger, tidsriktige features og aktiv treningsinnlesing gjenstår.

Start med [CURRENT.json](CURRENT.json), [arbeidsrekkefølgen](WORK_ORDER.md) og
[ny direkte lokasjonsavstemming](followup_2026_10_08/fotmob_keeper_location/README.md).
[Restliste](followup_2026_10_08/fotmob_keeper_location/results/remaining_fields.csv.xz),
[full ledger](followup_2026_10_08/fotmob_keeper_location/results/requirements.csv.xz)
og [assistavhengigheter](priority/assist_groups.csv) er oppdatert sammen.
Ti nye tester består; elleve resultater gjenskapes byteidentisk uten nettverk.
Det [generelle CBI-forsøket](followup_2026_10_08/fotmob_cbi_conservation/README.md)
feilet på ni kontrollsammenligninger og har ikke endret noen verdier.
Den tidligere [skuddavstemmingen](followup_2026_10_08/fotmob_shot_conservation/README.md)
lukket alle 994 skuddkrav. Eldre beregninger bruker fortsatt originale snapshot.

## Historikk fra tidligere publiseringer

# Gjeldende historisk harmonisering og restliste

Oppdatert 8. oktober 2026, batch 2: **24 285 åpne feltkrav i 22 496 unike
spillerkamper**. **54 784 spillerkamper og 489 hele kamper** har komplette inputfelt.
Siste batch avklarte **4 649 krav (16,07 %)**. Tilgjengelig input er ikke ferdig
kvalifisert scoring.

Start med [CURRENT.json](CURRENT.json), [arbeidsrekkefølgen](WORK_ORDER.md) og
[nyeste batch](followup_2026_10_08/bulk_batch2/README.md).
[Restliste](followup_2026_10_08/bulk_batch2/results/remaining_fields.csv.gz),
[full ledger](followup_2026_10_08/bulk_batch2/results/requirements.csv.xz) og
[prioriterte assistavhengigheter](priority/assist_groups.csv) er oppdatert sammen.
Kildebelegg og kode er innchecket; offline replay krever Python3.12 og pandas.
Kjør snapshot-bootstrap før replaykommandoen i CURRENT. 22 nye tester og33
identiske replayfiler; full repositorietest/GitHub CI er ikke bekreftet.

Eldre øyeblikksbilder og kildediagnoser beholdes nedenfor; de er ikke dagens kø.

## Historisk dokumentasjon fra forrige publisering

# Gjeldende restliste og arbeidsrekkefølge

Oppdatert 8. oktober 2026. **28 934 åpne feltkrav i 24 716 unike spillerkamper.**
**52 564 spillerkamper og 479 hele kamper har komplette nødvendige inputfelt.**
Dette er datatilgjengelighet, ikke ferdig kvalifiserte poeng, BPS eller bonus.

- [Maskinlesbar inngang og kontrollsummer](CURRENT.json)
- [Full gjeldende kravtabell](followup_2026_10_08/bulk_followup/results/requirements.csv.xz)
- [Kun gjenværende feltkrav](followup_2026_10_08/bulk_followup/results/remaining_fields.csv.gz)
- [Prioritert arbeidsrekkefølge](WORK_ORDER.md)
- [Målgrupper og betinget assistpotensial](priority/assist_groups.csv)
- [Siste batch: metode, kildebelegg og valideringsgrenser](followup_2026_10_08/bulk_followup/README.md)

| Felt | Åpne krav |
|---|---:|
| `assists_2026_27` | 20 288 |
| `goal_line_clearances` | 3 540 |
| `times_tackled` | 1 693 |
| `shots_on_target` | 1 314 |
| `clearances_blocks_interceptions` | 585 |
| `legacy_net_tackles` | 357 |
| `fouls_won` | 356 |
| `won_tackles` | 352 |
| `saves_outside_box` | 342 |
| `penalty_goals` | 56 |
| `big_chance_saves` | 38 |
| `total_tackles` | 11 |
| `historical_bps` | 1 |
| `recoveries` | 1 |

Sammenlignet med sist publiserte kø på 119 780 er 90 846 ytterligere feltkrav
avklart gjennom de mellomliggende arbeidsstegene. Den siste batchen alene
avklarte 2 724 av 31 658 (8,6 %): 1 868 taklingsfelt og 856 assistfelt.
Populasjonen er fortsatt 77 280 spillerkamper / 2 660 kamper.

Øyeblikksbildet inneholder siste fullstendige kravtabell, forrige fullstendige
lokale tabell som replay-input, kode, frosne kontrollfiler og 297 nye primærsvar.
De to store originale gzip-tabellene er lagret som byte-deler. Kjør først
`python followup_2026_10_08/bootstrap.py`; dette gjenskaper begge filene med
identiske kontrollsummer uten omkomprimering. Gjeldende fulltabell finnes også
som vanlig `CSV.xz`, lesbar direkte med pandas.

Siste batch er verifisert med 26 nye tester og 27 identiske resultatfiler fra en
separat kopi. Replay krever Python 3.12 og pandas 2.2.3, ingen tidligere lokale
mapper eller ny nedlasting. Det gjenskaper siste batch, ikke alle historiske
mellomsteg. Filer med `published=false` og omtale av upublisert arbeid inne i det
uforandrede øyeblikksbildet beskriver opprinnelig kjørestatus; denne inngangen
publiserer materialet. Full repository-test og GitHub CI er ikke bekreftet.

Eksterne kvalitetsflagg: 569 151 kravrader i 73 ikke-tomme felt-/sesonggrupper.
Kvalitet behandles gruppevis med unntak; felles Opta-opphav er ikke uavhengig
validering. Rå FPL, eksplisitte nuller, keeperverdier, godkjente offisielle
målrettelser, frosne kontroller og låste etiketter/modeller/benchmark bevares.

**De øvrige CSV-/JSON-filene direkte i denne katalogen og teksten nedenfor er
historiske resultater fra den første masseavklaringen.** De bevares for replay.
Bruk alltid CURRENT.json og øyeblikksbildet over som gjeldende arbeidskø.

---

# Bulk reconciliation: current requirements ledger

8 October 2026. Historical FPL remains authoritative for compatible fields.
This phase follows `assist_reconciliation/` and changes only missing external
counters. No raw sources, approved keepers, assists or locked scoring labels change.

## Result

**138,522 missing field requirements are now available**
(53.6% of the previous open queue).
The new queue contains **119,780 open cells in
63,882 unique player-matches**.

| Field | Newly available | Still open |
|---|---:|---:|
| fouls_won | 29, 693 | 356 |
| goal_line_clearances | 6,085 | 59,216 |
| legacy_net_tackles | 37,733 | 357 |
| shots_on_target | 27,276 | 1,314 |
| won_tackles | 37,735 | 352 |

Player-match input inventories complete: **13,398**,
of which **2,205** are newly complete.
Whole-fixture inventories complete: **119**,
of which **0** are newly complete.
These are available input inventories, not final points/BPS/bonus labels.
**Zero fixtures receive newly qualified bonus labels in this phase.**
Season-specific BPS qualification, clipping/revision rules and quality caveats
remain explicit gates. Readiness is reported for all 77,280 active player-match
records and 2,660 fixtures, including the known FPL extraction exception.

## Four-step workflow

1. **Find shared causes.** The four large groups were sparse won/net tackles,
   line clearances, fouls won and shots on target. Ordinary source blanks are
   not generally observed zeros. Explicit zero total tackles does, however,
   bound both won and lost tackles to zero under the qualified definition.
2. **Probe before scaling.** Twelve pilot fixtures across six seasons produced
   consistent explicit team totals. Twelve preselected later fixtures confirmed
   the same mapping: **194 explicit comparisons
   agree, 0 disagree**. Missing team totals
   are excluded, not counted as correct zeros. A second archive was rejected:
   its new normalized zeros lack demonstrated observational provenance.
   The useful source was then collected once per match for all 2,280 fixtures
   in 2019/20–2024/25, replacing tens of thousands of player requests.
3. **Apply and check in bulk.** Only exact nonnegative sum conservation and the
   explicit tackle-zero subset are used. Every team/field is checked, along
   with population identity, integer domains, contradictory event evidence,
   source preservation and deduplicated change accounting. Failed groups stay
   visible. Further quality work is grouped by field/season plus exceptions,
   not scheduled as one manual task per available cell.
4. **Measure complete units.** `player_match_readiness.csv.gz` and
   `match_readiness.csv` show availability before and after, remaining fields,
   source-quality needs and the separate scoring/bonus qualification gate.

## Why these zeros are justified

The [Opta definitions](https://www.statsperform.com/opta-event-definitions/)
partition tackles into won and lost. Therefore a compatible explicit total of
zero proves both subcounts zero. FotMob explicitly records total tackles;
43,185 overlapping explicit archive totals were screened, with eight
counter disagreements retained. Known contradictory event counts also prevent
a subset derivation. Definition agreement does not independently verify every
FotMob row; the external-source caveat is retained.

For team conservation, all explicit player counts, including bench/non-FPL
players, are summed. When an explicit official team total equals this known
sum, the remaining nonnegative contributions must be zero. A missing team
total or a positive/unexplained residual never licenses a zero. Team and player
IDs, fixture code/date/result, counter domains and source scope are checked.
No positive residual is assigned to an arbitrary player. The primary team field
`fk_foul_won` is checked against player `wasFouled`; it is not a player alias.

For net tackles, use `2 * won - total` only with compatible observed/derived
inputs; retain negative results. This resolves a raw statistic, **not** the
still-unqualified historical BPS clipping rule. Existing source conflicts are
not overwritten. Missing primary line-clearance totals are particularly common
and remain an important blocker; no global omission-to-zero rule was adopted.
A proposed line-clearance bound from clearances plus blocks was rejected after
three observed counterexamples (`line_subset_counterexamples.csv`). This avoids
a fast but incorrect reduction of the queue.

## Quality and validation limits

The control method and plans were frozen before the later 12-fixture responses.
The 194 agreeing controls compare aggregate totals; they do not estimate
individual-player accuracy. Archive and primary responses share Opta ancestry.
Exact aggregate agreement can still coexist with compensating source errors,
so new cells are `external_derived`, not individually primary-verified.

There are 478,305 available external cells with retained quality
caveats. This is a coverage/assurance count, **not that many manual jobs**.
`quality_review_groups.csv` groups the population by field/season and
`automated_quality.json` records population checks. The unique union of open
requirements and source-quality caveats is 77,214
player-matches. It must not be added to open-field counts.

## Files and reproduction

- `requirements.csv.gz`: latest full ledger with previous values/statuses.
- `derived_values.csv.gz`: exact changed cells, method, parent value and group ID.
- `conservation.csv.gz`: successful and rejected team/field proofs.
- `field_summary.csv`, `remaining_player_matches.csv.gz`, `player_summary.csv`:
  field/player queues; keys include season, fixture and FPL player code.
- `match_readiness.csv`, `player_match_readiness.csv.gz`: complete input units.
- `full_team_totals.csv`, `full_sources.json`, `inputs/matches/`: primary evidence.
- `protocol.json`, `control_summary.csv`, `definitions.json`: method and controls.

The collector is resumable and bounded at four concurrent requests and at most
two new request starts per second. It stops new submissions after HTTP
401/403/429. Every stored response is hashed; raw files support offline replay.
No paid data, model training or main merge. Cost: 0 NOK.

```sh
python collect.py plan
python collect.py pilot
python prepare.py
python probe.py pilot
# protocol.json was frozen before collecting the later controls
python collect.py holdout
python probe.py holdout
python collect.py full
python build.py
python report.py
python -m unittest discover -s . -p 'test_*.py'
```

`prepare.py` needs the pinned raw player archive and pyarrow; its compact inputs
are committed, so the build itself needs only pandas and the committed files.
All locked FPL/keeper/assist and model artifacts remain unchanged.

## Verification

24 new and 145 existing focused tests pass (169 total). All 2,280 retained
primary responses were hash-checked and reproduce 4,560 normalized team rows.
An offline collection/build/report replay leaves all 2,332 checked data,
control, manifest and raw-evidence files byte-identical. Full repository tests
and GitHub CI were not verified. See `test_results.json`,
`existing_test_results.json`, `source_verification.json` and
`replay_verification.json`.
