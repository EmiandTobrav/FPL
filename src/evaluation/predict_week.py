"""Generate weekly FPL predictions from completed rows and upcoming fixture rows."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from features.rolling_features import build_rolling_features
from models.baseline import (
    ColumnBaseline,
    MinutesAdjustedRollingMeanBaseline,
)


DEFAULT_HISTORICAL_PATH = Path("data/processed/modeling_dataset.parquet")
DEFAULT_FPL_API_ROOT = Path("data/interim/fpl_api")
DEFAULT_OUTPUT_PATH = Path("data/predictions/latest_predictions.csv")
DEFAULT_REPORT_PATH = Path("reports/weekly_prediction_report.md")
PREDICTION_FILE_PATTERN = "prediction_rows_gw*.parquet"
PREDICTION_FILE_RE = re.compile(r"prediction_rows_gw(?P<gw>\d+)\.parquet$")
ROLLING_3 = ColumnBaseline("rolling_3_gameweek_mean_prediction", "points_mean_last_3")
ROLLING_5 = ColumnBaseline("rolling_5_gameweek_mean_prediction", "points_mean_last_5")
MINUTES_ADJUSTED = MinutesAdjustedRollingMeanBaseline()
OUTPUT_COLUMNS = (
    "prediction_level",
    "season",
    "gw",
    "element",
    "name",
    "team",
    "position",
    "value",
    "fixture",
    "fixture_count",
    "expected_points_primary",
    "rolling_3_gameweek_mean_prediction",
    "rolling_5_gameweek_mean_prediction",
)
ROLLING_REQUIRED_COLUMNS = ("season", "gw", "element", "total_points", "minutes", "bonus", "bps")


class WeeklyPredictionError(ValueError):
    """Raised when weekly prediction rows cannot be generated."""


@dataclass(frozen=True)
class WeeklyPredictionSummary:
    season: str
    gw: int
    prediction_rows_path: Path
    output_path: Path
    fixture_rows: int
    aggregated_rows: int
    blank_report_available: bool


def read_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise WeeklyPredictionError(f"Input file does not exist: {path}")
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise WeeklyPredictionError(f"Unsupported input format: {path}")


def prediction_rows_path(
    *,
    season: str,
    gw: int,
    fpl_api_root: Path = DEFAULT_FPL_API_ROOT,
) -> Path:
    return fpl_api_root / season / f"prediction_rows_gw{gw}.parquet"


def _gw_from_prediction_path(path: Path) -> int | None:
    match = PREDICTION_FILE_RE.match(path.name)
    return int(match.group("gw")) if match else None


def find_latest_prediction_rows(fpl_api_root: Path = DEFAULT_FPL_API_ROOT) -> Path:
    candidates = []
    for path in fpl_api_root.glob(f"*/{PREDICTION_FILE_PATTERN}"):
        gw = _gw_from_prediction_path(path)
        if gw is None:
            continue
        candidates.append((path.parent.name, gw, path))
    if not candidates:
        raise WeeklyPredictionError(f"No prediction rows found under {fpl_api_root}")
    return sorted(candidates, key=lambda item: (item[0], item[1]))[-1][2]


def prediction_identity(prediction_rows: pd.DataFrame) -> tuple[str, int]:
    missing = [column for column in ("season", "gw") if column not in prediction_rows.columns]
    if missing:
        raise WeeklyPredictionError(f"Prediction rows missing required columns: {missing}")
    seasons = sorted(prediction_rows["season"].dropna().astype(str).unique())
    gameweeks = sorted(pd.to_numeric(prediction_rows["gw"], errors="coerce").dropna().astype(int).unique())
    if len(seasons) != 1 or len(gameweeks) != 1:
        raise WeeklyPredictionError("Prediction rows must contain exactly one season and one gameweek.")
    return seasons[0], gameweeks[0]


def _ensure_rolling_columns(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    for column in ROLLING_REQUIRED_COLUMNS:
        if column not in data.columns:
            data[column] = pd.NA
    return data


def prediction_feature_skeleton(prediction_rows: pd.DataFrame) -> pd.DataFrame:
    key_columns = ["element", "season", "gw"]
    missing = [column for column in key_columns if column not in prediction_rows.columns]
    if missing:
        raise WeeklyPredictionError(f"Prediction rows missing required columns: {missing}")
    return prediction_rows.sort_values(key_columns).drop_duplicates(key_columns).copy()


def build_prediction_features(historical: pd.DataFrame, prediction_rows: pd.DataFrame) -> pd.DataFrame:
    """Build leakage-safe rolling features for one prediction row per player-GW."""
    historical_completed = historical.loc[historical["total_points"].notna()].copy()
    skeleton = prediction_feature_skeleton(prediction_rows)
    combined = pd.concat(
        [_ensure_rolling_columns(historical_completed), _ensure_rolling_columns(skeleton)],
        ignore_index=True,
        sort=False,
    )
    featured = build_rolling_features(combined)
    keys = ["element", "season", "gw"]
    wanted = skeleton[keys].drop_duplicates()
    return wanted.merge(featured, on=keys, how="left", suffixes=("", "_featured"))


def add_baseline_predictions(featured_prediction_rows: pd.DataFrame) -> pd.DataFrame:
    data = featured_prediction_rows.copy()
    data["rolling_3_gameweek_mean_prediction"] = ROLLING_3.predict(data)
    data["rolling_5_gameweek_mean_prediction"] = ROLLING_5.predict(data)
    data["expected_points_primary"] = MINUTES_ADJUSTED.predict(data)
    return data


def fixture_level_predictions(
    prediction_rows: pd.DataFrame,
    prediction_features: pd.DataFrame,
) -> pd.DataFrame:
    keys = ["element", "season", "gw"]
    prediction_columns = [
        *keys,
        "expected_points_primary",
        "rolling_3_gameweek_mean_prediction",
        "rolling_5_gameweek_mean_prediction",
    ]
    fixture_rows = prediction_rows.merge(
        prediction_features[prediction_columns],
        on=keys,
        how="left",
    )
    fixture_counts = fixture_rows.groupby(keys, dropna=False).size().rename("fixture_count")
    fixture_rows = fixture_rows.merge(fixture_counts.reset_index(), on=keys, how="left")
    fixture_rows["prediction_level"] = "fixture"
    for column in OUTPUT_COLUMNS:
        if column not in fixture_rows.columns:
            fixture_rows[column] = pd.NA
    return fixture_rows[[*OUTPUT_COLUMNS, *[c for c in fixture_rows.columns if c not in OUTPUT_COLUMNS]]]


def aggregate_player_gameweek_predictions(fixture_predictions: pd.DataFrame) -> pd.DataFrame:
    group_columns = ["season", "gw", "element"]
    metadata_columns = ["name", "team", "position", "value"]
    agg_spec = {
        **{column: "first" for column in metadata_columns if column in fixture_predictions.columns},
        "fixture_count": "max",
        "expected_points_primary": "sum",
        "rolling_3_gameweek_mean_prediction": "sum",
        "rolling_5_gameweek_mean_prediction": "sum",
    }
    aggregated = fixture_predictions.groupby(group_columns, dropna=False).agg(agg_spec).reset_index()
    aggregated["fixture"] = pd.NA
    aggregated["prediction_level"] = "player_gw"
    for column in OUTPUT_COLUMNS:
        if column not in aggregated.columns:
            aggregated[column] = pd.NA
    return aggregated[list(OUTPUT_COLUMNS)]


def generate_weekly_predictions(
    *,
    historical: pd.DataFrame,
    prediction_rows: pd.DataFrame,
    prediction_rows_path: Path,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> tuple[pd.DataFrame, WeeklyPredictionSummary]:
    season, gw = prediction_identity(prediction_rows)
    prediction_features = add_baseline_predictions(build_prediction_features(historical, prediction_rows))
    fixture_predictions = fixture_level_predictions(prediction_rows, prediction_features)
    aggregated = aggregate_player_gameweek_predictions(fixture_predictions)
    output = pd.concat([fixture_predictions[list(OUTPUT_COLUMNS)], aggregated], ignore_index=True)
    output = output.sort_values(
        ["prediction_level", "expected_points_primary", "team", "element"],
        ascending=[True, False, True, True],
        na_position="last",
    ).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_path, index=False)
    summary = WeeklyPredictionSummary(
        season=season,
        gw=gw,
        prediction_rows_path=prediction_rows_path,
        output_path=output_path,
        fixture_rows=int(fixture_predictions.shape[0]),
        aggregated_rows=int(aggregated.shape[0]),
        blank_report_available=DEFAULT_REPORT_PATH.exists(),
    )
    return output, summary


def write_weekly_prediction_report(
    summary: WeeklyPredictionSummary,
    *,
    output_path: Path = DEFAULT_REPORT_PATH,
    prediction_row_report_path: Path = Path("reports/prediction_row_builder_report.md"),
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    blank_note = "No prediction-row report was found."
    if prediction_row_report_path.exists():
        blank_note = (
            f"Blank team/player diagnostics are available in "
            f"`{prediction_row_report_path.as_posix()}`."
        )
    output_path.write_text(
        "\n".join(
            [
                "# Weekly Prediction Report",
                "",
                f"Season: `{summary.season}`",
                f"GW: `{summary.gw}`",
                f"Prediction rows: `{summary.prediction_rows_path.as_posix()}`",
                f"Output: `{summary.output_path.as_posix()}`",
                "",
                "| level | rows |",
                "| --- | ---: |",
                f"| fixture | {summary.fixture_rows} |",
                f"| player_gw | {summary.aggregated_rows} |",
                "",
                "Model: `minutes_adjusted_rolling_mean` only.",
                "",
                "Prediction rows are combined with completed historical rows only for leakage-safe "
                "rolling feature calculation. Outcome and target columns remain missing for the "
                "upcoming rows.",
                "",
                blank_note,
                "",
            ]
        ),
        encoding="utf-8",
    )


def predict_from_files(
    *,
    historical_path: Path = DEFAULT_HISTORICAL_PATH,
    prediction_rows: Path | None = None,
    season: str | None = None,
    gw: int | None = None,
    fpl_api_root: Path = DEFAULT_FPL_API_ROOT,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
) -> tuple[pd.DataFrame, WeeklyPredictionSummary]:
    if prediction_rows is None:
        if season is not None and gw is not None:
            prediction_rows = prediction_rows_path(season=season, gw=gw, fpl_api_root=fpl_api_root)
        else:
            prediction_rows = find_latest_prediction_rows(fpl_api_root)
    historical = read_table(historical_path)
    upcoming = read_table(prediction_rows)
    output, summary = generate_weekly_predictions(
        historical=historical,
        prediction_rows=upcoming,
        prediction_rows_path=prediction_rows,
        output_path=output_path,
    )
    write_weekly_prediction_report(summary, output_path=report_path)
    return output, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical", type=Path, default=DEFAULT_HISTORICAL_PATH)
    parser.add_argument("--prediction-rows", type=Path, default=None)
    parser.add_argument("--season", default=None)
    parser.add_argument("--gw", type=int, default=None)
    parser.add_argument("--fpl-api-root", type=Path, default=DEFAULT_FPL_API_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _, summary = predict_from_files(
        historical_path=args.historical,
        prediction_rows=args.prediction_rows,
        season=args.season,
        gw=args.gw,
        fpl_api_root=args.fpl_api_root,
        output_path=args.output,
        report_path=args.report,
    )
    print(f"Season: {summary.season}")
    print(f"GW: {summary.gw}")
    print(f"Fixture rows: {summary.fixture_rows}")
    print(f"Aggregated rows: {summary.aggregated_rows}")
    print(f"Wrote: {summary.output_path}")
    print(f"Wrote report: {args.report}")


if __name__ == "__main__":
    main()
