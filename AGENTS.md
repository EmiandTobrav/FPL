# Project Rules

- No data leakage.
- Time-based validation only.
- Every model must beat baselines.
- Keep feature engineering separate from model training.
- Write tests for key data transformations.


- For new experiments, read `research/current/benchmark.json` and use its active benchmark (`fixture_full_h3_adaptive_tc`) as the primary model comparator on matching evaluation seasons and resources.
- Keep archived experiment reference definitions and results unchanged; the old `mix_ridge_extra_50` remains a secondary historical control.

## Historical scoring source authority

- Historical FPL is authoritative for compatible existing statistics, including minutes and explicit zeros. Never replace it by external source voting.
- Use external sources for missing/new inputs and documented season-to-2026/27 transformations. Keep missing values missing.
- The current requirements ledger is `research/current/scoring_2026_27/delta_input_audit/`, based on the authority policy in `fpl_authority/`. Older conflict/minute queues are historical diagnostics, not current work priorities.
- Preserve raw FPL, approved keeper values, approved official-event exceptions and locked labels/models/benchmark. Build derived corrections separately.
- Retain historical FPL BPS components that have not changed; qualify changed components before recalculating BPS and reranking whole-match bonus. Do not label baseline totals as harmonized outputs.

- External source checks do not make omitted values zero. Keep signed legacy net-tackle counters separate from the still-unqualified historical BPS clipping rule; distinguish field mapping checks, direct primary agreement and unresolved conflicts.
