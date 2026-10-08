"""Verify primary positive terms and freeze bounds before reading FPL BPS."""
from pathlib import Path
import hashlib
import json
import tarfile

import pandas as pd

from bounds import POSITIVE, NEGATIVE, counter, known, upper_bound
from certificates import zero_certificate
from prepare import P, R, S, K, digest, write_locked
from collect import check_freeze, normalize

CONSERVABLE = {'total_clearance':'totalClearance', 'outfielder_block':'outfielderBlock',
              'interception':'interception', 'total_tackle':'totalTackle', 'won_tackle':'wonTackle'}


def check_conservation_scope(source, fixtures, verified):
    if source.duplicated(['match_id','player_id']).any():
        raise ValueError('Duplicate source-player conservation inventory')
    if fixtures.index.duplicated().any() or verified.index.duplicated().any():
        raise ValueError('Ambiguous fixture identity')
    groups = source[['season','fixture','match_id','team_id']].drop_duplicates()
    for row in groups.itertuples(index=False):
        if row.match_id not in fixtures.index or (row.season,row.fixture) not in verified.index:
            raise ValueError('Conservation source has unknown fixture')
        fx, identity = fixtures.loc[row.match_id], verified.loc[(row.season,row.fixture)]
        expected_season = row.season[:4] + '-' + str(int(row.season[:4])+1)
        if (identity.match_id != row.match_id or str(fx.season) != expected_season
                or row.team_id not in [fx.home_team_id,fx.away_team_id]):
            raise ValueError('Conservation source season/fixture/team disagreement')


