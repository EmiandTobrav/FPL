# Explicit attacking ball touch: candidate upper bounds

A positively recorded type61 ball-touch event supplies an attacking-touch boundary. Its event-schema route is tested separately; it is not an inference from a missing assist marker.

**151 additional complete assist fields at this stage**; cumulative closure
against the batch2 ledger is **8,058**. These cumulative
numbers overlap between stages and must not be summed. The stage adds
199 candidate exclusions; no new per-goal assist awards.
Previously complete totals are preserved (67,203).

Only normal goals are eligible: penalties, direct free kicks and own goals are
excluded. Missing identities, ambiguous attacking boundary events, fouls, deleted
rows, other goals and coverage interruptions make the rule abstain. All relevant
same-time actors are retained. The scorer cannot assist their own goal.

Predictions, source inputs and the full2025 plan were frozen before comparison.
Controls: 40 one-goal comparisons and
78 applicable unresolved goal predictions;
all566 team vectors in353 fixtures remain feasible, with zero one-goal errors,
protected-award conflicts or positive-certificate contradictions. This reuses
previously seen/shared-Opta outcomes: temporal regression, not an independent
provider test or pristine holdout. Counts overlap with other stages.

All qualified old and new bounds are also tested **together**, forcing existing
goal awards and checking the intersection of allowed candidate sets against FPL
player totals. See `bulk_batch3/joint_validation_summary.json`. Separate-rule
feasibility alone is not the combined publication gate.

Run `predict.py`, `validate.py`, then `build.py`, in stage order documented in
`bulk_batch3/reproduce.py`. The cumulative ledger remains input availability only;
rawFPL, approved corrections, frozen earlier files and locked scoring are unchanged.
