# Fortsett her

Oppdatert 6. oktober 2026. Brukeren ønsker GitHub som sentral for kode og fremgang på tvers av enheter. Denne mappen og repositoryet skal være tilstrekkelig kontekst uten den gamle samtalen eller ZIP-filene.

## Mål og avklaringer

Maksimer robust FPL-sluttscore etter at hovedmodellen tar over fra startmodellen. Test enkeltmodeller, faste og lærte prognosekombinasjoner, og separate variabler for motstanderens angrep og forsvar. Startmodellens overlevering skal inneholde den faktiske troppen, bank, kjøpspriser og gratisbytter. Ikke tilpass startlaget til et kunstig idealmottakerlag. Startstrategiens delmål ved GW8,12,15,19 beholdes separat.

Kvantifisering av elite-managere var et tidligere spor. Brukeren gikk videre til hovedmodellen; dette er nå hovedprioriteten. Rå elite-eierskapsarkiv er ikke nødvendig for gjeldende eksperiment og er ikke flyttet inn som aktivt datasett.

## Gjeldende arbeidsreferanse

Brukeren har 6. oktober 2026 valgt **global, lært HGB-vekt med tre-rundersplanlegging (`constant_h3`)** som ny referanse/benchmark for videre forsøk. [Maskinlesbart benchmarkmanifest](../research/current/benchmark.json) låser modellregelen, evidens, kildehash og de åtte sesongsporene.

Primærmål: nettosesongpoeng med fast chipkalender. Benchmarken har **2308,25 poeng** i gjennomsnitt på 2022/23–2025/26; uten chips 2172,75. Nye kandidater skal vurderes mot denne på samme sesonger og ressurser. Den gamle `mix_ridge_extra_50` beholdes som historisk sekundærkontroll. Gamle protokoller, tabeller og differanser skal ikke skrives om; deres «referanse» betyr fortsatt den opprinnelige modellen. Dette er en arbeidsreferanse valgt etter observert primærscore, ikke en påstand om uavhengig bekreftet overlegenhet eller produksjonssetting.

## Historisk referanse og opprinnelig forsøk

Startmodell: `handoff=4`, `look=3`, `carry=1`, `friction=0.5`, `prior_mix=0`, `chip_reserve=1000`, `scenario=neutral`. Modeller trenes på eldre sesonger; hovedmottakerens optimizer har én-rundes horisont. Alle ti kandidater får samme starttilstand. Friksjon 0,5, benkvekt 0,10. Fast chipkalender: WC6, TC15, FH18, BB19, WC24, FH33, BB36, TC37. Det kjøres også uten chips.

120 ferdige forløp: seks sesonger × ti modeller × to chipregimer, totalt 4080 hovedmodellbeslutninger. Modeller: Ridge, Bayesian Ridge, Extra Trees, HGB med grunnvariabler, HGB med utvidelser, Ridge/Extra Trees 50/50, Ridge/utvidet HGB med HGB-vekt 25/50/75 %, og treveis lik blanding.

50/50 Ridge + Extra Trees ga +37,17 uten chips / +55,67 med fast kalender mot Ridge, med positiv gevinst i 5/6 og 4/6 sesonger. Fritt modellvalg kun ut fra eldre sesonger ga +3,75/+2,25 i fire evalueringssesonger. Beskrivende vinner og tidsordnet modellvalg er ulike sammenligninger. Ingen urørt holdout gjenstår i disse dataene. Ingen produksjonsmodell er automatisk byttet.

Utvidet HGB mot enkel HGB ga +15,17 poeng uten chips og −6,50 med chips. Det er en samlet featurepakke, ikke en isolert xG-effekt. Eget lags/motstanderens mål for/mot, Elo og lagget xG finnes; `starts_m6` er en 60+-minuttersproxy. Enkle målrateprodukter og `exp(-lambda_against)` er ikke en kalibrert Dixon–Coles-modell.

## Hva som ble gjort ved GitHub-integrasjonen

