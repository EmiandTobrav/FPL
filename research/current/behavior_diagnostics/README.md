# Hvorfor chips endrer retreningsgevinsten – og hvor modellene treffer

Diagnostisk oppfølging 6. oktober 2026 av [retreningsforsøket](../retrained_ensemble/README.md). **Prediksjonene blir litt bedre, men det er ikke nok til å garantere bedre sesongvalg. Muligheten til å bygge om troppen forklarer en vesentlig del av chipforskjellen i denne simulatoren. Utvidet HGB har dessuten en tydelig relativ styrke ved ustabil og fallende spilletid.**

Analysen omfatter 12 prognosemodeller, 140 455 spiller–runde-observasjoner med planlagt kamp, 4536 nye beslutninger fra identisk tilstand og 144 nye komplette sesongforløp med chiptyper slått av/på. Ingen prognoser er trent på nytt. Seks tidligere undersøkte sesonger, 2020/21–2025/26. Dette er forklaring og hypotesebygging, ikke en uavhengig sluttprøve eller en ny modellseleksjon.

## 1. Prognosefeilen forklarer ikke alene omslaget

Samme før-frist-prognoser brukes med og uten chips. Prognosemodellen vet ikke hvilken chipstrategi som simuleres. Det er valg, budsjett og troppshistorikk som endres.

Blant et fast utvalg av referansens 60 høyest rangerte spillere per runde faller RMSE ved retrening av Extra Trees fra **3,8139 til 3,8013**, og Ridge fra **3,7971 til 3,7935**. Begge forbedrer dette målet i alle seks sesonger. Forbedringene er små. De kan eksistere samtidig med dårligere rangering av en bestemt kandidat, et dårlig bytte eller et uheldig kapteinsvalg.

Oppdatert treveisblanding har RMSE 3,7806 mot referansens 3,7977 i samme utvalg, bedre i 6/6 sesonger. Blant modellens egne topp 20 gir den 5,029 faktiske poeng per spiller mot 4,913, bedre i 5/6 sesonger. Den er dermed en relevant bred utfordrer, men prediksjonsmål og realisert sesonggevinst må fortsatt vurderes separat.

## 2. Direkte bonuspoeng er en liten del av forklaringen

Vi dekomponerer hvert faktisk sesongspor i poeng fra tellende ellever etter vanlige autosubs, vanlig kapteinsbonus, ekstra TC-/BB-poeng og minus treffkostnad. For TC/BB avregnes **nøyaktig samme valgte lag uten chip**. Bench Boost-bidraget ekskluderer dermed benkpoeng som ville kommet inn ved en vanlig autosub. Wildcard og Free Hit gir ingen direkte poengmultiplikator; virkningen deres kommer gjennom andre valg og tilstander.

For Extra Trees mot sin egen frosne kontroll er retreningsgevinsten −28,2 uten chips og +68,8 med chips. Omslaget på **97,0 poeng** består av:

| Komponent | Bidrag til omslaget |
|---|---:|
| Vanlig tellende ellever | +70,7 |
| Vanlig kapteinsbonus | +18,2 |
| Endret treffkostnad | +6,7 |
| Ekstra Bench Boost-poeng | +4,7 |
| Ekstra Triple Captain-poeng | −3,2 |
| **Totalt** | **+97,0** |

De direkte chipbonusene forklarer altså bare +1,5 av +97,0. Mot den sterke 50/50-referansen er Extra Trees-omslaget +76,2; de direkte bonusene bidrar da **−2,0**. Dette er en eksakt bokføringsidentitet, ikke i seg selv en kausal fordeling av hvilke tidligere bytter som skapte gevinsten.

## 3. Kontrollerte chipablasjoner peker mot troppsendringer

Etter den første dekomponeringen låste vi en separat [oppfølgingsprotokoll](chip_ablation_protocol.json). Den ble altså motivert av de innledende funnene. Fire nye regimer med originale datoer: bare WC, bare FH, WC+FH, og TC+BB. Samme åpning, prognoser, priser, optimizer og regler. Ingen flytting av chips til gunstige runder.

Tallene under er **retrent minus egen frossen modell**, i gjennomsnittlige nettosesongpoeng. For 50/50 er den frosne kontrollen vår sterke referanse.

| Tilgjengelige chips | Ridge | Extra Trees | Ridge/Extra 50/50 |
|---|---:|---:|---:|
| Ingen | -14,7 | -28,2 | -30,0 |
| Bare Wildcard | +20,0 | +39,0 | +31,2 |
| Bare Free Hit | -1,0 | +12,2 | -11,7 |
| Wildcard + Free Hit | +37,8 | +31,0 | +44,8 |
| Triple Captain + Bench Boost | -9,2 | +15,7 | -6,5 |
| Hele den faste kalenderen | +48,7 | +68,8 | +30,5 |

