"""Build the processed FPL modeling dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from features.rolling_features import (
    FeatureBuildError,
    build_rolling_features,
    player_key_column,
)
from features.target_builder import build_targets


DEFAULT_INPUT_PATH = Path("data/interim/all_merged_gw.parquet")
DEFAULT_OUTPUT_PATH = Path("data/processed/modeling_dataset.parquet")
REQUIRED_COLUMNS = ("season", "gw", "total_points", "minutes")


class DatasetBuildError(ValueError):
    """Raised when the processed modeling dataset cannot be built."""


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
) -> pd.DataFrame:
    """Apply leakage-safe rolling features and future point targets."""
    missing = validate_required_columns(
        frame,
        fail_on_missing_required_columns=fail_on_missing_required_columns,
    )
    if missing:
        raise DatasetBuildError(f"Cannot build dataset with missing required columns: {missing}")

    features = build_rolling_features(frame)
    return build_targets(features, target_horizon=target_horizon)


def write_dataset(frame: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output_path, index=False)


def dataset_summary(frame: pd.DataFrame, *, target_horizon: int) -> str:
    horizon_column = f"next_{target_horizon}_gw_points"
    seasons = sorted(frame["season"].dropna().astype(str).unique())
    target_columns = ["next_gw_points", horizon_column]
    missing_targets = {
        column: int(frame[column].isna().sum())
        for column in target_columns
        if column in frame.columns
    }
    return "\n".join(
        [
            f"Rows: {len(frame)}",
            f"Columns: {len(frame.columns)}",
            f"Seasons: {len(seasons)} ({', '.join(seasons)})",
            f"Missing targets: {missing_targets}",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
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
    )
    write_dataset(modeling_dataset, args.output)
    print(dataset_summary(modeling_dataset, target_horizon=args.target_horizon))
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