- Mai-repositoryet gjennomgått og bevart; nytt arbeid integrert under `research/current`.
- Hele aktive forsøket med rådata, startinnganger, prognoser, 120 beslutningsspor og resultattabeller flyttet inn.
- Individuelle gzip-innganger med SHA-256 og automatisk klargjøring erstatter manuell ZIP-utpakking.
- Residualideen implementert som opt-in HGB-kandidat og kjørt som separat prediksjonstest. RMSE bedret seg bare i 1/6 sesonger mot direkte HGB; ingen ny sluttscore påstås.
- Eldre API-/feature-/ensemblekode beholdt. Metodeproblemene er dokumentert i REPOSITORY_REVIEW, ikke skjult ved å overskrive gamle resultater.

## Bekreftede aktive utfordrere

Brukeren bekreftet 6. oktober 2026 at `re_refresh_h3` og `constant` skal videreføres som aktive utfordrere. Reglene og evidensen er registrert i [challengers.json](../research/current/challengers.json). Den opprinnelige referansen beholdes som historisk kontroll. [Kombinasjonsforsøket](NEXT_EXPERIMENT.md) er nå fullført med 16 nye forløp. Kombinasjonen har +70,0 med chips mot referansen, men ustabil tilleggsverdi over global H1; brukeren har deretter valgt den som ny arbeidsbenchmark.

## Siste forsøk: posisjonsspesialisering

Fullført 6. oktober 2026: **32 nye forløp** mot `constant_h3` på 2022/23–2025/26. Posisjonsbestemte blandingsvekter gir −42,50 poeng med chips; egne posisjons-HGB gir −83,50; global/posisjons-HGB 50/50 gir −3,00. De to første taper alle fire sesonger. Hybriden har +53,25 uten chips, men bredt intervall [−0,25; +134,00] og en stor gevinst i 2023/24. Benchmarken beholdes. Hybriden lagres som forskningskandidat for uten-chips-regimet, ikke ny primær utfordrer.

Alle åtte benchmarkforløp gjenskaper nøyaktig beslutninger og poeng. 1088 beslutninger er kontrollert; syv målrettede tester består ved direkte kjøring. [Rapport og kontroller](../research/current/position_specialist/README.md), [sesongresultater](../research/current/position_specialist/results/all_seasons.csv). Ingen urørt holdout eller ny produksjonsmodell.

## Siste forsøk: historisk kampkalender

Fullført 6. oktober 2026: 82 historiske kalenderuttrekk er rekonstruert ved 136 beslutningstidspunkter. Med grense på 14 dagers alder er dekningen 31/34, 33/34, 33/34 og 8/34 runder i 2022/23–2025/26. Sluttkalender brukes bare til datakontroll, ikke fremtidsprognoser.

En isolert test av fremtidig **antall kamper** gir `calendar_count_h3` **2343,75 poeng med chips (+35,50 mot constant_h3)** og 2218,25 uten chips (+45,50). Sesonggevinst med chips: −29, +143, +28, 0. Primært 95 %-intervall [−14,75; +107,25]; ingen urørt holdout. Alle 8 kontrollforløp gjenskapes nøyaktig. Benchmarken beholdes, kalenderkandidaten registreres som lovende forskning.

[Kalenderrevisjon](../research/current/calendar_audit/README.md), [forsøksrapport](../research/current/calendar_counts/README.md). Nåværende rundeprognoser og frister beholder gamle proxybegrensninger. Neste steg: bedre arkivdekning og motstander/hjemme-borte i egen ablasjon. Lesbare CSV-/JSON-arkiver gjenopprettes automatisk av `scripts/prepare_data.py`; nye prognoser regenereres av forsøksbyggeren.

## Prioritert neste arbeid

Oppdatert etter første kalenderforsøk:

