# Global, lært HGB-vekt med tre-rundersplanlegging

Forsøksrunde 6. oktober 2026. Utfører den avtalte [2 × 2-testen](../../../docs/NEXT_EXPERIMENT.md). [Protokollen](protocol.json) ble låst før kjøring. Ingen nye modeller eller vekter er trent; prognoser og globalvekter gjenbrukes fra `decision_specialist`. Primærmål er nettosesongpoeng med fast chipkalender; uten chips er diagnostikk.

## Konklusjon

**Kombinasjonen får høyest primært gjennomsnitt i denne sammenligningen: +70,0 mot referansen, med 4/4 sesongseire.** Men tilleggsverdien over globalvekt med H1 er usikker: +15,75 med chips kommer fra bare én sesongseier, og uten chips er effekten −16,75. Vi beholder de to bekreftede utfordrerne og registrerer kombinasjonen som forskningskandidat, ikke som en dokumentert bedre erstatning.

## Samme fire sesonger for alle celler

Alle tall gjelder 2022/23–2025/26. 2020/21 og 2021/22 er innledende metatreningssesonger for globalvekten. Dette fire-sesongsutvalget må ikke blandes med den tidligere H3-evalueringen over seks sesonger.

| Prognose og horisont | Med chips | Gevinst mot referansen | Uten chips | Gevinst mot referansen |
|---|---:|---:|---:|---:|
| Opprinnelig frossen referanse | 2238,25 | +0,00 | 2149,00 | +0,00 |
| Oppdatert Ridge/Extra, H1 | 2279,25 | +41,00 | 2112,50 | -36,50 |
| Oppdatert Ridge/Extra, H3 | 2273,75 | +35,50 | 2174,00 | +25,00 |
| Global HGB-vekt, H1 | 2292,50 | +54,25 | 2189,50 | +40,50 |
| Global HGB-vekt, H3 | 2308,25 | +70,00 | 2172,75 | +23,75 |
| Oppdatert Extra Trees, original H1 | 2292,75 | +54,50 | 2122,00 | -27,00 |

Kombinasjonen mot referansen: +70,0 med chips, beskrivende 95 %-intervall [23,0;106,5], 4/4 seire. Uten chips: +23,75, intervall [−46,25;99,5], 3/4 seire. Referansegevinst alene viser ikke at kombinasjonen er bedre enn de eksisterende utfordrerne.

## Isolerte effekter og samspill

| Sammenligning | Med chips | Uten chips |
|---|---:|---:|
| Global H3 minus global H1 | +15,75 | −16,75 |
| Global H3 minus Ridge/Extra H3 | +34,50 | −1,25 |
| Global H3 minus oppdatert Extra Trees | +15,50 | +50,75 |
| Samspill mellom globalvekt og H3 | +21,25 | −78,25 |

Samspill er `(global H3 − global H1) − (Ridge/Extra H3 − Ridge/Extra H1)`. Positivt tall betyr at H3-effekten blir bedre med globalvekten; negativt betyr at den blir svakere. Det er ikke det samme som kandidatens totale gevinst mot referansen.

Med chips er samspillsintervallet [−40,0;71,75], og den isolerte horisonteffekten for globalvekten har intervall [−10,0;58,25]. Vi har derfor ikke dokumentert sikker positiv synergi. Uten chips er samspillet negativt i alle fire sesonger, med beskrivende intervall [−136,5;−20,0]. Gevinstene fra tidligere separate forsøk kan ikke summeres.

Mot Ridge/Extra H3 vinner global H3 bare 2/4 sesonger med chips, og intervallet er [−28,0;112,75]. Mot retrent Extra Trees vinner den 3/4, men intervallet [−62,75;72,25] er bredt. Ingen stabil overlegenhet over alle sterke alternativer.

## Sesongvis primærgevinst

| Sesong | Global H3 mot referansen | Global H3 mot global H1 | Global H3 mot Ridge/Extra H3 |
|---|---:|---:|---:|
| 2022-23 | +75 | -1 | +40 |
| 2023-24 | +2 | -13 | -45 |
| 2024-25 | +86 | +78 | -11 |
| 2025-26 | +117 | -1 | +154 |

Den positive gjennomsnittlige H3-effekten over global H1 kommer fra +78 i 2024/25; de andre sesongene gir −1,−13,−1. Mot Ridge/Extra H3 kommer den største fordelen i 2025/26 (+154). Ulike sammenligninger forteller derfor ulike historier.

