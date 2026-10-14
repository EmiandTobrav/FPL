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

Les `reports/fpl_improvement_2026_10_14/orchestration_state.json` direkte eller bruk `python3 scripts/research.py status`. Ved kartleggingen var Wave6 med full H8-planhorisont registrert som pågående P1. Ikke start en ekstra kopi, restart eller ny variant basert på denne oversikten.

Hvis den fasen fortsatt pågår, fortsett fra dens faktisk registrerte fremdrift og eksisterende protokoll. Hvis den er avsluttet, les fullføringskvittering, uavhengig kontroll og numerisk gate før du trekker en konklusjon. Oppdater katalogen med det dokumenterte utfallet og friske opp oversikten.

Wave6 er konfigurasjon 8 i den eksisterende kampanjen, med et tak på åtte konfigurasjoner. Et nytt forslag må derfor avklare en ny eller eksplisitt endret kampanjeramme; registreringsverktøyet gir ikke tillatelse til å utvide det eksisterende søket.

## Når et nytt forsøk er berettiget

Velg én mekanisme fra dokumenterte svakheter i eksisterende logger. Forklar hva som endres og hvilket tidligere negativt funn hypotesen tar hensyn til. Behold de øvrige forholdene så langt forsøksdesignet tillater det. Bruk [arbeidsflyten](WORKFLOW.md) og registrer kontrakten før kjøring.

Undersøk ny informasjon eller en ny mekanisme fremfor å variere navn, vekter og terskler på allerede undersøkte resultater. En ny dataversjon eller policy trenger en tilpasset benchmarkkjøring, og allerede inspiserte sesonger skal fortsatt omtales som utviklings-/rapporteringsdata.

## Fast avslutning av en arbeidsøkt

Noter forsøks-ID, faktisk status, resultat eller årsak til at det står stille, filene som dokumenterer dette, og én konkret neste handling. Registrer også feil og avviste hypoteser. Oppdater statusoversikten; ikke kopier hele data- eller kodegrunnlaget til enda en arbeidsmappe.