1. Bruk `constant_h3` som ny arbeidsbenchmark for alle kommende forsøk, i tråd med brukerens beslutning. Behold `re_refresh_h3`, `constant` og den gamle frosne referansen som kontroller. Rapporter gevinst mot ny benchmark på samme evalueringssesonger; ingen omskriving av historiske resultater.
2. Prioriter før-frist-kalender/tilgjengelighetsdata og en låst prospektiv evaluering. Flere historiske vekt-/horisontsøk gir ikke en urørt bekreftelse.
3. Gjør håndtering av likeverdige valg mer deterministisk før praktisk bruk. Global H1 gjenskaper arkivet i kombinasjonstesten, men tidligere motoravvik viser at dette fortsatt er relevant.
4. Første kalenderablasjon er fullført med positiv, men ujevn gevinst. Forbedre særlig 2025/26-dekningen og test deretter motstander/hjemme-borte i en separat ablasjon. Faktiske frister og aktuell kalender trenger en ny felles baseline.
5. Gate og nye spilleres roller/tilgjengelighet er fortsatt forskning. Ingen nye terskler eller blandingsvekter er valgt etter siste resultater.

Rapporter nettosesongpoeng med chips som forhåndsbestemt primærmål, treffkostnad, usikkerhet og sesongvise forskjeller. Uten chips er diagnostikk. Samme starttilstand og samme beslutningsmotor skal brukes for å isolere modellendringer.

## Reproduksjon og begrensninger

Se rot-README. `prepare_data.py` må kjøres før forsøkene på ny maskin. Prognosebygging bruker lokale rådata. Modellkandidater og dataendringer skal ha separate protokoller/resultater; gammel trace-cache må ikke brukes ved endringer.

Historiske poeng, moderne chips/FT-regler; priser er laggede proxyer; skader og spilleravganger er ufullstendige; endelig historisk kamptildeling i aktuell GW antas kjent ved frist. Dette er forskningssimulering, ikke dokumentert faktisk rank eller topp-prosent-sannsynlighet. De gamle Parquet-LFS-filene er ikke nødvendige for det aktive forsøket.

## Siste verifikasjon

156 tester bestått etter klargjøring (152 eksisterende funksjonstester, reparert mappestrukturtest og tre nye forskningstester). 367 deprecation/future-advarsler fra eldre pandas-kode; ingen testfeil. De 47 pakkede inngangene er kontrollert mot både lagret og gjenopprettet SHA-256. Residualpiloten er gjennomført for alle seks sesonger. GitHub Actions er konfigurert for samme testkommando; lokal teststatus er ikke det samme som bekreftet CI-status.


## Litteraturgjennomgang

Se [LITERATURE_REVIEW.md](LITERATURE_REVIEW.md) for primærkilder, kildekritikk og prioriterte forsøk. Flerukers planlegging, prognosediversitet og separat angrep/forsvar er prioritert. Crowd-signaler og beslutningsrettet læring er videre kandidater. ORiON-artikkelens topp-4 %-resultat har et dokumentert chipavvik; det brukes ikke som regelkorrekt benchmark. Ingen nye modeller er trent eller ny sluttscore produsert i litteraturgjennomgangen.


## Oppsidetest fullført

Se [forsøksrapporten](../research/current/upside/README.md). Fire kandidater er trent og kjørt gjennom 48 nye sesongforløp: ren oppside, 25 % oppsideblanding, relevansvektet HGB og 50 % relevansvektet blanding. Alle taper i gjennomsnitt mot Ridge/Extra Trees 50/50: henholdsvis −163,7/−134,2, −56,5/−35,0, −72,5/−100,2 og −46,7/−53,5 poeng uten/med fast chipkalender. Ingen produksjonsendring.

Topp-20-treff på 8+ forbedres opptil 0,67 prosentpoeng, men billige spillere og kort historikk får ikke bedre treffandel. Tidsordnet modellvalg beholder referansen i alle fire evalueringssesonger. Ren oppside er ikke kalibrert forventet totalpoeng; endret scoreskala påvirker også byttevilje. Ingen urørt holdout.