H3 øker globalvektens treffkostnad fra 15 til 25 poeng per sesong med chips, og fra 11 til 26 uten. Antall bytter øker fra 77,25 til 77,50 med chips og fra 36,50 til 40,50 uten. Dette er ingen dokumentert mekanisme for automatisk færre eller billigere bytter. Med chips er bruttopoengøkningen nok til å dekke ekstrakostnaden i gjennomsnitt; uten chips er den ikke det.

## Kontroller

16 nye forløp, 544 nye beslutninger. De 16 Ridge/Extra-kontrollforløpene gjenbrukes med verifiserte SHA-256 fra tidligere utdataarkiv. Den matchede matrisen har 32 forløp; med eksterne kontroller sammenlignes 56 totalt.

Planlegger, solvertoleranser, shortlist, regelverk og faktisk GW4-overlevering er uendret. AST-kontroll bekrefter at `run` og `horizon_chips` er identiske med forrige forsøks funksjoner. Den nye globale H1-kontrollen gjenskaper alle åtte opprinnelige globalvektforløp med identiske troppsvalg og poeng. Det finnes altså ikke et motoravvik som forklarer den målte H3-effekten her.

Fremtidsprognosen bruker samme `future_proxy`: én nøytral fremtidig kamp, gammel referansenøytral rate korrigert med aktuell globalvekt-minus-referanse per kamp, halvering av aktuell kampeffekt og referansefallback ved blank aktuell runde. Kontrollprognosene for Ridge/Extra gjenskapes med største avvik 2,22×10⁻¹⁵ over 136 runder. Ingen fremtidige `games`-rader eller faktiske fremtidige utfall inngår i planens input.

Alle nye beslutninger har optimal solverstatus innen toleransen, største gap 9,55×10⁻⁶. Identisk åpning, poengregnskap, bank, FT og posisjoner er kontrollert. De tre relevante eksisterende regresjonstestene for fremtidsproxy, ekspertvekting og planleggerens bank/FT er kjørt på nytt og består. Ingen nye algoritmer eller nye enhetstester er innført i denne runden. GitHub CI-status er ikke verifisert.

## Begrensninger og videre beslutning

Fire allerede undersøkte sesonger, ingen urørt holdout. Parete intervaller bruker 50 000 bootstrap-resamplinger og korrigerer ikke for de mange tidligere forsøkene. Fremtidig kampkalender er fortsatt en nøytral proxy; pris, tilgjengelighet og spillerpool fryses i planen. Historiske pris-/registrerings-/kalenderproxyer og moderne chip-/FT-regler beholdes. Solveroptimalitet gjelder den eksisterende kandidatlisten; likeverdige valg kan fortsatt gi ulike forløp i andre sammenligninger.

Behold `re_refresh_h3` og original `constant` som aktive utfordrere, og `constant_h3` som forskningskandidat med høy primær middelgevinst, men usikker tilleggsverdi. Ingen produksjonsendring eller tilpasning av vekter/hyperparametere etter disse resultatene.

Neste prioritet er bedre før-frist-kalender/tilgjengelighetsdata, deterministisk håndtering av likeverdige valg og prospektiv evaluering med låste kandidater. Det foreslås ikke et nytt historisk vektsøk. Spesielt bør den store, ujevne gevinsten mot global H1 ikke brukes alene til å velge mer komplekse modeller.

## Reproduksjon

Etter miljøoppsett og `python scripts/prepare_data.py`, fra repositoryroten:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/global_horizon/build.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/global_horizon/run.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/global_horizon/summarize.py
```

Eksisterende spor gjenbrukes bare med samme manifest. Endrede kilder/input krever en separat forsøkskopi og nye spor. Prognoser/koeffisienter og kontrollspor fra `decision_specialist` er nødvendige og allerede lagret i repositoryet; basismodellene skal ikke retrenes for å gjenskape denne testen.

[Modelloversikt](results/model_summary.csv), [alle sesongresultater](results/all_seasons.csv), [parete effekter](results/paired_summary.csv), [sesongvise effekter](results/paired_seasons.csv), [motorparitet](results/engine_parity.csv), [kontroller](results/checks.json), [inputmanifest](results/horizon_manifest.json) og [utdatahash](results/output_manifest.json).
