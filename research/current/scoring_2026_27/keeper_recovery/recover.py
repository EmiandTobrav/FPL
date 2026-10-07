"""Reconstruct labelled big-chance saves; never infer them from xG.

Run from this directory with pandas and pyarrow installed. Source archives are
kept in raw/. Outputs are supplemental retrospective labels, not model features.
"""
import ast
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent.parent / 'project/data'
YEARS = range(2019, 2027)
TEAM_ALIASES = {
    'man city': 'manchester city', 'man utd': 'manchester united',
    'spurs': 'tottenham hotspur', 'wolves': 'wolverhampton wanderers',
    'brighton': 'brighton and hove albion', 'newcastle': 'newcastle united',
    'norwich': 'norwich city', 'leicester': 'leicester city',
    'sheffield utd': 'sheffield united', 'leeds': 'leeds united',
    'west brom': 'west bromwich albion', "nott m forest": 'nottingham forest',
    'west ham': 'west ham united', 'luton': 'luton town', 'ipswich': 'ipswich town',
}


def norm(s):
    s=str(s).translate(str.maketrans({'ø':'o','Ø':'O','ı':'i','ł':'l','Ł':'L'}))
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


def team(s):
    s = re.sub(r'\b(afc|fc)\b', '', norm(str(s).replace('&',' and '))).strip()
    s = re.sub(r'\s+', ' ', s)
    return TEAM_ALIASES.get(s, s)


def name_match(fpl, provider):
    """Exact normalized names or whole surname/web-name tokens; unique only."""
    fs = norm(fpl['second_name'])
    ff = norm(fpl['first_name'])
    fw = norm(fpl['web_name'])
    ps = norm(provider['last_name'])
    pf = norm(provider['first_name'])
    pn = norm(provider['player_name'])
    if f'{ff} {fs}'==f'{pf} {ps}' or (fs == ps and (ff == pf or ff[:1] == pf[:1])):
        return 2
    # Nicknames such as Alisson, Ederson, Neto, Kepa and José Sá are explicit
    # names in the input, never a fuzzy string-distance or team-only match.
    return int(len(fw) >= 3 and (fw == pn or fw == ps or
                           f' {fw} ' in f' {pf} {ps} ' or
                           f' {fw} ' in f' {pn} '))


def build_targets(stats, fixtures):
    stats=stats[['match_id','player_id','player_name','first_name','last_name',
                 'team_id','team_position','minsPlayed','saves','bigChanceSaves']]
    fm=pd.read_csv(ROOT/'fotmob_keepers.csv.gz')
    fmgroup=dict(tuple(fm.groupby(['season','fixture'])))
    source_fixtures = {}
    for r in fixtures.to_dict('records'):
        if r['season'][:4] not in {str(y) for y in YEARS}:
            continue
        key=(r['season'], str(r['match_date'])[:10], team(r['home_team']), team(r['away_team']))
        if key in source_fixtures:
            raise ValueError(f'Duplicate fixture key {key}')
        source_fixtures[key]=r
    bymatch=dict(tuple(stats.groupby('match_id')))
    targets=[]
    matches=[]
    for y in YEARS:
        season=f'{y}-{str(y+1)[-2:]}'
        full=f'{y}-{y+1}'
        players=pd.read_csv(DATA/f'{season}_players.csv.gz').set_index('id')
        teams=pd.read_csv(DATA/f'{season}_teams.csv.gz').set_index('id')['name'].to_dict()
        ff=pd.read_csv(DATA/f'{season}_fixtures.csv.gz')
        for f in ff.to_dict('records'):
            if not f.get('finished') or pd.isna(f.get('kickoff_time')):
                continue
            key=(full,f['kickoff_time'][:10],team(teams[f['team_h']]),team(teams[f['team_a']]))
            match=source_fixtures.get(key)
            mapped=match is not None
            if mapped and (int(match['home_score'])!=int(f['team_h_score']) or
                           int(match['away_score'])!=int(f['team_a_score'])):
                raise ValueError(f'Score mismatch {key}')
            base=dict(season=season,fixture=f['id'],fixture_code=f['code'],
                      date=key[1],home=teams[f['team_h']],away=teams[f['team_a']],
                      match_id=match['match_id'] if mapped else '')
            matches.append(base)
            raw=ast.literal_eval(f['stats'])
            bps=next((x for x in raw if x['identifier']=='bps'), {'h':[],'a':[]})
            saves=next((x for x in raw if x['identifier']=='saves'), {'h':[],'a':[]})
            people=[]
            if y<2026:
                # The frozen provider appearances define our historical scope.
                # FPL fixture BPS lists omit some zero-BPS keepers.
                bycode=players.reset_index().set_index('code')
                for appearance in fmgroup.get((season,f['id']),fm.iloc[:0]).to_dict('records'):
                    fp=bycode.loc[appearance['code']]
                    if isinstance(fp,pd.DataFrame):raise ValueError('Duplicate FPL code')
                    side=next((side for side in ('h','a') if any(x['element']==fp['id'] for x in bps[side])),None)
                    people.append((side,int(fp['id']),appearance))
            else:
                for side in ('h','a'):
                    people.extend((side,int(b['element']),None) for b in bps[side] if int(players.loc[b['element']].element_type)==1)
            for side,element,appearance in people:
                fp=players.loc[element]
                if int(fp.element_type)!=1:
                    continue
                candidates=[]
                if mapped:
                    ms=bymatch.get(match['match_id'],stats.iloc[:0])
                    if side:
                        mt=match['home_team_id' if side=='h' else 'away_team_id']
                        ms=ms[ms.team_id.eq(mt)]
                    for ps in ms.to_dict('records'):
                        score=name_match(fp,ps)
                        if score: candidates.append((score,ps))
                if candidates:
                    best=max(x[0] for x in candidates)
                    candidates=[x[1] for x in candidates if x[0]==best]
                pr=candidates[0] if len(candidates)==1 else None
                if pr:
                    pside='h' if pr['team_position']=='home' else 'a'
                    if side and pside!=side:raise ValueError('Keeper team mismatch')
                    side=pside
                elif not side:
                    side='unknown_'+str(element)
                sv={x['element']:x['value'] for x in saves.get(side,[])}
                targets.append({**base,'element':element,'code':int(fp['code']),
                    'name':fp['first_name']+' '+fp['second_name'],'side':side,
                    'fpl_saves':sv.get(element,0),'fotmob_saves':appearance['saves'] if appearance else None,
                    'fotmob_minutes':appearance['minutes_played'] if appearance else None,
                    'provider_minutes':pr['minsPlayed'] if pr else None,
                    'player_id':pr['player_id'] if pr else '',
                    'provider_name':pr['player_name'] if pr else '',
                    'team_id':pr['team_id'] if pr else '',
                    'source_saves':pr['saves'] if pr else None,
                    'explicit_big_chance_saves':pr['bigChanceSaves'] if pr else None,
                    'identity_status':'matched' if pr else ('missing_match' if not mapped else f'name_candidates_{len(candidates)}')})
    t=pd.DataFrame(targets);m=pd.DataFrame(matches)
    if t.duplicated(['season','fixture','element']).any():raise ValueError('Duplicate target')
    return t,m


