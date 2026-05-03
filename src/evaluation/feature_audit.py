"""Audit modelling dataset columns before feature ablation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from evaluation.backtest import STABLE_FEATURE_COLUMNS


DEFAULT_INPUT_PATH = Path("data/processed/modeling_dataset.parquet")
DEFAULT_CSV_PATH = Path("reports/full_feature_audit.csv")
DEFAULT_MARKDOWN_PATH = Path("reports/full_feature_audit.md")

IDENTIFIER_COLUMNS = {
    "name",
    "element",
    "id",
    "fixture",
    "team",
    "opponent_team",
}
METADATA_COLUMNS = {
    "season",
    "gw",
    "GW",
    "round",
    "kickoff_time",
    "kickoff_time_formatted",
    "modified",
}
TARGET_COLUMNS = {"next_gw_points", "next_3_gw_points"}
POSITION_COLUMNS = {"position"}
FIXTURE_COLUMNS = {"was_home"}
PRICE_VALUE_COLUMNS = {"value"}
OWNERSHIP_TRANSFER_COLUMNS = {"selected", "transfers_balance", "transfers_in", "transfers_out"}
BASELINE_PREDICTION_COLUMNS = {
    "pred_rolling_3_gameweek_mean",
    "pred_rolling_5_gameweek_mean",
    "pred_minutes_adjusted_rolling_mean",
}
PLAYER_ROLLING_COLUMNS = {
    "points_last_1",
    "points_mean_last_3",
    "points_mean_last_5",
    "minutes_mean_last_3",
    "minutes_mean_last_5",
    "starts_last_5",
    "bonus_last_5",
    "bps_last_5",
    "xG_last_5",
    "xA_last_5",
}
TEAM_ELO_COLUMNS = {
    "team_elo_pre_gw",
    "opponent_elo_pre_gw",
    "elo_difference",
    "home_adjusted_elo_difference",
}
TEAM_FORM_COLUMNS = {
    "team_goals_scored_mean_last_5",
    "team_goals_conceded_mean_last_5",
    "opponent_goals_scored_mean_last_5",
    "opponent_goals_conceded_mean_last_5",
    "team_clean_sheet_rate_last_5",
    "opponent_clean_sheet_rate_last_5",
}
RAW_CURRENT_OUTCOME_COLUMNS = {
    "assists",
    "attempted_passes",
    "big_chances_created",
    "big_chances_missed",
    "bonus",
    "bps",
    "clean_sheets",
    "clearances_blocks_interceptions",
    "completed_passes",
    "creativity",
    "defensive_contribution",
    "dribbles",
    "errors_leading_to_goal",
    "errors_leading_to_goal_attempt",
    "expected_assists",
    "expected_goal_involvements",
    "expected_goals",
    "expected_goals_conceded",
    "fouls",
    "goals_conceded",
    "goals_scored",
    "ict_index",
    "influence",
    "key_passes",
    "minutes",
    "mng_clean_sheets",
    "mng_draw",
    "mng_goals_scored",
    "mng_loss",
    "mng_underdog_draw",
    "mng_underdog_win",
    "mng_win",
    "offside",
    "open_play_crosses",
    "own_goals",
    "penalties_conceded",
    "penalties_missed",
    "penalties_saved",
    "recoveries",
    "red_cards",
    "saves",
    "starts",
    "tackled",
    "tackles",
    "target_missed",
    "team_a_score",
    "team_h_score",
    "threat",
    "total_points",
    "winning_goals",
    "yellow_cards",
}
ADVANCED_STATS_COLUMNS = {
    "creativity",
    "expected_assists",
    "expected_goal_involvements",
    "expected_goals",
    "expected_goals_conceded",
    "ict_index",
    "influence",
    "threat",
    "xG_last_5",
    "xA_last_5",
}


def read_dataset(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported dataset format: {path}")


def semantic_type(series: pd.Series, column: str) -> str:
    if column in TARGET_COLUMNS:
        return "target"
    if column in IDENTIFIER_COLUMNS:
        return "identifier"
    if column in METADATA_COLUMNS:
        return "metadata"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    return "categorical"


def column_group(column: str, missing_pct: float) -> str:
    if column in IDENTIFIER_COLUMNS or column in METADATA_COLUMNS:
        return "identifiers and metadata"
    if column in TARGET_COLUMNS:
        return "targets"
    if column in RAW_CURRENT_OUTCOME_COLUMNS:
        return "raw current-GW outcome columns"
    if column in PLAYER_ROLLING_COLUMNS:
        return "leakage-safe rolling player features"
    if column in BASELINE_PREDICTION_COLUMNS:
        return "baseline prediction features"
    if column in POSITION_COLUMNS:
        return "position features"
    if column in TEAM_ELO_COLUMNS:
        return "team-strength Elo features"
    if column in TEAM_FORM_COLUMNS:
        return "rolling team form features"
    if column in PRICE_VALUE_COLUMNS:
        return "price/value features"
    if column in OWNERSHIP_TRANSFER_COLUMNS:
        return "ownership/transfer features"
    if column in ADVANCED_STATS_COLUMNS:
        return "xG/xA/advanced stats"
    if column in FIXTURE_COLUMNS:
        return "fixture/home-away features"
    if missing_pct >= 0.75:
        return "unavailable or mostly missing features"
    return "unclassified/investigate"


def classify_action(column: str, group: str, missing_pct: float) -> str:
    if group in {"identifiers and metadata", "targets"}:
        return "metadata_only" if group == "identifiers and metadata" else "exclude"
    if column in RAW_CURRENT_OUTCOME_COLUMNS:
        return "keep_lagged_only"
    if group in {
        "leakage-safe rolling player features",
        "baseline prediction features",
        "position features",
        "team-strength Elo features",
        "rolling team form features",
    }:
        return "keep"
    if group in {"fixture/home-away features", "price/value features"}:
        return "investigate"
    if group in {"ownership/transfer features", "xG/xA/advanced stats"}:
        return "keep_lagged_only"
    if missing_pct >= 0.75:
        return "investigate"
    return "investigate"


def availability_flags(column: str, group: str) -> dict[str, bool]:
    after_gameweek = column in RAW_CURRENT_OUTCOME_COLUMNS or column in TARGET_COLUMNS
    deadline_available = group in {
        "leakage-safe rolling player features",
        "baseline prediction features",
        "position features",
        "team-strength Elo features",
        "rolling team form features",
        "fixture/home-away features",
    }
    if group in {"price/value features", "ownership/transfer features"}:
        deadline_available = False
    return {
        "appears_leakage_safe": deadline_available and not after_gameweek,
        "appears_potentially_leaky": after_gameweek
        or group in {"price/value features", "ownership/transfer features", "xG/xA/advanced stats"},
        "available_before_deadline": deadline_available,
        "available_after_gameweek_completed": after_gameweek,
    }


def missing_by_season(frame: pd.DataFrame, column: str) -> str:
    if "season" not in frame.columns:
        return "{}"
    values = (
        frame.groupby(frame["season"].astype(str))[column]
        .apply(lambda series: round(float(series.isna().mean() * 100), 2))
        .to_dict()
    )
    return json.dumps(values, sort_keys=True)


def audit_columns(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    model_features = set(STABLE_FEATURE_COLUMNS)
    for column in frame.columns:
        series = frame[column]
        missing_pct = float(series.isna().mean() * 100)
        group = column_group(column, missing_pct)
        flags = availability_flags(column, group)
        rows.append(
            {
                "column_name": column,
                "dtype": str(series.dtype),
                "non_missing_rows": int(series.notna().sum()),
                "missing_pct_overall": round(missing_pct, 2),
                "missing_pct_by_season": missing_by_season(frame, column),
                "unique_values": int(series.nunique(dropna=True)),
                "semantic_type": semantic_type(series, column),
                "column_group": group,
                "currently_used_as_model_feature": column in model_features,
                **flags,
                "recommended_action": classify_action(column, group, missing_pct),
            }
        )
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "None."
    headers = list(frame.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_reports(audit: pd.DataFrame, csv_path: Path, markdown_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(csv_path, index=False)

    used = audit.loc[audit["currently_used_as_model_feature"]]
    present_columns = set(audit["column_name"])
    configured_feature_rows = pd.DataFrame(
        [
            {
                "feature": column,
                "present_in_dataset": column in present_columns,
                "column_group": (
                    audit.loc[audit["column_name"] == column, "column_group"].iloc[0]
                    if column in present_columns
                    else "created during backtest or unavailable"
                ),
            }
            for column in STABLE_FEATURE_COLUMNS
        ]
    )
    configured_missing = configured_feature_rows.loc[
        ~configured_feature_rows["present_in_dataset"]
    ]
    used_review = used.loc[used["recommended_action"].isin(["investigate", "keep_lagged_only", "exclude"])]
    safe_unused = audit.loc[
        (~audit["currently_used_as_model_feature"])
        & audit["appears_leakage_safe"]
        & audit["recommended_action"].isin(["keep", "investigate"])
    ]
    best_candidates = safe_unused.loc[
        safe_unused["column_group"].isin(
            ["fixture/home-away features", "price/value features", "position features"]
        )
    ][["column_name", "column_group", "recommended_action", "missing_pct_overall"]]
    never_direct = audit.loc[
        audit["column_group"].isin(["targets", "identifiers and metadata"])
        | audit["column_name"].isin({"team_a_score", "team_h_score"})
    ][["column_name", "column_group", "recommended_action"]]
    lagged_only = audit.loc[
        audit["recommended_action"] == "keep_lagged_only"
    ][["column_name", "column_group", "missing_pct_overall"]]

    group_counts = (
        audit.groupby("column_group", as_index=False)
        .size()
        .rename(columns={"size": "columns"})
        .sort_values(["columns", "column_group"], ascending=[False, True])
    )
    used_summary = used[["column_name", "column_group", "appears_leakage_safe", "recommended_action"]]

    lines = [
        "# Full Feature Audit",
        "",
        f"Total columns: {len(audit)}",
        f"Configured model features: {len(STABLE_FEATURE_COLUMNS)}",
        (
            "Configured model features present in dataset: "
            f"{int(audit['currently_used_as_model_feature'].sum())}"
        ),
        f"Excluded columns: {int((audit['recommended_action'] == 'exclude').sum())}",
        f"Likely leakage columns: {int(audit['appears_potentially_leaky'].sum())}",
        f"Mostly missing columns: {int((audit['missing_pct_overall'] >= 75).sum())}",
        "",
        "## Column Groups",
        "",
        markdown_table(group_counts),
        "",
        "## Currently Used Model Features",
        "",
        markdown_table(used_summary),
        "",
        "## Configured Model Features Not Present In Dataset",
        "",
        markdown_table(configured_missing),
        "",
        "## Currently Used Features Needing Review",
        "",
        markdown_table(
            used_review[["column_name", "column_group", "recommended_action", "missing_pct_overall"]]
        ),
        "",
        "## Safe Unused Candidate Features",
        "",
        markdown_table(best_candidates.head(20)),
        "",
        "## Features That Should Never Be Used Directly",
        "",
        markdown_table(never_direct.head(40)),
        "",
        "## Features That Should Only Be Lagged Or Rolled",
        "",
        markdown_table(lagged_only),
        "",
        "## Recommendations",
        "",
        "- Keep the current stable feature list unchanged until ablations are run.",
        "- Treat raw current-GW outcomes as source columns only; add them through lagged or rolling transformations.",
        "- Run the next ablation on supported seasons only: current stable set, then remove team form, remove Elo, and remove baseline prediction features.",
        "- Investigate `was_home`, `value`, and transfer/ownership timing before using them directly.",
        "",
    ]
    markdown_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = read_dataset(args.input)
    audit = audit_columns(frame)
    write_reports(audit, args.csv_output, args.markdown_output)
    print(f"Wrote: {args.csv_output}")
    print(f"Wrote: {args.markdown_output}")


if __name__ == "__main__":
    main()
