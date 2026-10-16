# Git struktur og publiseringsomfang

Dette repoet har én felles startside og én katalog over datasett, metoder og funn. Hovedgrenen er main. Oppdateringen er forberedt fra main 6730554e uten å slå sammen rekonstruksjonsgrener eller endre fryste resultater.

## Roller

| Område | Rolle |
|---|---|
| datasets | Tre publiserte trinn: rekonstruert datasett, featuregrunnlag og modellpipeline. Ingen full datakopi per eksperiment. |
| overview | Aktive innganger, metodekatalog, arbeidshistorikk og registreringsmaler. |
| reports med dato | Utvalgte nyere resultater og kildekvitteringer. |
| research/current og gammel src | Bevart eldre forskning. Navnet current er historisk og betyr ikke at alle undermapper er aktive. |
| scripts/research.py | Lesende navigasjon og eksklusiv registrering av nye forsøkskontrakter og resultater. |
| scripts/prepare_data.py | Bevart eldre klargjøringsløp; gjelder den historiske pipelinen. |

## Hva som kan gjøres fra denne publikasjonen

De tre datasettene og modellpipelinen er komplette filpakker med innlesere, tabeller og schema. Metoderegisteret viser historiske og nyere funn uten å kopiere alle arbeidsmapper. Nye foldbaserte modellforsøk kan bygges fra pipelinepakken med dens oppgitte avhengigheter.

Den avanserte FPL-simulatoren og den avsluttede H8-kjøringen er indeksert gjennom status, protokoller og resultatuttrekk. Full kjøring, uavhengig replay av alle revisjoner eller gjenopptakelse krever det separate lokale arbeidsarkivet. Et sammendrag merket completed er ingen garanti for at alle refererte bevisfiler er inkludert i denne publikasjonen. Rekonstruksjonens CURRENT er lagret som et kildeuttrekk under overview/evidence og er ikke en operativ rekonstruksjonsinngang her.

Store historiske snapshots, videoer, bilder fra kildearbeid, ZIP-eksporter og regenererbare arbeidsmapper inngår ikke i denne oppdateringen. Dette er en publikasjon med eksplisitt omfang, ikke en full sikkerhetskopi av lokal hovedmappe. Tidligere Git-historikk og grener er bevart.

## Regler for nye endringer

Bruk én avgrenset gren og en pull request per dataversjon eller metodehypotese. Behold baselinefiler uendret. Oppdater prosjektregisteret bare når et nytt utgangspunkt er dokumentert. Loggfør forkastede metoder med årsak, og bind resultatene til inputhash og sammenligningskontrakt. Registrering erstatter ikke kampanjens tak på antall forsøk.

Samme input og parametere skal gjenbrukes via dokumenterte filer, ikke enda en datasettkopi. Cache er lokalt arbeidsmateriale inntil en avgrenset utgivelse trenger den for gjentakelse; da publiseres den eksplisitt med manifest. Ikke bruk git add av hele arbeidsmappen uten å kontrollere filutvalget.

Genererte inventarer er lokale navigasjonshjelpemidler. De oppdaterer ikke automatisk en fryst dataversjon, og diskstørrelsen i det lokale prosjektet gjelder ikke denne Git-klonen.

## Felles testrammeverk

model_lab er en portabel inngang for små prognoseprøver og lovlig FPL-simulering fra eksplisitt låste input. Den gjenbruker pipelinepakken og eksakte kopier av den eksisterende regel-/policykoden. To små eksempler kan kjøres direkte; større studier må bindes til registrerte kontrakter og tilstrekkelige inputbundles. Full replay eller gjenopptakelse av den tidligere H8-kampanjen inngår fortsatt ikke i denne publikasjonen.

Rammeverket er kontrollert med 40 tester, prognosegjenbruk og en liten simulering som gjenskaper tidligere loggede handlinger. Se model_lab/VALIDATION.json. En avgrenset lært TC/BB-reserve er nå testet; full managerlæring og vinnermål er videre forskning.

## Lært managerpilot, 15. oktober

`reports/learned_manager_2026_10_15` publiserer policykode, fryst originalkjører, eksplisitt mekanisk retting, protokoll, treningsrader/koeffisienter, maskinell etterkontroll og sesongresultater. Alle låste rundebeslutninger og oppgjør er bevart i `round_evidence.tar.gz`; seks sammendrag ligger direkte under `runs/`. Arkivet unngår hundrevis av store rålogger i diffen. `result.json` binder hver enkelt originalfil med SHA-256.

Protokoll og registrerte resultater er byteidentiske med lokalt arkiv; historiske stier under `FPL_training_dataset/` er derfor beholdt der. Full kjøring av `audit.py` eller `resume_v002.py` krever de fryste forecast-cachefilene, lærerloggene og de eldre oppgjørshjelperne fra lokalt arkiv, på de opprinnelige stiene. De store inputene er ikke kopiert inn i Git. Det er mulig å kontrollere det publiserte resultatmaterialets hasher og policytestene uten disse inputene. En bestått slik kontroll erstatter ikke full input-/regelreplay.

Publiserte resultater er ikke en automatisk oppgradering av benchmark. `failure.json` dokumenterer den bevarte oppsummeringsfeilen; faktisk fullføring og audit ligger i egne filer.

## Sesonglang managerlæring

`reports/season_manager_2026_10_15` inneholder den separate episodiske managerhypotesen, alle fire chips og komplett handlingsrangering. Kontroll med samme forslagsregler uten læring skiller læringen fra endret handlingsutvalg. Trening og evaluering har egne kvitteringer. Ingen automatisk benchmarkoppgradering.

Fryste modeller, treningsrader, åtte sammendrag, protokoll, kode og etterkontroll er publisert. Alle opprinnelige rundeavgjørelser, forslagssett og utfall er bevart byte for byte i `episode_evidence.tar.gz`. `verify_saved.py` kontrollerer hver resultatbundet fil direkte eller i arkivet. Full simulatorreplay trenger fortsatt den lokale prognosecachen, gamle lærerlogger og oppgjørshjelpere. Komprimert publisering kopierer ikke disse store inputene.

De seks treningskvitteringene med gjentatte radprefikser er bevart samlet i `training_evidence.tar.gz`, og de to fryste evalueringsmodellene ligger direkte i `models/`. Dette holder gjennomgangen kort uten å endre de resultatbundne originalfilene. `verify_saved.py` kontrollerer begge arkivene.
