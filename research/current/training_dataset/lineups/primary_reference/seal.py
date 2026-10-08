"""Preserve the exact reference response bytes in a portable deterministic archive."""
from pathlib import Path
import sys
import io
import gzip
import tarfile
import json

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P.parent))
from predict import digest
from collect import check_plan


def main():
    check_plan()
    sources = json.loads((P / 'sources.json').read_text())
    if len(sources) != 142 or len({x['file'] for x in sources}) != 142:
        raise ValueError('Incomplete reference collection')
    target = io.BytesIO()
    with gzip.GzipFile(fileobj=target, mode='wb', mtime=0, filename='') as zipped:
        with tarfile.open(fileobj=zipped, mode='w') as archive:
            for row in sorted(sources, key=lambda x: x['file']):
                path = P / row['file']
                if digest(path) != row['sha256']:
                    raise ValueError('Reference response changed')
                info = tarfile.TarInfo(row['file'])
                info.size = path.stat().st_size
                archive.addfile(info, io.BytesIO(path.read_bytes()))
    (P / 'raw_inputs.tar.gz').write_bytes(target.getvalue())
    manifest = dict(archive_sha256=digest(P / 'raw_inputs.tar.gz'), entries=sources,
        sources_sha256=digest(P / 'sources.json'), plan_lock_sha256=digest(P / 'plan_lock.json'),
        collection_code_sha256=digest(P / 'collect.py'), seal_code_sha256=digest(Path(__file__)))
    (P / 'raw_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(dict(responses=len(sources), bytes=len(target.getvalue())))


if __name__ == '__main__':
    main()
