# Public factual goal inventory: 54 penalty-goal gaps closed

The current missing-data queue selected 44 fixtures needing penalty-goal or
foul-won counters. Thirty additional control fixtures were fixed before their
public ESPN summaries were collected. A completed-FT date/team/final-score
bridge identifies all 74 fixtures. The source supplies explicit player counters,
typed goal events and commentary; provider assists are not target-rule assists.

**54 of 56 penalty-goal requirements are filled: 50 explicit inventory-backed
zeros and four penalties.** By season: 2019/20 eight, 2020/21 nineteen,
2022/23 twenty, 2024/25 seven. The positive events belong to Aubameyang (2019
fixture 137), De Bruyne (2020 fixture 104), Mac Allister (2022 fixture 283) and
Kane (2022 fixture 286). This is factual counter acquisition, not new scoring.

Qualification requires a unique full scoring inventory, recognized scored
penalty type, exact final-score counts, unique scorer identities and complete
native FPL goal/own-goal vectors. Six fetched fixtures abstain on unresolved
scorer identity, including two planned controls. No unknown event is assigned
zero. The fixed penalty gate requires 20 control fixtures, 100 values, ten
positive values and zero errors. Actual results: **769 unique planned-control
values from 28 fixtures, 14 positive values, zero errors**. All available
references in the fetched population give 1,829 comparisons on 1,815 unique
keys, also zero errors. References comprise closed approved counters, explicit
archive counters and the exact native FPL zero-goals subset bound. Counts overlap.

The foul mapping fails globally: **five reference disagreements on three
distinct player keys**, despite 655 planned-control values. No fouls-won values
are filled, including the plausible keeper zeros. Existing source-specific
gates and failed studies remain unchanged. These comparisons are previously
observed regression/source compatibility, with possible shared upstream data;
they are not an independent holdout or final scoring/source qualification.

The new authoritative rest is **11,260** (previously 11,314), still affecting
10,822 player-matches. **66,458 player-matches and 824 whole fixtures** have
complete scoring input. This batch adds no complete player-match/fixture because
other fields remain missing. Exactly 54 previously absent cells change;
775,194 other ledger rows and every raw/native/source/previous-value column are
asserted unchanged. Collective source-quality flags remain enabled. No BPS,
bonus, assists, points, features, training rows or models are rebuilt.

`raw_inputs.tar.gz` preserves **119 exact public responses** (45 scoreboards,
74 summaries), with every byte verified by `raw_manifest.json`. The summaries
include **1,279 key events and 7,508 commentary entries**, available as source
evidence for later goal/causal work. Commentary is not a complete Opta touch
inventory. The raw archive is about 2.46 MB compressed; downloaded responses
are not duplicated as ordinary tracked files. Six unresolved scorer cases stay
explicit in `fixture_gates.csv`; the two remaining penalty requirements are
in the incomplete Arsenal-Leeds 2022 fixture 281 goal vector.

The separate archive-refresh check found unchanged 67,518 EPL shot records,
no new keys or changed existing recovery-projection values, and no coverage
for the 21 missing archive fixtures. `archive_refresh_findings.json` records
the version evidence; that route is set aside until relevant data changes.

Five tests pass. An isolated offline replay reproduces **16 generated files**
byte-identically, including physical predictions, validation, ledger/readiness
outputs and their manifests. Source dependencies and all frozen plans are pinned.

From this directory:

```sh
python test_acquisition.py
python reproduce.py
```

Initial `prepare.py`/`collect.py` are acquisition steps, not normal replay.
Replay uses the frozen native input projection and parent pointers; it requires
neither current network access nor the large parquet archives. Full collective
QA, historical rescoring and training integration remain later phases.