def main():
    check_freeze()
    plan = pd.read_csv(P / 'plan.csv')
    original_collection_plan = json.loads((P / 'source_manifest.json').read_text())
    if (digest(P / 'raw_inputs.tar.gz') != original_collection_plan['archive_sha256']
            or digest(P / 'direct_primary_plan/freeze.json') != original_collection_plan['plan_freeze_sha256']
            or digest(P / 'collect.py') != original_collection_plan['collector_code_sha256']):
        raise ValueError('Primary responses differ from original frozen collection')
    entries = original_collection_plan['entries']
    if (len(entries) != len(plan) or len({tuple(x[k] for k in K) for x in entries}) != len(plan)
            or set(tuple(x[k] for k in K) for x in entries) != set(map(tuple,plan[K].to_numpy()))):
        raise ValueError('Primary response inventory differs from fixed control population')
    source = pd.read_csv(S / 'bulk_reconciliation/inputs/source_players.csv.gz', low_memory=False)
    if source.duplicated(['match_id','player_id']).any():
        raise ValueError('Duplicate source-player conservation inventory')
    fixtures = pd.read_csv(P.parents[1] / 'lineups/opta_fixtures.csv.xz').set_index('match_id')
    if fixtures.index.duplicated().any():
        raise ValueError('Ambiguous source fixture identity')
    verified = pd.read_csv(P.parents[1] / 'lineups/fixture_identity.csv').set_index(['season','fixture'])
    check_conservation_scope(source, fixtures, verified)
    native = pd.read_csv(P.parent / 'results/historical_inventory.csv.xz', usecols=K+['was_home']).set_index(K)
    team_totals = pd.read_csv(S / 'bulk_reconciliation/full_team_totals.csv').set_index(['season','fixture','side'])
    if team_totals.index.duplicated().any():
        raise ValueError('Duplicate primary team totals')
    line_source = json.loads((P / 'primary_line_totals_source.json').read_text())
    if digest(P / line_source['file']) != line_source['sha256']:
        raise ValueError('Primary season-total evidence changed')
    line = json.loads((P / line_source['file']).read_text())
    if line['entity'] != 'clearance_off_line' or line['stats']['pageInfo']['numPages'] != 1:
        raise ValueError('Wrong/incomplete line-clearance season rank')
    line_totals = {}
    for row in line['stats']['content']:
        team = int(row['owner']['id'])
        if team in line_totals:
            raise ValueError('Duplicate primary season-total team')
        line_totals[team] = counter(row, 'value')
    by_target = plan.set_index(K)
    comparisons, predictions, proofs = [], [], []
    with tarfile.open(P / 'raw_inputs.tar.gz') as archive:
        files = [x.name for x in archive.getmembers() if x.isfile()]
        if len(files) != len(set(files)) or set(files) != {e['file'] for e in entries}:
            raise ValueError('Archive contains wrong or duplicated response members')
        for entry in entries:
            key = tuple(entry[k] for k in K)
            row = by_target.loc[key].to_dict()
            row.update(dict(zip(K,key)))
            raw = archive.extractfile(entry['file']).read()
            if hashlib.sha256(raw).hexdigest() != entry['sha256']:
                raise ValueError('Primary member hash changed')
            stats = normalize(raw, row)
            fx = fixtures.loc[row['match_id']]
            side = 'home' if bool(native.loc[key,'was_home']) else 'away'
            expected_team = fx[side + '_team_id']
            identity = verified.loc[key[:2]]
            if (identity.match_id != row['match_id'] or identity.status != 'verified_full_lineup'
                    or str(fx.season) != key[0][:4] + '-' + str(int(key[0][:4])+1)
                    or expected_team != row['team_id']):
                raise ValueError('Verified fixture/season/clubside identity disagreement')
            group = source[source.match_id.eq(row['match_id']) & source.team_id.eq(row['team_id'])]
            target_source = group[group.player_id.eq(row['player_id'])]
            if len(target_source) != 1 or group.empty:
                raise ValueError('Missing source participant in fixed conservation group')
            target_source = target_source.iloc[0]
            primary_team = team_totals.loc[(*key[:2],side)]
            if (primary_team.match_id != row['match_id'] or int(primary_team.pulse_id) != int(row['pulse_id'])
                    or float(fx.home_score) != float(primary_team.home_score)
                    or float(fx.away_score) != float(primary_team.away_score)):
                raise ValueError('Primary team scope differs from verified fixture')
            local = []
            def get_field(name):
                if name in stats:
                    return counter(stats,name), 'explicit_primary_counter'
                if name in CONSERVABLE:
                    field = CONSERVABLE[name]
                    value = zero_certificate(primary_team[name], group[field], target_source[field])
                    if value is not None:
                        proofs.append(dict(zip(K,key), field=name, method='exact_team_match_conservation',
                            primary_total=primary_team[name], known_sum=float(group[field].sum()),
                            primary_team_id=int(primary_team.primary_team_id), source_team_id=row['team_id']))
                        return value, 'exact_primary_team_match_conservation_zero'
                if name == 'clearance_off_line' and key[0] == '2024-25':
                    season = source[source.season.eq(key[0]) & source.team_id.eq(row['team_id'])]
                    total = line_totals.get(int(primary_team.primary_team_id))
                    value = zero_certificate(total, season.clearanceOffLine, target_source.clearanceOffLine)
                    if value is not None:
                        proofs.append(dict(zip(K,key), field=name, method='exact_team_season_conservation',
                            primary_total=total, known_sum=float(season.clearanceOffLine.sum()),
                            primary_team_id=int(primary_team.primary_team_id), source_team_id=row['team_id']))
                        return value, 'exact_primary_team_season_conservation_zero'
                return None, 'primary_omitted_unqualified'
            def compare(field, expected, value, method):
                status = 'missing' if value is None else 'agreed' if value == expected else 'disagreed'
                local.append(dict(zip(K,key), field=field, archived=expected,
                    primary=value, primary_method=method, status=status))
                return status == 'agreed'
            candidate, good = row.copy(), True
            for archived, primary in POSITIVE.items():
                value, method = get_field(primary)
                good &= compare(primary, row[archived], value, method)
                candidate[archived] = value
            components = {}
            for primary in ['total_clearance','outfielder_block','interception','total_tackle','won_tackle']:
                value, method = get_field(primary)
                components[primary] = value
                # Known original components are also compared independently.
                old = target_source[CONSERVABLE[primary]]
                if known(old):
                    good &= compare(primary, old, value, method)
            cbi = sum(components[f] for f in ['total_clearance','outfielder_block','interception']) if all(components[f] is not None for f in ['total_clearance','outfielder_block','interception']) else None
            net = 2 * components['won_tackle'] - components['total_tackle'] if components['won_tackle'] is not None and components['total_tackle'] is not None else None
            good &= compare('clearances_blocks_interceptions', row['clearances_blocks_interceptions'], cbi, 'verified_component_sum')
            good &= compare('legacy_net_tackles', row['legacy_net_tackles'], net, 'verified_component_difference')
            candidate['clearances_blocks_interceptions'], candidate['legacy_net_tackles'] = cbi, net
            for field, (primary, _) in NEGATIVE.items():
                value = counter(stats,primary) if primary in stats else None
                candidate[field] = value
                if known(row[field]) and value is not None:
                    good &= compare(primary,row[field],value,'explicit_primary_negative_counter')
            value = counter(stats,'times_tackled') if 'times_tackled' in stats else None
            candidate['times_tackled'] = value
            if known(row.get('times_tackled')) and value is not None:
                good &= compare('times_tackled',row['times_tackled'],value,'explicit_primary_negative_counter')
            if key[0] == '2024-25':
                for field, primary in [('goal_line_clearances','clearance_off_line'),
                                       ('fouls_won','was_fouled'),('shots_on_target','ontarget_scoring_att')]:
                    value, method = get_field(primary)
                    good &= compare(primary,row[field],value,method)
                    candidate[field] = value
            comparisons.extend(local)
            if good:
                signed, terms_signed, ignored = upper_bound(candidate, 'signed')
                clipped, terms_clipped, _ = upper_bound(candidate, 'clipped')
                predictions.append(dict(zip(K,key), primary_upper_signed=signed,
                    primary_upper_clipped=clipped, ignored_negative_fields='|'.join(sorted(ignored)),
                    primary_source_sha256=entry['sha256'], source_verified=True))
    pd.DataFrame(comparisons).to_csv(P / 'primary_comparisons.csv', index=False)
    pd.DataFrame(proofs).to_csv(P / 'zero_certificates.csv', index=False)
    pd.DataFrame(predictions).to_csv(P / 'primary_predictions.csv', index=False)
    files = ['primary_comparisons.csv','zero_certificates.csv','primary_predictions.csv']
    write_locked(P / 'primary_prediction_freeze.json', dict(
        input_sha256={name:digest(R/name) for name in json.loads((P/'freeze.json').read_text())['input_sha256']},
        primary_source_manifest_sha256=digest(P / 'source_manifest.json'),
        primary_archive_sha256=digest(P / 'raw_inputs.tar.gz'),
        predictor_code_sha256=digest(Path(__file__)), outcomes_read=False,
        plan_freeze_sha256=digest(P / 'freeze.json'),
        output_sha256={name:digest(P/name) for name in files}))
    counts = pd.DataFrame(predictions).groupby('season').size().to_dict() if predictions else {}
    print(dict(planned=len(plan), primary_verified_predictions=len(predictions),
        predictions_by_season=counts, comparisons=len(comparisons),
        explicit_disagreements=sum(x['status']=='disagreed' for x in comparisons),
        qualified_zero_certificates=len(proofs), outcomes_read=False))


if __name__ == '__main__':
    main()
