# Historisk beregning etablert; kvalifisering gjenstår

**Ny gjeldende delversjon:** [2025/26 etter 2026/27-reglene](season_2025/README.md)
har 363 kvalifiserte hele kamper og 10 971 poengetiketter. Den har en egen
låst ledger, regel-/kildekvalifisering og helkampbonus. Features og loader
gjenstår. Resten av denne siden beskriver den bevarte opprinnelige beregningen;
den gamle versjonens 489 kandidater og mislykkede globale gater endres ikke.

Dette trinnet bruker gjeldende batch-3-ledger og originale FPL-innganger.
Rådata, fryste labels, modeller og benchmark er bevart. Ingen modelltrening.

## Kontrollert grunnlag

185 573 entydige spillerkamp-observasjoner er samlet fra 2019/20–2025/26,
inklusive kjent ikke-deltakelse. Historisk FPL-posisjon og faktisk klubbside
beholdes. Alle opprinnelige grunnpoeng stemmer med et uavhengig komponentregnskap.
Kontrollen bruker eksplisitte FPL-verdier for clean sheet/baklengsmål og
hashkontrollerte fryste defcon-awards. Offisielle 2025/26-awards legges ikke til
på nytt. Dette validerer originale grunnpoeng, ikke nye historiske BPS-labels.

59 motstridende observasjoner i 2019/20 fixture 275 ble avstemt med den unike
raden på offisiell runde og kickoff, etter eksisterende kildepolicy. Råfiler og
restart-nummerering beholdes. Assistant-manager-rader er ikke spillerdata.

Fullpopulasjonskontrollen fant **12 null-minutt-rader med kort utenfor den
gamle ledgeren**. De må inkluderes med avklarte endringsledd før fullføring.
To kildespørsmål er også registrert: 2021/22 fixture 263 har kickoff 15:00 i
historikken og 15:30 i kampregisteret; fixture 8 har Shane Duffys BPS som 28
i historikken og 29 i kampregisteret. Ingen verdi er overskrevet.

Historisk bonus kontrolleres mot hele det observerte scoring-relevante
kampinventaret. Ett avvik finnes: Duffy har publisert bonus 1, mens
historikkens BPS 28 gir bonus 0. Det er samme kildekonflikt, ikke en ny
uavhengig bonusfeil. Kampregisterets høyere verdi blir ikke automatisk fasit.

## Beregningsstatus

| Område | Antall |
|---|---:|
| Spillerkamper i gammel ledger | 77 280 |
| Inputkomplette spillerkamper | 62 290 |
| Inputkomplette hele kamper | 490 |
| Spillerkamper med BPS-kandidat | 62 217 |
| Hele kamper med bonus-/poengkandidater | 489 |
| Historiske kamper kvalifisert for trening her | 0 |

73 inputkomplette spillerkamper sperres av de fire uferdige målrettelsespakkene.
Én inputkomplett kamp holdes dessuten tilbake av kickoff-konflikten. De øvrige
nye populasjons-/kildeproblemene ligger i kamper med eksisterende åpne krav.
Den gamle restlisten har fortsatt **16 227** feltkrav; dette tallet omfatter
ikke de ekstra populasjons-/kildespørsmålene og globale kvalifiseringsgatene.

`core.py` bevarer historisk FPL-BPS og erstatter bare endrede komponenter.
Den bruker FPLs samlede keeperredninger uten å anta S=I+O. Hendelsesrettelser
krever en komplett godkjent pakke med eksplisitt BPS-delta; de fire kjente
uferdige pakkene anvendes ikke. Manglende endringsfelt gir feil, ikke null.

Gammel netto-taklingsklipping beregnes som to separate hypoteser. Signerte
råtellere beholdes. Hypotesene gir forskjellig BPS i **9 293** beregnede
spillerkamper og forskjellig bonus for **221** spillere i **122** beregnede
hele kamper. Dette er sensitivitet, ikke bevis for hvilken regel som er riktig.

## Resultater og sperrer

- `results/historical_inventory.csv.xz`: hele den kanoniske originalhistorikken,
  tilgjengelige rikere statistikker, kildehenvisninger og originalpoengregnskap.
- `results/player_match_candidates.csv.xz`: original baseline, nullable input,
  defcon-award, kravstatus og separate hypotesekandidater.
- `results/bps_component_changes.csv.xz`: hvert endret BPS-bidrag per hypotese.
- `results/fixture_status.csv`: kampvise input-, populasjons-, kilde- og pakkesperrer.
- `results/*residuals.csv`: avstemming av opprinnelige grunnpoeng og bonus.
- `results/source_population_gaps.csv` og `fixture_source_disagreements.csv`:
  konkrete oppgaver utenfor gammel restliste.
- `results/statistic_coverage.csv`: original FPL-dekning per sesong/felt.
- `results/manifest.json`: inngangs-, kode- og utgangsfingeravtrykk.

Endelige `assists_2026_27`, `bps_2026_27`, `bonus_2026_27` og
`total_points_2026_27` er **tomme for alle historiske rader**. Statusene
`scoring_qualified` og `training_ready` er false. Kandidater må ikke brukes
som treningsfasit. `qualification.json` dokumenterer uferdige globale gater.

Eldre manglende xG/xA/xGI/xGC/starter er fortsatt manglende; de er ikke hentet
eller imputert i dette trinnet. Pris/status/kalender er ikke kvalifiserte
før-frist-features. Komplette BGW-rostre, rundeaggregater, features/targets og
aktiv treningsinnlesing gjenstår.

## Reproduksjon

Fra repositoryroten med Python 3.12 og pandas 2.2.3:

```sh
python research/current/training_dataset/scoring/historical.py
python research/current/training_dataset/scoring/reproduce.py
python research/current/training_dataset/reproduce.py
python -m unittest discover -s research/current/training_dataset -p 'test_*.py' -v
```

Den samlede offline-replayen gjenskaper **25 resultatfiler identisk** i en
separat kopi: offisiell 2026/27, tidligere straffepilot og historisk beregning.
19 aktuelle tester består, inklusive 14 nye historiske transformasjons- og
sperretester. Full repository-/CI-test påstås ikke.

Neste arbeid må kvalifisere gamle taklingsregler, komponent-/revisjonssamsvar
og de 73 eksterne kvalitetsgruppene, løse de reelle årsaks-/tallgapene og de nye
populasjons-/kildeproblemene. Deretter skal hele den avtalte treningsleveransen
ferdigstilles. Beregningsutgangen alene oppfyller ikke målet.
