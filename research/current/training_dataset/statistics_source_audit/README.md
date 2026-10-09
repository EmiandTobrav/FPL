# Expected-statistic source qualification

A short source/schema check finds no expected metrics in the inspected raw
Opta player_stats archive. The refreshed shot_events archive has xg/xgot.
The subsequent [pinned shot-lineage check](../shot_xg_lineage/README.md)
establishes that the published enrichment routes use Panna's own models;
native FPL/Opta model provenance is not certified. The repository's
season-level xmetrics use generated XGBoost/xPass model outputs.

[Maintainer README](https://github.com/peteowen1/pannadata/blob/main/README.md),
[data dictionary](https://github.com/peteowen1/pannadata/blob/main/DATA_DICTIONARY.md)
and [raw extraction code](https://github.com/peteowen1/pannadata/blob/main/scripts/opta/opta_scraper.py)
are primary source documentation. No expected-statistic value or ledger field
is filled by this check. Preserve the distinction between source event data,
computed alternate model metrics and native FPL expected statistics. Inspect
verified metric lineage or another compatible source before a comparison
pilot; do not spend time on a bulk substitute that cannot meet the standard.
The [official SDP route extension](../official_expected_metrics/README.md)
of the older source pilot provides team-match and player-season metrics, but
no per-player per-match expected values in the observed routes. Both completed
checks import zero metrics; unchanged routes must not be repeated.
