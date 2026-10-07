# Explicit event qualifier audit

Continuation of PR #1 from `fcbef323cba697af865ca978d4a162d72a990791`.
This adds a versioned decoder and coverage audit without changing the earlier
`assist_rules` experiment or any approved historical labels.

## Source and interpretation

[`schema.json`](schema.json) records a pinned [optasoccer parser dictionary](https://github.com/andrewRowlinson/optasoccer/blob/825cadb56c9c976a8c34c9d5da26d6e37c6ff239/optasoccer/metadata.py),
its commit, Git blob and SHA-256, plus 17 selected numeric mappings.
This is a published parser implementation, **not a provider-certified dictionary**.
The mappings identify 383 as control, 384 as pass and 385 as clearance;
328 identifies a first-touch shot. The pass mapping agrees with the two
previously collected official Gross/Jensen scenarios. Those are development
controls, not an independent test of the dictionary across every season.

The decoder uses an explicitly present, unique subtype on tackles/interceptions.
Missing or contradictory subtypes remain unknown. It never interprets a missing
384 as evidence of a non-pass. A first-touch shot marker supports using the shot
coordinates for the scorer's contact only when the episode contains no earlier
scorer action. It does not establish pass intention, continuity, complete touch
counts or an assist award. General shot coordinates are still not receiving
coordinates. Qualifier 154 is inventoried, not used to infer the intended
recipient for arbitrary deflected passes.

## Results

The same ten preselected controls improve from three to **four resolved negative
decisions**, all agreeing with their official decisions; six remain unknown.
The extra decision is Jensen: the defender's explicit pass subtype supports
denial. Gross gains a pass route but remains unresolved. Four cases gain a
conditional receiving-location fact from explicit first-touch markers. These
are four facts, not four new assist awards. No positive award is generated.
Official narrative annotations are not injected into the raw-data calculation.
Expected official decisions are used only for comparison.

Across the existing mapped historical archive, 4,125 of 7,543 goal events have
an explicit first-touch marker. This is a marker inventory, not 4,125 resolved
assists. Among 136,432 tackles/interceptions, 31,063 have an explicit pass
subtype and 20,553 lack all three subtypes. No conflicting subtypes were found.

| Season | Tackles/interceptions | Missing subtype |
|---|---:|---:|
| 2019/20 | 20,337 | 20,246 |
| 2020/21 | 19,266 | 2 |
| 2021/22 | 19,721 | 1 |
| 2022/23 | 19,175 | 2 |
| 2023/24 | 19,728 | 0 |
| 2024/25 | 19,254 | 1 |
| 2025/26 | 18,951 | 301 |

The strong season dependence prevents treating missing tags as zero/non-pass.
The audit covers the existing mapped matches only; it does not fill the
previously identified missing fixtures/events. The goal ledger preserves raw
qualifiers and IDs for later review and contains no new labels.

## Reproduction and limits

Run from the repository root with pandas and pyarrow available:

```bash
python research/current/scoring_2026_27/assist_schema/run.py
python research/current/scoring_2026_27/assist_schema/coverage.py
python -m unittest discover -s research/current/scoring_2026_27/assist_schema -p 'test_*.py'
```

`run.py` reuses the frozen six-match and three-match inputs from `bps_recovery`
and `assist_rules`. `coverage.py` verifies the frozen events archive through
`bps_recovery.prepare_sources.verify` before reading selected columns and seasons.
Its archive SHA-256 is
`a69184e1c0d35ed39e1146b748f0ff3b649750bb1d52624286406e0cacd4b6f2`.
`manifest.json` records this experiment and its reused input hashes.

Eight tests cover absent/conflicting markers, three-way decoding, the new
negative decision, remaining ambiguity, first-touch location, and the earlier
scorer-action guard. Replay validation is recorded in `validation.json`.
Candidate/goal IDs are still preselected. Complete physical touch counts,
sequence verification, recipient intention and handball causality remain
limitations; own-goal and general rebound routes are not fully implemented.
Next: automatic candidate selection with explicit abstention, then new held-out
official controls before any historical assist approval.

Keeper coverage remains 5,343/5,381, with 38 unresolved observations. Historical
points, BPS, bonus, models and benchmark are unchanged. Full 2026/27 historical
harmonization remains incomplete.
