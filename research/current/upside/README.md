# Oppside og beslutningsrelevant læring

Kjørt 6. oktober 2026. **Ingen av de fire nye kandidatene forbedret gjennomsnittlig sluttscore mot 50/50 Ridge + Extra Trees.** Noen blandinger fant flere store enkeltprestasjoner, men denne forbedringen ga ikke bedre FPL-lag. Referansen beholdes; ingen produksjonsmodell er byttet.

## Spørsmålet og forsøket

Vi trenger gode beslutninger blant aktuelle kjøp, startspillere og kapteiner, ikke lik prediksjonsnøyaktighet for alle spillere. Samtidig skal billige spillere og spillere med kort historikk kunne oppdages. Derfor testes både en egen oppsidemodell og en modell som legger større treningsvekt på beslutningsrelevante observasjoner. Ingen spillere velges ut etter navn eller fremtidig prestasjon.

[Protokollen](protocol.json) ble skrevet før dette forsøket ble trent og simulert. Det er ikke en ekstern forhåndsregistrering. Referansefamilien og alle seks evalueringssesongene var allerede studert; dette er utforskende retrospektiv forskning, uten urørt holdout.

Modellene bruker samme HGB-arkitektur og BASE+FX-variabler som eksisterende enkel HGB. Ingen ny xG-pakke innføres samtidig. Trening bruker bare tidligere sesonger og utfall tilgjengelige før første beslutningsfrist; modellene holdes faste gjennom evalueringssesongen.

| Kandidat | Definisjon |
|---|---|
| Ren oppside | HGB estimerer `E[Y * 1(Y >= 8)]` per kamp: hele poengbidraget fra store prestasjoner, null ellers |
| 25 % oppside | 75 % referanse + 25 % oppsidesignal |
| Relevansvektet | HGB estimerer vanlige poeng, men med større treningsvekt på tidligere poengform, minutter og kort historikk |
| 50 % relevansvektet | 50 % referanse + 50 % relevansvektet HGB |

Relevansvekten er `1 + 3 * clip(historic_m6,0,4)/4 * clip(minutes_m6,0,60)/60 + 1(n_history<12)`. Alle observasjoner har vekt minst 1; nye spillere får ekstra vekt. Vekten bruker bare før-kamp-variabler. Manglende form/minutter settes til null. Terskelen 8, vektene og blandingene ble ikke justert etter resultatene.

Oppsidesignalet er verken en kvantil, en sannsynlighet for 8+ eller forventet totalpoeng. I dobbeltrunder summeres forventede oppsidebidrag fra hver kamp; dette er ikke forventet bidrag fra en 8+-runde. Rangeringsevalueringen måler derimot faktisk 8+ i hele runden.

## Sluttscore

Seks sesonger, 2020/21–2025/26, fire nye modeller og to chipregimer gir **48 nye sesongforløp og 1632 beslutninger**. Samme opprinnelige GW1–4-startmodell og faktisk overlevert tropp, bank, kjøpspriser og gratisbytter. Hovedmodellen bestemmer GW5–38. Optimizer, spillerpool, regler og chipkalender er uendret. Tabellen viser gjennomsnittlig nettosesongpoeng etter treffkostnader; differanser er paret mot referansen.

| Modell | Uten chips | Differanse | Fast chipkalender | Differanse |
|---|---:|---:|---:|---:|
| Referanse: Ridge/Extra Trees 50/50 | 2155,7 | — | 2216,3 | — |
| Ren oppside | 1992,0 | −163,7 | 2082,2 | −134,2 |
| 25 % oppside | 2099,2 | −56,5 | 2181,3 | −35,0 |
| Relevansvektet | 2083,2 | −72,5 | 2116,2 | −100,2 |
| 50 % relevansvektet | 2109,0 | −46,7 | 2162,8 | −53,5 |

Mot samme algoritme uten relevansvekting (vanlig HGB) er relevansvektet HGB −0,7/−29,7 poeng. Dette isolerer vektingen bedre enn sammenligningen mot Ridge/Extra Trees. Blandingsforsøket har ikke tilsvarende blandinger med vanlig HGB som ekstra kontroll; hele differansen kan derfor ikke tilskrives oppsidemålet alene.

Tidsordnet modellvalg blant referansen og de fire nye kandidatene velger referansen i alle fire sesonger 2022/23–2025/26, i begge chipregimer. Gevinst: 0.

[Sesongvise resultater](results/season_results.csv), [sammendrag](results/model_summary.csv), [tidsordnet valg](results/chronological_selection.csv) og [paret bootstrap](results/season_bootstrap.csv) er vedlagt. Bootstrap bruker 50 000 resamplinger av seks sesongpar; intervallene er beskrivende og korrigerer ikke for tidligere modellleting. Bare seks sesonger gir stor usikkerhet.

