"""Build the processed FPL modeling dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from evaluation.backtest import POSITION_COLUMN, POSITION_LABEL_MAP, normalized_position_labels
from features.rolling_features import (
    FeatureBuildError,
    build_rolling_features,
    expected_candidate_feature_columns,
    player_key_column,
    skipped_candidate_sources,
)
from features.target_builder import build_targets
from features.team_strength import (
    TeamStrengthError,
    build_team_strength_features,
    team_identifier_diagnostics,
)


DEFAULT_INPUT_PATH = Path("data/interim/all_merged_gw.parquet")
DEFAULT_OUTPUT_PATH = Path("data/processed/modeling_dataset.parquet")
DEFAULT_TEAM_PRIORS_PATH = Path("data/manual/team_season_priors.csv")
DEFAULT_TEAM_STRENGTH_REPORT_PATH = Path("reports/team_strength_feature_report.md")
DEFAULT_CANDIDATE_FEATURE_REPORT_PATH = Path("reports/candidate_feature_report.md")
REQUIRED_COLUMNS = ("season", "gw", "total_points", "minutes")
POSITION_FILTER_DIAGNOSTICS_ATTR = "position_filter_diagnostics"


class DatasetBuildError(ValueError):
    """Raised when the processed modeling dataset cannot be built."""


def normalize_and_filter_positions(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize FPL positions and remove rows outside the supported position set."""
    data = frame.copy()
    if POSITION_COLUMN not in data.columns:
        data.attrs[POSITION_FILTER_DIAGNOSTICS_ATTR] = {
            "position_column_present": False,
            "rows_removed": 0,
            "labels_removed": {},
            "seasons_affected": [],
        }
        return data

    raw_positions = data[POSITION_COLUMN].astype("string").str.upper()
    normalized_positions = normalized_position_labels(data[POSITION_COLUMN])
    valid_positions = set(POSITION_LABEL_MAP.values())
    unsupported_mask = raw_positions.notna() & ~normalized_positions.isin(valid_positions)
    removed = data.loc[unsupported_mask].copy()
    diagnostics = {
        "position_column_present": True,
        "rows_removed": int(unsupported_mask.sum()),
        "labels_removed": raw_positions.loc[unsupported_mask].value_counts().sort_index().to_dict(),
        "seasons_affected": (
            sorted(removed["season"].dropna().astype(str).unique())
            if "season" in removed.columns
            else []
        ),
    }
    data[POSITION_COLUMN] = normalized_positions
    data = data.loc[~unsupported_mask].copy()
    data.attrs[POSITION_FILTER_DIAGNOSTICS_ATTR] = diagnostics
    return data


def read_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise DatasetBuildError(f"Input dataset does not exist: {path}")
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise DatasetBuildError(f"Unsupported input format for {path}; expected .parquet or .csv")


def validate_required_columns(
    frame: pd.DataFrame,
    *,
    fail_on_missing_required_columns: bool,
) -> list[str]:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    try:
        player_key_column(frame)
    except FeatureBuildError:
        missing.append("player identifier column: one of element, id, name")

    if missing and fail_on_missing_required_columns:
        raise DatasetBuildError(f"Missing required columns: {missing}")
    return missing


def build_modeling_dataset(
    frame: pd.DataFrame,
    *,
    target_horizon: int = 3,
    fail_on_missing_required_columns: bool = True,
    team_priors_path: Path = DEFAULT_TEAM_PRIORS_PATH,
) -> pd.DataFrame:
    """Apply leakage-safe rolling features and future point targets."""
    missing = validate_required_columns(
        frame,
        fail_on_missing_required_columns=fail_on_missing_required_columns,
    )
    if missing:
        raise DatasetBuildError(f"Cannot build dataset with missing required columns: {missing}")

    source = normalize_and_filter_positions(frame)
    features = build_rolling_features(source)
    try:
        team_priors = pd.read_csv(team_priors_path) if team_priors_path.exists() else None
        team_strength = build_team_strength_features(features, team_season_priors=team_priors)
        features = pd.concat([features.reset_index(drop=True), team_strength.reset_index(drop=True)], axis=1)
    except TeamStrengthError:
        # Team-strength features require reliable team/opponent/home/score source
        # columns. Minimal test fixtures and older raw extracts may not include
        # them, so dataset building falls back to player-only features.
        pass
    dataset = build_targets(features, target_horizon=target_horizon)
    dataset.attrs[POSITION_FILTER_DIAGNOSTICS_ATTR] = source.attrs.get(
        POSITION_FILTER_DIAGNOSTICS_ATTR,
        {},
    )
    return dataset


