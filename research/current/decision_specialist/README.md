# Tre-runders bytteplanlegging og tidsordnet HGB-spesialist

Forsøksrunde 6. oktober 2026, etter [chip- og scenariodiagnostikken](../behavior_diagnostics/README.md). [Protokollen](protocol.json) ble låst før nye resultater. Primærmål: nettosesongpoeng med eksisterende fast chipkalender. Uten chips er diagnostikk. Alle historiske sesonger er allerede undersøkt; ingen urørt holdout.

## To adskilte forsøk

### A: planlegg bytter over tre runder

Frossen Ridge/Extra-referanse, oppdatert Extra Trees og oppdatert Ridge/Extra 50/50 kjøres med én og tre runders horisont, seks sesonger og to chipregimer: **72 nye sesongforløp**. Bare første handling i planen utføres før ny prognose og ny plan. Bank, kjøpspriser, treff og gratisbytter følger samme opprinnelige regler. Fremtidige WC/FH avgrenser horisonten; aktuell FH løses alene.

Den eksisterende flertrinns MILP-planleggeren kopieres inn uten endring i beslutningsreglene. Solvegrensen settes til 10 sekunder og relativt gap 1e-5, mot tidligere 5 sekunder / 0,001. Kandidatlisten bruker bare prognosene innen den aktive horisonten. Matchede H1-kontroller bruker samme motor; avvik mot den opprinnelige énrundesmotoren rapporteres separat. Optimalitet gjelder den eksisterende kandidatlisten. Planen kan ikke selge og gjenkjøpe samme opprinnelige spiller innen horisonten; priser og tilgjengelig spillerpool fryses i planen.

**Fremtidige kamper er fortsatt en proxy.** Det finnes ikke et verifisert arkiv over fremtidig kampkalender slik den var kjent ved hver frist. Vi bruker én nøytral kamp per fremtidig runde, ikke den endelige historiske kalenderen. Den frosne referansens nøytrale rate rekonstrueres fra tidligere lagrede, før-frist-beregnede prognoser. For oppdaterte modeller legges deres aktuelle poengforskjell mot referansen per kamp til den nøytrale raten. Den aktuelle kampeffekten halveres for hver fremtidig runde, som i tidligere pilot. Dette er en felles motstanderjustering, ikke en ny nøytral prediksjon direkte fra hver retrent estimator.

Dobbeltrundens poeng gjentas ikke i hver fremtidig runde. Spillere uten aktuell kamp bruker den frosne referansens nøytrale fallback; deres oppdaterte prognoser gir da ikke et separat nøytralt signal. Ingen fremtidige `games`-rader, utfall eller skader leses for å lage planen. Dette tester en konkret flerukersproxy, ikke det fulle potensialet til planlegging med korrekt kjent kampprogram.

### B: lær når HGB skal få større vekt

To komponenter: `a` er oppdatert Ridge/Extra 50/50, og `b` er oppdatert utvidet HGB. Prognosen er `(1-w)*a+w*b`.

- `constant`: én lært global HGB-vekt per sesong.
- `gate`: HGB-vekten varierer med tidligere spilletid, fall i spilletid og en rotasjonsindikator.
- Kontroller: fast treveisblanding (`w=1/3`), de to enkeltkomponentene og den sterke frosne referansen.

Vekten er sigmoid av en liten lineær modell. Variablene er konstantledd, minutter6/90, positiv del av (minutter12−minutter6)/90 og indikator for 30≤minutter6<70. Kontinuerlige variabler klippes til 0–1. Manglende minutter6 settes til 0; manglende minutter12 til minutter6. Parametere begrenses til [−4,4]. Kvadratisk regularisering 0,01 trekker mot fast treveisblanding. Ingen søk i styrke, variabler eller terskler.