Wildcard alene snur gjennomsnittsgevinsten til positiv for alle tre modellfamilier. WC+FH gir +44,8 for retrent 50/50, med 5/6 sesongseire. For Extra Trees gir WC alene +39,0, også 5/6 seire. Dette støtter at friheten til å omsette oppdaterte prognoser i en ny tropp er en viktig mekanisme i denne énrundes beslutningsmotoren.

**Effektene er ikke additive.** Mot ingen chips endrer WC+FH retreningsgevinsten med +59,2 for Extra Trees, mens TC+BB endrer den med +43,8; samspillseffekten er −6,0, slik at totalen blir +97,0. For 50/50 er de tilsvarende tallene +74,8, +23,5 og −37,8. TC/BB kan altså påvirke bytter, lag og senere valg mye mer enn deres rent mekaniske bonuspoeng tilsier. Ingen av disse tallene beviser at WC+FH er den beste chipstrategien generelt: vi sammenligner modellgevinster, og datoene er historiske proxyer i én fast kalender.

## 4. Samme tropp gir mer avgrensede svar

Hver av ni modeller tar nye beslutninger fra referansens **identiske tropp, kjøpspriser, bank og gratisbytter før runden**, både fra spor med og uten chips. På de åtte chiprundene løses både den planlagte chipen og ingen chip. Bare den umiddelbare faktiske poengsummen evalueres; nye valg føres ikke videre i denne delen.

På referansens tilstand fra chipsporet gir retrent Extra Trees mot frossen Extra Trees:

| Situasjon | Umiddelbar gevinst per beslutning |
|---|---:|
| Wildcard aktiv | +5,33 |
| Samme WC-runder og tilstand, uten chip | +1,83 |
| Free Hit aktiv | +3,08 |
| Bench Boost aktiv | +1,67 |
| Triple Captain aktiv | −3,92 |
| Vanlige runder | +0,09 |

WC-resultatet er positivt i 5/6 sesonger. På tilstander fra sporet uten chips gir WC +4,25 mot +1,75 uten WC på samme datoer. Dette støtter en umiddelbar fordel ved fri troppsbygging for Extra Trees. Ridge har derimot −2,08 på tilsvarende WC-beslutninger, selv om fullsesongablasjonen med WC er positiv. Hele forklaringen kan derfor ikke reduseres til at retrening alltid velger et bedre WC-lag akkurat den runden.

På tilstandene fra referansens spor uten chips gir retrent Extra Trees i gjennomsnitt +0,23 per vanlig, chipfri beslutning over alle 34 runder mot frossen Extra Trees. Likevel taper dens eget selvstendige chipfrie sesongspor −28,2. Dette illustrerer betydningen av hvilke tilstander tidligere valg fører modellen inn i. Det er ingen additiv årsaksdekomponering: de matchede beslutningene kommer fra referansens, ikke Extra-modellenes egne, tilstander.

Den samlede forklaringen støttes derfor best som **et samspill mellom små prognoseendringer, diskrete kjøps-/kapteinsvalg og troppshistorikk i en kortsiktig optimizer**. At prognoser rangerer litt bedre globalt, garanterer ikke at byttene deres er lønnsomme over flere runder. Vi har ikke identifisert én bestemt feilaktig spiller eller én universell bytteregel som forklarer alt.

## 5. Situasjoner der modellene har relative styrker og svakheter

Alle grupper bestemmes før fristen. Spilletid er gjennomsnitt av tidligere kamprader, ikke bekreftet kommende spilletid. «Fallende» betyr minutter6 minus minutter12 ≤−15; «rotasjon» betyr 30–under70 minutter over seks observasjoner. Kort historikk er under12 observerte kamprader, ikke en sikkert identifisert debutant eller gjennombruddsspiller.

I tabellen er gevinst forskjellen i **faktiske poeng per spiller blant modellens topp10 innen samme gruppe**, sammenlignet med den sterke frosne 50/50-referansen. De er ikke sesongpoeng. «Bedre sesonger» teller sesongvis gjennomsnitt. Gruppene overlapper.

