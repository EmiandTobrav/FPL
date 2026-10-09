# Fifteen keeper counters; source exceptions block whole team-seasons

**15 missing big-chance-save counters are closed at zero:** one in 2019/20,
seven in 2020/21 and seven in 2022/23. Open requirements fall
**11,234 → 11,219**. Input-complete player-matches increase
**66,477 → 66,478**; input-complete whole fixtures remain **824**.
All 775,233 other ledger rows and all original source columns are preserved.

The [original route](../big_chance_zero_bounds/README.md) remains failed:
1/983 known cases disagree and its original 16 candidates were not applied.
New evidence was located in the pre-existing approved keeper exception:
Alex McCarthy, Southampton–Aston Villa, 2019/20 fixture 269, code 58376.
An unblocked saved-shot qualifier 214 establishes a big-chance save, and the
approved complete paired-save reconstruction explicitly records a
`big_chance_missed_conflict`. The sparse aggregated counter cannot support
a physical zero for that source team-season, despite its exact season sum.

This source version therefore disqualifies **all of Aston Villa's 2019/20
aggregated missed-big-chance bounds**, based on the pre-existing approved
exception and its shot evidence. The guard is frozen before new prediction
comparison. It applies to the whole group, including unknown targets and
correct-looking zero controls; it never overrides the approved keeper 1.
Other source groups still require explicit season totals, complete 38-match
inventories and exact exhaustion, reusing the frozen four-season projection.

All **983 original control identities remain** in the new comparison file:
**971 numeric predictions in 835 fixtures** agree, **12 controls abstain**
for the source guard, and one of those is the verified positive negative
control. All 13 guarded source rows abstain, including **one missing target**
which remains open. Only 15 of the original 16 candidates are emitted.
An unexplained disagreement in any other group still vetoes the whole route.
The zero-error limit and minimum numeric-control/fixture gates are unchanged;
source-guard violations have a separate zero-error gate. These checks share
upstream evidence; abstentions are not numeric agreement or a new holdout.

Three transformation/preservation tests pass. **17 generated files** reproduce
byte-identically in a fresh offline tree. Collective source QA remains pending;
no historical BPS, bonus, point labels or features are recalculated.

From the repository root:

```sh
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/big_chance_zero_bounds_guarded/test_guards.py
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/big_chance_zero_bounds_guarded/reproduce.py
```
