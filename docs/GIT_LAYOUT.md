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

Den avanserte FPL-simulatoren og den pågående H8-kampanjen er indeksert gjennom status, protokoller og resultatuttrekk. Full kjøring, uavhengig replay av alle revisjoner eller gjenopptakelse krever det separate lokale arbeidsarkivet. Et sammendrag merket completed er ingen garanti for at alle refererte bevisfiler er inkludert i denne publikasjonen. Rekonstruksjonens CURRENT er lagret som et kildeuttrekk under overview/evidence og er ikke en operativ rekonstruksjonsinngang her.

Store historiske snapshots, videoer, bilder fra kildearbeid, ZIP-eksporter og regenererbare arbeidsmapper inngår ikke i denne oppdateringen. Dette er en publikasjon med eksplisitt omfang, ikke en full sikkerhetskopi av lokal hovedmappe. Tidligere Git-historikk og grener er bevart.

## Regler for nye endringer

Bruk én avgrenset gren og en pull request per dataversjon eller metodehypotese. Behold baselinefiler uendret. Oppdater prosjektregisteret bare når et nytt utgangspunkt er dokumentert. Loggfør forkastede metoder med årsak, og bind resultatene til inputhash og sammenligningskontrakt. Registrering erstatter ikke kampanjens tak på antall forsøk.

Samme input og parametere skal gjenbrukes via dokumenterte filer, ikke enda en datasettkopi. Cache er lokalt arbeidsmateriale inntil en avgrenset utgivelse trenger den for gjentakelse; da publiseres den eksplisitt med manifest. Ikke bruk git add av hele arbeidsmappen uten å kontrollere filutvalget.

Genererte inventarer er lokale navigasjonshjelpemidler. De oppdaterer ikke automatisk en fryst dataversjon, og diskstørrelsen i det lokale prosjektet gjelder ikke denne Git-klonen.
