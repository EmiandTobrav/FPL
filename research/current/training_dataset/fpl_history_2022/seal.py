"""Freeze exact archived CSV response bytes for portable offline reproduction."""
import gzip
import io
import json
import tarfile

from plan import P, digest
from collect import check_plan


def main():
    check_plan()
    sources = json.loads((P / 'sources.json').read_text())
    plan = json.loads((P / 'source_plan.json').read_text())
    if [x['element'] for x in sources] != [x['element'] for x in plan['players']]:
        raise ValueError('Incomplete source acquisition inventory')
    target = io.BytesIO()
    with gzip.GzipFile(fileobj=target, mode='wb', filename='', mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w') as archive:
            for row in sources:
                if row['status'] != 'archived':
                    continue
                path = P / row['file']
                if digest(path) != row['sha256']:
                    raise ValueError('Source CSV bytes changed')
                info = tarfile.TarInfo(row['file'])
                info.size = path.stat().st_size
                archive.addfile(info, io.BytesIO(path.read_bytes()))
    (P / 'raw_inputs.tar.gz').write_bytes(target.getvalue())
    manifest = dict(archive_sha256=digest(P / 'raw_inputs.tar.gz'), entries=sources,
        plan_lock_sha256=digest(P / 'plan_lock.json'), collection_code_sha256=digest(P / 'collect.py'),
        seal_code_sha256=digest(P / 'seal.py'), repository_commit=plan['commit'])
    (P / 'raw_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(dict(sources=len(sources), archived=sum(x['status']=='archived' for x in sources), bytes=len(target.getvalue())))


if __name__ == '__main__':
    main()
