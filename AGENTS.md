# Project Rules

- No data leakage.
- Time-based validation only.
- Every model must beat baselines.
- Keep feature engineering separate from model training.
- Write tests for key data transformations.


- For new experiments, read `research/current/benchmark.json` and use its active benchmark (`fixture_full_h3_adaptive_tc`) as the primary model comparator on matching evaluation seasons and resources.
- Keep archived experiment reference definitions and results unchanged; the old `mix_ridge_extra_50` remains a secondary historical control.
