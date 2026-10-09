# Shot xG/xGOT lineage — completed, no native imports

Six retained primary source files are pinned to Pannadata commit
`55d2a80b097bbeac1c0093f572d5ce7efa41f675` and verified by SHA-256.
The published legacy enrichment predicts xG using its own `xg_model.rds`;
the source explicitly states that the model is its only current xG source.
Its xGOT route also predicts from its own model. The current workflow chooses
context scoring with `xg_model_v5.rds` / `xgot_model_v3.rds`.

[Pinned enrichment source](https://github.com/peteowen1/pannadata/blob/55d2a80b097bbeac1c0093f572d5ce7efa41f675/scripts/enrich_shots_xg.R),
[pinned workflow](https://github.com/peteowen1/pannadata/blob/55d2a80b097bbeac1c0093f572d5ce7efa41f675/.github/workflows/daily-opta-scrape.yml).
Exact code anchors and line numbers are in `findings.json`.

These model outputs have no certified native FPL model provenance. Preserving
existing non-null values does not establish each historical row's model
version or source. Do not import them as native FPL xG/xA/xGI/xGC or use them
to clear a required comparable-statistics field. Physical shot events remain
available for separately qualified event reconstruction.

**Zero imports and zero requirement closures.** The investigation is finished;
unchanged archive/schema/code checks must not be repeated. A new native-compatible
provenance version or another qualified source is needed to reopen this route.

Offline verification: `python reproduce.py` from this directory. It verifies
all six source hashes and reproduces the decision byte-identically. No network,
ledger, canonical table, scoring label or model is changed.
