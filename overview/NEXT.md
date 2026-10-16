# Utgangspunkt og neste steg for FPL modellen

Bruk `fpl_2026_27_best_effort_v1` som poeng- og datagrunnlag og `fpl_model_pipeline_v1` som modellinngang. Den aktive sammenligningsfamilien er `fixture_full_h3_adaptive_tc_harmonized_causal_v1`. Ingen ny produksjonsmodell er valgt. Se [prosjektregisteret](PROJECT.json) for konkrete filer og kontrakter.

## Hva vi allerede vet

- Bedre prognosefeil alene ga ikke en bedre manager i simulatorfasen. Todelt modell ble valgt for RMSE, mens den tilpassede benchmarken vant managerens utviklingssnitt.
- De første direkte kamp- og spilletidsmodellene ga positive utviklingssnitt i S2, men tapte i enkelte sesonger og bestod ikke oppgraderingskravet.
- Faste chips, vektet tap, ny deltakelseshistorikk og fast prognoseblanding er gjennomført. Ingen av disse bestod sine oppgraderingskrav. Ikke kjør dem om igjen uendret.
- Horisont, prognose, chipvalg, åpningslag og løserressurser virker sammen. Sammenligninger skal derfor beholde eksplisitte kontrakter og kontrollspor.
- Datakvalitet og historisk tilgjengelighet har fortsatt proxyer og estimater. Nye kildefunn må vurderes separat før de blir features eller poengmål.

Resultater og dokumentasjon finnes i [metodeoversikten](METHODS.md) og [arbeidsstatusen](STATUS.md).

## Første handling ved neste arbeidsøkt

Piloten `learned-manager-20261015-v1` er fullført og etterkontrollert: **+47.0 netto poeng per sesong** i de to lærte evalueringsårene. Les [resultatet](../reports/learned_manager_2026_10_15/RESULTATER.md), [etterkontrollen](../reports/learned_manager_2026_10_15/audit.json) og chipforløpene før neste hypotese. 2022/23 er kontroll uten læring, ikke et tredje lært evalueringsår. Dagens benchmark er beholdt. Ingen prosess trenger videreføring for dette forsøket.

Ikke kjør kandidaten om igjen uendret eller bruk de samme resultatene til ubundet parameterjakt. Før en ny variant bør vi først vurdere det svært lille antallet uavhengige chiputfall, hvordan læringen verdsetter alternative lovlige viderehandlinger og hvilken ny tidsordnet evaluering som kan avtales på forhånd. Full RL og et eksplisitt vinnermål er ikke testet her.

Den eldre H8-kjøringen stoppet med feil 14. oktober kl. 15:01 UTC, dokumentert i [hendelsesloggen](../reports/fpl_improvement_2026_10_14/waves/wave6_full_horizon_reuse_v2/p1_run_events.jsonl). Dens gamle status viste fortsatt pågående arbeid. Managerpiloten er en separat, eksplisitt autorisert kampanje med én konfigurasjon; den utvider ikke taket på åtte i den gamle kampanjen.

## Når et nytt forsøk er berettiget

Velg én mekanisme fra dokumenterte svakheter i eksisterende logger. Forklar hva som endres og hvilket tidligere negativt funn hypotesen tar hensyn til. Behold de øvrige forholdene så langt forsøksdesignet tillater det. Bruk [arbeidsflyten](WORKFLOW.md) og registrer kontrakten før kjøring.

Undersøk ny informasjon eller en ny mekanisme fremfor å variere navn, vekter og terskler på allerede undersøkte resultater. En ny dataversjon eller policy trenger en tilpasset benchmarkkjøring, og allerede inspiserte sesonger skal fortsatt omtales som utviklings-/rapporteringsdata.

## Fast avslutning av en arbeidsøkt

Noter forsøks-ID, faktisk status, resultat eller årsak til at det står stille, filene som dokumenterer dette, og én konkret neste handling. Registrer også feil og avviste hypoteser. Oppdater statusoversikten; ikke kopier hele data- eller kodegrunnlaget til enda en arbeidsmappe.