def recover_team(keepers, opponent_stats, shots, events):
    """Return counts only when shot coverage and keeper allocation are unambiguous.

    Sparse player box-score counters are summed for coverage cross-checks only.
    Missing bigChanceSaves is NEVER used as a zero label. A derived zero requires
    complete opponent shots and no qualifying saves against this keeper.
    """
    problems=[]
    counts={r['player_id']:0 for r in keepers}
    evidence=[]
    if not keepers or any(not r['player_id'] for r in keepers):
        return {}, ['identity_unresolved'], []
    if len(counts)!=len(keepers):
        raise ValueError('Duplicate keeper identity')
    if shots.duplicated('event_id').any():
        raise ValueError('Duplicate shot event')
    player_rows=(int(opponent_stats.record_count.sum()) if 'record_count' in opponent_stats else len(opponent_stats))
    if player_rows<11:
        problems.append('incomplete_boxscore')
    # A missing own-goal flag cannot safely remove or retain the row.
    if shots.is_own_goal.isna().any() or shots.big_chance.isna().any():
        problems.append('missing_shot_flags')
    n=shots[shots.is_own_goal.eq(False)]
    expected=int(opponent_stats.totalScoringAtt.sum())
    if len(n)!=expected:
        problems.append('shot_count_mismatch')
    if n.big_chance.sum()==0 and expected>0 and shots.empty:
        problems.append('missing_shots')
    # Big chances missed also includes opportunities with NO shot (type 60).
    # Consequently its box-score total is an upper bound on missed BC shots.
    if n.loc[n.type_id.ne(16),'big_chance'].sum()>opponent_stats.bigChanceMissed.sum():
        problems.append('big_chance_missed_conflict')
    if n.loc[n.type_id.eq(16),'big_chance'].sum()!=opponent_stats.bigChanceScored.sum():
        problems.append('big_chance_scored_conflict')
    byid={int(r['event_id']):r for r in events.to_dict('records')}
    for row in n.to_dict('records'):
        raw=byid.get(int(row['event_id']))
        if raw and bool(row['big_chance']) != ('214' in raw['q']):
            problems.append('shot_event_bc_conflict')
    candidates=n[n.type_id.eq(15)&n.big_chance.eq(True)]
    for shot in candidates.to_dict('records'):
        eid=int(shot['event_id'])
        raw=byid.get(eid)
        blocked=shot['is_blocked']
        if pd.isna(blocked):
            if raw and raw['q']:
                blocked='82' in raw['q']
            else:
                problems.append('missing_block_flag')
                continue
        if raw and bool(blocked)!=('82' in raw['q']):
            problems.append('shot_event_block_conflict')
            continue
        saver=None
        method='excluded_outfield_block'
        save_id=None
        if not blocked:
            if len(keepers)==1:
                saver=keepers[0]['player_id']
                method='sole_active_fpl_keeper'
            elif raw:
                # Period is essential: first-half stoppage and second-half
                # clock values overlap. Same second alone is not a valid join.
                hits=[]
                for ev in events.to_dict('records'):
                    dt=ev['minute']*60+ev['second']-shot['minute']*60-shot['second']
                    if (ev['type_id']==10 and ev['player_id'] in counts and
                        ev['team_id']==keepers[0]['team_id'] and
                        ev['period_id']==raw['period_id'] and -1<=dt<=3 and
                        '94' not in ev['q']):
                        hits.append(ev)
                if len({hit['player_id'] for hit in hits})==1:
                    saver=hits[0]['player_id'];save_id=int(hits[0]['event_id'])
                    if len(hits)==1:
                        method='unique_paired_keeper_save'
                    else:
                        save_id=None;method='unique_keeper_in_save_sequence'
                else:
                    problems.append('ambiguous_keeper_substitution')
            else:
                problems.append('missing_period_for_keeper_substitution')
            if saver:counts[saver]+=1
        evidence.append(dict(shot_event_id=eid,shooter=shot['player_name'],
                             minute=shot['minute'],second=shot['second'],
                             blocked=bool(blocked),keeper_id=saver or '',
                             save_event_id=save_id,method=method,
                             qualifier_json=raw['qualifier_json'] if raw else ''))
    for r in keepers:
        value=counts[r['player_id']]
        if value>r['fpl_saves']:
            problems.append('exceeds_fpl_saves')
        ex=r['explicit_big_chance_saves']
        if pd.notna(ex) and value!=ex:
            problems.append('explicit_count_conflict')
    return counts,sorted(set(problems)),evidence


