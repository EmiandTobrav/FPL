# Prøv en begrenset demonstrasjon

[Startside](../README.md) · [Full Model Lab-guide](../model_lab/README.md) · [Hva følger med?](PUBLICATION_SCOPE.md)

Demoen bruker filer som allerede følger med repoet. Den trenger ingen FPL-innlogging, API-nøkkel, modell-API eller separat lokalt forskningsarkiv. Internett trengs for kloning og installasjon. Selve demoen kjører lokalt. Beregn noen minutter til oppsett; kjøretid avhenger av maskinen.

## 1. Hent repoet og installer

Bruk **Python 3.12**. Fra en terminal på macOS/Linux:

```sh
git clone --depth 1 https://github.com/EmiandTobrav/FPL.git
cd FPL
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r model_lab/requirements.txt
```

På Windows brukes `py -3.12 -m venv .venv` og `.venv\Scripts\Activate.ps1` i PowerShell. Deretter brukes de samme `python`-kommandoene. Windows-oppskriften er ikke kjørt i kontrollen nedenfor.

Denne installasjonen dekker den lille Ridge-demoen og simulatoren. Du trenger ikke installere hele den eldre kodebasen med `pip install .` eller kjøre `scripts/prepare_data.py` for disse to eksemplene. CatBoost/LightGBM og eldre tester har egne avhengigheter; se [Model Lab](../model_lab/README.md) og [bidragsguiden](../CONTRIBUTING.md).

## 2. Kjør to prognoserunder

Kjør fra repoets rot:

```sh
python -m model_lab run model_lab/examples/smoke.json
```

Dette sammenligner Ridge med en enkel gjennomsnittsmodell i runde 1–2 av 2023/24, med høyst fire modelltilpasninger. Terminalen viser stien til `REPORT.md` under `lab_results/runs/`. Rapporten viser RMSE og MAE (prognosefeil; lavere er bedre) for begge modeller. Gjennomsnittsmodellen er en teknisk kontroll, ikke prosjektets managerbenchmark.

## 3. Kjør én simulert runde

```sh
python -m model_lab run model_lab/examples/simulation_smoke.json
```

Dette bruker en liten medfølgende pakke med låste prognoser og oppgjørsdata fra én runde i 2023/24. To metoder kjøres med maksimalt to beslutninger totalt, 16 noder per løserkall og 40 kall per beslutning. Rapporten ligger under `lab_results/simulations/` og er merket som en delvis simulering. Den viser netto poeng og ressursbruk; den er ikke en sesongscore eller ny dokumentasjon på modellgevinst.

Resultater opprettes under `lab_results/`, som er utelatt fra Git. Tidligere forskningsrapporter endres ikke. En identisk fullført kjøring kan gjenbrukes. Hvis en kjøring avbrytes, behold feilen og bruk en ny utdatamappe for en ny funksjonsprøve, for eksempel:

```sh
python -m model_lab run model_lab/examples/smoke.json --output lab_results/demo_retry_01
```

## 4. Kontroller rammeverket og lagrede bevis

```sh
python -m unittest discover -s model_lab/tests
python reports/learned_manager_2026_10_15/verify_saved.py
python reports/season_manager_2026_10_15/verify_saved.py
python reports/explicit_planning_2026_10_15/verify_saved.py
```

De tre siste kommandoene kontrollerer publiserte filers identitet mot resultatbundne hasher, også i arkiver. De trener ikke modellene på nytt og gjentar ikke full historisk simulering.

## Kontrollert 22. oktober 2026

Installasjonen ble prøvd i et nytt Python 3.12-miljø på macOS/Apple Silicon. Kjøringene brukte en ren eksport av Git-treet `53dbafbcc22179e5b5343a7730a96c25f04a8825`, identisk med GitHub main ved kontrollen. Ingen filer fra det separate arbeidsarkivet var med. Selve nettverkskloningen ble ikke kjørt på nytt.

| Kontroll | Resultat |
|---|---|
| Installasjon av `model_lab/requirements.txt` | Bestått med de oppgitte versjonene |
| Prognosedemo fra tom resultatmappe | Bestått; omtrent 27 sekunder på kontrollmaskinen |
| Simuleringsdemo fra tom resultatmappe | Bestått; omtrent 2 sekunder |
| Model Lab-tester | 52 bestått |
| Lært chip-policy, lagrede bevis | 483 filer verifisert |
| Sesongmanager, lagrede bevis | 641 filer verifisert |
| Eksplisitt planlegging, lagrede bevis | 471 filer verifisert |

Disse kontrollene dekker den beskrevne demoen og publiserte bevisfiler. Hele den eldre testsuiten og full replay av forskningsforsøkene ble ikke kjørt. De opprinnelige forsøksresultatene er uendret.
