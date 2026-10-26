# Felles modellgrunnlag, 26. oktober 2026

Dette er selve tabellene fra det kvalifiserte kalendergrunnlaget, eksportert til CSV/XZ slik at de kan leses uten Python-pickle eller Git LFS.

| Tabell | Rader | Formål |
|---|---:|---|
| `training.csv.xz` | 135441 | Historisk trening, 2020/21–2025/26; tilgjengelige utfall og eksplisitt treningsstatus |
| `pool_features.csv.xz` | 111562 | Faste spiller-/rundepooler, 2022/23–2025/26; metadata, lærerstatus og åtte framoverskuende kalenderfelt |

`schema.json` beskriver 341 forskningsfelt. `active325_schema.json` er den valgte operative listen med 325 felt; de 16 kvalifiserte xG/xA-feltene er **ikke** aktivert. Kolonner med mål/utfall, lærerstatus og metadata er ikke frie prediktorer. Bruk listen i skjemaet, ikke alle kolonner som modellinput. `tables.json` bevarer kildetyper, rader og filhasher.

Været er observert, retrospektivt kampvær. Prognosemodellen bruker bare lagget vær fra tidligere kamper; faktisk vær i målkampen er utelatt. Historiske kilde-/statistikktider har dokumenterte proxybegrensninger. Nye kalenderopptak er valgt fra før fristene, ikke fylt bakover fra sluttkalenderen. Ukjente verdier er tomme, aldri automatisk null.

Eksempel med pandas: last `loader.py` med importlib og kall `load_table('training')`. Funksjonen kontrollerer filhash og gjenoppretter numeriske typer og datoer. Full modell-/sesongreplay krever også lokale kilde-, lærer- og modellarkiver; disse to tabellene alene er ikke hele replaypakken.
