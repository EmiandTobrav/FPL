# Oppside som variabel og avgrenset kapteinssignal

Forsøk 6. oktober 2026. Dette følger opp oppsidemodellen i `../upside/`. Formålet er å teste om signalet tilfører verdi når hovedmodellen fortsatt lærer alle poeng, og når oppside bare påvirker kapteinsvalget blant nesten like alternativer.

## Fast forsøksoppsett

[Protokollen](protocol.json) ble skrevet før treningen og resultatene. Ingen terskler eller blandingsvekter justeres etter resultatene. Alle evalueringssesongene er allerede studert; dette er ikke en urørt holdout.

Oppsidevariabelen er estimert `E[Y * 1(Y >= 8)]` per kamp, klippet til minst null. Det er samme signal som forrige forsøk, ikke en ny 8+-sannsynlighetsmodell. Hovedmodellene er HGB med samme hyperparametre og BASE+FX-variabler; målvariabelen er alle faktiske poeng.

For hver historiske sesong lages oppsidevariabelen med en modell trent bare på tidligere sesonger og utfall tilgjengelige før sesongens første frist. Hovedmodellene trenes deretter på eldre sesongers slike tidsriktige prognoser. Ved evaluering trenes oppsidemodellen på all tilgjengelig eldre historikk; evalueringssesongens utfall inngår aldri i treningen. Før-frist-historikk oppdateres mellom rundene, men modellene er sesongfrosne.

2019/20 brukes som oppvarming for oppsidemodellen, og 2020/21 blir første sesong med treningsrader for hovedmodellene. Vi evaluerer derfor fem sesonger, 2021/22–2025/26. Begge hovedmodellene får nøyaktig samme treningsrader, også kontrollen uten oppside. Denne kontrollen er ikke identisk med tidligere HGB, som også trente på 2019/20.

| Modell | Definisjon |
|---|---|
| Matchet kontroll | HGB uten oppsidevariabel |
| Med oppsidevariabel | Samme HGB og treningsrader, én ekstra oppsidevariabel |
| Kontrollblanding | 50 % sterk referanse + 50 % matchet kontroll |
| Oppsideblanding | 50 % sterk referanse + 50 % HGB med oppsidevariabel |

Sterk referanse er fryst Ridge/Extra Trees 50/50. Alle fire modeller simuleres med samme GW1–4-overlevering og optimizer til GW38, både uten chips og med tidligere fast chipkalender: 40 nye sesongforløp.

Kapteinsregelen spilles separat på referansens 10 sesongforløp. Blant de opprinnelige startspillerne som ligger høyst 0,5 forventede poeng bak beste starter, velges høyest oppsidesignal. Like oppsidescorer brytes med høyest forventede poeng og deretter laveste spiller-ID. Ved kapteinsbytte blir tidligere kaptein visekaptein; ellers beholdes opprinnelig vise. Tropp, startellever, benk, bytter og chips er identiske. Oppgjøret bruker faktisk tilgjengelighet for visekapteinsfallback og riktig TC-multiplikator. GW1–4 endres ikke.

Ingen separat hard avgrensning av kjøpspool testes her. Vi tester én ekstra variabel og én kapteinsregel, ikke alle mulige oppsidesignaler eller filtergrenser.

## Resultater

**Ingen ny kandidat gir en robust forbedring over den sterke referansen. Referansen beholdes.**

Gjennomsnittlig nettosesongpoeng over de samme fem sesongene:

| Modell | Uten chips | Mot sterk referanse | Fast chipkalender | Mot sterk referanse |
|---|---:|---:|---:|---:|
| Sterk referanse | 2171,8 | — | 2234,2 | — |
| Matchet kontroll | 2128,8 | −43,0 | 2153,0 | −81,2 |
| Med oppsidevariabel | 2116,8 | −55,0 | 2166,6 | −67,6 |
| Kontrollblanding | 2133,6 | −38,2 | 2230,6 | −3,6 |
| Oppsideblanding | 2160,8 | −11,0 | 2196,6 | −37,6 |
| Bare kapteinsregel | 2166,8 | −5,0 | 2240,0 | +5,8 |

Den isolerte effekten av variabelen er **−12,0/+13,6** poeng mot samme hovedmodell uten variabelen, uten/med chips. I blandingen er effekten **+27,2/−34,0** mot den tilsvarende kontrollblandingen. Oppsideblandingen vinner over sin kontroll i 4/5 sesonger uten chips, men bare 1/5 med chips. Alle fire parete bootstrapintervallene for disse featureeffektene inkluderer null. Dette gir ikke grunnlag for å velge modellen generelt eller tilpasse en ny chipavhengig regel etter fasit.