Kode, protokoll, prognoser, 48 spor, usikkerhet og kontroller er lagret under `research/current/upside`. 156 eksisterende tester og tre nye tester bestått lokalt. Kontroll-HGB gjenskaper alle tidligere prognoser nøyaktig. Neste arbeid bør prioritere eksisterende plan for flerukers optimizer og bedre minutter/rolle-signaler fremfor å lete videre etter blandingsvekter på samme fasit.


## Oppside som variabel og kapteinssignal fullført

[Oppfølgingstesten](../research/current/upside_feature/README.md) bruker tidsriktige historiske oppsideprognoser: indre modeller trener bare på eldre sesonger. Matchede hovedmodeller med/uten ekstra variabel får identiske treningsrader. 2019/20 og 2020/21 bygger treningsgrunnlaget, og fem sesonger 2021/22–2025/26 evalueres med 40 nye hovedmodellforløp og 10 isolerte kapteinsreplay.

Variabelen gir −12,0/+13,6 poeng mot matchet HGB-kontroll uten/med chips. I 50/50-blanding med sterk referanse gir den +27,2/−34,0 mot kontrollblandingen, men oppsideblandingen taper fortsatt −11,0/−37,6 mot sterk referanse. Kapteinsfilter innen 0,5 forventede poeng gir −5,0/+5,8, med brede intervaller over null. Ingen robust vinner og ingen produksjonsendring. Ingen egen hard kjøpspoolavgrensning ble testet.

Alle fem sesonger var allerede undersøkt; ingen urørt holdout. Kode, protokoll, historiske oppsidevariabler, prognoser, spor, kapteinsvalg og parete resultater er lagret under `research/current/upside_feature`. 162 tester bestått lokalt. Videre arbeid bør prioritere bedre informasjon og flerukers optimizer fremfor å tune oppsidesignalet på samme sesongfasit.


## Fire-runders planlegging og dekomponert oppside fullført

[Rapport](../research/current/horizon_upside/README.md): seks sesonger × tre modeller × to horisonter × to chipregimer = 72 nye forløp. Full flertrinns bytteplan med bank og eksakte FT-overganger; bare første handling utføres. Fremtidig kamparkiv mangler før-frist-snapshots, så prognosene bruker én nøytral kamp per fremtidig runde og gradvis tilbakevending mot nøytral motstander, uten fremtidige utfall eller prognoser.

Dekomponert forventning `p*E[Y|Y>=8]+(1-p)*E[Y|Y<8]` gir +30,0/+72,5 mot vanlig HGB ved én-rundesplanlegging, med seier i 3/6 og 5/6 sesonger. Den taper fortsatt −45,8/−18,5 mot matchet sterk H1-referanse. Ved H4 taper dekomponert modell −40,0/−15,2 mot vanlig HGB. Ingen ny totalvinner.

H4 mot matchet H1: Ridge/Extra −22,0/+25,3; HGB +37,3/+35,3; dekomponert −32,7/−52,3 (uten/med chips). Sterk H4 er best med chips, men ikke robust på tvers av regimer. Ingen produksjonsendring. De 287 tidsbegrensede H4-beslutningene (maks gap 1,552 %) gjør at små gevinster må kontrolleres med strammere solver før eventuell bruk.

168 tester bestått på ferdig kode. Alle 2448 beslutninger har gjennomførbart oppgjør og identisk åpning. Prognoser, kilde-/inputfingeravtrykk, 72 spor med fremtidige planer, sesongvise effekter, solverdiagnostikk og usikkerhet er lagret under `research/current/horizon_upside`. Ingen urørt holdout. Dekomponert modell blandet med sterk referanse er ikke testet her.


## Løpende retrening og hendelsesmodell fullført

