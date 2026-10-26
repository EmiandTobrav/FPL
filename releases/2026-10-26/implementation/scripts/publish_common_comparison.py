"""One navigable project overview, combining the common and weather studies."""
import sys,json,re
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json
from scripts.report_common_model_retest import NAMES
BASE=R/'reports/common_model_retest_2026_10_25_v3';W=R/'reports/common_weather_proxy_2026_10_25';D=R/'datasets/fpl_common_training_v1'

def main():
    assert json.loads((BASE/'verification.json').read_text())['passed'];assert json.loads((W/'verification.json').read_text())['passed']
    summary=pd.read_csv(BASE/'summary.csv');weather=pd.read_csv(W/'metrics.csv');gates=json.loads((BASE/'score.json').read_text())['gates'];lines=['# Samlet oversikt: felles datasett og nye modelltester','','25. oktober 2026. Én fryst treningstabell, 18 modell-/featurevarianter, fire evalueringssesonger og et separat forsøk med faktisk kampvær.','','## Hovedfunn','']
    families=[n for n in NAMES if not n.startswith('catboost_')]
    for h in [1,3]:
        s=summary[summary.period.eq('development')&summary.horizon.eq(h)&summary.arm.isin(families)].sort_values('point_mse');best=s.iloc[0];gate=next(g for g in gates if g['horizon']==h and g['arm']==best.arm)
        comparison='Dette er den felles referansen.' if best.arm=='ridge' else f'Den slår felles Ridge i {gate["wins"]} av 3 utviklingssesonger.'
        lines.append(f'- H{h}, forventede poeng: **{NAMES[best.arm]}** har lavest utviklings-MSE blant de komplette modellfamiliene: **{best.point_mse:.4f}**. '+comparison)
        overall=summary[summary.period.eq('development')&summary.horizon.eq(h)].sort_values('point_mse').iloc[0]
        if overall.arm!=best.arm:lines.append(f'- H{h}, alle forhåndsvalgte feltvarianter inkludert: **{NAMES[overall.arm]}** har lavest utviklings-MSE: **{overall.point_mse:.4f}**. Dette er et feltvalg innen en modellfamilie, ikke en egen arkitektur.')
    s=summary[summary.period.eq('development')&summary.horizon.eq(1)&summary.arm.isin(families)].sort_values('minute_mse');best=s.iloc[0]
    lines.append(f'- Forventede minutter H1: **{NAMES[best.arm]}** har lavest utviklings-MSE: **{best.minute_mse:.2f}**. Dette er et separat mål fra poengprognosene.')
    for h in [1,3]:
        s=weather[~weather.season.eq('2025-26')&weather.horizon.eq(h)].groupby('scenario').point_mse.mean();change=(s['actual']/s['control']-1)*100
        lines.append(f'- Faktisk-vær-proxy H{h}: MSE endres **{change:+.2f} %** mot samme CatBoost uten målkampens vær. Negativt er bedre. Dette er en optimistisk proxy, ikke en test av faktisk tilgjengelige værmeldinger.')
    lines+=['- Dagens operative modell er bevart. Testen dokumenterer prognosekvalitet; ingen ny rangering etter netto manager-/sesongpoeng er laget.','','De tre utviklingssesongene er 2022/23–2024/25. 2025/26 vises separat; alle disse periodene har vært undersøkt tidligere. Små forskjeller, mange sammenligninger og ufullstendig kildehistorikk begrenser hvor sikkert resultatene kan overføres til fremtidige runder.','','## Full modelloversikt','']
    text=(BASE/'RESULTATER.md').read_text().replace('tremålshorisonter','prognosehorisonter på tre runder')
    def absolute_link(match):
        label,target=match.group(1),match.group(2)
        if target.startswith(('http:','https:','/','#')):return match.group(0)
        return '['+label+']('+str((BASE/target).resolve())+')'
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',absolute_link,text)
    lines.append(text)
    lines+=['## Tillegg: faktisk kampvær som proxy for værmeldinger','',
      'Etter brukerens ønske er det også trent en egen værvariant. Den bruker samme fryste tabell, treningsrader, evalueringsrader, oppdateringspunkter og CatBoost-parametre som fullpakken, med fem ekstra felt: temperatur, vind, nedbør, skydekke og solminutter i målkampene. Modellen trenes med historisk rekonstruert faktisk vær. Deretter testes den med faktisk vær og med to forhåndsvalgte feilscenarioer i værverdiene.','',
      'Det er mulig å bruke værmeldinger på slike modeller i praksis. Historisk faktisk vær gir likevel mer presis og mer komplett informasjon enn et varsel ved FPL-fristen, særlig flere runder frem. Også faktisk kampdato, kampsted og hvilke kamper som ble gjennomført kan avvike fra det man visste da. Resultatene her skal derfor leses som en optimistisk proxy. De er ikke en realistisk førfristtest av historiske værvarsler.','',
      'Støytesten er en følsomhetsanalyse. Den viser ikke værmeldingenes målte feilfordeling. Feilene trekkes én gang per fysisk kamp og deles av alle spillerne i kampen; de trekkes ikke uavhengig per spiller. Samme grunnfeil skaleres mellom de to feilnivåene. Modellene trenes ikke om mellom scenarioene.','',
      '| Scenario | Temperatur, standardavvik | Vind | Nedbør | Skydekke | Solminutter |','|---|---:|---:|---:|---:|---:|',
      '| Faktisk rekonstruert vær | 0 | 0 | 0 | 0 | 0 |',
      '| Syntetisk feilnivå 1 | 2 °C | 1,5 m/s | 1 mm | 15 prosentpoeng | 15 min |',
      '| Syntetisk feilnivå 2 | 4 °C | 3 m/s | 2 mm | 30 prosentpoeng | 30 min |','',
      'Nedbør/vind avgrenses ved null og skydekke ved 0–100 %. Solminutter begrenses av astronomisk dagslys i kampvinduet, slik at nattkamper fortsatt har null sol. Dette er enkle illustrative scenarier, ikke en kalibrert meteorologisk feilmodell. H3 bruker gjennomsnitt av de tre rundenes kampvær.','']
    labels={'control':'Full CatBoost, uten målkampvær','actual':'Med faktisk rekonstruert kampvær','noise_1':'Samme modell, syntetisk feilnivå 1','noise_2':'Samme modell, syntetisk feilnivå 2'}
    for h in [1,3]:
        lines += [f'### Vær H{h}','', '| Scenario | 2022/23 MSE | 2023/24 MSE | 2024/25 MSE | 2025/26 MSE |','|---|---:|---:|---:|---:|']
        z=weather[weather.horizon.eq(h)].pivot(index='scenario',columns='season',values='point_mse')
        for name in labels:lines.append('| '+labels[name]+' | '+' | '.join(f'{z.loc[name,s]:.4f}' for s in ['2022-23','2023-24','2024-25','2025-26'])+' |')
        for name in ['actual','noise_1','noise_2']:
            dev=z.loc[name,['2022-23','2023-24','2024-25']];control=z.loc['control',['2022-23','2023-24','2024-25']];passed=bool((dev<control).all());lines.append('') if name=='actual' else None
            lines.append(f'- {labels[name]}: '+('lavere poeng-MSE i alle tre utviklingssesongene.' if passed else 'lavere poeng-MSE i alle tre utviklingssesongene er ikke oppnådd.'))
        lines+=['']
    lines+=['Værforsøket har 40 modelltilpasninger og 120 prognosefiler som er gjenspilt i etterkontrollen. Alle armer bruker de samme kjente fasitene som hovedforsøkets CatBoost. Minuttresultatene finnes i den samlede resultatfilen for vær. Ingen aktiv modell eller forseglede fremtidige prognoser er endret.','',f'[Værresultater for poeng og minutter]({W}/metrics.csv) · [Værkontroll]({W}/verification.json) · [Værprotokoll]({W}/proposal.json)','',
      '## Filer og videre bruk','',f'- [Datakort og innlesingsregler]({D}/README.md)',f'- [Portabel treningstabell]({D}/training.csv.gz)',f'- [Tillatte prognosefelt]({D}/schema.json)',f'- [Alle hovedresultater per sesong og gruppe]({BASE}/metrics.csv)',f'- [Felles operative referanserader]({BASE}/operational_anchor_metrics.csv)','',
      'Den neste systemvurderingen må sammenligne forhåndsvalgte kandidater med dagens operative modell gjennom en lovlig sesongsimulering med samme spillerpool, priser, åpningslag, manager, chips og ressursgrenser. Denne oversikten dokumenterer ikke at én av de nye prognosemodellene gir flere netto FPL-sesongpoeng.','']
    output=R/'overview/COMMON_MODEL_RESULTS_2026_10_25.md';assert not output.exists();output.write_text('\n'.join(lines))
    sources=[BASE/n for n in ['RESULTATER.md','metrics.csv','summary.csv','verification.json','operational_anchor_metrics.csv']]+[W/n for n in ['metrics.csv','verification.json','proposal.json']]+[D/'manifest.json',D/'verification.json']
    atomic_json(output.with_suffix('.sources.json'),dict(overview_sha256=sha(output),source_hashes={str(p.relative_to(R)):sha(p) for p in sources},production_changed=False))
    print(output)

if __name__=='__main__':main()
