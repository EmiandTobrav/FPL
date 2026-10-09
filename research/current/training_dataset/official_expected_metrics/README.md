# Official Premier League SDP source — bounded audit completed

The [official expected-goals page](https://www.premierleague.com/en/stats/top/players/expected-goals)
and retained production frontend identify a public SDP API. This extends the
[earlier SDP schema pilot](../../scoring_2026_27/bulk_reconciliation/followup_2026_10_08/sdp_schema_pilot/README.md),
which already established team-match statistics and the missing individual
inventory. It is not a new provider. The repeated match-schema probe was
unnecessary; its bytes are retained without counting it as new progress.
Additional observed player-season, leaderboard, lineup and match-list routes
still supply no player-match values. Anonymous public reads succeed; no authentication is used.
URL/status/response hashes and bytes are preserved in `api_sources.json`.

The observed routes return:

- Ten player-season leaderboard rows with xG/xA and defensive season counters.
- Donnarumma's player-season defensive statistics and full match list.
- Two team-match statistic rows with expected metrics.
- Individual lineups with verified player codes, but no player-match statistics.

The official numeric match ID agrees with the native FPL fixture code;
the archive UUID probe returns an empty array. An unused `vX` route from
the frontend returns HTTP 400; the actual match-list route works. These responses
remain preserved, and no empty/sparse response becomes a zero.

**Zero fields filled.** None of the observed responses provides a matched
per-player per-match CBI or expected-statistic value. Season totals and team
metrics cannot be allocated to individual matches/players. The six native
keeper-CBI vetoes remain unresolved, and all 341 keeper requirements remain
missing. `six_case_coverage.csv` preserves the six required native values and
numeric player/match identities without inventing comparison values.

This audit is limited to the observed official frontend routes; it does not
prove that another public or licensed route cannot exist. Do not repeat these
unchanged requests. Reopening requires a documented player-match route/export
with concrete compatible values; the full existing native/historical gates must
then pass before any application. No canonical, scoring, model or raw-data change.

Offline verification: `python reproduce.py` from this directory. All three
decisions regenerate byte-identically after verifying retained input hashes.
`collect.py URL NAME` only retains a new anonymous response and refuses to
overwrite an existing response; it is not part of the offline replay.