| Modell / situasjon | Poenggevinst i topp10 | Bedre sesonger |
|---|---:|---:|
| Utvidet HGB, fallende spilletid | +0,369 | 6/6 |
| Utvidet HGB, rotasjonsspilletid | +0,270 | 6/6 |
| Utvidet HGB, under30 tidligere minutter | +0,267 | 6/6 |
| Utvidet HGB, billige spillere | +0,144 | 5/6 |
| Treveisblanding, fallende spilletid | +0,208 | 6/6 |
| Treveisblanding, midtbanespillere | +0,076 | 6/6 |
| Treveisblanding, keepere | +0,076 | 6/6 |
| Extra Trees, premiumpris | +0,054 | 5/6 |
| Extra Trees, kort historikk | −0,014 | 1/6 |
| Extra Trees, angripere | −0,059 | 1/6 |
| Ridge, kort historikk | −0,025 | 0/6 |
| Ridge, forsvarsspillere | −0,080 | 1/6 |
| Ridge, angripere | −0,027 | 1/6 |

Alle modellene i tabellen er retrente. De positive HGB-mønstrene er spesielt interessante fordi den utvidede modellen har nyere spilletids-/tilstedeværelsesvariabler. Men dette forsøket isolerer ikke den kausale effekten av akkurat de variablene; HGB er også en annen modellfamilie med andre utvidelser.

Ved fallende spilletid gir referansens topp10 2,391 faktiske poeng mot HGBs 2,760. Treffandelen på 8+ går fra 8,72 % til 10,14 %. Dette er en tydelig relativ forbedring innen gruppen; det betyr ikke at spillere med fallende spilletid generelt er attraktive kjøp.

Ridge forbedrer sin egen frosne prediksjonsfeil, men retrening svekker topp10-rangeringen av angripere, spillere med økende minutter og spillere mot sterkt forsvar i 5/6 sesonger. Tapene er små: henholdsvis −0,023, −0,035 og −0,026 per valgt spiller. Det taler mot å anta at raskere tilpasning alltid fanger nye roller bedre.

Extra Trees får en mer konsistent forbedring mot **sin egen frosne versjon** ved jevne Elo-oppgjør (+0,104, 6/6) og mot svakt forsvar (+0,121, 6/6). Motstanderens forsvar måles her med før-frist, eksponentielt laggede innslupne mål: ≤1 sterkt, >1,6 svakt. Angrep og forsvar måles separat. Tallene er aggregert over posisjoner; vi har ikke dokumentert en egen taktisk kampstil-effekt.

### Hva som ikke er løst

- **Kort historikk:** treveisblandingen gir praktisk talt ingen rangeringseffekt, +0,001 med bare 2/6 sesongforbedringer; HGB gir −0,014 med 3/6. Vi har ikke vist en gjennombruddsmodell.
- **Dobbeltrunder:** treveisblandingen er lovende (+0,142 mot referansen, 5/6), men topp10-målet har bare 43 kvalifiserende runder totalt og minst3 i én sesong. Dette oppfyller ikke vårt krav til et godt dekket, gjentakende scenario. Rå RMSE er også høyere ved flere kamper fordi poengskalaen er større; det alene beviser ikke dårligere modellering.
- **Reserve-/tilgjengelighetsrisiko:** omtrent62 % av de planlagte spiller–rundene har under30 minutter i historisk snitt. God gjennomsnittsfeil over hele spillerpoolen kan derfor være lite relevant for lagvalg. Blant referansens topp60 finnes bare69 slike lavminutt-observasjoner totalt, så den delgruppens kalibrering er for sparsom og variabel til sterke påstander.
- **Ingen sikker specialistregel:** vi har undersøkt mange overlappende grupper på seks kjente sesonger. 5/6 eller 6/6 gode sesonger er beskrivende konsistens, ikke en korrigert signifikanstest. Ett stort tap kan dessuten oppveie flere små seire.

## Hva dette tilsier for neste forsøk

1. **Beslutninger og vedlikehold av tropp:** test en låst mekanisme som verdsetter å beholde/selge en spiller over flere runder, med ordentlig før-frist-kampinformasjon. WC-ablasjonen peker mot dette behovet; den beviser ikke at den tidligere nøytrale H4-piloten allerede løser det. Ikke tune chipdatoer på de samme sesongene.
2. **Situasjonsstyrt kombinasjon:** HGB som supplerende ekspert ved fallende/ustabil spilletid er en konkret hypotese. Eventuelle vekter eller en portmodell må læres på tidsordnede treningsprognoser fra eldre data, med samme kapasitetskontroll og sammenligning mot fast treveisblanding. Vi har ikke testet eller godkjent en slik ekspertregel her.
3. **Nye spillere og tilgjengelighet:** bedre rolle-, laguttaks- og registreringsdata før fristen samt deling av informasjon mellom sammenlignbare spillere. Dagens kort-historikk-resultater gir ingen grunn til å stole på at vanlig retrening alene løser dette.

