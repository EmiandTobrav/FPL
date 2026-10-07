"""Resolve remaining labels using frozen primary counters and complete save evidence.

Run recover.py first, then this script. Never changes locked scoring labels.
"""
import json
import gzip
import hashlib
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
FOLLOW=ROOT/'followup'
KEY=['season','fixture','code']


def verify_primary_inputs(primary, base):
    sources={s['file']:s for s in json.loads((FOLLOW/'primary_sources.json').read_text())}
    blobs=[json.loads(line) for line in gzip.decompress((FOLLOW/'primary_raw.jsonl.gz').read_bytes()).decode().splitlines()]
    identities=json.loads(gzip.decompress((FOLLOW/'identity_evidence.json.gz').read_bytes()))
    fixtures={(g['season'],int(f['id'])):int(f['altIds']['opta'].lstrip('g')) for g in identities for f in g['fixtures']}
    by_provider={(int(r.pl_player_id),int(r.pulse_id)):key for key,r in primary.iterrows()}
    seen=set()
    for b in blobs:
        source=sources[b['file']]
        assert hashlib.sha256(b['raw_json'].encode()).hexdigest()==source['sha256']
        d=json.loads(b['raw_json']);pid=int(d['entity']['id'])
        mid=int(source['url'].split('fixtures=')[1].split('&')[0])
        key=by_provider[(pid,mid)];assert key not in seen;seen.add(key)
        row=primary.loc[key];original=base.set_index(KEY).loc[key]
        assert int(d['entity']['altIds']['opta'].lstrip('p'))==key[2]
        assert fixtures[(key[0],mid)]==original.fixture_code
        stats={s['name']:s['value'] for s in d['stats']}
        assert stats['appearances']==1 and stats['mins_played']>0
        for field in ['saves','big_chance_saves']:
            frozen=row.get('pl_'+field);raw=stats.get(field)
            assert (raw is None and pd.isna(frozen)) or raw==frozen
    assert len(seen)==len(primary)==len(blobs)==len(sources)


def paired_saves(row, primary, events):
    """Every official save must pair uniquely to a labelled, non-blocked shot."""
    if pd.notna(row.explicit_big_chance_saves):
        return None, []  # A contradictory explicit source needs adjudication.
    total=primary.get('pl_saves')
    if pd.isna(total) or total!=row.fotmob_saves or total<=0:
        return None, []
    es=events[events.match_id.eq(row.match_id)]
    saves=es[es.player_id.eq(row.player_id)&es.type_id.eq(10)]
    saves=saves[~saves.q.map(lambda q:'94' in q)]
    if len(saves)!=total:return None, []
    shots=es[es.team_id.ne(row.team_id)&es.type_id.eq(15)]
    pairs=[]
    for save in saves.itertuples():
        hits=shots[shots.period_id.eq(save.period_id)&
          (save.minute*60+save.second-shots.minute*60-shots.second).between(-1,3)]
        hits=hits[~hits.q.map(lambda q:'82' in q)]
        if len(hits)!=1:return None, []
        shot=hits.iloc[0]
        pairs.append({'save_event_id':int(save.event_id),'shot_event_id':int(shot.event_id),
                      'big_chance':'214' in shot.q})
    if len({p['shot_event_id'] for p in pairs})!=len(pairs):return None, []
    return sum(p['big_chance'] for p in pairs),pairs


def team_shot_count(shots, shooters):
    """Count BC saves if all shots and all relevant block states are established.

    Unknown block flags can be resolved only by exhaustive per-shooter counts:
    zero blocked attempts, or every saved/blocked attempt being blocked.
    Goal classifications are unnecessary for a non-goal save count; total goals
    and every shooter's total attempts still must match the second projection.
    """
    if shots.empty or shots.big_chance.isna().any():return None
    shooters=shooters[shooters.total_shots.gt(0)]
    if shooters.player_name.duplicated().any():return None
    if set(shots.player_name)!=set(shooters.player_name):return None
    total=0
    for player,g in shots.groupby('player_name'):
        sr=shooters[shooters.player_name.eq(player)].iloc[0]
        if len(g)!=sr.total_shots or g.type_id.eq(16).sum()!=sr.goals:return None
        attempts=g[g.type_id.eq(15)]
        bc=attempts[attempts.big_chance.eq(True)]
        for shot in bc.itertuples():
            block=shot.is_blocked
            if pd.isna(block):
                if sr.shots_blocked==0:block=False
                elif sr.shots_blocked==len(attempts):block=True
                else:return None
            if not block:total+=1
    return total


