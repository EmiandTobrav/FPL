# Candidate bounds after documented defensive possession

**2,304 additional complete assist fields**, including 2,192 zeros and 112 positive
totals assembled from already qualified awards, are available after 3,818 new
candidate exclusions across 558 previously unresolved historical goals. This
stage awards no new goal assist. All 56,992 previously complete totals are preserved.

For normal open-play goals, two successive successful opposing passes establish
controlled defensive possession. A defensive pass breaks an earlier assist chain;
the possible candidate set therefore includes every identified scoring-team event
actor after the last pass, except the scorer. Actors are never selected from an
absence of an assist marker. The rule excludes penalties, direct free kicks and
own goals, and abstains on fouls, deletions, incomplete actor identity, coverage
interruptions or ambiguous boundary cases. Administrative exceptions and exact
conditions are pinned in `protocol.json` and `certificates.py`.

The predictor and full 2025/26 scoring-team plan were frozen before comparison.
74 applicable unresolved control goals, 566 team vectors in 353 fixtures and 44
one-goal controls produced zero incompatibilities; there were no contradictions
of previous awards or positive candidate bounds. These are temporal/shared-Opta
regression checks with previously seen outcomes, not a pristine holdout or an
independent-provider test. Source-quality flags remain on all derived fields.

Use `predict.py`, `validate.py`, then `build.py`. Input dependencies are frozen in
`freeze.json`; all are present in the enclosing published snapshot. This stage
preserves previous goal decisions and adds only candidate exclusions. A player
match total is emitted only when every goal contribution is known. Missing goal
inventories remain open. Twelve focused rule/guard tests accompany the transform.
