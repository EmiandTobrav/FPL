# Assist rule controls with explicit evidence gaps

7 October 2026; follows PR #1 commit `e8677041fdd13fc8e516378a72dad0e0c7547904`.
No new historical assist labels, keeper values, points, BPS, bonus or model
inputs are changed. Decisions here concern **one candidate for one goal**, not
the player's complete match assist count.

## Results

The partial rule engine produces the documented result for all ten examples
when supplied with their officially described situation facts. These are
consistency/development checks, **not ten independent automatic predictions**.
The six previous examples and four additional cases were all read before the
implementation was finalised. There is no untouched holdout in this report.

| Candidate | Season | Official result | Raw-event decision |
|---|---|---|---|
| Marmoush | 2024/25 | Assist | Unresolved |
| Pedro Porro | 2024/25 | Assist | Unresolved |
| Alex Scott | 2024/25 | Assist | Unresolved |
| Pickford | 2024/25 | Assist | Unresolved |
| Bruno Fernandes | 2024/25 | No assist | Unresolved |
| Cunha | 2024/25 | No assist | No assist: two defensive contacts |
| Gross | 2025/26 | Assist | Unresolved |
| Jensen | 2025/26 | No assist | Unresolved |
| Semenyo | 2025/26 | No assist | No assist: scorer's own rebound |
| Marmoush | 2025/26 | No assist | No assist: scorer's own rebound |

Raw events support three negative decisions and zero positive decisions in
these deliberately difficult cases. This cannot estimate accuracy or coverage
for all goals. The previous four official historical additions are preserved.
The extra four cases are in three matches; full event projections are committed.

## Concrete findings

- Porro's episode includes an aerial-duel row and a clearance for Gabriel.
  These must not automatically become two physical touches. Error, recovery and
  challenge records also cannot simply be added to a touch count.
- Ugarte's shot is at Opta x=84.9, inside the box. Beto's clearance endpoint in
  the attacking orientation is x=81.5, outside. Both are retained as proxies;
  neither is silently converted to a verified receiving location. The official
  description supplies the receiving location and intended-recipient judgement.
- Pickford's pass is at 36:54; the penalty goal is at 41:33. A two-minute goal
  window misses the originating incident. Deleted-event/VAR records are retained
  as evidence, not counted as contacts or proof of causal completeness.
- Cunha's goal is in first-half stoppage time at 49:54. Second-half events with
  similar clock values must not enter that episode. Events are restricted by
  match and period, then ordered by clock; global event IDs are not chronological.
- A tackle/interception can have a pass interpretation. Both the Gross and
  Thiaw incidents carry raw qualifier `384`; the official article describes
  pass-type touches in both. This is a promising **schema hypothesis**, not a
  verified universal code dictionary. The extractor does not decode it as fact.

## Rule and evidence boundaries

`rules.py` returns awarded, denied or unresolved. A verified disqualifying fact
can deny a candidate without knowing unrelated fields. A positive decision
requires verified sequence facts and the relevant touch bound, recipient or
set-piece conditions. Unknown does not mean zero or false. A zero-to-one bound
can suffice when both possibilities qualify. Passes and inadvertent touches
have different criteria; self-rebounds are excluded. Penalty/handball causality
is a distinct route. General own-goal and non-self rebound awards are explicitly
unsupported by this partial engine.

`extract.py` inspects **preselected** candidate/goal IDs. It is not a universal
candidate finder. Distinct defensive contact participants provide a lower
bound; omitted events cannot establish an upper bound. Same-second order,
receiving position, complete continuity and intention remain unverified.
Coordinate checks use Opta's standardized box boundary (x=83; y=21.1..78.9),
not a linear 105-by-68-metre conversion.

`inputs/official_facts.json` supplies narrative-based adjudication facts,
including continuity implied by the official description. The labels are
separate in `inputs/cases.json`, but the cases are already known; do not present
this as a blind evaluation. `fact_provenance.csv` marks every annotation and
`run.py` rejects conflicting known raw facts. Tightening a lower bound is allowed.
`evidence.json` retains raw facts, proxies and remaining missing requirements.

## Sources

- Target rules checked against the official [FPL rules page](https://www.premierleague.com/en/news/4661029)
  and the previously captured 2026/27 rule component, whose hash is in `sources.json`.
- [Six original official examples](https://www.premierleague.com/en/news/4362187/whats-new-in-202526-fantasy-changes-to-assists-rules).
- [Four additional official decisions](https://www.premierleague.com/en/news/4655693).
  The article's title/body disagree on the gameweek number; match identity is
  based on date, teams, score, scorer and goal event, not that gameweek text.
- [Opta event definitions](https://www.statsperform.com/opta-event-definitions/)
  distinguish touches, duels, errors and goalkeeper drops.
- Kloppy's own parser and pitch model, pinned at commit
  `11822569caa4490e99321be54afc3919ad6b417a`, identify basic numeric event types
  and coordinate geometry. This is an implementation reference, not a substitute
  for an authoritative definition of qualifier 384.
- Raw match events derive from the same hash-pinned Pannadata archive as keeper
  and BPS recovery. No source refresh or paid access was used.

Source URLs, hashes, IDs and unresolved schema interpretation are recorded in
`sources.json`. The large raw archive and earlier six-match projection are reused,
not duplicated. The new three-match projection is reproducible with
`prepare_inputs.py` from the original archive.

## Replay and next gate

From this directory:

```sh
python run.py
python -m unittest discover -p 'test_*.py'
```

Seventeen tests cover missingness, upper bounds, recipient intention, handball
causality, period isolation, ID ordering, contact duplication, unsupported routes
and the raw evidence gaps. Replay output hashes are checked in `validation.json`.

Before applying these rules to the 7,543-goal historical queue, obtain verified
receiving/intent facts and a touch-type schema; establish complete event sequences
and candidate selection; then freeze the implementation before testing new
matches. Continue to keep partial decisions separate from exact historical labels.
Keeper status remains 5,343/5,381, with 38 unresolved observations. Cost: 0 NOK.
