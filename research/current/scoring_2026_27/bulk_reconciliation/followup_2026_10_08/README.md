# Current snapshot: batch 3

The current ledger is `bulk_batch3/results/requirements.csv.xz`: 16,227 open fields,
14,990 affected player-matches; 62,290 complete player-matches and490 whole fixtures.
Batch3 closes8,058 fields (33.18%). Run `python bulk_batch3/reproduce.py` directly;
this batch needs no bootstrap or network. All earlier stages and raw inputs remain
preserved. The historical instructions below still apply to older-stage replays.

# Published follow-up snapshot — 8 October 2026

The current queue and work order are linked from [CURRENT.json](../CURRENT.json)
and [WORK_ORDER.md](../WORK_ORDER.md). The full current ledger is
[requirements.csv.xz](bulk_batch3/results/requirements.csv.xz); the open-only
queue is [remaining_fields.csv.gz](bulk_batch3/results/remaining_fields.csv.gz).
Both can be read directly with `pandas.read_csv`.

Batch 2 adds primary_gap_recovery, assist_possession_bounds, a withheld penalty
pilot, and bulk_batch2: 4,649 more fields resolved, 24,285 remaining. Its replay
verifies 33 outputs and the new raw responses offline.

The original local snapshot is preserved, including its historical
`published=false` run metadata. This Git commit publishes it; that metadata is
not a statement about the branch's current publication status.

## Exact offline restoration and replay

Two original gzip ledgers exceed the upload request size after base64 encoding.
Their bytes are committed in parts, with SHA256 hashes in `ledger_parts.json`.
Restore them before running the original frozen scripts:

```sh
python bootstrap.py
python bulk_batch3/reproduce.py
# From the parent bulk_reconciliation directory:
python priority/build.py
```

The bootstrap concatenates bytes; it does NOT recompress CSV or depend on a
particular zlib version. It refuses to overwrite a differing local ledger.
Python3.12 and pandas2.2.3 are the original replay environment. No network,
old workstation directories, DuckDB or large raw downloads are required.

[Original batch report](bulk_followup/README.md) documents source authority,
control limitations and preservation.26 new tests and27 replay outputs passed
before publication. This is a checkpoint plus a replay of the latest increment,
not a promise to rebuild every prior intermediate stage. The incoming cumulative
ledger is included exactly, and all prior published repository history remains.
No model training, scoring recomputation, main merge or production promotion
is part of this publication.
