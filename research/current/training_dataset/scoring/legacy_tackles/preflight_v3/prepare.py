"""Freeze complete-positive-component legacy controls without reading FPL BPS."""
from pathlib import Path
import hashlib
import json

import pandas as pd

from bounds import POSITIVE, NEGATIVE, upper_bound

P = Path(__file__).resolve().parent
R = P.parents[2]
S = R / 'scoring_2026_27'
K = ['season','fixture','code']
LEDGER_FIELDS = ['legacy_net_tackles','clearances_blocks_interceptions','times_tackled',
                 'goal_line_clearances','fouls_won','shots_on_target']
ANCHORS = ['position','minutes','goals_scored','assists','clean_sheets','goals_conceded',
           'penalties_missed','yellow_cards','red_cards','own_goals']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_locked(path, value):
    raw = json.dumps(value, indent=2) + '\n'
    if path.exists() and path.read_text() != raw:
        raise ValueError('Frozen legacy control input/protocol changed: ' + str(path))
    path.write_text(raw)


def main():
    current = S / 'bulk_reconciliation/CURRENT.json'
    pointer = json.loads(current.read_text())
    req_path = S / 'bulk_reconciliation' / pointer['requirements']
    if digest(req_path) != pointer['requirements_sha256']:
        raise ValueError('Current ledger fingerprint changed')
    req = pd.read_csv(req_path, usecols=K + ['field','value','status','is_open'])
    req.loc[req.is_open, 'value'] = float('nan')
    wide = req[req.field.isin(LEDGER_FIELDS)].pivot(index=K, columns='field', values='value').reset_index()
    paths, frames = [current, req_path, P / 'bounds.py', P / 'certificates.py', P / 'rule_corroboration.json'], []
    cols = K + ['mapping_status','match_id','player_id','team_id','wasFouled','ontargetScoringAtt'] + list(POSITIVE) + list(NEGATIVE)
    for year in range(2019, 2025):
        season = f'{year}-{str(year+1)[2:]}'
        path = S / f'bps_recovery/inputs/counts-{season}.csv.gz'
        frames.append(pd.read_csv(path, usecols=cols, low_memory=False))
        paths.append(path)
    source = pd.concat(frames, ignore_index=True).merge(wide, on=K, validate='one_to_one')
    # These components already exist in old 2024 BPS and are absent from its delta ledger.
    last_legacy = source.season.eq('2024-25')
    source.loc[last_legacy,'fouls_won'] = source.loc[last_legacy,'wasFouled']
    source.loc[last_legacy,'shots_on_target'] = source.loc[last_legacy,'ontargetScoringAtt']
    inv_path = P.parent / 'results/historical_inventory.csv.xz'
    # Published BPS/bonus/totals are deliberately not read during selection/prediction.
    native = pd.read_csv(inv_path, usecols=K + ANCHORS)
    paths.append(inv_path)
    source = source.merge(native, on=K, validate='one_to_one')
    candidates = source[source.mapping_status.eq('matched') & source.legacy_net_tackles.lt(0)
                        & source.position.isin(['DEF','MID','FWD'])].copy()
    fields = list(POSITIVE) + ['clearances_blocks_interceptions']
    candidates = candidates[candidates[fields].notna().all(axis=1)]
    current_terms = ['goal_line_clearances','fouls_won','shots_on_target']
    candidates = candidates[candidates.season.ne('2024-25') | candidates[current_terms].notna().all(axis=1)]
    # Known official event-revision bundles remain outside this component study.
    blocked = {('2019-20',115),('2022-23',265),('2023-24',201),('2024-25',83)}
    candidates = candidates[[tuple(r) not in blocked for r in candidates[['season','fixture']].to_numpy()]]
    candidates = candidates.sort_values(K).reset_index(drop=True)
    candidates['bound_signed'], candidates['bound_clipped'] = [upper_bound(r,'signed')[0] for r in candidates.to_dict('records')], [upper_bound(r,'clipped')[0] for r in candidates.to_dict('records')]
    directories = {}
    catalog_path = S / 'bulk_reconciliation/collection_plan.csv'
    catalog = pd.read_csv(catalog_path).set_index(['season','fixture'])
    if catalog.index.duplicated().any():
        raise ValueError('Ambiguous verified primary fixture catalog')
    paths.append(catalog_path)
    for season in sorted(candidates.season.unique()):
        path = S / f'delta_input_audit/inputs/primary/players_{season}.json'
        data = json.loads(path.read_text())['stats']
        if data['pageInfo']['numPages'] != 1:
            raise ValueError('Incomplete primary player directory')
        ids = {}
        for record in data['content']:
            owner = record['owner']
            if owner.get('altIds',{}).get('opta'):
                code, pid = int(owner['altIds']['opta'].lstrip('p')), int(owner['id'])
                if code in ids and ids[code] != pid:
                    raise ValueError('Ambiguous primary player code')
                ids[code] = pid
        directories[season] = ids
        paths.append(path)
        path = R / f'project/data/{season}_fixtures.csv.gz'
        fixtures = pd.read_csv(path).set_index('id')
        selected = candidates.season.eq(season)
        candidates.loc[selected,'pl_player_id'] = candidates.loc[selected,'code'].map(ids)
        candidates.loc[selected,'pulse_id'] = candidates.loc[selected,'fixture'].map(catalog.loc[season].pulse_id)
        paths.append(path)
    if candidates[['pl_player_id','pulse_id']].isna().any().any():
        raise ValueError('Unresolved primary identity in frozen candidate population')
    candidates[['pl_player_id','pulse_id']] = candidates[['pl_player_id','pulse_id']].astype(int)
    if candidates.duplicated(K).any():
        raise ValueError('Duplicate control identity')
    required_seasons = [f'{year}-{str(year+1)[2:]}' for year in range(2019,2025)]
    if sorted(candidates.season.unique()) != required_seasons:
        raise ValueError('At least one legacy season has no complete-positive controls')
    certificate_inputs = [S / 'bulk_reconciliation/inputs/source_players.csv.gz',
        S / 'bulk_reconciliation/full_team_totals.csv',
        P / 'primary_line_totals_2024.json', P / 'primary_line_totals_source.json',
        P.parents[1] / 'lineups/opta_fixtures.csv.xz',
        P.parents[1] / 'lineups/fixture_identity.csv']
    paths += certificate_inputs
    protocol = dict(version='legacy_net_tackle_upper_bound_v3',
        design='Retrospective fixed source/BPS control study, not an untouched scoring holdout. All complete-positive negative-net archived rows selected without reading published BPS/bonus/totals; full pre-known revision fixtures excluded.',
        hypotheses=['signed','clipped'],
        method='Every positive component must be explicit and primary-agreed or have an exact compatible nonnegative total-conservation zero certificate. Allow maximum minute/winning-goal awards; subtract only known nonnegative negative counters. Unknown negative counts remain unknown and are ignored only when computing an upper bound, never stored as observed zero.',
        primary_gate='Require explicit primary positive counters, all three CBI components and both raw tackle components; equality against frozen source/ledger. For an omitted CBI/raw tackle component, certify zero only when that player archive cell is missing and all known source-player contributions exactly exhaust its explicit primary team-match total. The 2024 line-zero certificate requires exact source-player season sums against an explicit primary team-season total and consistent team identity. Other primary omissions abstain before outcomes; positive residuals never imply zero.',
        acceptance=dict(minimum_discriminating_rows=20, minimum_discriminating_rows_per_season=2,
            required_seasons=required_seasons, maximum_clipped_bound_violations=0,
            maximum_primary_explicit_disagreements=0),
        authority='Published historical FPL BPS discriminates only source-verified upper bounds. Dated copied FPL no-negative footnote is corroboration, not authenticated primary rule evidence.',
        source_limits='Primary PL and archive share Opta ancestry; no independent provider holdout. Empirical rule qualification does not approve every external input or final points/bonus.',
        missing_policy='No unknown negative count becomes an observed zero; incomplete positive terms have no bound.',
        training_labels_enabled=False)
    write_locked(P / 'protocol.json', protocol)
    raw = candidates.to_csv(index=False, lineterminator='\n')
    path = P / 'plan.csv'
    if path.exists() and path.read_text() != raw:
        raise ValueError('Frozen candidate selection changed')
    path.write_text(raw)
    paths += [path, P / 'protocol.json']
    write_locked(P / 'freeze.json', dict(input_sha256={str(p.relative_to(R)):digest(p) for p in paths},
        code_sha256=digest(Path(__file__)), outcomes_read=False))
    print(dict(candidates=len(candidates), by_season=candidates.groupby('season').size().to_dict(),
        outcomes_read=False))


if __name__ == '__main__':
    main()
