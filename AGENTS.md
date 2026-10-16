# Project Rules

- No data leakage.
- Time-based validation only.
- Every model must beat baselines.
- Keep feature engineering separate from model training.
- Write tests for key data transformations.


- For new experiments, read `research/current/benchmark.json` and use its active benchmark (`fixture_full_h3_adaptive_tc`) as the primary model comparator on matching evaluation seasons and resources.
- Keep archived experiment reference definitions and results unchanged; the old `mix_ridge_extra_50` remains a secondary historical control.


## Current reconstructed data and experiment navigation

- Read README.md, overview/PROJECT.json, overview/STATUS.md and overview/NEXT.md before new model work.
- For the reconstructed 2026/27 best-effort dataset, use datasets/fpl_model_pipeline_v1 and compare against fixture_full_h3_adaptive_tc_harmonized_causal_v1 under a matched contract. The earlier benchmark instruction above applies to archived historical-point experiments. Never transfer old benchmark scores to rescored targets.
- Search overview/research_catalog.json and read related findings before proposing another experiment. Follow overview/WORKFLOW.md; preserve negative results and explicitly explain changes from prior work.
- Do not launch a duplicate of a recorded ongoing campaign or exceed its frozen configuration cap. Registration does not authorize a launch.
- Published advanced campaign summaries are scoped snapshots; full replay or resume requires the separate local archive described in docs/GIT_LAYOUT.md.
- Keep archived references and locked results unchanged. Record new work separately.

- Use model_lab as the shared entry point for bounded forecast trials and legal manager simulations. Framework validation is not a new model-selection result. Manager-learning pilots are implemented and evaluated; consult their recorded results in docs/RESULTS_INDEX.md and overview/MANAGER_LEARNING.md before proposing new work. Failed candidates remain research history, not the default manager.