[Rapport](../research/current/adaptive_events/README.md). Ni forhåndsbestemte kandidater, seks sesonger og to chipregimer ga 108 nye forløp. Primærmålet ble fast chipkalender; uten chips diagnostikk. Modeller trenes hver fjerde GW med kun før-frist-utfall, mot frosne kontroller. Selvstendig modell for 0/1–59/60+ minutter og betingede mål/assists/CS-/øvrige poeng. Tre faste blandinger inkludert.

Utvidet HGB med retrening er beskrivende primærvinner: 2224,7 poeng, +8,3 mot sterk referanse. Bare 3/6 seire, intervall [−62,7; 79,7], tap i de to siste sesongene. Ingen robust ny totalvinner; behold som utfordrer uten produksjonsendring. Tidsordnet modellvalg beholder referansen i alle fire primære evalueringssesonger (0 gevinst).

Det tydeligste funnet er retrening av vanlig HGB: +54,7 med chips / +85,8 uten mot samme sesongfrosne HGB, med 5/6 seire i begge regimer. 365-dagers tidsvekter svekket modellen. Oppdatert hendelsesmodell tapte −89,2/−51,0 mot sterk referanse; direkte/hendelsesblanding ga −21,5/+22,2. Blandingens treff blant billige spillere bedret seg, men primær sesongscore falt.

Neste kontrollforsøk kan teste retrening også av den sterke referansefamilien, samtidig som utvidet oppdatert HGB beholdes som selvstendig utfordrer. Hendelsesmodellen trenger komponentdiagnostikk og bedre rolle-/tilgjengelighetsdata. Ingen blending av nye undergrupper etter fasit. Data for xG starter i 2022/23; manglende verdier ble ikke fylt med framtidig informasjon.

172 tester bestått; 60 tidsriktige treningsvinduer kontrollert; alle 3672 nye beslutninger har optimal solverstatus innen toleransen. Kode, prognoser, treningsauditer, 108 spor og resultater ligger i `research/current/adaptive_events`. Ingen urørt holdout.


## Retrening av Ridge/Extra Trees og faste blandinger fullført

[Rapport](../research/current/retrained_ensemble/README.md). Fire nye kandidater og én matchet frossen treveiskontroll ga 60 nye sesongforløp. Utvidet HGB gjenbrukes uendret fra forrige runde. Samme før-frist-treningsvinduer, variabler, optimizer og åpning. 108 forløp sammenlignes totalt.

Retrenet Extra Trees er beskrivende primærvinner: 2253,5 poeng, +37,2 mot referansen, 4/6 seire og beskrivende 95 %-intervall [1,5; 73,3]. Den vinner i de tre siste sesongene. Retrenet 50/50 gir +30,5 og treveis +26,3. Retrenet Ridge alene gir −7,0. Extra Trees og Ridge forbedrer sine egne frosne kontroller med +68,8/+48,7, begge 5/6 seire.

Uten chips snur retreningseffekten for Extra og Ridge: −28,2/−14,7 mot egne kontroller. Mot sterk referanse gir Extra −39,0 og 50/50 −30,0. Treveisblandingen gir +10,3 uten chips, men −1,5 mot sin matchede frosne treveiskontroll. Ingen universell blandings- eller retreningsgevinst er dokumentert. Tidsordnet modellvalg gir −4,25 med chips og −10,25 uten. Ingen automatisk produksjonsendring.

Retrenet treveisblanding øker topp-20-treff på 8+ fra 23,97 % til 25,18 %, men dette forklarer ikke alene sesongscore. Behold Extra Trees som primær utfordrer og treveis som utfordrer på tvers av regimer. Neste spor er samspillet med chips/troppsendringer og prospektiv evaluering med låste regler.

173 tester bestått lokalt; 60 tidsriktige treningsvinduer, 2040 nye beslutninger og identisk åpning kontrollert. Alle nye solveravgjørelser er optimale innen toleransen. Kode, prognoser, auditer, 60 spor og resultater er lagret under `research/current/retrained_ensemble`. Ingen urørt holdout eller bekreftet GitHub CI-status.


## Chipmekanismer og scenariodiagnostikk fullført