def main():
    # Frozen projections allow replay after the external release tag changes.
    s=pd.read_csv(ROOT/'inputs/player_stats.csv.gz')
    h=pd.concat([pd.read_csv(path,dtype={
        'big_chance':'boolean','is_own_goal':'boolean','is_blocked':'boolean'})
        for path in sorted((ROOT/'inputs').glob('shots-*.csv.gz'))],ignore_index=True)
    e=pd.concat([pd.read_csv(path) for path in sorted((ROOT/'inputs').glob('events-*.csv.gz'))],ignore_index=True)
    targets=pd.read_csv(ROOT/'inputs/targets.csv.gz')
    for col in ['match_id','player_id','team_id']:
        targets[col]=targets[col].fillna('')
    e['q']=e.qualifier_json.map(json.loads)
    sg=dict(tuple(s.groupby('match_id')));hg=dict(tuple(h.groupby('match_id')));eg=dict(tuple(e.groupby('match_id')))
    results=[];evidence=[]
    for (season,fixture,side),g in targets.groupby(['season','fixture','side']):
        k=g.to_dict('records');mid=k[0]['match_id'];tid=k[0]['team_id']
        if not mid or not tid or any(r['identity_status']!='matched' for r in k):
            counts={};problems=['identity_unresolved'];ev=[]
        else:
            st=sg[mid];st=st[st.team_id.ne(tid)]
            hs=hg.get(mid,h.iloc[:0]);hs=hs[hs.team_id.ne(tid)]
            es=eg.get(mid,e.iloc[:0])
            counts,problems,ev=recover_team(k,st,hs,es)
        for r in k:
            results.append({**r,'candidate_big_chance_saves':counts.get(r['player_id']),
                'big_chance_saves':counts.get(r['player_id']) if not problems else None,
                'status':'reconstructed' if not problems else 'unresolved',
                'reason':';'.join(problems)})
        evidence.extend(dict(season=season,fixture=fixture,side=side,match_id=mid,**x) for x in ev)
    out=pd.DataFrame(results);out.to_csv(ROOT/'keeper_counts.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    out[out.status.eq('unresolved')].to_csv(ROOT/'unresolved_keepers.csv',index=False)
    pd.DataFrame(evidence).to_csv(ROOT/'save_evidence.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    coverage=out.groupby('season').agg(keepers=('element','size'),reconstructed=('status',lambda x:x.eq('reconstructed').sum()),big_chance_saves=('big_chance_saves','sum'))
    coverage.to_csv(ROOT/'coverage.csv');print(coverage.to_string())
    print(out[out.status.eq('unresolved')].reason.value_counts().to_string())


if __name__=='__main__':main()