Begge metamodellene trener på de samme historiske prognoseradene og det samme kvadratiske totalpoengtapet. Observasjonsvekten er 1+4 hvis minst én komponent predikerer ≥3 poeng per aktuell kamp, ellers1. Relevansvekten bruker ikke fasit. Dobbeltrunder beholder totalpoeng som mål; de får dermed større potensielle absolutte feil. Det er ingen direkte optimalisering av sesongpoeng.

Metamodellen trenes én gang før sesongen, bare på eldre sesongers prognoser med hele rundens utfall tilgjengelig før GW1-fristen. Komponentprognosene var selv laget før de historiske utfallene. 2020/21 og 2021/22 bygger det første metatreningsgrunnlaget; **2022/23–2025/26 er de fire evalueringssesongene**. Komponentene fortsetter sin eksisterende retrening hver fjerde GW; metavektene bruker ingen utfall fra evalueringssesongen. To nye modeller × fire sesonger × to chipregimer gir **16 nye forløp**.

Dette skiller den eventuelle verdien av situasjonsstyring fra verdien av å endre HGB-andelen generelt. Modellfamilien og scenariovariablene ble valgt etter tidligere analyser av de samme sesongene; tidsriktig metatrening gjør derfor ikke forsøket til en uavhengig holdout.


## Resultater A: tre-rundersplanlegging

**Oppdatert Ridge/Extra 50/50 med tre runder er den mest lovende flerukerskandidaten:** 2267,3 poeng med chips, **+51,0** mot den opprinnelige sterke referansen, med 5/6 seire. Uten chips får den 2186,8, **+31,2**, med 4/6 seire. Beskrivende 95 %-intervaller er [11,8;87,0] og [−32,2;89,2].

Alle tall nedenfor gjelder de samme seks sesongene. Gevinst er mot opprinnelig frossen Ridge/Extra 50/50.

| Modell og horisont | Med chips | Gevinst | Uten chips | Gevinst |
|---|---:|---:|---:|---:|
| Opprinnelig referanse | 2216,3 | +0,0 | 2155,7 | +0,0 |
| Frossen referanse, matchet H1 | 2216,7 | +0,3 | 2157,8 | +2,2 |
| Frossen referanse, H3 | 2219,8 | +3,5 | 2158,7 | +3,0 |
| Oppdatert Extra Trees, matchet H1 | 2250,2 | +33,8 | 2140,2 | -15,5 |
| Oppdatert Extra Trees, H3 | 2244,3 | +28,0 | 2145,2 | -10,5 |
| Oppdatert 50/50, matchet H1 | 2246,8 | +30,5 | 2125,7 | -30,0 |
| Oppdatert 50/50, H3 | 2267,3 | +51,0 | 2186,8 | +31,2 |

Mot **sin egen matchede H1-kontroll** gir H3 for oppdatert 50/50 **+20,5 med chips og +61,2 uten**. Den vinner henholdsvis 3/6 og 5/6 sesonger. Intervallene er [−42,2;87,7] og [30,0;92,5]. Primærgevinsten over den sterke referansen er derfor bedre støttet enn påstanden om at tre runder alltid er bedre enn én med samme oppdaterte modell. Uten chips er horisontforbedringen mer konsistent.

Det er ingen universell H3-gevinst: oppdatert Extra Trees får −5,8/+5,0 med/uten chips mot egen H1, og frossen referanse bare +3,2/+0,8. Kombinasjonen av oppdatert blanding og planlegging er lovende; det er ikke nok å øke horisonten for enhver modell.

### Sesongvariasjon for oppdatert 50/50 med H3

| Sesong | Med chips | Mot opprinnelig referanse |
|---|---:|---:|
| 2020-21 | 2241 | +114 |
| 2021-22 | 2268 | +50 |
| 2022-23 | 2294 | +35 |
| 2023-24 | 2216 | +47 |
| 2024-25 | 2501 | +97 |
| 2025-26 | 2084 | -37 |

