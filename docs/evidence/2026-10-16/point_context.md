# Kampkontekst i poengmodellen — kontrollert forsøk

Den forhåndsvalgte kandidaten består forskningskravene i denne utviklingsperioden. Minuttprognoser og kategorisannsynligheter er nøyaktig uendret. Det er gjennomført 228 poengfit og null minuttfit, uten parametersøk eller etterfølgende kandidatbytte.

## Hovedresultat

Hele pakken gir 1.604 % reduksjon i MSE på alle evaluerbare spillerrader og 3.288 % på den faste kandidatlisten. Negative prosenttall betyr forverring.

| Spor | MSE, alle | RMSE, alle | MSE, lagkandidater | MAE, lagkandidater |
|---|---:|---:|---:|---:|
| Beholdt poengmodell / kontroll | 3.662726 | 1.9138 | 13.375402 | 2.8875 |
| Gammel kalender, streng policy | 3.656891 | 1.9123 | 13.329047 | 2.8843 |
| Reparert kalender, streng policy | 3.656418 | 1.9122 | 13.324411 | 2.8839 |
| Gammel kalender, videreført | 3.651941 | 1.9110 | 13.327856 | 2.8853 |
| Reparert kalender, videreført | 3.615574 | 1.9015 | 13.012207 | 2.8619 |
| Reparert + videreført + lagstyrke | 3.603974 | 1.8984 | 12.935643 | 2.8634 |

Alle tall gjelder 2025/26, en tidligere undersøkt utviklingsperiode. Samme 29 144 evaluerbare rader i alle spor, inkludert 2 070 kandidatrader. Kjøpbare etter fristens univers: 29553; manglende mål: 409. Kandidatlisten er valgt før utfall fra den tidligere låste benchmarken og blir ikke rerangert med nye prognoser.

## Hva skyldes hva?

Tabellen viser MSE for første spor minus sammenligningssporet. Negativt er forbedring. Parvise 95 % blokkintervaller står i hakeparentes.

| Isolert forskjell | Alle spillere | Fast kandidatliste |
|---|---:|---:|
| Videreføring, gammel kalender | -0.004949 [-0.011181, +0.002746] | -0.001191 [-0.051766, +0.072134] |
| Videreføring, reparert kalender | -0.040844 [-0.115995, +0.001715] | -0.312203 [-0.921962, +0.066088] |
| Reparasjon, streng policy | -0.000473 [-0.000478, +0.000188] | -0.004636 [-0.004681, +0.001713] |
| Reparasjon, videreført kalender | -0.036368 [-0.108201, +0.000000] | -0.315648 [-0.881479, +0.000000] |
| Lag-/motstanderstyrke | -0.011600 [-0.026996, +0.003524] | -0.076565 [-0.187484, -0.003242] |
| Hele pakken mot kontroll | -0.058753 [-0.139292, -0.010749] | -0.439759 [-1.089623, -0.065289] |

Videreføring er sammenlignet innen samme reparasjonsstatus; reparasjon innen samme videreføringspolicy. Lagstyrke sammenlignes med den ellers identiske reparerte og videreførte kalenderen. Effektene er derfor ikke slått sammen til én kalendergevinst. De er likevel effekter av hele retrente prognosemodeller; interaksjoner og endret beslutningstrestruktur gjør at effekter ikke nødvendigvis summeres på tvers av spor.

Featurekontrollen (`feature_changes.csv`) viser at reparasjon endrer kampantall for 247 prognoser i GW33, 248 i GW34 og 82 i GW36 under videreføring. I de strenge sporene forblir kampantallet ukjent; reparasjonen endrer bare antall ufordelte kamper for 82 prognoser per runde i GW35–38. Dette forklarer hvorfor «reparasjon under streng policy» ikke tester nytte av oppdaterte kampantall.

De strenge sporene beholder den tidligere aldersgrensen og manglende felt for klubber med ufordelte kamper. Reparasjon gjør ikke gamle snapshots ferske. Alder og antall ufordelte kamper er synlige også når kampantallet mangler. Videreføring gir kalenderfelt for alle 29 574 prognoser i 2025/26, mot 9 674 under streng policy; dette endrer ikke evalueringsutvalget. Historisk styrke kan være ukjent ved manglende klubbhistorikk eller ingen planlagt motstander.

Intervallene bruker 2 000 parvise fire-runders blokker. De er beskrivende, ikke korrigert for de mange sammenligningene og ikke nye uavhengige sesonger. Et intervall som krysser null gir ikke tydelig støtte for fortegnet. Den forhåndsregistrerte terskelen er streng MSE-forbedring, ikke statistisk signifikans.

## Kontroller og metode

- Kontrollsporet gjenskaper beholdte prognoser: største absolutt avvik 0.
- Minutter og alle tre kategorisannsynligheter er identiske med lagrede innganger. Brier(play) 0.068649881, Brier(any60) 0.075048258, uendret i alle spor.
- Verifisert 1036 inngangshasher, 38 tidsriktige fitfrister, alle 12 MSE-gruppetall og 426 990 historiske kalenderkontekstrader. Alle spor har identiske treningsnøkler ved hver frist.
- Historisk kalender og styrke hentes ved hver treningsrads egen frist, aldri ved den senere modellfitten. Poeng- og minuttmål er tilgjengelige strengt før fit.
- Styrke er siste seks kjente klubbkamper, med avspark +24 timer som tilgjengelighetsproxy. Gjennomsnitt av motstandernes historikk brukes ved flere kamper. Ingen nåværende kampresultater eller observerte minutter er nye features.
- Alle spor bruker beholdt CatBoost-oppsett, 200 iterasjoner, dybde 5, rate 0,05, samme fraværsgjennomsnitt og faste p(play). Negative poeng beholdes. Målkontrakten er hashbundet.

## Beslutning og begrensninger

Den forhåndsvalgte kandidaten består forskningskravene i denne utviklingsperioden. Forskningskravene er lavere MSE enn kontroll i hele 2025/26 samt det ekstra relevanskravet om lavere MSE blant den faste kandidatlisten; uendrede sannsynligheter oppfyller Brier-kravet. Ingen manager eller produksjonsmodell er oppgradert.

Git-tidsstempel, publiseringsdato og avspark +24 timer er fortsatt kildeproxyer. Kalenderrekonstruksjonen med videreføring er en eksplisitt policy, ikke bevis for ferske historiske snapshots. Eksakte fremtidige avspark er ikke brukt. Kalenderreparasjoner er utledet fra daterte meldinger, ikke sluttkalenderen. 2025/26 kan ikke brukes som urørt testsett etter disse analysene.

Se `FORSOKSDESIGN.md`, `proposal.json`, `metrics.csv`, `intervals.csv`, `feature_coverage.csv` og `verification.json`. Reproduser fra prosjektroten med `python -B -m model_lab.point_context context`, `run`, `score`, og deretter denne mappens `verify.py`. Den eksisterende kjøremappen skal ikke overskrives for et nytt forsøk.
