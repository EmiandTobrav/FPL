"""Lightweight position-specific statistical feature relevance audit."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

from evaluation.backtest import (
    POSITION_COLUMN,
    RAW_CURRENT_GW_OUTCOME_COLUMNS,
    RAW_TEAM_COLUMNS,
    STABLE_FEATURE_COLUMNS,
    TARGET_COLUMN,
    add_baseline_prediction_features,
    feature_selection_candidate_columns,
    markdown_table,
    normalize_position_column,
)


DEFAULT_INPUT_PATH = Path("data/processed/modeling_dataset.parquet")
DEFAULT_CSV_PATH = Path("reports/position_feature_relevance.csv")
DEFAULT_MARKDOWN_PATH = Path("reports/position_feature_relevance.md")
POSITIONS = ("GK", "DEF", "MID", "FWD")
MAX_MI_ROWS = 10_000
MIN_CORRELATION_ROWS = 20
MIN_REGRESSION_TRAIN_ROWS = 30
MIN_REGRESSION_VALIDATION_ROWS = 10
USEFUL_ABS_SPEARMAN_THRESHOLD = 0.03
HIGH_MISSING_THRESHOLD = 0.50

IDENTIFIER_COLUMNS = {
    "name",
    "element",
    "id",
    "fixture",
    "kickoff_time",
    "kickoff_time_formatted",
    "modified",
    "round",
    "GW",
    "season",
    "gw",
    "team_id_normalized",
    "opponent_team_id_normalized",
    "team_name_normalized",
    "opponent_team_name_normalized",
}
TARGET_COLUMNS = {TARGET_COLUMN, "next_3_gw_points"}
EXCLUDED_COLUMNS = {
    *RAW_CURRENT_GW_OUTCOME_COLUMNS,
    *RAW_TEAM_COLUMNS,
    *IDENTIFIER_COLUMNS,
    *TARGET_COLUMNS,
    POSITION_COLUMN,
}


def read_dataset(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def prepare_frame(frame: pd.DataFrame) -> pd.DataFrame:
    data = normalize_position_column(frame)
    return add_baseline_prediction_features(data)


def candidate_feature_columns(frame: pd.DataFrame) -> tuple[str, ...]:
    """Return the current leakage-safe numeric/bool candidate feature pool."""
    prepared = prepare_frame(frame)
    configured = [*STABLE_FEATURE_COLUMNS, *feature_selection_candidate_columns(prepared)]
    seen: set[str] = set()
    candidates: list[str] = []
    for column in configured:
        if column in seen or column in EXCLUDED_COLUMNS or column not in prepared.columns:
            continue
        seen.add(column)
        if pd.api.types.is_numeric_dtype(prepared[column]) or pd.api.types.is_bool_dtype(
            prepared[column]
        ):
            candidates.append(column)
    return tuple(candidates)


def _safe_correlation(x: pd.Series, y: pd.Series, *, method: str) -> float:
    pair = pd.concat([x, y], axis=1).dropna()
    if (
        len(pair) < MIN_CORRELATION_ROWS
        or pair.iloc[:, 0].nunique(dropna=True) < 2
        or pair.iloc[:, 1].nunique(dropna=True) < 2
    ):
        return float("nan")
    return float(pair.iloc[:, 0].corr(pair.iloc[:, 1], method=method))


def _safe_mutual_information(x: pd.Series, y: pd.Series, *, random_state: int) -> float:
    pair = pd.concat([x, y], axis=1).dropna()
    if (
        len(pair) < MIN_CORRELATION_ROWS
        or pair.iloc[:, 0].nunique(dropna=True) < 2
        or pair.iloc[:, 1].nunique(dropna=True) < 2
    ):
        return float("nan")
    if len(pair) > MAX_MI_ROWS:
        pair = pair.sample(n=MAX_MI_ROWS, random_state=random_state)
    x_values = pair.iloc[:, [0]].astype(float)
    y_values = pair.iloc[:, 1].astype(float)
    return float(mutual_info_regression(x_values, y_values, random_state=random_state)[0])


def _single_feature_validation_rows(
    position_frame: pd.DataFrame,
    feature: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seasons = sorted(position_frame["season"].dropna().astype(str).unique())
    for validation_season in seasons[1:]:
        train = position_frame.loc[position_frame["season"].astype(str) < validation_season]
        validation = position_frame.loc[position_frame["season"].astype(str) == validation_season]
        train = train.dropna(subset=[feature, TARGET_COLUMN])
        validation = validation.dropna(subset=[feature, TARGET_COLUMN])
        if len(train) < MIN_REGRESSION_TRAIN_ROWS or len(validation) < MIN_REGRESSION_VALIDATION_ROWS:
            continue

        baseline_prediction = np.repeat(float(train[TARGET_COLUMN].mean()), len(validation))
        baseline_mae = mean_absolute_error(validation[TARGET_COLUMN], baseline_prediction)

        model = LinearRegression()
        model.fit(train[[feature]].astype(float), train[TARGET_COLUMN].astype(float))
        prediction = model.predict(validation[[feature]].astype(float))
        model_mae = mean_absolute_error(validation[TARGET_COLUMN], prediction)
        spearman = _safe_correlation(validation[feature], validation[TARGET_COLUMN], method="spearman")
        rows.append(
            {
                "validation_season": validation_season,
                "single_feature_mae": float(model_mae),
                "baseline_mae": float(baseline_mae),
                "mae_delta_vs_baseline": float(model_mae - baseline_mae),
                "season_spearman": spearman,
                "season_abs_spearman_rank": np.nan,
                "season_useful": bool(
                    pd.notna(spearman)
                    and abs(float(spearman)) >= USEFUL_ABS_SPEARMAN_THRESHOLD
                    and model_mae <= baseline_mae
                ),
            }
        )
    return rows


def _season_rank_lookup(position_frame: pd.DataFrame, features: tuple[str, ...]) -> dict[tuple[str, str], float]:
    ranks: dict[tuple[str, str], float] = {}
    for season, season_frame in position_frame.groupby("season", sort=True):
        values = []
        for feature in features:
            spearman = _safe_correlation(season_frame[feature], season_frame[TARGET_COLUMN], method="spearman")
            values.append({"feature": feature, "abs_spearman": abs(spearman) if pd.notna(spearman) else np.nan})
        rank_frame = pd.DataFrame(values).dropna(subset=["abs_spearman"])
        if rank_frame.empty:
            continue
        rank_frame["rank"] = rank_frame["abs_spearman"].rank(method="min", ascending=False)
        for row in rank_frame.itertuples(index=False):
            ranks[(str(season), str(row.feature))] = float(row.rank)
    return ranks


def build_relevance_table(
    frame: pd.DataFrame,
    *,
    random_state: int = 42,
) -> pd.DataFrame:
    data = prepare_frame(frame)
    features = candidate_feature_columns(frame)
    data = data.dropna(subset=[TARGET_COLUMN, POSITION_COLUMN]).copy()
    data["season"] = data["season"].astype(str)

    rows: list[dict[str, Any]] = []
    for position in POSITIONS:
        position_frame = data.loc[data[POSITION_COLUMN].astype(str) == position].copy()
        if position_frame.empty:
            continue
        season_ranks = _season_rank_lookup(position_frame, features)
        for feature in features:
            validation_rows = _single_feature_validation_rows(position_frame, feature)
            season_spearman_values = [
                row["season_spearman"]
                for row in validation_rows
                if pd.notna(row["season_spearman"])
            ]
            non_missing_pct = float(position_frame[feature].notna().mean())
            spearman = _safe_correlation(
                position_frame[feature],
                position_frame[TARGET_COLUMN],
                method="spearman",
            )
            pearson = _safe_correlation(
                position_frame[feature],
                position_frame[TARGET_COLUMN],
                method="pearson",
            )
            mutual_information = _safe_mutual_information(
                position_frame[feature],
                position_frame[TARGET_COLUMN],
                random_state=random_state,
            )
            useful_seasons = sum(bool(row["season_useful"]) for row in validation_rows)
            validation_seasons = len(validation_rows)
            ranks = [
                season_ranks[(row["validation_season"], feature)]
                for row in validation_rows
                if (row["validation_season"], feature) in season_ranks
            ]
            signs = {np.sign(value) for value in season_spearman_values if value != 0}
            rows.append(
                {
                    "position": position,
                    "feature": feature,
                    "non_missing_pct": non_missing_pct,
                    "spearman": spearman,
                    "pearson": pearson,
                    "mutual_information": mutual_information,
                    "single_feature_mae": np.nanmean(
                        [row["single_feature_mae"] for row in validation_rows]
                    )
                    if validation_rows
                    else np.nan,
                    "baseline_mae": np.nanmean([row["baseline_mae"] for row in validation_rows])
                    if validation_rows
                    else np.nan,
                    "mae_delta_vs_baseline": np.nanmean(
                        [row["mae_delta_vs_baseline"] for row in validation_rows]
                    )
                    if validation_rows
                    else np.nan,
                    "validation_seasons": validation_seasons,
                    "useful_seasons": useful_seasons,
                    "useful_in_at_least_2_of_3": useful_seasons >= 2,
                    "mean_abs_spearman_rank": float(np.nanmean(ranks)) if ranks else np.nan,
                    "stable_sign": len(signs) <= 1 and bool(signs),
                    "unstable_sign": len(signs) > 1,
                    "high_missingness": non_missing_pct < (1 - HIGH_MISSING_THRESHOLD),
                }
            )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["relevance_score"] = (
        result["spearman"].abs().fillna(0)
        + result["pearson"].abs().fillna(0)
        + result["mutual_information"].fillna(0)
        + result["useful_seasons"].fillna(0) * 0.05
        - result["mae_delta_vs_baseline"].fillna(0).clip(lower=0)
    )
    return result.sort_values(["position", "relevance_score"], ascending=[True, False])


def write_relevance_csv(relevance: pd.DataFrame, path: Path = DEFAULT_CSV_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    relevance.to_csv(path, index=False)


def _top_features(relevance: pd.DataFrame, position: str, n: int = 12) -> pd.DataFrame:
    rows = relevance.loc[relevance["position"].eq(position)].sort_values(
        ["relevance_score", "non_missing_pct"],
        ascending=[False, False],
    )
    return rows.head(n)[
        [
            "feature",
            "non_missing_pct",
            "spearman",
            "pearson",
            "mutual_information",
            "mae_delta_vs_baseline",
            "useful_seasons",
            "stable_sign",
        ]
    ]


def _irrelevant_features(relevance: pd.DataFrame, position: str, n: int = 12) -> pd.DataFrame:
    rows = relevance.loc[
        relevance["position"].eq(position)
        & relevance["spearman"].abs().fillna(0).lt(USEFUL_ABS_SPEARMAN_THRESHOLD)
        & relevance["pearson"].abs().fillna(0).lt(USEFUL_ABS_SPEARMAN_THRESHOLD)
        & relevance["useful_seasons"].eq(0)
    ].sort_values(["non_missing_pct", "feature"], ascending=[False, True])
    return rows.head(n)[["feature", "non_missing_pct", "spearman", "pearson", "useful_seasons"]]


def _suggested_mask(relevance: pd.DataFrame, position: str) -> list[str]:
    rows = relevance.loc[
        relevance["position"].eq(position)
        & relevance["high_missingness"].eq(False)
        & (
            relevance["useful_in_at_least_2_of_3"].eq(True)
            | relevance["spearman"].abs().ge(0.05)
            | relevance["mutual_information"].ge(0.01)
        )
    ].sort_values(["relevance_score", "non_missing_pct"], ascending=[False, False])
    return list(rows.head(20)["feature"])


def write_markdown_report(
    relevance: pd.DataFrame,
    path: Path = DEFAULT_MARKDOWN_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Position Feature Relevance",
        "",
        "Lightweight statistical audit of leakage-safe candidate features on the current "
        "trimmed rich-feature modelling dataset. This does not change model logic and does "
        "not run wrapper feature selection or broad ablation.",
        "",
        f"Candidate features audited: {relevance['feature'].nunique() if not relevance.empty else 0}",
        "",
    ]
    for position in POSITIONS:
        position_rows = relevance.loc[relevance["position"].eq(position)]
        lines.extend([f"## {position}", "", "### Top Features", ""])
        lines.append(markdown_table(_top_features(relevance, position)) if not position_rows.empty else "No rows.")
        lines.extend(["", "### Appears Irrelevant", ""])
        irrelevant = _irrelevant_features(relevance, position)
        lines.append(markdown_table(irrelevant) if not irrelevant.empty else "No clearly irrelevant features.")
        unstable = position_rows.loc[position_rows["unstable_sign"].eq(True)][
            ["feature", "spearman", "useful_seasons", "mean_abs_spearman_rank"]
        ].head(15)
        lines.extend(["", "### Unstable Sign Across Seasons", ""])
        lines.append(markdown_table(unstable) if not unstable.empty else "No unstable signs among evaluated features.")
        missing = position_rows.loc[position_rows["high_missingness"].eq(True)][
            ["feature", "non_missing_pct", "spearman", "mutual_information"]
        ].sort_values(["non_missing_pct", "feature"]).head(15)
        lines.extend(["", "### High Missingness", ""])
        lines.append(markdown_table(missing) if not missing.empty else "No features exceeded the missingness threshold.")
        mask = _suggested_mask(relevance, position)
        lines.extend(["", "### Suggested Statistical Mask", ""])
        lines.extend([f"- `{feature}`" for feature in mask] if mask else ["No mask suggested."])
        lines.append("")

    mask_sizes = pd.DataFrame(
        [{"position": position, "suggested_feature_count": len(_suggested_mask(relevance, position))} for position in POSITIONS]
    )
    lines.extend(
        [
            "## Recommended Next Test",
            "",
            markdown_table(mask_sizes),
            "",
            "Test these masks as a separate modelling experiment, starting with the position-specific "
            "masks for GK and FWD where role-specific signal is usually most distinct. Keep the "
            "current global feature set as the control and continue using rolling-origin validation.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_MARKDOWN_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    relevance = build_relevance_table(read_dataset(args.input))
    write_relevance_csv(relevance, args.csv)
    write_markdown_report(relevance, args.report)
    print(f"Wrote: {args.csv}")
    print(f"Wrote: {args.report}")


if __name__ == "__main__":
    main()