Behold den sterke referansen og de låste utfordrerne til prospektiv evaluering. Ingen produksjonsmodell, blendingsvekt eller chipregel er endret.

## Metode, kontroll og reproduksjon

[Opprinnelig diagnoseprotokoll](protocol.json) ble låst før denne analysens utdata. Chipablasjonen er særskilt merket som eksplorativ oppfølging av de første funnene. Ingen nye modeller eller features er trent; gruppene er kun evalueringsinndelinger.

Feilmål summeres innen hver sesong og rapporteres deretter som likevektet sesongmiddel. Topp10-mål krever minst10 spillere i gruppen; totalt topp20 krever20. Hver kvalifiserende runde får lik vekt innen sesongen. Grupper uten tilstrekkelige spillere bidrar ikke til rangeringsmiddelet. Et godt dekket, gjentakende rangeringsmønster krever minst12 kvalifiserende runder i minst5 sesonger og forbedring i minst5 sesonger; støtte og gjennomsnitt må alltid leses sammen. Referansens topp60 gir en felles relevant evalueringspopulasjon, men er ikke et perfekt eller nøytralt sett av alle mulige gode kjøp. MAE/RMSE, bias, faktisk topputbytte og 8+-treff måler ulike egenskaper.

Priskategorier: billig ≤4,5 keeper /5,0 forsvar /6,0 midtbane og angrep; premium ≥5,5/6,0/9,0/9,0. Motstanderangrep og eget angrep bruker laggede mål for med grenser1 og1,6. Elo-forskjell under−100 er underdog, over100 favoritt. Hjemme/borte vurderes separat for enkeltkamper. Hele terskelsettet finnes i protokollen. Vi ser ikke på fremtidige utfall for å plassere en spiller i en gruppe.

Kjør fra repositoryroten etter miljøoppsett og `python scripts/prepare_data.py`:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/behavior_diagnostics/chips.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/behavior_diagnostics/scenarios.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/behavior_diagnostics/ablation.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/behavior_diagnostics/verify.py
```

`chips.py` bygger nye matchede beslutninger; `scenarios.py` gjenbygger før-frist-grupper og feilmål; `ablation.py` gjør hele sesongavspillinger. Ablasjonsspor er cachet under `results/ablation_*`; ved endrede kilder/input skal disse fjernes i en separat arbeidskopi før ny kjøring. `verify.py` kontrollerer dataene og registrerer SHA-256 for kilder, input og utdata. Den store lokale featurecachen er gjenbyggbar fra de eksisterende repo-dataene og lastes ikke opp på nytt.

Kontrollmodellen gjenskaper alle 408 arkiverte valg der regime og modell er like. De 4536 nye matchede beslutningene har maks solvergap er 2,23×10⁻⁸ og alle har optimal status innen toleransen. De 144 ablasjonsforløpene gir ytterligere 4896 beslutninger, alle optimale innen toleransen, maks gap 1,57×10⁻⁹. Identisk åpning, korrekt chipkalender, poengregnskap og før-frist-variabler er kontrollert. **176 tester bestått lokalt**, inkludert nye kontroller for tilstand etter FH, BB utover autosubs og utfallsuavhengig gruppeinndeling. GitHub CI-status er ikke verifisert.

De eksisterende begrensningene gjelder: laggede prisproxyer, ufullstendig historisk tilgjengelighet/registrering, endelig aktuell kampkalender som før-frist-proxy, historiske poeng med moderne FT-/chipregler, optimalitet innen den eksisterende kandidatlisten og ingen urørt holdout. Resultatene identifiserer mekanismer innen denne simulatoren, ikke en bevist kausal effekt i virkelig FPL.

## Resultatfiler

- [Chipablasjoner, sesongvise gevinster](results/ablation_paired_seasons.csv) og [sammendrag](results/ablation_paired_summary.csv).
- [Additiv poengdekomponering](results/path_interaction_summary.csv) og [chipenes samspill i hele sesonger](results/ablation_factorial_summary.csv).
- [Matchede beslutninger, sammendrag](results/matched_paired_summary.csv).
- [Scenarioer per modell](results/scenario_summary.csv), [parete sesongvise forskjeller](results/scenario_paired_seasons.csv) og [konsistensoversikt](results/scenario_paired_summary.csv).
- [Verifikasjon](results/verification.json), [inputfingeravtrykk](results/source_input_manifest.json) og [utdatafingeravtrykk](results/output_manifest.json).