def write_dataset(frame: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output_path, index=False)


def write_team_strength_report(source: pd.DataFrame, output_path: Path) -> None:
    diagnostics = team_identifier_diagnostics(source)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    supported = ", ".join(diagnostics.supported_seasons) or "None"
    unsupported_lines = [
        f"- `{season}`: {reason}"
        for season, reason in sorted(diagnostics.unsupported_season_reasons.items())
    ]
    if not unsupported_lines:
        unsupported_lines = ["- None"]
    output_path.write_text(
        "\n".join(
            [
                "# Team-Strength Feature Report",
                "",
                "## Identifier Mapping Diagnostics",
                "",
                "| diagnostic | value |",
                "| --- | ---: |",
                (
                    "| rows with valid normalized team IDs | "
                    f"{diagnostics.valid_team_id_rate:.1%} |"
                ),
                (
                    "| rows with valid normalized opponent IDs | "
                    f"{diagnostics.valid_opponent_id_rate:.1%} |"
                ),
                "",
                f"Seasons where mapping works: {supported}",
                "",
                "Seasons where mapping fails:",
                "",
                *unsupported_lines,
                "",
                "## Features Added",
                "",
                "- `team_elo_pre_gw`",
                "- `opponent_elo_pre_gw`",
                "- `elo_difference`",
                "- `home_adjusted_elo_difference`",
                "- `team_goals_scored_mean_last_5`",
                "- `team_goals_conceded_mean_last_5`",
                "- `opponent_goals_scored_mean_last_5`",
                "- `opponent_goals_conceded_mean_last_5`",
                "- `team_clean_sheet_rate_last_5`",
                "- `opponent_clean_sheet_rate_last_5`",
                "",
                "Raw `team` and `opponent_team` are used only as source columns for "
                "normalized identifiers and are not model features.",
                "",
                "## Rolling Team Form",
                "",
                "Rolling team attack and defence features are shifted by team-season "
                "gameweek, so GW t uses only gameweeks before GW t. Seasons without "
                "reliable normalized team/opponent IDs are left missing.",
                "",
                "## Elo Initialization",
                "",
                "- `base_elo = 1500`",
                "- `k_factor = 20`",
                "- `home_advantage = 50`",
                "- Optional manual priors are read from `data/manual/team_season_priors.csv` "
                "when present.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "None."
    headers = list(frame.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in frame.iterrows():
        values = []
        for value in row:
            if isinstance(value, float):
                values.append(f"{value:.2f}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def candidate_feature_coverage(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    candidate_columns = [
        column for column in expected_candidate_feature_columns() if column in frame.columns
    ]
    for column in candidate_columns:
        coverage_by_season = (
            frame.groupby(frame["season"].astype(str))[column]
            .apply(lambda series: round(float(series.notna().mean() * 100), 2))
            .to_dict()
        )
        rows.append(
            {
                "feature": column,
                "non_missing_pct": round(float(frame[column].notna().mean() * 100), 2),
                "missing_pct": round(float(frame[column].isna().mean() * 100), 2),
                "high_missingness": frame[column].isna().mean() >= 0.75,
                "coverage_by_season": coverage_by_season,
            }
        )
    return pd.DataFrame(rows)


def write_candidate_feature_report(
    source: pd.DataFrame,
    dataset: pd.DataFrame,
    output_path: Path = DEFAULT_CANDIDATE_FEATURE_REPORT_PATH,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    coverage = candidate_feature_coverage(dataset)
    skipped = pd.DataFrame(
        [
            {"source": source_column, "reason": reason}
            for source_column, reason in skipped_candidate_sources(source).items()
        ]
    )
    high_missing = (
        coverage.loc[coverage["high_missingness"], ["feature", "missing_pct"]]
        if not coverage.empty
        else pd.DataFrame(columns=["feature", "missing_pct"])
    )
    recommended = coverage.loc[
        ~coverage["high_missingness"],
        ["feature", "non_missing_pct", "missing_pct"],
    ]
    excluded = pd.DataFrame(
        [
            {
                "feature": column,
                "reason": "raw source remains excluded; use candidate lagged/rolling feature only",
            }
            for column in (
                "goals_scored",
                "assists",
                "clean_sheets",
                "goals_conceded",
                "influence",
                "creativity",
                "threat",
                "ict_index",
                "expected_goals",
                "expected_assists",
                "expected_goal_involvements",
                "expected_goals_conceded",
                "selected",
                "transfers_in",
                "transfers_out",
                "transfers_balance",
            )
            if column in source.columns
        ]
    )
    lines = [
        "# Candidate Feature Report",
        "",
        "Candidate features are created in the processed dataset but are not added to "
        "the stable model feature list yet.",
        "",
        "## Candidate Features Created",
        "",
        markdown_table(coverage[["feature", "non_missing_pct", "missing_pct", "high_missingness"]]),
        "",
        "## Coverage By Season",
        "",
        markdown_table(coverage[["feature", "coverage_by_season"]]),
        "",
        "## Candidate Features Skipped",
        "",
        markdown_table(skipped),
        "",
        "## High-Missingness Candidate Features",
        "",
        markdown_table(high_missing),
        "",
        "## Recommended For Ablation",
        "",
        markdown_table(recommended),
        "",
        "## Features That Should Still Be Excluded Directly",
        "",
        markdown_table(excluded),
        "",
        "## Notes",
        "",
        "- Rolling candidate features are shifted within player-season before averaging.",
        "- Ownership and transfer candidates use lag-1 values only because current-GW timing is not assumed safe.",
        "- `was_home` is retained as a direct fixture candidate because it is known before the gameweek.",
        "- Raw `team` and `opponent_team` remain internal metadata and are not candidate model features.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def dataset_summary(frame: pd.DataFrame, *, target_horizon: int) -> str:
    horizon_column = f"next_{target_horizon}_gw_points"
    seasons = sorted(frame["season"].dropna().astype(str).unique())
    target_columns = ["next_gw_points", horizon_column]
    missing_targets = {
        column: int(frame[column].isna().sum())
        for column in target_columns
        if column in frame.columns
    }
    position_filter = frame.attrs.get(POSITION_FILTER_DIAGNOSTICS_ATTR, {})
    position_lines = []
    if position_filter:
        labels_removed = position_filter.get("labels_removed", {})
        seasons_affected = position_filter.get("seasons_affected", [])
        position_lines = [
            f"Rows removed for unsupported positions: {position_filter.get('rows_removed', 0)}",
            f"Unsupported position labels removed: {labels_removed}",
            f"Position-filter seasons affected: {seasons_affected}",
        ]
    return "\n".join(
        [
            f"Rows: {len(frame)}",
            f"Columns: {len(frame.columns)}",
            f"Seasons: {len(seasons)} ({', '.join(seasons)})",
            f"Missing targets: {missing_targets}",
            *position_lines,
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--team-priors", type=Path, default=DEFAULT_TEAM_PRIORS_PATH)
    parser.add_argument("--target-horizon", type=int, default=3)
    parser.add_argument(
        "--fail-on-missing-required-columns",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fail before building if required columns are missing. Enabled by default.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = read_dataset(args.input)
    modeling_dataset = build_modeling_dataset(
        source,
        target_horizon=args.target_horizon,
        fail_on_missing_required_columns=args.fail_on_missing_required_columns,
        team_priors_path=args.team_priors,
    )
    write_dataset(modeling_dataset, args.output)
    write_team_strength_report(source, DEFAULT_TEAM_STRENGTH_REPORT_PATH)
    write_candidate_feature_report(source, modeling_dataset)
    print(dataset_summary(modeling_dataset, target_horizon=args.target_horizon))
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
