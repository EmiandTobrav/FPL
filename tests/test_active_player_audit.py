from pathlib import Path
import shutil

import pandas as pd

from evaluation.active_player_audit import (
    add_active_player_flag,
    build_active_player_audit,
    write_reports,
)


def clean_scratch(name: str) -> Path:
    path = Path("tests") / f".tmp_{name}"
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


def audit_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "season": ["2022-23", "2022-23", "2022-23", "2023-24"],
            "gw": [1, 1, 6, 11],
            "element": [1, 2, 3, 4],
            "position": ["MID", "FWD", "DEF", "GKP"],
            "minutes_mean_last_3": [0, 10, 0, 0],
            "minutes_mean_last_5": [0, 20, 30, 0],
            "starts_last_5": [0, 0, 0, 1],
            "next_gw_points": [12, 4, 6, 2],
        }
    )


def test_active_player_flag_uses_leakage_safe_rule_and_normalizes_position() -> None:
    flagged = add_active_player_flag(audit_rows())

    assert flagged["is_active"].tolist() == [False, True, True, True]
    assert flagged["position"].tolist() == ["MID", "FWD", "DEF", "GK"]


def test_active_player_audit_reports_counts_and_inactive_nonzero_share() -> None:
    audit = build_active_player_audit(audit_rows())
    overall = audit.loc[
        audit["section"].eq("segment_summary")
        & audit["segment_type"].eq("overall")
        & audit["segment"].eq("all")
    ]
    inactive = overall.loc[overall["active_status"].eq("inactive")].iloc[0]

    assert int(inactive["rows"]) == 1
    assert inactive["avg_next_gw_points"] == 12
    assert inactive["nonzero_next_gw_points_share"] == 1.0


def test_inactive_rows_in_top_actual_scorers_are_counted() -> None:
    audit = build_active_player_audit(audit_rows())
    top_10 = audit.loc[
        audit["section"].eq("top_actual_scorers") & audit["segment"].eq("top_10")
    ].iloc[0]

    assert int(top_10["inactive_rows_in_top_k"]) == 1
    assert float(top_10["inactive_share_in_top_k"]) > 0


def test_active_player_audit_writes_csv_and_markdown() -> None:
    scratch = clean_scratch("active_player_audit")
    try:
        audit = build_active_player_audit(audit_rows())
        csv_path = scratch / "active.csv"
        markdown_path = scratch / "active.md"

        write_reports(audit, csv_path, markdown_path)

        assert csv_path.exists()
        assert markdown_path.exists()
        text = markdown_path.read_text(encoding="utf-8")
        assert "Active Player Audit" in text
        assert "Counts By Position" in text
        assert "Recommendation" in text
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
