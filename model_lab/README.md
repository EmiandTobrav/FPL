# Felles rammeverk for modelltesting og simulering

Bruk én forsøksfil og én kjørekommando. Nye modeller bruker samme data, tidskontroll, resultatformat og simulator. Start med en liten kontroll; utvid først når koblingene fungerer. Rammeverket velger ikke en ny produksjonsmodell automatisk.

## Vanlig bruk

Installer avhengighetene fra `model_lab/requirements.txt` i et eget Python 3.12-miljø. Kjør fra prosjektets hovedmappe.

```sh
python -m model_lab init experiments/min_modell.json --model ridge
python -m model_lab run experiments/min_modell.json
```

Første kommando lager en liten test med to runder og maksimalt fire modelltilpasninger. Andre kommando kjører den og viser hvor resultatkortet ligger. Et nytt forsøk trenger normalt bare endringer i modell, parametere, features, sesonger og runder. Resten av kontrollene er felles.

Ridge, CatBoost og LightGBM bruker den eksisterende [modellpipelinen](../datasets/fpl_model_pipeline_v1/README.txt). En enkel gjennomsnittsmodell er en sanity-kontroll for prognosetesten. Den er **ikke** den primære FPL-managerbenchmarken.

Basisinstallasjonen dekker Ridge og simulatoren. For CatBoost eller LightGBM brukes `model_lab/requirements-models.txt` i stedet.

## Tre enkle trinn

| Trinn | Hva det svarer på | Inngang |
|---|---|---|
| Liten kontroll | Kan modellen trene, predikere og følge tidskontrakten? | `python -m model_lab run model_lab/examples/smoke.json` |
| Tidsordnet prognosetest | Blir prognosene bedre på de samme spillerne og tidsperiodene? | Samme forsøksfil med eksplisitt større rundeutvalg og fitbudsjett. |
| FPL-simulering | Gir prognosene bedre lovlige lagvalg og netto poeng under samme policy? | `python -m model_lab run model_lab/examples/simulation_smoke.json` |

Resultatkortet heter `REPORT.md`. Tall og kontroller ligger i `summary.json`, prognoser eller beslutningslogger og en fullføringskvittering. Alle filer ligger under `lab_results/`; store datasett kopieres ikke per prognoseforsøk.

Den medfølgende simuleringen har én runde med allerede låste prognoser fra 2023/24. Den verifiserer integrasjonen med regelmotor og ressursstyrt policy, og er ingen ny sesongtest eller dokumentasjon på en bedre modell.

## Nye modellfamilier

For en modell som ikke finnes i pipelinen, lag en liten adapterfil med denne funksjonen:

```python
def fit_predict(X_train, y_train, X_predict, config):
    model = build_model(config)
    model.fit(X_train, y_train)
    return model.predict(X_predict)
```

Sett `backend` til `custom`, oppgi filen i `adapter`, og bind den med hash i `input_hashes`. Modellen får bare de valgte featurekolonnene i prediksjonsgrunnlaget. Den får ingen fremtidige målverdier fra rammeverket. Egne transformasjoner må læres fra treningsdelen. Bruk et eget versjonert adapter og bind også eventuelle egne hjelpefiler.

## Det som håndteres automatisk

- Trening bruker bare rader med prognosetid og hele målhorisontens tilgjengelighet strengt før ny prognose. H1, H3 og H6 er støttet. Fremtidige mål imputeres ikke.
- Modeller sammenlignes på samme observerte prognoserader. Utvalget er prognosediagnostikk og brukes ikke som en historisk kjøpbar spillerpool i simulatoren.
- Ferdige prognosefolder kan gjenbrukes på tvers av forsøksfiler når modell, inputhash, origin, horisont, historikk, implementasjon og kjøremiljø er uendret. Endret visningsnavn alene krever ikke ny trening. En endring i rapportkode krever ikke nye prognosefolder.
- Fullførte kjøringer gjenbrukes etter kontroll av utdatahash. En påbegynt eller feilet kjøring blir ikke automatisk kjørt om igjen. En eksplisitt ny `cache_attempt` gir et nytt cacheforsøk ved dokumentert behov; tidligere feil beholdes.
- Simulatoren gjenbruker den eksisterende regelmotoren og den kontrollerte nodebudsjett-policyen. De opprinnelige filene er bevart; eksakte kildekopier og hash ligger under `vendor/fpl_rules_v1`.
- Lagbudsjett, posisjoner, klubbgrense, kaptein, benk, autosubstitusjoner, overgangskostnader og chips behandles av samme motor for alle modeller. Beslutningen låses før utfall leses. Ukjente valgte utfall stopper forsøket.
- Delvise simuleringer merkes som delvise. Netto poeng fra én runde blir aldri presentert som en sesongscore. Verken et positivt prognosemål eller en enkelt simulering endrer benchmark.