Kandidaten taper altså i siste sesong. Den tar også mer treffkostnad med chips: 31,3 mot H1-kontrollens 24,0 i snitt. Gevinsten kommer ikke av at bytter nødvendigvis blir færre eller billigere; bruttopoengene øker nok til å mer enn dekke kostnaden.

Tidsordnet valg som bare ser tidligere evalueringssesonger velger `re_refresh_h3` i alle fire sesonger fra 2022/23, med gevinstene +35,+47,+97,−37: **+35,5 i gjennomsnitt**. Uten chips gir samme valgregel −7,25. Familien er foreslått etter tidligere analyser av de samme dataene; dette er fortsatt ikke en urørt holdout.

### Beslutningsmotor og likeverdige valg

H1-kontrollene må ikke automatisk likestilles med det gamle sesongsporet. For oppdatert 50/50 gjenskaper H1 alle tolv gamle sesongscorer og alle troppsvalg nøyaktig. Dette gjør dens H3-sammenligning spesielt nyttig.

For Extra Trees gir H1-motorbyttet derimot −20 poeng med chips i 2020/21 og +55/+86 uten chips i 2020/21 og2022/23. De første ulike troppsvalgene har **lik økonomisk prognoseverdi** før små tie-break-ledd. Forskjellige spillere med lik beregnet verdi fører til ulike senere forløp. Frossen referanse avviker +13 uten chips i 2020/21 og +2 med chips i 2024/25; det siste starter med en objektivforskjell på rundt −0,000076 forventede poeng. Ingen av disse avvikene skal tilskrives H3. [Motorparitet](results/h1_engine_parity.csv) viser alle36 sammenligninger.

Alle H1/H3-beslutninger har optimal solverstatus innen den låste toleransen; største rapporterte gap er omtrent 1e-5, det vil si 0,001 %. Dette fjerner problemet med tidligere tidsavbrutte H4-løsninger i denne runden, men det fjerner ikke følsomheten for likeverdige valg eller den begrensede kandidatlisten.

## Resultater B: situasjonsstyrt HGB-blanding

**Begge lærte blandinger slår den opprinnelige referansen i alle fire sesonger med chips.** Den situasjonsstyrte gir **+62,0**, den globale vekten **+54,3**. Men den ekstra verdien av situasjonsstyringen er foreløpig usikker.

Denne tabellen gjelder bare 2022/23–2025/26. Den skal ikke direkte rangeres mot seks-sesongstabellen over.

| Modell | Med chips | Mot referansen | Uten chips | Mot referansen |
|---|---:|---:|---:|---:|
| Frossen referanse | 2238,2 | +0,0 | 2149,0 | +0,0 |
| Oppdatert 50/50 | 2279,2 | +41,0 | 2112,5 | -36,5 |
| Oppdatert utvidet HGB | 2253,8 | +15,5 | 2116,2 | -32,8 |
| Fast treveisblanding | 2279,2 | +41,0 | 2183,5 | +34,5 |
| Oppdatert Extra Trees (supplerende kontroll) | 2292,8 | +54,5 | 2122,0 | -27,0 |
| Lært global HGB-vekt | 2292,5 | +54,2 | 2189,5 | +40,5 |
| Situasjonsstyrt HGB-vekt | 2300,2 | +62,0 | 2161,0 | +12,0 |

Gate mot referansen har beskrivende intervall [22,3;123,3] med chips. Global vekt har [11,5;97,0]. Mot **globalvektkontrollen** gir gate bare **+7,75** med chips, 3/4 seire og intervall [−68,3;62,5]. Uten chips taper gate **−28,5**, med bare 1/4 seire. Mot fast treveisblanding gir gate +21,0 med chips, men −22,5 uten; den taper uten chips i alle fire sesonger.

Dette støtter å lære en generell HGB-andel som kandidat, men ikke en sikker påstand om at scenariostyringen tilfører sesonggevinst. Selv den globale vekten er bare +13,25/+6,0 mot fast treveis med/uten chips, med 2/4 seire i begge regimer og intervaller over null.