def main():
    base=pd.read_csv(ROOT/'keeper_counts.csv.gz')
    if 'resolution_method' in base:raise ValueError('Run recover.py before reconciliation')
    primary=pd.read_csv(FOLLOW/'primary_verified/observations.csv').set_index(KEY)
    verify_primary_inputs(primary,base)
    events=pd.read_csv(FOLLOW/'raw_event_evidence.csv.gz')
    events['q']=events.qualifier_json.map(json.loads)
    shots=pd.concat(pd.read_csv(p,dtype={'big_chance':'boolean','is_blocked':'boolean'})
                    for p in sorted((ROOT/'inputs').glob('shots-*.csv.gz')))
    shooters=pd.read_csv(FOLLOW/'shooter_totals.csv.gz')
    base['resolution_method']=base.status.map({'reconstructed':'original_shot_reconstruction','unresolved':'unresolved'})
    base['original_reason']=base.reason
    decisions=[]
    def approve(i,value,method,evidence):
        r=base.loc[i]
        decisions.append({**{k:r[k] for k in KEY},'name':r['name'],
            'big_chance_saves':int(value),'method':method,'original_reason':r.original_reason,
            'historical_fpl_save_conflict':bool(value>r.fpl_saves),
            'evidence':json.dumps(evidence,ensure_ascii=False)})
        base.loc[i,['big_chance_saves','status','reason','resolution_method']]=[int(value),'reconstructed','',method]
    for i,r in base[base.status.eq('unresolved')].iterrows():
        pr=primary.loc[tuple(r[k] for k in KEY)]
        v=pr.get('pl_big_chance_saves')
        if pd.notna(v) and pd.notna(pr.pl_saves) and 0<=v<=pr.pl_saves:
            approve(i,v,'explicit_primary_counter',{'pl_player_id':int(pr.pl_player_id),'pulse_id':int(pr.pulse_id),'primary_saves':pr.pl_saves,'archive_counter':None if pd.isna(r.explicit_big_chance_saves) else r.explicit_big_chance_saves})
        elif r.fpl_saves==0 and r.fotmob_saves==0 and (pd.isna(pr.pl_saves) or pr.pl_saves==0) and (pd.isna(r.explicit_big_chance_saves) or r.explicit_big_chance_saves==0):
            approve(i,0,'verified_zero_save_bound',{'fpl_saves':0,'fotmob_saves':0,'primary_counter_missing':bool(pd.isna(pr.pl_saves))})
        else:
            value,pairs=paired_saves(r,pr,events)
            if value is not None:
                approve(i,value,'complete_paired_save_inventory',{'primary_saves':pr.pl_saves,'fotmob_saves':r.fotmob_saves,'pairs':pairs})
    for (season,fixture,side),g in base[base.match_id.notna()].groupby(['season','fixture','side']):
        missing=g[g.status.eq('unresolved')]
        if len(missing)!=1:continue
        r=missing.iloc[0]
        # Only the three genuinely thin source matches need this fallback.
        if not str(r.original_reason).startswith(('missing_shot_flags','big_chance_scored_conflict')):continue
        hs=shots[shots.match_id.eq(r.match_id)&shots.team_id.ne(r.team_id)]
        ss=shooters[shooters.match_id.eq(r.match_id)&shooters.team_id.ne(r.team_id)]
        total=team_shot_count(hs,ss)
        if total is None:continue
        value=total-g[g.status.eq('reconstructed')].big_chance_saves.sum()
        pr=primary.loc[tuple(r[k] for k in KEY)]
        if pd.notna(pr.pl_saves) and value==int(value) and 0<=value<=pr.pl_saves:
            approve(missing.index[0],value,'complete_team_shots_and_shooter_blocks',{'team_big_chance_saves':total,'other_verified_keeper_saves':int(total-value),'primary_saves':pr.pl_saves})
    base.to_csv(ROOT/'keeper_counts.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    base[base.status.eq('unresolved')].to_csv(ROOT/'unresolved_keepers.csv',index=False)
    pd.DataFrame(decisions).to_csv(FOLLOW/'decisions.csv',index=False)
    coverage=base.groupby('season').agg(keepers=('element','size'),reconstructed=('status',lambda x:x.eq('reconstructed').sum()),big_chance_saves=('big_chance_saves','sum'))
    coverage.to_csv(ROOT/'coverage.csv')
    hist=base[base.season.ne('2026-27')]
    findings=json.loads((ROOT/'findings.json').read_text())
    findings.update(reconstructed=int(hist.status.eq('reconstructed').sum()),unresolved_observations=int(hist.status.eq('unresolved').sum()),unresolved_matches=int(hist[hist.status.eq('unresolved')][['season','fixture']].drop_duplicates().shape[0]),historical_coverage_fraction=float(hist.status.eq('reconstructed').mean()),followup_primary_observations=len(primary),followup_resolved=len(decisions),followup_methods=pd.Series([d['method'] for d in decisions]).value_counts().to_dict())
    (ROOT/'findings.json').write_text(json.dumps(findings,indent=2)+'\n')
    print(pd.DataFrame(decisions)[['name','method','big_chance_saves']].to_string(index=False))
    print('Historical resolved',findings['reconstructed'],'remaining',findings['unresolved_observations'])

if __name__=='__main__':main()
