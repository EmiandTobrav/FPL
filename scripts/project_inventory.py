"""Read-only inventory of project data, duplicate bytes and experiment receipts.

Writes only overview/ outputs. Never deletes, moves or changes source artifacts.
Run from any directory with: python3 scripts/project_inventory.py
"""
from pathlib import Path
from collections import defaultdict, Counter
import csv
import hashlib
import json
import os
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'overview'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save_csv(name, rows, fields):
    with (OUT / name).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    OUT.mkdir(exist_ok=True)
    files = []
    sizes = defaultdict(list)
    folders = defaultdict(lambda: [0, 0])
    counts = Counter()
    ledgers = []
    media = []
    for root, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', 'sources', 'overview')]
        for name in names:
            p = Path(root) / name
            if p.is_symlink():
                continue
            st = p.stat()
            rel = p.relative_to(ROOT).as_posix()
            row = {'path': rel, 'bytes': st.st_size, 'allocated_bytes': st.st_blocks * 512}
            files.append(row)
            sizes[st.st_size].append(row)
            folders[rel.split('/')[0]][0] += 1
            folders[rel.split('/')[0]][1] += row['allocated_bytes']
            counts[p.suffix] += 1
            if name.startswith('requirements.csv'):
                ledgers.append(row)
            if p.suffix.lower() in {'.jpg', '.png', '.jpeg', '.webp', '.gif', '.bmp', '.tiff', '.mp4', '.mkv', '.webm', '.mov', '.avi', '.m4v'}:
                media.append(row)
    duplicates = []
    for size, group in sizes.items():
        if size == 0 or len(group) < 2:
            continue
        hashes = defaultdict(list)
        for row in group:
            hashes[digest(ROOT / row['path'])].append(row)
        for sha, rows in hashes.items():
            if len(rows) > 1:
                duplicates.append({'sha256': sha, 'bytes_each': size,
                    'redundant_logical_bytes': size * (len(rows) - 1),
                    'paths': [r['path'] for r in rows]})
    duplicates.sort(key=lambda g: g['redundant_logical_bytes'], reverse=True)
    runs = []
    for base in ('reports/fpl_simulator_2026_10_13', 'reports/fpl_improvement_2026_10_14'):
        for p in sorted((ROOT / base).rglob('summary.json')):
            try:
                d = json.loads(p.read_text())
            except (ValueError, OSError):
                continue
            if 'experiment_id' not in d:
                continue
            runs.append({'path': p.relative_to(ROOT).as_posix(), 'experiment_id': d['experiment_id'],
                'candidate': d.get('candidate', ''), 'season': d.get('season', ''),
                'mode': d.get('mode', ''), 'setting': d.get('setting', ''),
                'complete_season': d.get('complete_season', False),
                'net_points': d.get('net_points', d.get('net_season_points', '')),
                'contract_sha256': d.get('contract_sha256', ''),
                'interpretation': 'stored run receipt; audit approval must be read separately'})
    stats = {'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Excludes Git databases, synced sources and generated overview; active files may change during scan.',
        'files': len(files), 'allocated_bytes': sum(r['allocated_bytes'] for r in files),
        'folder_counts_and_allocated_bytes': dict(folders), 'extension_counts': dict(counts),
        'requirements_snapshot_files': len(ledgers),
        'requirements_snapshot_allocated_bytes': sum(r['allocated_bytes'] for r in ledgers),
        'remaining_media_files': len(media),
        'remaining_media_allocated_bytes': sum(r['allocated_bytes'] for r in media),
        'text_document_files': counts['.md'] + counts['.txt'],
        'text_document_logical_bytes': sum(r['bytes'] for r in files if Path(r['path']).suffix in ('.md', '.txt')),
        'duplicate_groups': len(duplicates),
        'duplicate_redundant_logical_bytes': sum(g['redundant_logical_bytes'] for g in duplicates),
        'duplicate_caution': 'Byte equality does not establish safe deletion: paths, manifests, replay inputs and immutable experiment references may depend on copies.',
        'stored_experiment_receipts': len(runs)}
    (OUT / 'inventory.json').write_text(json.dumps(stats, indent=2, ensure_ascii=False) + '\n')
    (OUT / 'duplicates.json').write_text(json.dumps(duplicates, indent=2, ensure_ascii=False) + '\n')
    save_csv('snapshots.csv', ledgers, ['path', 'bytes', 'allocated_bytes'])
    save_csv('remaining_media.csv', media, ['path', 'bytes', 'allocated_bytes'])
    save_csv('runs.csv', runs, ['path', 'experiment_id', 'candidate', 'season', 'mode', 'setting', 'complete_season', 'net_points', 'contract_sha256', 'interpretation'])
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
