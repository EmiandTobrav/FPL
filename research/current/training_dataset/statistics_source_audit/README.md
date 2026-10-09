# Expected-statistic source qualification

A short source/schema check finds no expected metrics in the inspected raw
Opta player_stats archive. The refreshed shot_events archive has xg/xgot,
but their native FPL/Opta model lineage is not established. The repository's
season-level xmetrics use generated XGBoost/xPass model outputs.

[Maintainer README](https://github.com/peteowen1/pannadata/blob/main/README.md),
[data dictionary](https://github.com/peteowen1/pannadata/blob/main/DATA_DICTIONARY.md)
and [raw extraction code](https://github.com/peteowen1/pannadata/blob/main/scripts/opta/opta_scraper.py)
are primary source documentation. No expected-statistic value or ledger field
is filled by this check. Preserve the distinction between source event data,
computed alternate model metrics and native FPL expected statistics. Inspect
verified metric lineage or another compatible source before a comparison
pilot; do not spend time on a bulk substitute that cannot meet the standard.
