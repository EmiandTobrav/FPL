# Litteratur og forsøksprioritering

Gjennomgått 6. oktober 2026. Formålet er å finne testbare forbedringer til hovedmodellen etter GW4. Dette er en målrettet litteraturgjennomgang, ikke en uttømmende systematisk oversikt. Ingen nye modellresultater for vårt prosjekt er produsert i denne gjennomgangen.

## Hva har andre faktisk lykkes med?

### 1. Sekvensielle beslutninger i FPL

**Matthews, Ramchurn og Chalkiadakis (AAAI 2012), “Competing with Humans at Fantasy Football”.** Historisk evaluering over 30–50 gjentakelser av 2010/11, med modellparametere lært fra 2009/10. Den enkleste manageren fikk gjennomsnittlig 1981,3 poeng; beste Bayesian Q-learning-variant 2068,5, tilsvarende omtrent plass 26 065 / topp 1,1 %. Mellomvariantene endret priors, kandidatgenerering og planlegging. Hele forskjellen kan derfor ikke tilskrives lengre horisont. Dette er simulering av én gammel sesong, ikke dokumentasjon av vedvarende live-rangering.

**Vår tolkning:** Sterk tematisk støtte for å teste flere runder og usikre fremtidsforløp. Begynn med en enklere rullerende MILP-horisont før full reinforcement learning.

