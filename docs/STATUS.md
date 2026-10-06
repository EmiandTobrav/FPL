# Fortsett her

Oppdatert 6. oktober 2026. Brukeren ønsker GitHub som sentral for kode og fremgang på tvers av enheter. Denne mappen og repositoryet skal være tilstrekkelig kontekst uten den gamle samtalen eller ZIP-filene.

## Mål og avklaringer

Maksimer robust FPL-sluttscore etter at hovedmodellen tar over fra startmodellen. Test enkeltmodeller, faste og lærte prognosekombinasjoner, og separate variabler for motstanderens angrep og forsvar. Startmodellens overlevering skal inneholde den faktiske troppen, bank, kjøpspriser og gratisbytter. Ikke tilpass startlaget til et kunstig idealmottakerlag. Startstrategiens delmål ved GW8,12,15,19 beholdes separat.

Kvantifisering av elite-managere var et tidligere spor. Brukeren gikk videre til hovedmodellen; dette er nå hovedprioriteten. Rå elite-eierskapsarkiv er ikke nødvendig for gjeldende eksperiment og er ikke flyttet inn som aktivt datasett.

## Gjeldende referanse

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

## Prioritert neste arbeid

Oppdatert etter chip- og scenariodiagnostikken:

1. Test hvordan oppdaterte prognoser omsettes i lønnsomme troppsendringer over flere runder. WC/FH-ablasjonene viser at dette er sentralt: 50/50-retrening gir −30,0 uten chips og +44,8 med bare WC/FH. Ikke tune chipdatoer på samme sesonger; flerukers forsøk trenger før-frist-kalenderdata.
2. En tidsordnet trent ekspertblanding med utvidet HGB ved fallende/ustabil spilletid er en konkret hypotese. Lær eventuell vekting på eldre treningsprognoser og sammenlign mot låst treveisblanding. Diagnostiske undergrupper er ikke i seg selv en validert kjøps-/kapteinsregel.
3. Skaff før-frist-data om roller, tilgjengelighet, registrering og kampkalender. Kort historikk er ikke løst av vanlig retrening eller de nye blandingene.
4. Behold retrent Extra Trees og treveisblandingen som låste utfordrere. Prospektiv evaluering er nødvendig etter mange undersøkelser av de samme seks sesongene; ingen automatisk produksjonsendring.
5. Hendelsesmodellen trenger fortsatt kalibrerings-/komponentdiagnostikk før mer kompleksitet. Ikke gjør nye brede parameter- eller blandingsvektssøk på samme fasit.

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
