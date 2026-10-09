# Positive player-season goal-line exhaustion — finished, no candidates

Reuse explicit primary goal-line counters and native FPL minutes for six
historical ledger seasons. Select complete appearance groups before comparing
their counters. The approved Ferguson minute correction is an identity-scope
input only; native raw rows remain unchanged.

All **371 complete positive player-seasons / 10,109 player-matches** agree with
the explicit source season counters; there are zero sum errors. The original
minimum gates (1,000 complete matches, 100 positive seasons, 20 groups in each
historical season, no errors or negative residuals) pass unchanged. This checks
same-source conservation compatibility, not independent holdout performance.

There are **zero incomplete residual groups and zero candidate fields**. Every
one of the **16 remaining goal-line requirements** lacks an explicit primary
player-season counter. An omitted player is not a zero. Positive residuals are
never allocated to individual matches.

**Zero requirement closures.** Existing season-counter inputs cannot advance
this track; do not repeat them. Reopening requires a new explicit compatible
player/match counter or a qualified complete event inventory for a remaining key.
No ledger, scoring, canonical or raw-data change is applied.

Offline verification: `python reproduce.py` from this directory. All nine
generated files reproduce byte-identically from their frozen inputs.
`python test_gates.py` passes two counterexample tests: a complete counter
mismatch and a negative partial residual each block the full qualification.