Etter de innledende gate-resultatene la vi til en tydelig merket [supplerende sammenligning](supplementary_comparison.json) mot forrige rundes sterkeste primærkandidat, retrent Extra Trees, på samme fire sesonger. Gate er bare +7,5 med chips og slår Extra i 1/4 sesonger: +162 i 2022/23, deretter −60,−2,−70. Global vekt er praktisk talt lik Extra med chips (−0,25), men betydelig bedre uten (+67,5,4/4). Ingen kandidat har dermed dokumentert stabil overlegenhet over alle de sterke alternativene.

### Sesongvise gevinster med chips

| Sesong | Global vekt mot referansen | Gate mot referansen | Gate mot global vekt |
|---|---:|---:|---:|
| 2022-23 | +76 | +151 | +75 |
| 2023-24 | +15 | +40 | +25 |
| 2024-25 | +8 | +41 | +33 |
| 2025-26 | +118 | +16 | -102 |

Valgregelen som bare ser tidligere evalueringssesonger velger gate for 2024/25 og 2025/26, og får +41/+16 mot referansen: **+28,5 i gjennomsnitt over to sesonger**. Uten chips gir valgregelen +8,5. Dette er en liten, gjenbrukt evalueringsperiode, ikke bevis på produksjonsklar seleksjon.

### Hva metamodellen lærte

| Evalueringssesong | Global HGB-vekt | Gate, rotasjonsgruppen | Gate, fallende minutter |
|---|---:|---:|---:|
| 2022-23 | 42,5 % | 55,0 % | 44,9 % |
| 2023-24 | 44,7 % | 55,1 % | 46,7 % |
| 2024-25 | 48,2 % | 57,8 % | 49,2 % |
| 2025-26 | 49,4 % | 59,5 % | 50,4 % |

Dette er gjennomsnitt av før-frist-vekter per gruppe; modellen har ingen tilgang til sesongens fasit ved vekting. Den faste treveisblandingen bruker 33,3 % HGB. De lærte globale vektene ligger omtrent 43–49 %, og gate øker særlig HGB-andelen for 30–70 minutters historisk spilletid.

Prediksjonsgevinsten fra selve situasjonsstyringen er liten: relevant RMSE 3,7140 mot globalvektens 3,7145. Faktiske poeng blant topp20 er 5,039 mot5,035. Ved fallende minutter øker topp10-utbyttet fra 2,519 til 2,554, mens rotasjonsgruppens utbytte er praktisk talt uendret. Ren utvidet HGB rangerer fortsatt disse to gruppene bedre enn gate i dette fire-sesongsutvalget. Det er ikke vist at denne gate-konstruksjonen utnytter hele spesialistpotensialet.

Kort historikk er fortsatt uløst: topp10-utbytte 1,724 for gate mot 1,718 for referansen, uten en dokumentert gjennombruddseffekt. Metamodellen bruker heller ingen nye rolle-/tilgjengelighetsdata.

## Beslutning og neste spor

- Behold **oppdatert Ridge/Extra med H3** som en ny utfordrer: positiv gjennomsnittsgevinst mot referansen i begge regimer over seks sesonger, men tap siste sesong og stor variasjon i den isolerte primære horisonteffekten.
- Behold **lært global HGB-vekt** som en enkel utfordrer til fast treveisblanding. Gate beholdes som forskning, fordi den ikke har vist stabil tilleggsverdi over den globale vekten.
- En naturlig neste kombinasjon er den globale, tidsordnet lærte blandingen sammen med flerukersplanlegging. **Denne kombinasjonen er ikke testet her.** Den trenger en låst protokoll og samme før-frist- og kontrollkrav, og fortsatt tydelig merking av fremtidsproxyen.
- Før praktisk bruk bør likeverdige valg gjøres mer deterministiske og før-frist-kalender/tilgjengelighet forbedres. Prospektiv evaluering med låste kandidater er nødvendig. Ingen automatisk produksjonsendring.