[Kilde: fulltekst, særlig §5 og tabell 1](https://ojs.aaai.org/index.php/AAAI/article/view/8259/8118). Bruk konferanseåret 2012; nettsidens publiseringsmetadata viser også en senere registreringsdato.

### 2. Enkle blandinger vant M5

**Makridakis, Spiliotis og Assimakopoulos (International Journal of Forecasting 2022), M5 Accuracy.** Vinneren brukte LightGBM med forskjellige grupper av treningsdata og direkte/rekursive prognoser. Det ble trent 220 modeller totalt, men hver serie fikk et likt vektet gjennomsnitt av seks prognoser. Valideringen brukte flere tidsvinduer og både gjennomsnittlig feil og variasjon i feil.

**Vår tolkning:** Test prognosediversitet, ikke bare flere algoritmenavn: global modell, posisjonsmodell, kort/lang treningshistorikk og direkte horisonter. Faste vekter er en sterk referanse. Dette var detaljhandel, ikke FPL. Tweedie-tapet som ble brukt kan ikke ukritisk overføres til totale FPL-poeng, som også kan være negative.

[Kilde: artikkel](https://doi.org/10.1016/j.ijforecast.2021.11.013) · [Fulltekst av forfatterversjon, §5](https://statmodeling.stat.columbia.edu/wp-content/uploads/2021/10/M5_accuracy_competition.pdf).

### 3. Boosting med gjennomarbeidede lagratings vant en fotballkonkurranse

**Hubáček, Šourek og Železný, “Learning to predict soccer results from relational data with gradient boosted trees” (Machine Learning, publisert online 2018).** Vinnerløsningen i Soccer Prediction Challenge 2017 kombinerte konstruerte features med gradientboostede trær. Datagrunnlaget omfattet over 200 000 historiske kamper; pi-ratings og en PageRank-basert rating var blant signalene. Oppgaven gjaldt fremtidige kampresultater.

**Vår tolkning:** Oppdaterte og motstanderjusterte lagratings fortjener en egen ablasjon. Dette viser ikke at boosting alene slår våre spillerprognoser. Fulltekst var ikke tilgjengelig gjennom forlagssiden; funnene her er begrenset til forfatterabstractet.

[Kilde](https://link.springer.com/article/10.1007/s10994-018-5704-6).

### 4. Mangfoldig crowd kan være bedre enn historiske eksperter

**Bhatt mfl. (ICWSM 2019), “Who Should Be the Captain This Week?”** SmartCrowd valgte deltakere ut fra forskjeller i tekstene de publiserte, og kombinerte vurderingene. Forfatterne rapporterer at gruppen slo tilfeldige grupper, 93 % av enkeltpersonene i utvalget og grupper av de historisk beste 10–20 %. Dette gjelder kapteinsprognoser i studiens utvalg, ikke 93 % av alle FPL-managere eller en full sesongstrategi.

**Vår tolkning:** Dersom elite-manager-sporet gjenopptas, bør vi teste diversifisert konsensus mot ren historisk rangering. Lik laghistorikk kan avsløre at mange managere representerer samme signal. Overføringen fra tekstlig diversitet til lagvalg er vår hypotese. Fulltekstkontroll gjenstår; resultatet over er fra originalabstractet.

[Kilde](https://ojs.aaai.org/index.php/ICWSM/article/view/3213).

### 5. Lær for beslutningen, ikke bare prediksjonsfeilen

**Elmachtoub og Grigas, “Smart Predict, then Optimize” (Management Science 68, 2022; online 2021).** SPO/SPO+ lærer prediksjoner med hensyn til tapet de skaper i en etterfølgende optimering. Forsøk på korteste-vei- og porteføljeproblemer viste bedre beslutninger enn ordinær prediksjonstrening i de undersøkte oppsettene, særlig ved feilspesifiserte modeller. Dette er ikke FPL-evidens.

**Vår tolkning:** Nettosesongpoeng må være modellvalgets hovedmål. Før dyr SPO+-trening kan vi teste en enklere beslutningsrettet validering av ensemblevekter. Kapteins- og kjøpsfeil bør diagnostiseres separat; en forbedring blant mange uaktuelle nullpoengsspillere kan dominere global MAE uten å hjelpe laget.

[Kilde](https://doi.org/10.1287/mnsc.2020.3922) · [Forfatterpreprint](https://arxiv.org/abs/1710.08005).

### 6. Motstanderens angrep og forsvar kan modelleres separat

**Dixon–Coles (JRSS C, 1997)** bruker en Poisson-basert modell med dynamiske lagprestasjoner; studien rapporterte positiv avkastning i sin historiske oddsundersøkelse. **Baio–Blangiardo (Journal of Applied Statistics, 2010)** gir en hierarkisk modell med særskilte angreps- og forsvarseffekter, og drøfter problemet med at ekstreme lag trekkes for mye mot gjennomsnittet.

**Vår tolkning:** Bruk metodene som strukturelle kandidater, ikke som løfte om betting- eller FPL-suksess. Estimer eget angrep mot motstanderens forsvar og omvendt; avled forventede mål og clean-sheet-sannsynlighet. Sammenlign med nåværende Elo/EWMA og en enkel regularisert Poisson-modell før full Bayes. Baio-artikkelens posterior-prediktive tilpasning er ikke det samme som en urørt fremtidstest.

[Kilde Dixon–Coles](https://doi.org/10.1111/1467-9876.00065) · [Baio–Blangiardo fulltekst](https://discovery.ucl.ac.uk/16040/1/16040.pdf) · [Forfatterens metodekommentar](https://gianluca.statistica.it/research/football/).

### 7. Motspillernes valg er viktig når målet er en premie eller plassering

**Haugh og Singal (Management Science 2021), “How to Play Fantasy Sports Strategically (and Win)”.** Modellen tar hensyn til andres lagvalg og utbetalingsstruktur. I NFL-fantasy 2017 ga den strategiske varianten $280,74 i nettoresultat mot $91,50 for referansen i konkurranser med store toppremier. Den var dårligere enn referansen i de to øvrige konkurransetypene. Forfatterne understreker usikkerheten ved én sesong.

**Vår tolkning:** Eierskap og korrelasjoner er aktuelle ved mål om å slå en rival eller nå en bestemt plassering. Ved maksimering av forventede poeng for en fast ellever er forventningen summen av spillerforventningene; korrelasjon endrer ikke denne summen. Ikke belønn lavt eierskap eller flere spillere fra samme lag automatisk i vår nåværende poengmodell.

[Kilde: forfatterversjon, §6 og tabell 1](https://www.columbia.edu/~mh2078/DFS_Revision_1_May2019.pdf).

## Funn som ikke bør brukes som ukritiske suksessbevis

**Venter og van Vuuren (ORiON 2024)** rapporterer 2307 poeng og topp 4,08 % i en retrospektiv 2020/21-test. Men §5.4 beskriver Bench Boost og Triple Captain brukt sammen i GW35, mens §5.1.4 selv sier høyst én chip per GW. Tabellen viser også 170 bytter og 448 straffepoeng. Ideen om ensembleprognoser og lengre planlegging er interessant; rangeringen er ikke en ukvalifisert regelkorrekt referanse før chipavviket er avklart/reprodusert.

[Kilde: fulltekst, s. 91 og 99 / PDF-side 23 og 31](https://orion.journals.ac.za/pub/article/download/753/648).

**Ramezani og Dinh, arXiv:2505.02170v3 (3. januar 2026)** finner at robusthet og hybridskår ikke er jevnt overlegne, og fremhever ARIMA i sitt oppsett. Konklusjonen omtaler bytter, chips og dynamisk kaptein i rullerende planlegging som videre arbeid. Vi bør derfor ikke lese dette som en ferdig validert, full FPL-sesongmotor. Versjon 3 er vurdert; konklusjonene skiller seg fra versjon 1.

[Kilde](https://arxiv.org/html/2505.02170v3).

**Grinsztajn, Oyallon og Varoquaux (NeurIPS 2022)** sammenlignet modeller på 45 tabelldatasett og fant sterke trebaserte resultater på middels store data. Dette støtter dem som referanser, men avgjør ikke hvilke moderne nevrale modeller som kan vinne på våre data.

[Kilde](https://papers.neurips.cc/paper_files/paper/2022/hash/0378c7692da36807bdec87ab043cdadc-Abstract-Datasets_and_Benchmarks.html).

**Hewamalage mfl., “A Look at the Evaluation Setup of the M5 Forecasting Competition” (2021)** viser at modellrangeringer kan være følsomme for aggregering, skalering og prisvekting. En konkurranseseier er et konkret resultat i ett evalueringsoppsett, ikke et universelt bevis.

[Kilde](https://arxiv.org/abs/2108.03588).

## Konkret plan for vårt prosjekt — egne forslag, ikke publiserte FPL-gevinster

| Prioritet | Avgrenset forsøk | Hold fast | Avgjørende måling |
|---|---|---|---|
| 1 | Rullerende horisont 1, 3 og 5 runder, med eksplisitt verdi av bankede gratisbytter og resttropp | Ridge og Ridge/Extra Trees 50/50 testes separat; samme start og chipregime | Nettopoeng, hits og sesongvis gevinst |
| 2 | Faste blandinger av global boosting, posisjonsmodell og enkel lineær modell | Samme features, data og optimering | Poenggevinst og feilkorrelasjon målt på tidligere valideringsvinduer |
| 3 | Estimert angrep/forsvar: regularisert Poisson, deretter Dixon–Coles/hierarkisk kandidat | Samme spillerprognosemodell; legg til én featuregruppe av gangen | Kalibrering av mål/clean sheets og FPL-poeng |
| 4 | Sannsynlighet for 0, 1–59 og 60+ minutter, med betingede hendelsesrater | Øvrige modeller og budsjetter | Kalibrering, autosubs, kaptein og nettosesongpoeng |
| 5 | Konsensus fra ulike managergrupper som tilleggssignal | Utvalg basert bare på historikk tilgjengelig ved frist | Gevinst utover modellen, ikke bare korrelasjon med poeng |
| 6 | Beslutningsrettet vektvalg; eventuelt SPO+ senere | Samme kandidatsett og beregningsbudsjett | Ytre tidsordnet beslutningsverdi mot faste vekter |

**Forutsetning for prioritet 1:** Dagens fryste input inneholder prognoser beregnet ved hver senere rundes informasjonstidspunkt. Disse må ikke leses fremover som kjent ved dagens frist. Lag egne, daterte horisontprognoser. Uten historiske før-frist-kalendere må en tydelig konservativ proxy brukes, og kalenderfølsomhet rapporteres. Dette er viktigere enn å velge en avansert solver.

**Aktuelle engineered features:** `opp_attack`, `opp_defence`, `team_goal_mean`, `clean_sheet_prob`, `p_start`, `p_60plus`, `expected_minutes`, `days_rest`, lagget kampbelastning, spillerandel av lagets xG/xA, endring i rolle og tilgjengelighet, samt forskjell mellom crowd-prognose og egen prognose. Signalene er forslag og må ha før-frist-proveniens. Spredning mellom modeller er et mål på modelluenighet, ikke en ferdig kalibrert fordeling av faktiske poeng.

**Valg av tapsfunksjon:** MAE retter seg mot betinget median; kvadratisk tap mot betinget gjennomsnitt. For maksimering av forventede poeng er dette et viktig skille. Hendelsesmodeller med ikke-negative mål kan ha andre fordelinger enn totalpoeng, og sannsynlighet for 60+ minutter kan ikke utledes ved bare å sette forventede minutter over/under 60.

**Validering:** Behold GW4-overleveringen, samme regler og likt chipbudsjett. Lær modeller og eventuelle vekter i indre tidsvinduer, evaluer på etterfølgende vinduer, og rapporter alle kandidater og mislykkede forsøk. Separat test av gjennomsnittspoeng og eventuell rank-/risikonytte. Alle seks nåværende sesonger er allerede undersøkt; den nye litteraturen gjør dem ikke til en urørt holdout. Prospektive snapshots trengs for en uavhengig bekreftelse.
