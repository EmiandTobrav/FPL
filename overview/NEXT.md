# Utgangspunkt og neste steg for FPL modellen

**Oppdatert 26. oktober 2026:** [Utvidede datasett, korrigert kalender og valgt komponentmodell med fem runders planlegging](../releases/2026-10-26/README.md). Historisk gevinst +104 / −13 / +37 mot samme-kalender-kontroll. Selve observasjons- og modelltabellene følger med; full live-/modellreplay krever fortsatt arbeidsarkivet. Eldre daterte statusavsnitt nedenfor gjelder sitt opprinnelige tidspunkt.

Bruk `fpl_2026_27_best_effort_v1` som poeng- og datagrunnlag og `fpl_model_pipeline_v1` som modellinngang. Den aktive sammenligningsfamilien er `fixture_full_h3_adaptive_tc_harmonized_causal_v1`. Ingen ny produksjonsmodell er valgt. Se [prosjektregisteret](PROJECT.json) for konkrete filer og kontrakter.

## Hva vi allerede vet

- Bedre prognosefeil alene ga ikke en bedre manager i simulatorfasen. Todelt modell ble valgt for RMSE, mens den tilpassede benchmarken vant managerens utviklingssnitt.
- De første direkte kamp- og spilletidsmodellene ga positive utviklingssnitt i S2, men tapte i enkelte sesonger og bestod ikke oppgraderingskravet.
- Faste chips, vektet tap, ny deltakelseshistorikk og fast prognoseblanding er gjennomført. Ingen av disse bestod sine oppgraderingskrav. Ikke kjør dem om igjen uendret.
- Horisont, prognose, chipvalg, åpningslag og løserressurser virker sammen. Sammenligninger skal derfor beholde eksplisitte kontrakter og kontrollspor.
- Datakvalitet og historisk tilgjengelighet har fortsatt proxyer og estimater. Nye kildefunn må vurderes separat før de blir features eller poengmål.

Resultater og dokumentasjon finnes i [metodeoversikten](METHODS.md) og [arbeidsstatusen](STATUS.md).

## Første handling ved neste arbeidsøkt

Forsøket med eksplisitt H2-planlegging uten reservekostnader er fullført og etterkontrollert. H2 uten reserve: -69.3 mot samme planlegger med reserve og -55.7 mot historisk benchmark i sesongsnitt. Pilotkrav ikke bestått; benchmark beholdes.

Les [resultatet](../reports/explicit_planning_2026_10_15/RESULTATER.md) og [metodebegrensningene](../reports/explicit_planning_2026_10_15/README.md). Dette er en planlegger, ikke en ny trent sesongagent. Neste hypotese bør gi lengre fremtidsforløp eller validert verdi av gjenværende tilstand, med netto sesongpoeng som mål. Ikke erstatt reservekostnader med nye håndjusterte konstanter. Ingen prosess kjører videre, og ingen uendret konfigurasjon skal gjentas.

Det forrige sesonglange læringsforsøket er bevart med sitt negative resultat. Første TC/BB-pilot er bevart med +53 og +41 mot benchmark. Alle tre metodene har egne kontrakter og resultater i [metodeoversikten](METHODS.md).

## Nye forsøk

Velg én dokumentert mekanisme. Frys input, metode, kontroll, suksesskrav og ressursgrenser før kjøring. Bruk [arbeidsflyten](WORKFLOW.md) og registeret for å unngå dobbeltarbeid. Oppdater forsøksresultat og status også ved negative funn.
