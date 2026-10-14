# FPL arbeidsstatus

Dette er en lesende oversikt. Kildenes lagrede status beviser ikke at en prosess fortsatt kjører.

**Siste registrerte fase:** `wave6_P1_six_paired_seasons_running`.
**Status oppdatert i kildefilen:** 2026-10-14T15:00:43.983165+00:00.

Start med [arbeidsflyten](WORKFLOW.md), [neste steg](NEXT.md) og [prosjektregisteret](PROJECT.json).

| ID | Metode eller trinn | Status | Funn |
|---|---|---|---|
| data-reconstruction | [Historiske inputfelt](../overview/evidence/reconstruction_CURRENT_20261014.json) | completed_best_effort | Aktiv rest 0; 847 estimater beholdt; streng kildekvalifisering fortsatt separat. |
| data-release-v1 | [Rekonstruert treningsdatasett v1](../datasets/fpl_2026_27_best_effort_v1/README.txt) | released | 159291 modellrader med best-effort-mål og kvalitetsflagg. |
| features-v1 | [Tidsregler og 21 eller 97 features](../datasets/fpl_model_preparation_v1/README.txt) | completed | Operasjonell proxy og konservativ kontroll; samme spillerutvalg og targets. |
| pipeline-v1 | [Foldvis behandling og modellpipeline](../datasets/fpl_model_pipeline_v1/README.txt) | completed | Skalering og imputering læres fra tilgjengelig treningshistorikk. |
| walk-forward-v1 | [Walk-forward prognosemodeller](../reports/walk_forward_2026_10_13/RESULTATER.md) | completed | Todelt/97/expanding valgt for prognosefeil; H1 RMSE 1.964 i 2025/26. Ingen automatisk managerpromotering. |
| simulator-v1 | [Lovlig FPL-manager og spesialister](../reports/fpl_simulator_2026_10_13/final_report/RESULTATER.txt) | completed | Omregnet benchmark vant utviklingssnitt i både matched og manager. Kontraktene holdes adskilt. |
| legacy-upside | [Oppside](../research/current/upside/README.md) | archived | Ingen av fire nye kandidater forbedret gjennomsnittlig sluttscore. |
| legacy-upside_feature | [Oppside som feature og kapteinssignal](../research/current/upside_feature/README.md) | archived | Matchet kontroll; funn og begrensninger i egen rapport. |
| legacy-horizon_upside | [H4 og dekomponert poengforventning](../research/current/horizon_upside/README.md) | archived | 72 nye forløp med egne horisont- og modellkontroller. |
| legacy-adaptive_events | [Løpende retrening og hendelsesmodell](../research/current/adaptive_events/README.md) | archived | 108 nye forløp, ni kandidater; chipregimer sammenlignes separat. |
| legacy-retrained_ensemble | [Retrening og faste blandinger](../research/current/retrained_ensemble/README.md) | archived | 60 nye forløp; gevinst avhenger av chipregime. |
| legacy-behavior_diagnostics | [Chip og scenariodiagnostikk](../research/current/behavior_diagnostics/README.md) | archived | Små prognoseforbedringer garanterer ikke bedre manager; 144 ablasjoner. |
| legacy-decision_specialist | [H3 og HGB-spesialist](../research/current/decision_specialist/README.md) | archived | Separate planleggings- og blandingsforsøk; referanser beholdt. |
| legacy-global_horizon | [Global HGB og H3](../research/current/global_horizon/README.md) | archived | +70 mot datidens referanse med chips; usikker tilleggseffekt mot global H1. |
| legacy-calendar_counts | [Kalender og antall kamper](../research/current/calendar_counts/README.md) | archived | +35.5 med chips mot constant_h3, ujevn gevinst. |
| legacy-calendar_audit | [Kalenderdekning og kilderevisjon](../research/current/calendar_audit/README.md) | archived | 82 arkivversjoner for 136 beslutningstidspunkter; tidsproxy beholdt. |
| legacy-position_specialist | [Posisjonsspesialisering](../research/current/position_specialist/README.md) | archived | Ingen kandidat slo datidens primærbenchmark med chips. |
| legacy-fixture_strategy | [Kampjustering og adaptiv TC](../research/current/fixture_strategy/README.md) | archived | Grunnlag for gammel benchmark; 2351.5 kan ikke overføres til nye targets. |
| campaign1-fixture_direct_v1 | [Direkte kampmodell](../reports/fpl_improvement_2026_10_14/campaign_v1_outcome.json) | stopped | +55.3 poeng i snitt; ingen kvalifisert oppgradering. Komponentmodell målt i S1; øvrige i S2. |
| campaign1-minutes_hurdle_fixture_v1 | [Spilletidsmodell](../reports/fpl_improvement_2026_10_14/campaign_v1_outcome.json) | stopped | +26.3 poeng i snitt; ingen kvalifisert oppgradering. Komponentmodell målt i S1; øvrige i S2. |
| campaign1-component_points_fixture_v1 | [Komponentmodell](../reports/fpl_improvement_2026_10_14/s1_screening_result.json) | stopped | -25.7 poeng i snitt; ingen kvalifisert oppgradering. Komponentmodell målt i S1; øvrige i S2. |
| wave2_fixed_chips | [Direkte modell med faste chips](../reports/fpl_improvement_2026_10_14/waves/wave2_fixed_chips/outcome.json) | candidate_stopped_at_P1_no_qualifying_upgrade | +14.3 poeng i utviklingssnitt; oppgraderingskravet ikke bestått. |
| wave3_selectable_loss | [Vektet tap](../reports/fpl_improvement_2026_10_14/waves/wave3_selectable_loss/outcome.json) | candidate_stopped_at_P1 | -50.0 poeng i utviklingssnitt; oppgraderingskravet ikke bestått. |
| wave4_participation_history | [Historikk i deltakelsesmodell](../reports/fpl_improvement_2026_10_14/waves/wave4_participation_history/outcome.json) | candidate_stopped_at_P1 | +7.7 poeng i utviklingssnitt; oppgraderingskravet ikke bestått. |
| wave5_fixed_blend | [Fast prognoseblanding](../reports/fpl_improvement_2026_10_14/waves/wave5_fixed_blend/outcome.json) | candidate_stopped_at_P1 | -1.3 poeng i utviklingssnitt; oppgraderingskravet ikke bestått. |
| wave4-diagnostic | [Deltakelsesbias og trajektoriediagnose](../reports/fpl_improvement_2026_10_14/waves/wave4_planning/outcome.json) | completed | Nullhistorikkbias og sesongforløp undersøkt; førte til separat historikkhypotese. |
| wave6-h8 | [Full tilgjengelig planhorisont H8](../reports/fpl_improvement_2026_10_14/orchestration_state.json) | see_recorded_status | Ingen ferdig oppgradering konkludert; les status og registrerte neste handlinger. |
| archive-qualification | [Historiske arkiv og tilgjengelighet](../reports/fpl_improvement_2026_10_14/orchestration_state.json) | see_recorded_status | Kildearbeid registrert separat fra modellforsøk; proxyer beholdes inntil kvalifisering er dokumentert. |
| model-lab-v1 | [Felles rammeverk for modelltesting og simulering](../model_lab/README.md) | implemented_validation_only | Samme tidskontroller, prognosecache, regelmotor og resultatkort. 40 tester bestått; små funksjonsprøver er ikke nye modellvalgsresultater. |
| manager-learning-idea | [Lære en faktisk FPL-manager og senere optimere vinnsannsynlighet](../overview/MANAGER_LEARNING.md) | proposed_not_registered_not_trained | Første foreslåtte prøve: lær fremtidsverdi eller beslutningsrangering med uendrede prognoser. Vinnermål krever separat usikkerhets- og konkurrentmodell. |

Tall fra ulike kontrakter kan ikke summeres eller rangeres direkte. Se [metodeoversikten](METHODS.md) for sammenligningsgrunnlag. Negative resultater er del av utgangspunktet for neste hypotese.
