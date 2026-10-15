# FPL metoder og resultater

Metodene nedenfor beholder sine opprinnelige sammenligningsgrunnlag. Netto sesongpoeng, prognosefeil og kildekontroller svarer på ulike spørsmål. De kan ikke blandes til én rangering.

## Rekonstruksjon og modellgrunnlag

| Trinn | Resultat | Dokumentasjon |
|---|---|---|
| Historiske inputfelt | Aktiv inputrest er 0; 847 brukeraksepterte estimater er bevart. 2019/20 har 2711 utsatte krav. | [Ledgerstatus](../overview/evidence/reconstruction_CURRENT_20261014.json) |
| Praktisk omregning og utgivelse | 159 291 modellrader; best-effort-poengmål, kvalitetsflagg og masterdata beholdt. | [Datakort](../datasets/fpl_2026_27_best_effort_v1/README.txt) |
| Tidsregler og features | Operasjonell proxy og konservativ kontroll; 21/97 features; target-tilgjengelighet for H1/H3/H6. | [Featuregrunnlag](../datasets/fpl_model_preparation_v1/README.txt) |
| Behandling før trening | Foldvis imputering/skalering; Ridge, CatBoost og LightGBM har egne profiler. | [Pipeline](../datasets/fpl_model_pipeline_v1/README.txt) |

## Nyere prognose og simulatorforsøk

| Forsøk | Resultat og konklusjon | Kilde |
|---|---|---|
| Walk-forward, 13. oktober | Todelt modell med 97 features og expanding-historikk ble valgt på utviklingsdata for prognosefeil. H1 RMSE 1,964 mot historisk referanse 2,039 i 2025/26. Dette velger ikke automatisk beste FPL-manager. | [Rapport](../reports/walk_forward_2026_10_13/RESULTATER.md) |
| Simulator, felles åpning | Tilpasset benchmark: 2422,3 poeng i utviklingssnitt. Direkte CatBoost: −93,0 mot benchmark. | [Simulatorrapport](../reports/fpl_simulator_2026_10_13/final_report/RESULTATER.txt) |
| Simulator, eget GW1-lag | Tilpasset benchmark: 2407,0 i utviklingssnitt. Ingen av de fire nye kandidatene slo den i snitt. Rapportåret beholdes separat. | [Simulatorrapport](../reports/fpl_simulator_2026_10_13/final_report/RESULTATER.txt) |
| Første kampanje, direkte kampmodell | S1 +69,0 i matchet sammenligning. S2 +55,3 i manager-snitt, men sesongtap og oppgraderingskravet ikke oppfylt. | [S1](../reports/fpl_improvement_2026_10_14/s1_screening_result.json), [sluttutfall](../reports/fpl_improvement_2026_10_14/campaign_v1_outcome.json) |
| Første kampanje, spilletidsmodell | S1 +57,7. S2 +26,3, men sesongtap og oppgraderingskravet ikke oppfylt. | [Sluttutfall](../reports/fpl_improvement_2026_10_14/campaign_v1_outcome.json) |
| Første kampanje, komponentmodell | S1 −25,7 i snitt; gikk ikke videre. | [S1](../reports/fpl_improvement_2026_10_14/s1_screening_result.json) |
| Faste chips med direkte modell | +14,3 mot opprinnelig adaptiv benchmark; sesonggevinster −73, −3, +119. Stoppet. Policyen er endret, så dette er en systemsammenligning. | [Utfall](../reports/fpl_improvement_2026_10_14/waves/wave2_fixed_chips/outcome.json) |
| Vektet tap for spilletidsmodell | −50,0; sesonggevinster −72, −167, +89. Stoppet. | [Utfall](../reports/fpl_improvement_2026_10_14/waves/wave3_selectable_loss/outcome.json) |
| Historikk i deltakelsesmodell | +7,7; sesonggevinster +64, −63, +22. Stoppet. | [Utfall](../reports/fpl_improvement_2026_10_14/waves/wave4_participation_history/outcome.json) |
| Fast prognoseblanding | −1,3; sesonggevinster −22, +5, +13. Stoppet. | [Utfall](../reports/fpl_improvement_2026_10_14/waves/wave5_fixed_blend/outcome.json) |
| Full tilgjengelig horisont H8 | P1 avsluttet med exit 1 den 14. oktober kl. 15:01 UTC. Ingen fullført sammenligning eller oppgradering; eldre status var utdatert. | [Endringskontrakt](../reports/fpl_improvement_2026_10_14/waves/wave6_full_horizon_reuse_v2/amendment.json), [hendelseslogg](../reports/fpl_improvement_2026_10_14/waves/wave6_full_horizon_reuse_v2/p1_run_events.jsonl) |
| Lært TC/BB-reserve med uendrede prognoser | +47.0 netto poeng i snitt i 2023/24–2024/25; gevinster +53, +41. 2022/23 er identisk kontroll uten læring. Pilotkrav bestått; benchmark beholdt. | [Rapport](../reports/learned_manager_2026_10_15/RESULTATER.md), [etterkontroll](../reports/learned_manager_2026_10_15/audit.json) |
| Sesonglang lært manager, alle chips og komplette handlinger | -243.0 mot benchmark, -290.0 mot TC/BB-policy og -297.5 mot samme forslag uten læring i sesongsnitt. Pilotkrav ikke bestått; benchmark beholdt. | [Rapport](../reports/season_manager_2026_10_15/RESULTATER.md), [etterkontroll](../reports/season_manager_2026_10_15/audit.json) |

