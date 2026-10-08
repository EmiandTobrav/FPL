# Successful defensive pass: candidate upper bounds

A successful opposing-team pass positively breaks the preceding assist chain. The earlier version required two passes as additional corroboration. This separately frozen version tests one pass with the same size/error gates and retains all subsequent scoring-team actors.

**1,457 additional complete assist fields at this stage**; cumulative closure
against the batch2 ledger is **1,457**. These cumulative
numbers overlap between stages and must not be summed. The stage adds
2,123 candidate exclusions; no new per-goal assist awards.
Previously complete totals are preserved (59,296).

Only normal goals are eligible: penalties, direct free kicks and own goals are
excluded. Missing identities, ambiguous attacking boundary events, fouls, deleted
rows, other goals and coverage interruptions make the rule abstain. All relevant
same-time actors are retained. The scorer cannot assist their own goal.

Predictions, source inputs and the full2025 plan were frozen before comparison.
Controls: 74 one-goal comparisons and
132 applicable unresolved goal predictions;
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
