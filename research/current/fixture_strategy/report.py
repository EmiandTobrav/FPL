from pathlib import Path
import json,gzip
import pandas as pd
HERE=Path(__file__).resolve().parent;OUT=HERE/'results'

def main():
    d=pd.read_csv(OUT/'all_seasons.csv');s=pd.read_csv(OUT/'summary.csv');v=json.loads((OUT/'verification.json').read_text())
    fixed=s[s['mode']=='fixed_chips'][['model','points','gain','matched_gain','hits','nonoptimal','max_solver_gap']].sort_values('points',ascending=False)
    no=s[s['mode']=='no_chips'][['model','points','gain','matched_gain']].sort_values('points',ascending=False)
    chips=s[s['mode'].str.startswith('adaptive_')][['mode','points','gain','matched_gain','wins','ties','losses','matched_ci_low','matched_ci_high']].sort_values('points',ascending=False)
    seasonal=d[d['mode']!='no_chips'].pivot(index='season',columns=['model','mode'],values='points38')
    seasonal.columns=[' / '.join(x) for x in seasonal.columns]
    coverage=pd.read_csv(OUT/'forecast_audit.csv').groupby('season').agg(rounds=('gw','size'),fresh_snapshots=('calendar_used','sum'))
    selected=[]
    for path in OUT.glob('trace_*.json.gz'):
        z=json.loads(gzip.decompress(path.read_bytes()));selected.extend([dict(model=z['summary']['model'],mode=z['summary']['mode'],status=r['solver_status'],gap=r['solver_gap'],horizon=r.get('planned_horizon',None)) for r in z['trace']])
    selected=pd.DataFrame(selected);diag=selected.groupby(['model','mode']).agg(decisions=('status','size'),selected_nonoptimal=('status',lambda x:(x!=0).sum()),selected_max_gap=('gap','max'),mean_effective_horizon=('horizon','mean'))
    diag.to_csv(OUT/'solver_diagnostics.csv')
    body=f'''# Kampvise justeringer, lengre horisonter og adaptive chips

Fullført 6. oktober 2026. {v['season_runs']} nye sesongforløp, {v['decisions']} hovedmodellbeslutninger på 2022/23–2025/26. **Arbeidsbenchmarken `constant_h3` beholdes.** Dette er utforskende tester på fire allerede gjenbrukte sesonger, ikke en urørt validering eller en historisk rangbevisføring.

## Kampvise prognoser og horisonter

`count` er antall-kamper-kontrollen. `venue` legger til hjemme/borte, `opponent` separate motstanderangrep/-forsvar, `full` begge. H3, H5 og H8 betyr maksimalt antall runder i planen; kjente kommende Wildcard/Free Hit forkorter den. GW38 avslutter alle planer. Aktuell prognose, overlevering, priser, ressursregler og fast chipkalender er beholdt.

Tabellen viser netto poeng, gevinst mot benchmark (2308,25), og gevinst mot `count` ved **samme horisont**. `nonoptimal` er antall tidsbegrensede hovedbeslutninger, og gap er solverens relative objektivgap, ikke usikkerhet i sesongpoeng.

{fixed.to_markdown(index=False,floatfmt='.3f')}

Uten chips (benchmark 2172,75):

{no.to_markdown(index=False,floatfmt='.2f')}

## Adaptive chips på låst `full_h3`

Prognose og H3 ble låst til fulljustert modell før chipresultatene, uansett hvilken prognosevariant som vant. Én chiptype om gangen er adaptiv; de øvrige beholder opprinnelige datoer. `adaptive_all` velger alle fire adaptivt. Hver chip brukes én gang i hver halvdel, med én chip per runde og ingen to påfølgende Free Hits. Felles GW1–4-overlevering hadde ingen brukte chips.

`matched_gain` er mot fulljustert H3 med faste chips, **ikke** kalenderkontrollen eller benchmarken. Intervallene er beskrivende 95 % paret sesongbootstrap med 50 000 resamplinger, seed 173; de korrigerer ikke for modellutprøvingen.

{chips.to_markdown(index=False,floatfmt='.2f')}

[Alle sesongvise resultater](results/all_seasons.csv) og [valgte chipdatoer](results/chip_dates.csv) viser variasjon og faktiske beslutninger. Chiprundens poeng alene er ikke en kausal chipgevinst, siden tropp og bytter endres gjennom sesongen.

## Metode og beslutningsgrunnlag

- Separate Ridge-koeffisienter per posisjon, lært kun fra tidligere sesonger med labels tilgjengelige før evalueringssesongen. Målet er historiske spillerpoeng; spillerens tidligere poeng og minutter samt eget lags mål for/mot er kontrollvariabler. Motstanderens rullerende mål for/mot og hjemme/borte gir kampjusteringen. Dette er en justering av totalprognosen, ikke en full kalibrert mål-/clean-sheet-komponentmodell.
- Lagstyrke og spillerens forventede minuttandel oppdateres med kamper avsluttet før beslutningen. Fremtidig form, minutter, skader og priser fryses ved beslutningen. Effekten skaleres med tidligere minutter/90 og avgrenses til ±2 poeng per kamp. Ridge alpha=100 var låst før kjøring.
- Den gamle fremtidsproxyen inneholder en avtakende effekt fra aktuell kamp. Vi trekker fra vår estimerte aktuelle kampeffekt med samme avtakingsfaktor før fremtidig kampeffekt legges til. Dette reduserer dobbelttelling, men er en tilnærming, ikke en eksakt dekomponering av ensemblet. Blank gir null og flere kamper summeres separat.
- Chipvalg sammenligner forventet nytte mot ordinær plan med hits og byttefriksjon. Free Hit-verdien inkluderer videre plan fra opprinnelig tropp/bank. Wildcard vurderer varig troppsendring over gjenværende H3-vindu. Bench Boost inkluderer tropps- og byttekostnad i vinduet, men bruker eksisterende benkvekt som autosubproxy; forventet autosubverdi er ikke modellert eksplisitt.
- Chipene kan vente på bedre prospektive alternativer én/to runder frem, med 0,9 avtakingsfaktor per runde. TC/BB har i tillegg en grov opsjonsverdi fra opptil åtte runder. Verdien av å spare utover synlig vindu bruker arvede startmodellkonstanter TC=8 og øvrige=12, avtakende mot utløp. Disse er forhåndsvalgte heuristikker, ikke nye terskler tilpasset evalueringsresultatene. Strategien er dermed en testbar adaptiv kandidat, ikke bevist global chipoptimum.
- Ingen realiserte fremtidige poeng inngår i chipvalget. Realiserte poeng brukes først ved oppgjør av valgt handling. Scorings-/regelgrunnlaget er fortsatt historiske spillerpoeng med nyere chip- og bytteregler.

## Kalenderdekning og begrensninger

Samme arkiver og 14-dagersregel som forrige kalenderforsøk. Vi har **ikke forbedret arkivdekningen** i denne runden. Ved eldre snapshots beholdes den eksisterende nøytrale proxyen, og sluttsesongens kalender brukes ikke til å fylle hull i fremtiden. Tabellen teller beslutninger med et ferskt nok snapshot, ikke garantert komplett kalender.

{coverage.to_markdown()}

Aktuell runde og cutoff beholder benchmarkens historiske final-event/36-timersbegrensning. Gode resultater her dokumenterer derfor ikke en fullstendig tidsriktig live-backtest. H5/H8 gir mer beregningsarbeid og større eksponering mot usikker kalender og frosne spillerforutsetninger.

## Kontroller og solverbegrensninger

Alle åtte `count_h3`-kontroller gjenskaper arkiverte kalenderbeslutninger og poeng nøyaktig. Verifisering kontrollerer tropp/posisjoner, inn-/utbytter, kjøps-/salgspriser, bank, frie bytter, hits, chipbeholdning, Free Hit-retur og poengregnskap. Treningslabels, lag- og spillerhistorikk ligger før cutoff. Funksjonstestene dekker blank/dobbel, fallback, separate effekter, minuttandel, chipmuligheter, utløp og reserverte runder.

Solveren bruker den arvede 10-sekundersgrensen og toleranse 1e-5. Tidsbegrensede løsninger beholdes når de er gjennomførbare. I H5/H8 utløste manglende gjennomførbar løsning en dokumentert teknisk feilretting: bare status=1 uten incumbent gjenkjøres med 60 sekunder, etter samme regel for kontroll og kandidat. Dette ble lagt til etter observert solverfeil, ikke valgt etter poengresultater. Se feasibility_policy.json og feasibility_runs.json. Beregningsbudsjettet er derfor betinget utvidet for disse tilfellene. Chipforsøkets `nonoptimal` i råtabellen omfatter også forkastede/prospektive kandidater; tabellen under viser kun handlingen som faktisk ble valgt. Små forbedringer er ikke robuste bevis når optimeringen ikke er fullført. Kontroller/regnskap er bestått; det hevdes ikke at alle løsninger er bevist optimale.

{diag.to_markdown(floatfmt='.4f')}

## Reproduksjon og arkivering

Kode/protokoll ble låst lokalt før simuleringene. GitHub-kodecommit `171990e5b779f76734cb5de000b65c34f59153e5` kom mens H3 kjørte, før chip- og langhorisontkjøringene. Kilde-/prognosehash, miljø, koeffisienter og tidsrevisjon er i `results`. Solverens tidsgrense kan gi ulike gjennomførbare løsninger ved ny kjøring på en annen maskin.

Fra repositoryroten:

```bash
python scripts/prepare_data.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/calendar_counts/build.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/fixture_strategy/build.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/fixture_strategy/run.py --stage h3
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/fixture_strategy/complete_long.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/fixture_strategy/chips.py
python research/current/fixture_strategy/summarize.py
python research/current/fixture_strategy/verify.py
python research/current/fixture_strategy/report.py
```

Prognoser regenereres fra kode og arkiverte innganger. `portable` bevarer oppgjør, faktiske handlinger og chipvurderinger som lesbar JSON; store interne fremtidsplaner er utelatt der. Hashene i `verified_runs.csv` gjelder de komplette lokale kjøringssporene. Det hevdes ikke byteidentisk gjenoppretting av disse fra de forkortede beslutningsarkivene.
'''
    (HERE/'README.md').write_text(body)
if __name__=='__main__':main()
