"""Reconcile explicit primary team counters; retain bounded unknowns as null.

Replay after recover.py and reconcile_followup.py. No network required.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from recover import team

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'resumption'
KEY = ['season', 'fixture', 'code']


def explicit_team_value(active_keepers, minutes, keeper_saves, team_saves, explicit, archive):
    """Assign only an explicit counter to a sole, full-match active keeper."""
    if active_keepers != 1 or minutes != 90:
        return None
    values = [keeper_saves, team_saves, explicit]
    if any(pd.isna(v) for v in values):
        return None
    if any(v != int(v) or v < 0 for v in values):
        raise ValueError('invalid count')
    if keeper_saves != team_saves or explicit > team_saves:
        return None
    if pd.notna(archive) and archive != explicit:
        return None
    return int(explicit)


def upper_bound(saves, opponent_missed):
    """A saved big chance is a subset of saves and opponent missed big chances.

    Missing opponent counters add no constraint, especially no implicit zero.
    """
    if pd.isna(saves) or saves < 0 or saves != int(saves):
        raise ValueError('invalid save bound')
    if pd.isna(opponent_missed):
        return int(saves)
    if opponent_missed < 0 or opponent_missed != int(opponent_missed):
        raise ValueError('invalid missed-chance bound')
    return int(min(saves, opponent_missed))


def counters(payload, tid):
    pairs = payload['data'][str(tid)]['M']
    values = {s['name']: s['value'] for s in pairs}
    if len(values) != len(pairs):
        raise ValueError('duplicate statistic names')
    return values


def main():
    base = pd.read_csv(ROOT / 'keeper_counts.csv.gz')
    primary = pd.read_csv(ROOT / 'followup/primary_verified/observations.csv').set_index(KEY)
    manifest = pd.read_csv(ROOT / 'followup/primary_manifest.csv').set_index(KEY)
    sources = {(s['season'], s['fixture']): s for s in json.loads((OUT / 'sources.json').read_text())}
    bounds, decisions = [], []
    # Include already-applied rows to make replay idempotent.
    selected = base.status.eq('unresolved') | base.resolution_method.eq('explicit_primary_team_counter')
    for i, r in base[selected].iterrows():
        key = tuple(r[k] for k in KEY)
        source = sources[(r.season, int(r.fixture))]
        raw = (OUT / source['file']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise ValueError('source hash mismatch')
        payload = json.loads(raw)
        entity = payload['entity']
        assert entity['id'] == int(manifest.loc[key].pulse_id) == source['pulse_id']
        assert entity['gameweek']['compSeason']['label'] == r.season.replace('-', '/')[:5] + r.season[-2:]
        assert datetime.fromtimestamp(entity['kickoff']['millis'] / 1000, timezone.utc).date().isoformat() == r.date
        assert team(entity['teams'][0]['team']['name']) == team(r.home)
        assert team(entity['teams'][1]['team']['name']) == team(r.away)
        side = 0 if r.side == 'h' else 1
        own = counters(payload, entity['teams'][side]['team']['id'])
        opp = counters(payload, entity['teams'][1-side]['team']['id'])
        cohort = base[base.season.eq(r.season) & base.fixture.eq(r.fixture) & base.side.eq(r.side)]
        pr = primary.loc[key]
        saves = pr.get('pl_saves')
        assert saves == r.fpl_saves == r.fotmob_saves
        assert pr.get('pl_mins_played') == r.fotmob_minutes
        value = explicit_team_value(len(cohort), r.fotmob_minutes, saves,
                                    own.get('saves'), own.get('big_chance_saves'),
                                    r.explicit_big_chance_saves)
        if value is not None:
            evidence = dict(pulse_id=source['pulse_id'], source_sha256=source['sha256'],
                            team_saves=own['saves'], primary_keeper_saves=saves,
                            active_keepers=len(cohort), keeper_minutes=r.fotmob_minutes,
                            explicit_team_big_chance_saves=value,
                            archive_keeper_big_chance_saves=r.explicit_big_chance_saves,
                            conflicting_shot_candidate=r.candidate_big_chance_saves)
            decisions.append({**dict(zip(KEY, key)), 'name': r['name'],
                              'big_chance_saves': value, 'evidence': json.dumps(evidence)})
            base.loc[i, ['big_chance_saves', 'status', 'reason', 'resolution_method']] = [
                value, 'reconstructed', '', 'explicit_primary_team_counter']
        else:
            missed = opp.get('big_chance_missed')
            maximum = upper_bound(saves, missed)
            bounds.append({**dict(zip(KEY, key)), 'name': r['name'], 'minimum': 0,
                           'maximum': maximum, 'primary_saves': int(saves),
                           'opponent_big_chance_missed': missed,
                           'tightened': maximum < saves, 'status': 'unresolved',
                           'source_sha256': source['sha256']})
    pd.DataFrame(decisions).to_csv(OUT / 'decisions.csv', index=False)
    pd.DataFrame(bounds).to_csv(OUT / 'unresolved_bounds.csv', index=False)
    base.to_csv(ROOT / 'keeper_counts.csv.gz', index=False, compression={'method': 'gzip', 'mtime': 0})
    base[base.status.eq('unresolved')].to_csv(ROOT / 'unresolved_keepers.csv', index=False)
    base.groupby('season').agg(keepers=('element', 'size'),
        reconstructed=('status', lambda x: x.eq('reconstructed').sum()),
        big_chance_saves=('big_chance_saves', 'sum')).to_csv(ROOT / 'coverage.csv')
    hist = base[base.season.ne('2026-27')]
    findings = json.loads((ROOT / 'findings.json').read_text())
    findings.update(reconstructed=int(hist.status.eq('reconstructed').sum()),
        unresolved_observations=int(hist.status.eq('unresolved').sum()),
        unresolved_matches=len(hist[hist.status.eq('unresolved')][['season', 'fixture']].drop_duplicates()),
        historical_coverage_fraction=float(hist.status.eq('reconstructed').mean()),
        primary_match_totals_resolved=len(decisions), primary_match_totals_collected=len(sources))
    (ROOT / 'findings.json').write_text(json.dumps(findings, indent=2) + '\n')
    summary = dict(resolved=len(decisions), remaining=len(bounds),
                   tightened_bounds=int(sum(b['tightened'] for b in bounds)),
                   full_historical_rescoring_ready=False)
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(summary)


if __name__ == '__main__':
    main()
