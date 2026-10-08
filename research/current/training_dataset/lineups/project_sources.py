"""Produce lossless EPL source projections from separately frozen archives."""
from pathlib import Path
import hashlib
import json
import lzma
import pyarrow.parquet as pq

P = Path(__file__).resolve().parent


def main():
    manifest = json.loads((P / 'source_assets.json').read_text())
    sources = {}
    for asset in manifest['assets']:
        raw = P / 'raw' / asset['name']
        actual = hashlib.file_digest(raw.open('rb'), 'sha256').hexdigest()
        if actual != asset['digest'].removeprefix('sha256:'):
            raise ValueError(f'Archive fingerprint mismatch: {asset["name"]}')
        frame = pq.read_table(raw, filters=[('competition', '=', 'EPL'),
            ('season', 'in', [f'{year}-{year+1}' for year in range(2019, 2027)])]).to_pandas()
        frame = frame.sort_values(['season', 'match_id'] + (['player_id'] if 'player_id' in frame else []))
        name = asset['name'].replace('.parquet', '.csv.xz')
        path = P / name
        path.write_bytes(lzma.compress(frame.to_csv(index=False, lineterminator='\n').encode()))
        sources[name] = dict(rows=len(frame), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                             source_archive_sha256=actual, columns=list(frame.columns))
    (P / 'projection_manifest.json').write_text(json.dumps(dict(version='epl_lossless_lineups_and_fixtures_v1',
        scope='EPL seasons 2019-2020..2026-2027; all source columns and all lineup rows retained',
        source_assets_sha256=hashlib.sha256((P / 'source_assets.json').read_bytes()).hexdigest(),
        projection_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        pyarrow_version='18.1.0', projections=sources), indent=2) + '\n')
    print({name: value['rows'] for name, value in sources.items()})


if __name__ == '__main__':
    main()
