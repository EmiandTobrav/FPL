# Historiske poeng etter 2025/26-regler

Datakontroll utført 6. oktober 2026. **Full historisk omregning er ikke ferdig.** Målet er eksplisitt 2025/26, uavhengig av hvilken sesong som er «inneværende» ved kjøring.

## Rekonstruksjon videreført

[2024/25 med kvalitetsmerket defcon](defcon_2024/README.md) er ferdig: 1 253 utslag, 2 506 tilleggspoeng blant alle spillere. Historiske assists og bonus er foreløpig beholdt.

## Fullført sammenligning

[2025/26-validering](core_2025_validation/README.md): 99,67 % enighet i defcon-poeng på 10 457 komplette utespillerrader; 268 mangler nødvendige felt. Gratisdata videreføres som kvalitetsmerket treningsgrunnlag, ikke eksakt testfasit. Ingen penger brukt; eventuell datatilgang har totalramme 500 NOK.

## Nytt kildefunn

[Kampvise 2024/25-data er nå hentet og kontrollert](core_2024/README.md): 380 kamper og 11 567 rader med defensive tellinger. Dette avhjelper manglene i vårt opprinnelige FPL-arkiv, men definisjonene og ny-regel-BPS er ennå ikke verifisert.

## Verifisert nå

Kjør `python research/current/rescoring_2025/audit.py` fra repositoryets rot etter `scripts/prepare_data.py`.

- Arkivene 2019/20–2025/26 inneholder 185 964 rå spiller-/kamprader, med 380 kamp-ID-er per sesong. Dette inkluderer ubrukte spillere, duplikater og eventuelle manager-rader; det er ikke antall uavhengige treningsobservasjoner.
- Før 2025/26 mangler kolonnene klareringer/blokkeringer/interceptions, taklinger og gjenvinninger i våre filer. Historiske poeng, assists, bonus og samlet BPS finnes.
- 2025/26 har 29 747 unike spiller-/kamprader etter ti duplikater. Ingen duplikater er motstridende i kontrollerte scoringsfelt. Alle poeng gjenskapes nøyaktig med eksisterende kjerneberegning, offisielle assists/bonus og defensive tellinger.
- Bonusfordeling fra registrert BPS stemmer for alle 11 492 spiller-/kamprader med spilletid, fordelt på 380 kamper. Grenseverdier for defensive poeng og bonuslikhet er også kontrollert.

Se [dekning](results/coverage.csv), [avstemming](results/reconciliation.json) og [inputhash](results/input_sha256.json). Koden gjenbruker eksisterende aritmetikk i `project/scoring.py`; den hevder ikke at funksjonen merket 2026/27 er en komplett, uavhengig verifisert 2025/26-regelmotor. Sjeldne regelgrener må testes mot en egen versjonert spesifikasjon.

**Dette er samme-sesong-avstemming, ikke rekonstruksjon av eldre sesongers nye assists/BPS.** 2019/20 har også duplikater som må avklares før historisk omregning. Assistant Manager-rader fra 2024/25 må holdes utenfor vanlig spillerpoengberegning.

## Hva kan omregnes?

| Komponent | Nødvendig grunnlag | Status |
|---|---|---|
| Minutter, mål, clean sheet, baklengs, redninger, kort og straffer | Spillerens faktiske kampstatistikk, posisjon og versjonerte regler | Mye finnes allerede; bevar spillerbaserte clean sheets/baklengs |
| Defensive bidrag | Kampvise CBIT; i tillegg gjenvinninger for MID/FWD | Mangler før 2025/26 i arkivet |
| Assists | Hendelser som kan vurderes etter 2025/26-definisjonen | Gamle assistetiketter er ikke automatisk gyldige |
| BPS og bonus | Target-reglenes BPS for alle spillere på begge lag, deretter rangering med likhetsregler | Gammelt bonusfelt eller samlet BPS alene er utilstrekkelig |

Defensive poeng gis ved terskel per kamp, ikke ved sesongsnitt eller summering av to kamper før terskelen. DEF trenger 10 CBIT, MID/FWD 12 CBIRT. Keeper får ikke defensive bidragspoeng. BPS endret blant annet redninger innenfor feltet, mållinjeklareringer, straffemål og taklinger i 2025/26. En mulig effektiv 2024/25-pilot er gammel BPS pluss eksakte regelendringer, men bare dersom alle berørte hendelser, gamle definisjoner og assistendringer er verifisert. Eldre sesonger krever egne broer for mellomliggende regelendringer.

## Kilder undersøkt