## Fanger modellene flere store prestasjoner?

Andel faktisk 8+ blant de høyest rangerte spillerne, først gjennomsnitt per sesong og deretter lik vekt på seks sesonger:

| Modell | Alle, topp 20 | Billige, topp 10 | Kort historikk, topp 10 |
|---|---:|---:|---:|
| Referanse | 23,97 % | 16,89 % | 5,42 % |
| Ren oppside | 23,16 % | 15,11 % | 4,88 % |
| 25 % oppside | 24,44 % | 16,60 % | 5,37 % |
| Relevansvektet | 24,02 % | 16,25 % | 5,17 % |
| 50 % relevansvektet | 24,64 % | 16,35 % | 5,27 % |

Beste forbedring i topp-20-treff er omtrent **0,67 prosentpoeng**, men ingen kandidat forbedrer treffandelen blant billige spillere eller spillere med kort historikk. Blandingenes NDCG er også litt lavere enn referansens. Flere 8+-treff er ikke tilstrekkelig når resten av poengene, priser, posisjoner, kapteinsvalg og bytter påvirker sluttresultatet.

Billig defineres før fristen med lagget pris: keeper ≤4,5, forsvar ≤5,0, midtbane/angrep ≤6,0. Kort historikk betyr færre enn 12 observerte tidligere kamprader, inkludert nullminutter. Det er en proxy, ikke en identifikasjon av gjennombruddssesonger. Poolen omfatter spillere med kamp i aktuell runde etter samme kalenderproxy som referansen. Se [rangering per sesong](results/ranking_by_season.csv) og [sammendrag](results/ranking_summary.csv).

## Tolkning og begrensninger

Forsøket støtter å beholde referansen fremfor disse fire variantene. Det avviser ikke ideen om beslutningsrettet læring generelt.

- Ren oppside ignorerer poeng fra prestasjoner under 8. For vanlig forventet sesongpoeng teller også disse poengene. Dersom målet er en gitt rank eller sannsynlighet for å vinne, må et slikt risikomål defineres separat.
- Oppsidescoren har lavere skala enn forventet totalpoeng, mens byttetrekk og friksjon er uendret. Ren oppside tar i snitt bare 8,0/4,7 treffpoeng mot referansens 20,7/23,3. Resultatet gjelder denne konkrete beslutningsregelen, ikke alle måter å bruke oppside på.
- Ingen separat kapteinsablasjon er kjørt. Observerte kapteinsresultater inkluderer ulike tropper og kan ikke isolere effekten av et kapteinssignal.
- Datagrunnlaget bruker historiske poeng med moderne FT-/chipregler, laggede prisproxyer, ufullstendig skade-/registreringshistorikk og endelig kamptildeling i aktuell GW som kjent før frist. Resultatene er ikke faktiske historiske rangeringer.
- Modellene er sesongfrosne. Respons på gjennombrudd skjer via oppdaterte historikkvariabler, ikke løpende retrening.

En eventuell neste oppsidetest bør først forbedre før-frist-signaler for minutter, rolle, straffer/dødballer og xG/xA, og deretter teste oppside isolert for kaptein eller som tillegg til kalibrert forventet totalpoeng. Vekter bør velges kun på eldre data, og gevinst må måles i sesongpoeng i tillegg til topplistetreff.

## Reproduksjon og kontroller

Fra repositoryroten, med miljøet fra rot-README:

```bash
python scripts/prepare_data.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/upside/run.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/upside/summarize.py
```

Dette bruker de lagrede prognosene og beslutningssporene. For å kjøre simuleringene på nytt med samme kode/prognoser: slett bare `research/current/upside/results/trace_*.json.gz` i en separat arbeidskopi før `run.py`. For full retrening brukes `build.py` før `run.py`; ved endrede kode-/inputfingeravtrykk må både gamle spor og `run_manifest.json` fjernes i en ny forsøkskopi. Bevar dette forsøket som referanse. Ikke bland gamle spor med nye modeller.

`models.py` definerer mål/vekter; `features.py` bygger før-frist-variabler; `build.py` trener; `run.py` simulerer; `summarize.py` kontrollerer og rapporterer. Prognoser, 48 komprimerte beslutningsspor og kilde-/inputfingeravtrykk ligger i `results/` uten ZIP eller LFS.

[Kontrollrapport](results/checks.json): identisk starttilstand, poengregnskap og tidsgrenser godkjent; kontroll-HGB avviker **0,0** fra tidligere prognoser i alle seks sesonger. De nye beslutningene har optimal solverstatus. En utfallsblindhetstest av to modeller i én beslutningsrunde er bestått; den er ikke et fullstendig bevis mot alle former for lekkasje. 156 eksisterende tester og tre nye mål-/vekt-tester bestått lokalt. GitHub CI-status er ikke verifisert.
