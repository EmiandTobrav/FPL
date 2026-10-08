# Official SDP schema pilot — no eligible new fields

The current official statistics page and its versioned frontend bundle expose
public team-season and match-statistics routes. Exact URLs and fetched hashes are
recorded in the source metadata. `findings.json` records the relevant API schema.
The public HTML/JavaScript were inspected locally and are not copied into the repo.

The Manchester United 2019/20 team response has38 matches and66 goals, but omits
line clearances. The Liverpool–Norwich fixture1 response contains two team totals,
not a complete player inventory or times-tackled counter. Neither omission is zero.
No new fields, inferred zeros, source-quality upgrades or broad batch result.

The previous web retrieval of match1059702 did not obtain a payload. This pilot
was justified by current official frontend route discovery and a functioning
team-season endpoint, rather than retrying an inaccessible page blindly. Stop here
unless a new supported route can supply the missing variables. Scripts are optional
source investigations, not part of ordinary offline reconciliation/replay.