## Kontroller, usikkerhet og reproduksjon

**88 nye sesongforløp og 2992 beslutninger**, med identisk opprinnelig GW4-overlevering. Alle nye beslutninger har optimal solverstatus innen sine toleranser, og poengregnskap, bank, FT og posisjoner er kontrollert. **179 tester bestått lokalt**. Nye tester dekker nøytral fremtidsproxy ved dobbel/blank runde, lærbar og konveks ekspertvekting samt bank/FT i den kopierte planleggeren. GitHub CI-status er ikke verifisert.

Gate-auditen viser 41 449 til 114 065 treningsrader, bare fra eldre sesonger, og seneste treningsutfall før evalueringssesongens GW1-frist. Lagrede koeffisienter gjenskaper alle prognoser og vekter innen 1e-12. Referansens fremtidsproxy gjenskaper den tidligere lagrede før-frist-prognosen innen 1e-12. Input- og kildefingeravtrykk samt utdatahash er lagret.

En avhengighetsglob i gate-manifestet ble avgrenset fra alle `gate_*.csv*` til bare prognoseinnganger og treningsaudit, slik at nygenererte resultattabeller ikke ble behandlet som input. AST utenfor fingerprint-funksjonen ble kontrollert uendret; ingen beregninger eller input ble endret. Den metadatarettingen er dokumentert i `manifest_scope_correction.json`.

Intervaller er paret bootstrap av sesonger med 50 000 resamplinger. H3 bruker seks, gate fire sesonger. De er beskrivende og korrigerer ikke for tidligere modellforsøk, valg av scenariofamilie eller mange sammenligninger. Tidsordnet modellvalg starter først etter to evalueringssesonger og bruker middelgevinst minus 0,25 standardavvik; behold referansen innen to poeng fra best. H3-valget vurderer alle seks H1/H3-kandidater og referansen. Gate-valget vurderer gate, global vekt, fast treveis og referansen; den supplerende Extra-kontrollen legges ikke inn etter fasit.

Historiske pris-/registrerings-/tilgjengelighetsproxyer, moderne FT-/chipregler over historiske poeng og kjent aktuell endelig kampkalender som proxy beholdes. Fremtidig nøytral kampproxy begrenser hva horisonttesten kan si. Nye spillere eller nye skader inne i planen modelleres ikke. Ingen historisk rank eller ny faktisk sesongprestasjon påstås.

Etter miljøoppsett fra rot-README og `python scripts/prepare_data.py`, fra repositoryroten:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/decision_specialist/build.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/decision_specialist/run_gate.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/decision_specialist/run_horizon.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/decision_specialist/summarize.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/decision_specialist/verify.py
```

Lagrede spor gjenbrukes bare med samme manifest. Ved endret modell, protokoll eller input opprettes en ny forsøkskopi og de berørte sporene/manifestene fjernes før ny kjøring. Ikke overskriv referanseforsøkene. `build.py` regenererer prognoser fra de allerede publiserte komponentprognosene og før-frist-gruppene; det krever ikke ny trening av basismodellene. Den store gjenbyggbare featurecachen lastes ikke opp på nytt.

- [H3-modelloversikt](results/horizon_summary.csv), [sesongresultater](results/horizon_all_seasons.csv), [parete effekter](results/horizon_paired_summary.csv), [tidsordnet valg](results/horizon_selection.csv).
- [Gate-modelloversikt](results/gate_summary.csv), [sesongresultater](results/gate_all_seasons.csv), [parete effekter](results/gate_paired_summary.csv), [tidsordnet valg](results/gate_selection.csv).
- [Gate-koeffisienter](results/gate_coefficients.json), [treningsaudit](results/gate_training_audit.csv), [prediksjonsdiagnostikk](results/gate_diagnostics_summary.csv).
- [Kontrollrapport](results/checks.json), [motorparitet](results/h1_engine_parity.csv), [utdatafingeravtrykk](results/output_manifest.json).
