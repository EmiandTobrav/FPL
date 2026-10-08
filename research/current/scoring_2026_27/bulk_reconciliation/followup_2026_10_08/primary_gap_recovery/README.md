# Official player statistics for the 21 archive gaps

The fixed 21-fixture inventory is recovered through official fixture metadata,
lineups and substitutions, then fixture-scoped player statistics. Three later
2024/25 fixtures (1, 2, 3) were selected before control comparisons. All 593 gap
participants and 92 controls have unique official/FPL identities and exactly one
appearance: **685 player responses and 24 fixture responses**.

**2,345 current missing requirements become available:** 548 line clearances,
455 times tackled, 330 won tackles, 330 signed legacy net tackles, 322 fouls won,
320 shots on target and 40 CBI. Only currently missing cells are filled. The
21-fixture queue falls from 3,106 to **761** requirements; event inventories for
assists and big-chance saves are still missing. Official fixture goal descriptions
are all `G` here and cannot identify penalty goals or target-rule assists.

Explicit player counters are preserved. A missing component becomes zero only
when the complete active roster's known nonnegative sum exactly exhausts an
explicit compatible team total. CBI requires all three components. Legacy net
tackles remain `2*won-total`, including negatives; BPS clipping is not qualified.
Existing season-to-match line conservation is reused with newly verified team
identities and fresh positive-value contradiction vetoes. No omitted season total
is filled with zero.

The new source evidence is season-specific: `times_tackled` is explicitly present,
including zeros, in 2020/21 and 2022/23. It remains absent in these 2019/20 responses.
This explains why the earlier 2019/20 single-player pilot could not recover the
field. No alias or dribble proxy is used; do not repeat that failed 2019 route.

Control results: **532 existing-field comparisons and 344 explicit native-component
comparisons, zero disagreements**. These counts overlap and are not independent
samples. SOT, fouls won and keeper location are not required ledger fields in the
later control season, so their native counter pairs are the applicable checks
(16, 40 and 3 respectively). `initial_validation_summary.json` records the overly
narrow first ledger-only qualification report; the corrected validator uses the
native comparisons already required by the frozen protocol. Predictions, control
selection and zero-error policy did not change. Penalty goals have no applicable
controls here and are withheld. Checks reuse Opta-derived evidence and previously
seen seasons; they establish mapping/arithmetic consistency, not independent
provider validation or final scoring qualification.

`raw_inputs.tar.gz` contains 711 exact stored files (709 scoped responses plus the
team-season pilot response and its metadata); `raw_manifest.json` verifies every
byte. The first fixture pilot was JSON-normalized before storage; its stored bytes
and hash are preserved, and are not claimed to be original HTTP wire bytes. All
other collected scoped responses retain their response bytes. `sources.json`
records exact URLs and hashes. `bootstrap.py` restores offline and refuses to
overwrite differing local files. `verify_sources.py` repeats scope, identity,
active roster and full stat projection checks without network access.

The separate team/12 season/274 probe still omits `clearance_off_line`; this does
not establish zero. No further four-team batch was attempted on that route.

Reproduce from the enclosing snapshot after its root bootstrap:

```sh
python primary_gap_recovery/bootstrap.py
python primary_gap_recovery/verify_sources.py
python primary_gap_recovery/predict.py
python primary_gap_recovery/validate.py
```

`collect.py` is optional network collection; normal replay does not run it.