- [Vaastav FPL-arkiv](https://github.com/vaastav/Fantasy-Premier-League): naturlig grunnstamme for historiske spiller-ID-er, kampstatistikk, priser og FPL-etiketter. Lås commit og mål faktisk dekning; README og sesongmapper alene garanterer ikke komplett historikk eller alle BPS-felt.
- [StatsBomb/Hudl Open Data](https://github.com/hudl/open-data): konkurranse- og kampindeks kontrollert. Premier League 2015/16 har 380 kamper; 2003/04 har bare 38. Nyttig åpent hendelsesgrunnlag for pilot/tilleggsmodeller, ikke en komplett rekke av nyere PL-sesonger. StatsBomb-definisjoner er ikke automatisk Opta-definisjoner. Følg kildeangivelses- og lisensvilkår.
- [Wyscouts offentlige forskningsdatasett](https://figshare.com/collections/Soccer_match_event_dataset/4415000/4): alternativt hendelsesgrunnlag fra flere konkurranser. Feltdekning og leverandørforskjeller må kontrolleres før bruk som FPL-fasit.
- [Understat](https://understat.com/): nyttig for offensive hendelser/xG; ikke alene et tilstrekkelig grunnlag for full bonus/defcon-rekonstruksjon.
- [Opta/Stats Perform](https://www.statsperform.com/products/opta-data-feeds/): mest direkte leverandørspor fordi FPL bruker Opta. Historiske felt, definisjoner, dekning og tilgang må bekreftes; ingen betalt tilgang er anskaffet eller garantert.

Primære regelkilder: [2025/26-oversikt](https://www.premierleague.com/en/news/4373187), [BPS-endringer](https://www.premierleague.com/en/news/4362127/whats-new-in-202526-fantasy-changes-to-bonus-points-system), [assistendringer](https://www.premierleague.com/en/news/4362187). Lagre versjonert regelsnapshot ved implementasjon; en levende nettside kan endres.

## Neste gjennomførbare datapilot

1. Lås `ruleset=2025_26` og separate versjoner for spillerpoeng og lag-/bytte-/chipregler. Bevar originale rådata med leverandør, innhentingstid, lisens, commit/hash, kamp-ID og spiller-ID. Historisk posisjon er standard; eventuell ny posisjon er et separat scenario.
2. Lag én rad per spiller/kamp med poengkomponenter og kvalitetsflagg per komponent: `official_target`, `reconstructed_verified`, `estimated`, `missing`. Manglende data skal aldri bli null ved stilltiende utfylling. Krev komplett kamptropp før bonusrangering.
3. Bruk 2025/26 som kontroll av aritmetikk og leverandørmapping. Rekonstruer først et kontrollert utvalg 2024/25-kamper med dokumentert full hendelsesdekning. Sammenlign uavhengig mot offisielle registreringer der de finnes; gjennomfør manuell assistkontroll. Ikke utvid før avvik er forklart.
4. Dersom Opta-ekvivalente hendelser ikke er tilgjengelige, publiser eksakt kjerne separat fra estimerte assists/defcon/bonus. Estimater kan brukes som svakere treningssignal eller i sensitivitetsanalyse, men ikke som eksakt testfasit. Vis utvalgsbias fra manglende dekning.
5. Lær komponenter (minutter, mål/assists, clean sheet, defensive tellinger og BPS-fordeling), og la regelmotoren omsette disse til poeng. Da kan nye regler ofte endres uten å erstatte hele modellgrunnlaget. Felles kampsimulering er nødvendig for konsistent bonus og avhengigheter mellom spillere.
6. Tren og valider tidsordnet. Modeller som fyller hull i eldre etiketter må ikke lære fra fremtidige evalueringssesonger og deretter presenteres som historisk fasit. Endelige hendelser kan brukes til målvariabelen; modellens input må fortsatt være tilgjengelig før fristen. Bruk sesong-/kampblokker, ikke tilfeldig deling av spillerrader fra samme kamp.
7. Kjør den låste nye benchmark-algoritmen på det nye poenggrunnlaget sammen med utfordrerne. Den gamle scoren 2351,50 kan ikke overføres. Behold samme startoverlevering, priser, kalenderinformasjon, solverbudsjett og managerregler i sammenligningen; rekonstrueres startmodellen også, må alle kontroller kjøres på nytt.

Standardiserte poeng gir et mer konsistent læringsmål og potensielt flere brukbare sesonger. Det fjerner ikke endringer i spillestil, posisjoner, priser, spilletid eller gjentatt modellvalg på de samme fire testårene. En låst fremtidig evaluering trengs fortsatt.