[Rapport](../research/current/behavior_diagnostics/README.md). 12 prognosemodeller, 140 455 planlagte spiller–runder, 4536 nye beslutninger fra identisk referansetilstand og 144 nye chipablasjonsforløp. Ingen ny modelltrening. Opprinnelig diagnostikk låst før resultater; separat eksplorativ chipablasjon spesifisert etter de første regnskapsfunnene.

Extra Trees-retrening gir −28,2 uten chips og +68,8 med chips mot egen frossen kontroll: omslag +97,0. Direkte ekstra TC/BB-poeng forklarer bare +1,5; +70,7 kommer fra vanlig ellever, +18,2 vanlig kaptein og +6,7 endret treffkostnad. Mot sterk referanse er omslaget +76,2 og direkte bonuser −2,0. Dette er bokføring, ikke kausal allokering til tidligere bytter.

Kontrollerte hele-sesongablasjoner (retrent minus egen frossen): WC alene gir Ridge +20,0, Extra +39,0, 50/50 +31,2. WC+FH gir +37,8/+31,0/+44,8. TC+BB gir −9,2/+15,7/−6,5. Det finnes store samspillseffekter; mekaniske poengmultiplikatorer alene forklarer ikke resultatene. Fra identisk tropp gir retrent Extra bedre umiddelbare WC-valg, men dette gjelder ikke Ridge. Langsiktig troppshistorikk er viktig.

RMSE blant samme referanse-topp60 bedres litt av retrening av både Ridge og Extra i 6/6 sesonger, selv om deres chipfrie sesonggevinst faller. Utvidet HGB slår sterk referanse i topp10-rangering ved fallende minutter (+0,369 faktisk poeng per valgt spiller) og rotasjon (+0,270), begge 6/6 sesonger. Treveisblandingen gir +0,116 i samlet topp20 (5/6) og lavere relevant RMSE (6/6). Retrenet Ridge/Extra sliter relativt ved kort historikk; ingen gjennombruddsmodell er dokumentert. Dobbeltrunder er lovende for treveis, men har få kvalifiserende runder.

Ingen situasjonsstyrt ekspertregel er trent eller tatt i bruk. Scenarioer er overlappende og utforsket på kjente sesonger; konsistens er ikke en korrigert signifikanstest. 176 tester bestått lokalt. Alle nye 4536 matchede og 4896 ablasjonsbeslutninger har optimal status innen toleransen; 408 kontrollvalg gjenskaper arkivet. Kode, protokoller, scenariodata, beslutningsspor, auditer og fingeravtrykk er lagret under `research/current/behavior_diagnostics`. GitHub CI-status er ikke verifisert.


## Tre-rundersplanlegging og lært HGB-spesialist fullført

[Rapport](../research/current/decision_specialist/README.md). 72 nye H1/H3-forløp for frossen referanse, oppdatert Extra Trees og oppdatert Ridge/Extra 50/50 over seks sesonger. 16 nye gate-/globalvektforløp over fire sesonger, med to innledende metatreningssesonger. Primærmål er fortsatt nettosesongpoeng med fast chipkalender.

H3 med oppdatert 50/50 gir 2267,3 med chips, +51,0 mot referansen, 5/6 seire, beskrivende intervall [11,8;87,0]. Uten chips +31,2, 4/6, intervall over null. Mot egen H1 er gevinsten +20,5/+61,2 med/uten chips; primærintervallet inkluderer null, uten chips er intervallet [30,0;92,5]. Frossen referanse og Extra Trees får ingen stabil H3-gevinst. Kandidaten taper −37 mot referansen siste sesong. Tidsordnet primærvalg gir +35,5 over fire sesonger; uten chips −7,25.

