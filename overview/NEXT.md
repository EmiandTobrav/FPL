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

Det sesonglange forsøket `season-manager-20261015-v1` er fullført: fire nye treningsforløp, fire evalueringsforløp og 304 etterkontrollerte runder. Modellen velger blant komplette lovlige handlinger for alle chips, bytter/roll, startellever, benk og kaptein. Les [resultatet](../reports/season_manager_2026_10_15/RESULTATER.md), sammenligningen med samme forslag uten læring og [etterkontrollen](../reports/season_manager_2026_10_15/audit.json).

Episodisk manager ga -243.0 netto poeng mot benchmark, -290.0 mot chip-policyen og -297.5 mot samme forslag uten læring i sesongsnitt. Pilotkravet ikke bestått; dagens benchmark beholdes.

Dagens benchmark er beholdt. Det er ikke noen pågående prosess å videreføre. Ikke gjenta denne konfigurasjonen uendret eller gjør ubundet parameterjakt på de samme resultatene. En videre hypotese bør begrunnes i feilene i handlingsrangeringen, hvor få uavhengige sesonger som finnes og hvordan sesonglange belønninger kan anslås med mindre støy. Evalueringskontrakten må fryses før den nye prøven.

Den første TC/BB-piloten ga +53 og +41 poeng, +47 i snitt mot benchmark. Den er en egen metode med eget resultat og skal fortsatt være synlig som sammenligningsgrunnlag. Den eldre H8-kjøringen stoppet med feil 14. oktober, dokumentert i sin hendelseslogg; ingen automatisk gjenstart er godkjent gjennom disse nye, separate forsøkene.

## Når et nytt forsøk er berettiget

Velg én mekanisme fra dokumenterte svakheter i eksisterende logger. Forklar hva som endres og hvilket tidligere negativt funn hypotesen tar hensyn til. Behold de øvrige forholdene så langt forsøksdesignet tillater det. Bruk [arbeidsflyten](WORKFLOW.md) og registrer kontrakten før kjøring.

Undersøk ny informasjon eller en ny mekanisme fremfor å variere navn, vekter og terskler på allerede undersøkte resultater. En ny dataversjon eller policy trenger en tilpasset benchmarkkjøring, og allerede inspiserte sesonger skal fortsatt omtales som utviklings-/rapporteringsdata.

## Fast avslutning av en arbeidsøkt

Noter forsøks-ID, faktisk status, resultat eller årsak til at det står stille, filene som dokumenterer dette, og én konkret neste handling. Registrer også feil og avviste hypoteser. Oppdater statusoversikten; ikke kopier hele data- eller kodegrunnlaget til enda en arbeidsmappe.
