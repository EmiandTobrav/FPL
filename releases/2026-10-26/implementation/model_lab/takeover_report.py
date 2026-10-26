"""Describe the fixed experiment; never selects a rerun or changes a policy."""
import pandas as pd
from model_lab.takeover_campaign import R,P
from model_lab.common import read,sha,atomic_json

def main():
    verification=read(P/'verification.json');assert verification['status']=='passed'
    q=pd.read_csv(P/'paired_results.csv')
    overall=q.groupby(['forecast','manager']).agg(mean_points=('net_points','mean'),mean_delta=('delta','mean'),wins=('delta',lambda x:int((x>0).sum())),ties=('delta',lambda x:int((x==0).sum())),states=('delta','size'),mean_seconds=('seconds','mean')).reset_index().sort_values('mean_delta',ascending=False)
    overall.to_csv(P/'overall.csv',index=False)
    same=q[q.forecast.eq('benchmark')][['state_id','manager','net_points']].rename(columns={'net_points':'same_manager_reference'})
    q=q.merge(same,on=['state_id','manager'],validate='many_to_one');q['forecast_effect']=q.net_points-q.same_manager_reference
    q.to_csv(P/'forecast_effects.csv',index=False)
    bystart=q.groupby(['season','start','forecast','manager']).agg(mean_points=('net_points','mean'),mean_delta=('delta','mean'),forecast_effect=('forecast_effect','mean')).reset_index()
    bystart.to_csv(P/'by_start.csv',index=False)
    years=pd.read_csv(P/'summary.csv')
    candidates=years[~(years.forecast.eq('benchmark')&years.manager.eq('adaptive'))]
    gates=candidates.groupby(['forecast','manager']).mean_delta.apply(lambda v:bool((v>0).all()))
    best=overall.iloc[0]
    lines=['Historisk overtakelsestest – 17. oktober 2026','',
        'Fullført: 16 modelltreninger for to nye prognosefamilier, 96 overtakelsesforløp og 2 136 rundevalg. Alle 96 forløp starter fra en av de samme 16 låste lagtilstandene.',
        'To sesonger (2023/24, 2024/25), to laghistorikker og overtakelse i GW7,13,20,27. Hvert forløp fortsetter til GW38.',
        'Poengene nedenfor er realiserte, harmoniserte FPL-poeng etter byttefradrag. Delta er mot benchmark + adaptiv manager fra nøyaktig samme starttilstand.',
        'Gjennomsnitt over ulikt lange overtakelsesforløp er ikke en forventet full sesongscore. Sammenlign de parede forskjellene.', '',
        overall.to_string(index=False,float_format=lambda x:f'{x:.2f}'),'',
        'Per sesong:',years.to_string(index=False,float_format=lambda x:f'{x:.2f}'),'',
        'Forhåndsbestemt krav: positiv gjennomsnittlig forskjell i BEGGE sesonger. Resultat:',
        gates.to_string(),'',
        'trajectory_base og trajectory_full er NYE direkte forventningsmodeller for offset0..7, med delte modellparametere og offset som input. De er ikke identiske med de tidligere frosne base/full-énrundersmodellene.',
        'Base bruker spillerhistorikk, posisjon og horisont. Full legger til kampoppsett for mål-runden og lag-/motstanderstyrke beregnet ved prognosetidspunktet.',
        'Fremtidige målverdier er koblet til opprinnelige inngangsdata, ikke til fremtidige spillerhistorikker. Modellene trenes på nytt i GW7,15,23,31 med bare tidligere tilgjengelige målverdier.',
        'Tidlige treningssesonger uten kvalifisert kalender har ukjent kalender; dette begrenser særlig full-modellens kalendergrunnlag tidlig i 2023/24.',
        'Begge managere mottar opptil8 runder; deres eksisterende lokale planlegging går opptil3 runder. Dette er ikke en full åtterunders rollout-manager.',
        'Forecast-effekter med SAMME manager finnes i forecast_effects.csv. Oppdeling etter start finnes i by_start.csv.',
        'Prognosefeil per sesong/offset finnes i forecast_metrics.csv. Summer over komplette3/8-rundersvinduer finnes i forecast_sum_metrics.csv. repeat_H1 er kun en diagnostisk kontroll.',
        '', 'Utforskende diagnose (lagt til etter de første simuleringene; ikke et forhåndsregistrert beståttkrav):',
        pd.read_csv(P/'exploratory_top20_H1.csv').to_string(index=False,float_format=lambda x:f'{x:.3f}'),
        'Utvalget er de20 kjøpbare spillerne benchmark rangerte høyest før hver runde, valgt uten fremtidige resultater. Tallene beskriver kalibrering i dette utvalget, og beviser ikke årsaken til managerforskjellene.',
        '', 'Begrensninger:',
        'Sesongene er tidligere undersøkt: dette er utviklingsevidens. Overlappende forløp er korrelerte, og utvalget består av to simulerte laghistorikker, ikke representative menneskelag.',
        'Historiske tids- og prisdata bygger på prosjektets dokumenterte proxyer. Markedspriser holdes faste innen planleggingen og oppdateres ved neste faktiske beslutningsrunde.',
        'Reglene og poengene er harmonisert til prosjektets regelverk. Historisk native rank og topp1%-sannsynlighet kan derfor ikke utledes fra disse tallene.',
        'Ingen modell er automatisk satt i produksjon. Det aktive FPL-laget og den frosne prospektive testen er ikke endret.',
        '', 'Kontrollert: uendrede kildehasher, kausale treningstider, identiske starttilstander, alle lovlige beslutninger og alle poengoppgjør.']
    (P/'RESULTATER.txt').write_text('\n'.join(lines)+'\n')
    evidence=[P/n for n in ['proposal.json','forecast_lock.json','runtime_and_models.json','target_clock_audit.json','complete.json','verification.json','paired_results.csv','summary.csv','overall.csv','forecast_metrics.csv','forecast_sum_metrics.csv','forecast_coverage.csv','exploratory_top20_H1.csv','exploratory_diagnosis.json','RESULTATER.txt']]
    result=dict(conclusion=f"Best observed combination: {best.forecast}+{best.manager}; mean paired delta {best.mean_delta:.2f}. Development evidence only.",
        decision='retain_for_research',results=dict(overall=overall.to_dict('records'),season_gates={a+'__'+b:bool(v) for (a,b),v in gates.items()}),
        evidence_hashes={str(p.relative_to(R)):sha(p) for p in evidence})
    atomic_json(P/'registry_result.json',result)
    status=dict(id='takeover-workpackage-20261017-v1',status='completed_historical_takeover_campaign',model_fits=16,
        tests_passed=11,states_verified=16,episodes=96,manager_decisions=2136,manager_performance_test_run=True,
        rank_success_claimed=False,report=str((P/'RESULTATER.txt').relative_to(R)))
    # This file is a mutable dashboard, unlike immutable experiment evidence.
    import json
    (R/'overview/takeover_workpackage_status.json').write_text(json.dumps(status,indent=2)+'\n')
    print(overall.to_string(index=False))

if __name__=='__main__':main()
