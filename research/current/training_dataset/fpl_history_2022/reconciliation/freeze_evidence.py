"""Lock acquired provenance; explicitly post-diagnostic, never an unseen split."""
import json

from plan import P, digest
from collect import check_plan


def main():
    check_plan()
    names = ['end_season_file_blobs.csv', 'weekly_source.json', 'gw16_2022_11_23.csv']
    result = dict(stage='post-diagnostic source-evidence lock; no new holdout claimed',
        original_protocol_and_input_lock_sha256=digest(P / 'plan_lock.json'),
        input_sha256={name: digest(P / name) for name in names})
    encoded = json.dumps(result, indent=2) + '\n'
    path = P / 'evidence_lock.json'
    if path.exists() and path.read_text() != encoded:
        raise ValueError('Acquired source evidence changed after freezing')
    path.write_text(encoded)
    print(dict(locked_source_files=len(names)))


if __name__ == '__main__':
    main()