Kapteinsregelen endrer 22 av 170 valg uten chips og 29 av 170 med chips. Gjennomsnittlig gevinst er −5,0/+5,8 poeng; den vinner i 2/5 og 3/5 sesonger. Beskrivende 95 %-intervaller er henholdsvis [−17,4; 8,4] og [−12,8; 24,4]. En liten positiv middelverdi i ett regime er ikke robust dokumentasjon på forbedring.

### Rangering og oppdagelse

Andel faktisk 8+ i rundene blant topp 20 totalt og topp 10 innen billige spillere/kort historikk, med lik vekt på hver sesong:

| Modell | Alle, topp 20 | Billige, topp 10 | Kort historikk, topp 10 |
|---|---:|---:|---:|
| Sterk referanse | 23,76 % | 16,57 % | 5,27 % |
| Matchet kontroll | 23,70 % | 16,03 % | 4,97 % |
| Med oppsidevariabel | 24,53 % | 16,26 % | 5,32 % |
| Kontrollblanding | 24,15 % | 15,79 % | 5,14 % |
| Oppsideblanding | 24,50 % | 16,20 % | 5,20 % |

Variabelen forbedrer disse treffandelene mot matchet kontroll, og ren HGB med oppside har også marginalt høyere treffandel blant spillere med kort historikk enn sterk referanse. Det er en proxy for nye spillere, ikke en egen gjennombruddsanalyse. Bedre topplistetreff gir fortsatt ikke høyere samlet sesongscore. Uten chips kommer oppsideblandingen nærmere referansen, men den taper i gjennomsnitt i begge regimer.

Neste prioritet er bedre minutter-/rolle-/kampinformasjon og flerukers beslutninger, ikke mer tilpasning av oppsidevekter på disse fem sesongene. Oppsidesignalet beholdes som en dokumentert forskningskandidat; ingen produksjonsmodell eller kapteinsregel byttes.

Se [sesongresultater](results/season_results.csv), [parete sammenligninger og usikkerhet](results/paired_summary.csv), [kapteinsvalg](results/captain_decisions.csv) og [rangeringssammendrag](results/ranking_summary.csv).

## Kontroller og reproduksjon

Kjør fra repositoryroten etter miljøoppsett og `python scripts/prepare_data.py`:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/upside_feature/run.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/upside_feature/summarize.py
```

Lagrede prognoser og spor brukes som cache. For å simulere på nytt med identiske innganger fjernes bare `upside_feature/results/trace_*.json.gz` i en arbeidskopi. Full retrening bruker `build.py` først. Ved endret kode/input må gamle spor og `run_manifest.json` fjernes i en ny forsøkskopi; ikke overskriv dette referanseforsøket med nye innstillinger.

`honest_training_features.csv.gz` lagrer de tidsriktige historiske oppsidevariablene med radindeks, sesong, spiller og tilgjengelighetstid. `training_audit.csv` kontrollerer indre og ytre tidsgrenser. Oppsidemodellen gjenskaper det tidligere forsøks oppsideprognoser med maksimalt avvik omtrent 8,9 × 10⁻¹⁶ (numerisk avrunding). Matchede hovedmodeller har identiske treningsrader. `checks.json` kontrollerer overlevering, lovlig tropp, poengregnskap og solverstatus. Kapteinsreplay kontrollerer at opprinnelig oppgjør gjenskapes og at spillerne som teller er uendret.

Resultater og innganger arver forbeholdene om historiske pris-/registrerings-/skade-/kalenderproxyer og moderne chip-/FT-regler fra hovedforsøket. Oppsidemål per kamp summeres i dobbeltrunder; dette er ikke en sannsynlighet for 8+ i hele runden. Kort historikk betyr færre enn 12 observerte kamprader, ikke en sikkert identifisert gjennombruddssesong. Billiggrensene er keeper 4,5, forsvar 5,0 og midtbane/angrep 6,0, definert med lagget pris før frist.

Fem sesonger gir stor usikkerhet. De parete bootstrapintervallene resampler fem sesongpar 50 000 ganger og er beskrivende; de korrigerer ikke for tidligere modellleting. En variabel som er en funksjon av de samme opprinnelige inputvariablene tilfører ingen ny ekstern informasjon, men kan gi modellen en nyttig representasjon av dem. En forbedring mot matchet kontroll må derfor også vurderes mot den sterkere referansen.

162 tester bestått lokalt, inkludert tre nye tester av kapteinsgrensen, tie-break og startelleveravgrensning. GitHub CI-status er ikke verifisert. Alle 1360 nye hovedmodellbeslutninger har optimal solverstatus; maksimalt rapportert solver-gap er omtrent 2,05 × 10⁻⁸.