Gate er en sigmoid-vekt mellom oppdatert 50/50 og utvidet HGB, med før-frist-spilletid og endring i spilletid. Globalvektkontrollen lærer bare konstantleddet. Begge bruker identiske eldre, tidsriktige komponentprognoser og labels tilgjengelige før GW1; ingen labels fra evalueringssesongen. Evalueringssesonger 2022/23–2025/26. Global HGB-vekt øker fra 42,5 % til 49,4 %; gate gir omtrent 55–59 % til HGB i rotasjonsgruppen.

Gate gir +62,0/+12,0 mot referansen med/uten chips; global vekt +54,25/+40,5. Begge vinner 4/4 med chips. Gate mot global kontroll er bare +7,75 med chips, bredt intervall [−68,25;62,5], og −28,5 uten. Gate mot fast treveis er +21,0/−22,5. Supplerende, etterfølgende benchmark mot retrent Extra på samme fire sesonger gir gate +7,5 med chips, men bare 1/4 seire; global vekt −0,25 med chips og +67,5 uten. Ingen robust generell ekspertregel er dokumentert. Tidsordnet gate/global/treveis-valg gir +28,5 med chips over bare to sesonger, +8,5 uten.

Fremtidsprognosen er en nøytral proxy: gammel frossen referansenøytral rate pluss aktuell oppdatert per-kamp-forskjell; aktuell kampeffekt halveres fremover, én kamp per runde. Blank aktuell runde bruker referansens nøytrale fallback. Ingen faktisk arkivert fremtidig før-frist-kalender. H3 kan ikke selge og gjenkjøpe en opprinnelig spiller innen samme plan. Samme historiske pris-/tilgjengelighets-/chipregelbegrensninger som før.

H1-motorparitet er eksplisitt målt. 50/50 gjenskaper alle gamle troppsvalg og sesongscorer; Extra/ref kan avvike gjennom likeverdige valg og små solvertoleranser. Dette er ikke horisontgevinst. Alle 2992 nye beslutninger er optimale innen sine toleranser, største H3-gap omtrent 1e-5. 179 tester bestått lokalt. Prognoser, koeffisienter, eldre-sesong-auditer, 88 spor, usikkerhet, valg og fingeravtrykk ligger i `research/current/decision_specialist`. Ingen urørt holdout eller bekreftet CI-status. Globalvekt+H3 er et forslag, ikke et utført forsøk.


## Global HGB-vekt med H3 fullført

[Rapport](../research/current/global_horizon/README.md). 16 nye forløp, 544 beslutninger, 32 forløp i matchet 2 × 2-design og 56 inkludert eksterne kontroller. Samme fire sesonger 2022/23–2025/26, samme lærte globale vekter, samme planlegger og fremtidsproxy. Ingen ny modelltrening.

Global H3 gir 2308,25 med chips, +70,0 mot referansen (4/4, beskrivende intervall [23;106,5]), og 2172,75 uten, +23,75 (3/4). Mot global H1 er det +15,75 med chips (bare 1/4, intervall [−10;58,25]) og −16,75 uten. Sesongvise primære horisonteffekter er −1,−13,+78,−1. Mot Ridge/Extra H3 er det +34,5 med chips (2/4) og −1,25 uten. Mot retrent Extra er det +15,5/+50,75, med brede intervaller over null.

Samspill mellom globalvekt og H3 er +21,25 med chips, usikkert, men −78,25 uten og negativt i alle fire sesonger. Tidligere forbedringer kan ikke summeres. Global H1 gjenskaper alle åtte gamle globalvektspor med samme tropper og poeng. Alle 544 nye beslutninger er optimale innen toleransen, maks gap 9,55e-6. Poengregnskap, starttilstand, spillerkobling og matchede før-frist-prognoser er kontrollert. Tre relevante eksisterende regresjonstester er kjørt på nytt og består; ingen ny full testkjøring påstås.

De to bekreftede utfordrerne beholdes; `constant_h3` legges til som forskningskandidat. Kode, protokoll, prognoser, spor, parete resultater og hashkontroller er lagret under `research/current/global_horizon`. Ingen produksjonsendring, urørt holdout eller verifisert GitHub CI-status.
