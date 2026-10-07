# 2026/27 source qualification

GW1 was used to debug column mapping and compare formula variants. It is development data, not an independent accuracy estimate.

Before fetching GW2: freeze the candidate in validate_bps.py. Use FPL assists for the FPL-facing candidate; use PL accurate_cross_nocorner as the empirically supported cross counter (the public label says open-play cross; the observed inclusion of free-kick crosses needs to remain documented). Use was_fouled and fouls, not absent fk-prefixed names.

Evaluate GW2 without fitting further variants: report exact BPS agreement, bonus agreement, signed errors, identity/minutes/goals checks. A provisional source qualification pass requires at least 99% exact BPS agreement and at least 99% bonus agreement, plus a complete ten-match player set. Passing does not prove historical big-chance-save coverage or modern historical assists. Missing historical fields remain unknown. No dataset promotion from this pilot alone.