Fitbudsjettet begrenser antall planlagte modelltilpasninger. Det er ikke en hard tids- eller minnegrense for vilkårlig ny modellkode. Simulatoren begrenser noder per løserkall og antall kall per beslutning og registrerer faktisk bruk. Like grenser betyr ikke lik total regnetid.

## Fra nye prognoser til simulering

Simulatoren bruker et lite bundle med låst spillerpool, features, prognoser og separat oppgjørsgrunnlag. Alle metoder får identisk informasjon. Benchmark må kjøres under samme beslutningspolicy og ressurser; gamle sesongsummer gjenbrukes ikke som kontroll.

Eksisterende fryst forecast-cache kan pakkes uten å trene på nytt:

```sh
python -m model_lab export-bundle --cache reports/fpl_improvement_2026_10_14/cache --season 2023-24 --rounds 1 2 --models fixture_full_h3_adaptive_tc_harmonized_causal_v1 fixture_direct_v1 --output lab_results/min_bundle
```

`predict-bundle` trener en modell fra tillatt historikk og predikerer den felles, fryste spillerpoolen ved hvert eksisterende origin:

```sh
python -m model_lab predict-bundle model_lab/examples/bundle_forecast.json --bundle model_lab/examples/simulation_bundle --output lab_results/bundle_med_ny_modell
```

Den innebygde overgangen fra H1 til flere fremtidige runder krever eksplisitt `trajectory=repeat_h1_diagnostic`. Dette gjentar en prognose laget ved dagens origin; den leser ikke fremtidige featurefiler. Det er en synlig diagnostisk proxy, ikke en ny validert kampavhengig prognosemodell. En ny kalibrert prognosebane trenger et eget kontrollert adapterforsøk.

Lag deretter en liten simuleringsfil og kjør den:

```sh
python -m model_lab simulation-spec --bundle lab_results/bundle_med_ny_modell --models fixture_full_h3_adaptive_tc_harmonized_causal_v1 ridge_trial --output experiments/min_simulering.json
python -m model_lab run experiments/min_simulering.json
```

Bundle skal starte i GW1 og ha sammenhengende runder for én sesong. Alle valgte spilleres utfall må være kjent. Offisielle blankrunder kan bare behandles gjennom den eksplisitte, kvalifiserte blankkontrakten. Eksemplet bruker begrensede forskningsproxyer for historisk tilgjengelighet og spillerpool, i tråd med de tidligere simuleringene.

## Når kontrollen blir et forskningsforsøk

`init` og de medfølgende eksemplene er merket `framework_validation`. De etablerer ingen ny hypotese eller oppgraderingspåstand. Når et resultat skal brukes til modellvalg, bruk [arbeidsflyten](../overview/WORKFLOW.md), registrer hypotesen og bind kjøringen med `purpose=registered_research`, `proposal` og `proposal_fingerprint`.

Forsøket må følge den registrerte input-, sesong-, tids- og ressurskontrakten. En simuleringsregistrering binder også bundle og den konkrete beslutningspolicyen. Etter kjøring kobles resultat og filhash til samme forsøks-ID. Registrering gir ikke lov til å utvide en gammel kampanjes konfigurasjonstak. Den eksisterende H8-kampanjen er urørt.

For prognoseforsøk binder registreringens `model_parameters` kandidatens `backend`, `seed` og `parameters`. `decision_policy` binder `stage=forecast`, `horizon`, `reference`, `rounds` og `window_days`. Ressurskontrakten oppgir `maximum_fits`. Simulatorforsøk oppgir tilsvarende `maximum_decisions` og policy-/node-/kallgrensene. Dette fylles når et forskningsforsøk registreres; de små valideringseksemplene trenger ikke denne ekstra registreringen.

## Tester

```sh
python -m unittest discover -s model_lab/tests -v
```

Tester dekker blant annet hele målhorisontens tilgjengelighet, ingen fremtidige utfall i prediksjonsinput, endrede utfall uten endret lagvalg, manglende utfall, fremtidig metadata, avbrutte kjøringer, korrupte cachefiler og de eksisterende håndregnede FPL-regeltestene.
