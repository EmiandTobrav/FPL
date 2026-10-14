Modellpipeline – klargjøring ferdig

97 inngangsfeatures eller 21 referansefeatures. Raw featurefiler er identiske med modellgrunnlaget fra steg 1–2. Ingen globalt imputerte/skalerte tabeller opprettes: behandlingen læres separat fra treningshistorikken ved hver prognose.

Ridge: median fra treningsdelen, null kun ved fullstendig manglende treningskolonne, alltid med eget mangelflagg; StandardScaler på numeriske verdier; one-hot lag/posisjon med egne kategorier for manglende og ukjente verdier.
CatBoost: numeriske NaN beholdes; kategorier konverteres til strenger og egne manglende/ukjente verdier.
LightGBM: numeriske NaN beholdes; pandas-kategorier fastsettes fra treningsdelen. Null er en faktisk verdi, ikke et mangelsignal.

Alle profiler har mangelflagg for samtlige numeriske features, også hvis mangelen først oppstår ved prediksjon. Nullpoeng, benking, negative poeng og store utfall beholdes. Kvalitetsflagg brukes ikke som features. Manglende targets brukes ikke til trening; de hindrer ikke at prognoser lages.

Bruk:
from loader import load_rows
from pipeline import fit_fold, predict_rows
rows, schema = load_rows()
period = rows[(rows.season == "2024-25") & (rows["round"] == 1)]
fitted, audit = fit_fold(rows, schema, period.forecast_at.iloc[0], model="ridge", feature_set="extended", horizon=1)
predictions = predict_rows(fitted, period, schema, "extended")

Lag en NY fit_fold ved neste valgte oppdatering. Samme frist- og tilgjengelighetsregel gjelder H1/H3/H6. Ingen tidlig stopping eller parametervalg på rundene som evalueres. Modellene bruker kvadratisk tap som startpunkt; fabrikkparametrene er ikke tunet.

Installer requirements.txt i et separat Python-miljø. På macOS krever LightGBM OpenMP. Kontrollen brukte libomp.dylib fra scikit-learn-hjulets .dylibs-mappe via DYLD_LIBRARY_PATH. Ingen global programvareinstallasjon eller endring av systembiblioteker ble gjort.

Kontroll: sju målrettede tester, 26 funksjonskontroller med faktiske data fra to tidsoppsett, to prognosestarter og begge featuresett. Funksjonskontrollene trente små testmodeller; de er ikke en full walk-forward-sammenligning og rangerer ikke modellene. Ikke bruk disse testmodellene som valgt produksjonsmodell.

Tidsreglene er fortsatt proxyer; historiske frister, publiseringsvintager og kjøpbar tropp er ikke fullt rekonstruert. Kontroller med kvalitetsfiltrering utføres separat ved modellstudien.
