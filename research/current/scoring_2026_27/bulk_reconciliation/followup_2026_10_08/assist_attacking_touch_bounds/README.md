# Successful attacking pass: candidate upper bounds

A positively recorded pass by a scoring-team player other than the scorer excludes earlier other attackers as assist candidates. Keep the passer and every later scoring-team event actor; do not infer who actually receives an assist.

**5,440 additional complete assist fields at this stage**; cumulative closure
against the batch2 ledger is **6,897**. These cumulative
numbers overlap between stages and must not be summed. The stage adds
7,397 candidate exclusions; no new per-goal assist awards.
Previously complete totals are preserved (60,753).

Only normal goals are eligible: penalties, direct free kicks and own goals are
excluded. Missing identities, ambiguous attacking boundary events, fouls, deleted
rows, other goals and coverage interruptions make the rule abstain. All relevant
same-time actors are retained. The scorer cannot assist their own goal.

Predictions, source inputs and the full2025 plan were frozen before comparison.
Controls: 185 one-goal comparisons and
287 applicable unresolved goal predictions;
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