| Eksplisitte H2-planer uten reservekostnad | H2 uten reserve: -69.3 mot samme planlegger med reserve og -55.7 mot historisk benchmark i sesongsnitt. Pilotkrav ikke bestått; benchmark beholdes. | [Rapport](../reports/explicit_planning_2026_10_15/RESULTATER.md), [etterkontroll](../reports/explicit_planning_2026_10_15/audit.json) |

Kampanjer 14. oktober bruker allerede studerte utviklingssesonger. Positivt snitt alene dokumenterer ikke en robust oppgradering. S1, S2 og senere bølger har ulike sammenligningskontrakter; kontrollene følger hver kilde.

## Eldre metodefamilier

Disse forsøkene bruker eldre poengmål og egne chip- og startkontrakter. Resultater og protokoller beholdes som historiske referanser.

| Familie | Hva ble undersøkt eller funnet | Rapport |
|---|---|---|
| Oppside | Ingen av fire nye kandidater forbedret gjennomsnittlig sluttscore mot 50/50 Ridge og Extra Trees. | [Oppside](../research/current/upside/README.md) |
| Oppside som feature og kapteinssignal | Tidsriktig oppsidefeature og avgrenset kapteinssignal; sammenligninger og paired-summary beholdt. | [Rapport](../research/current/upside_feature/README.md) |
| Lengre plan og dekomponert poengmodell | H1/H4 og totalforventning fra høye/lave utfall, 72 nye sesongforløp. | [Rapport](../research/current/horizon_upside/README.md) |
| Løpende retrening og hendelser | Ni kandidater, 108 nye forløp; tidsvekting, hendelsesmodell og faste blandinger. | [Rapport](../research/current/adaptive_events/README.md) |
| Retrening av ensemble | Ridge/Extra Trees og faste blandinger, 60 nye forløp; gevinster avhenger av chipregime. | [Rapport](../research/current/retrained_ensemble/README.md) |
| Chip og scenariodiagnostikk | Små prognoseforbedringer garanterer ikke bedre lag; 144 chipablasjoner og matchede beslutninger. | [Rapport](../research/current/behavior_diagnostics/README.md) |
| Beslutningsspesialist | Tre-rundersplanlegging og tidsordnet HGB-blanding, separate kontroller. | [Rapport](../research/current/decision_specialist/README.md) |
| Global HGB og H3 | +70,0 med chips mot datidens referanse over fire sesonger; usikker tilleggsverdi mot global HGB med H1. | [Rapport](../research/current/global_horizon/README.md) |
| Kalender | +35,5 med chips mot constant_h3, ujevn gevinst; kalenderdekning har egne kildebegrensninger. | [Forsøk](../research/current/calendar_counts/README.md), [kalenderaudit](../research/current/calendar_audit/README.md) |
| Posisjonsspesialisering | Ingen kandidat slo datidens primærbenchmark med chips. | [Rapport](../research/current/position_specialist/README.md) |
| Kampjustering og adaptive chips | Grunnlaget for historisk valgt benchmark fixture_full_h3_adaptive_tc. | [Rapport](../research/current/fixture_strategy/README.md) |

## Registrering av nye forsøk

Hvert forsøk skal oppgi dataversjon og inputhash, feature-/tidskontrakt, prognosemodell, beslutningspolicy, benchmark, sesonger, ressurser, resultater og konklusjon. Skill mellom planlagt, pågående, fullført, kontrollert og godkjent. Behold også negative utfall og feil som forklarer hvorfor en metode ble stoppet.

[runs.csv](runs.csv) gir én rad per lagret sesongkvittering fra simulatorområdene og managerpiloten. Gamle forløp finnes via familierapportene over. CSV-registeret er ikke en samlet resultatrangering eller dokumentasjon på at hver kvittering er uavhengig godkjent.
