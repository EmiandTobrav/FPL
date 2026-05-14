"""Combine Vaastav historical rows with FPL API rows at a season boundary."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_VAASTAV_INPUT = Path("data/interim/all_merged_gw.parquet")
DEFAULT_FPL_API_ROOT = Path("data/interim/fpl_api")
DEFAULT_OUTPUT_PATH = Path("data/interim/combined_merged_gw.parquet")
DEFAULT_REPORT_PATH = Path("reports/combined_merged_gw_report.md")
DEFAULT_BOUNDARY_SEASON = "2025-26"
REQUIRED_COLUMNS = (
    "season",
    "gw",
    "element",
    "name",
    "team",
    "opponent_team",
    "was_home",
    "position",
    "total_points",
    "minutes",
    "bonus",
    "bps",
)
NUMERIC_COLUMNS = (
    "gw",
    "GW",
    "element",
    "fixture",
    "opponent_team",
    "round",
    "creativity",
    "influence",
    "threat",
    "ict_index",
    "expected_goals",
    "expected_assists",
    "expected_goal_involvements",
    "expected_goals_conceded",
    "total_points",
    "minutes",
    "starts",
    "bonus",
    "bps",
    "selected",
    "transfers_in",
    "transfers_out",
    "transfers_balance",
    "value",
    "now_cost",
    "assists",
    "clean_sheets",
    "goals_conceded",
    "goals_scored",
    "own_goals",
    "penalties_missed",
    "penalties_saved",
    "red_cards",
    "saves",
    "team_a_score",
    "team_h_score",
    "yellow_cards",
)
BOOLEAN_COLUMNS = ("was_home",)
STRING_COLUMNS = ("season", "name", "team", "position")
KEY_DTYPE_COLUMNS = (*STRING_COLUMNS, *BOOLEAN_COLUMNS, *NUMERIC_COLUMNS)


class SeasonCombinerError(ValueError):
    """Raised when season-boundary combining cannot be completed."""


@dataclass(frozen=True)
class CombineDiagnostics:
    seasons_by_source: pd.DataFrame
    row_counts: pd.DataFrame
    required_column_coverage: pd.DataFrame
    dropped_vaastav_rows: int
    dropped_vaastav_seasons: tuple[str, ...]
    skipped_fpl_api_seasons: tuple[str, ...]
    numeric_coercions: pd.DataFrame
    final_key_dtypes: pd.DataFrame


def read_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SeasonCombinerError(f"Input parquet does not exist: {path}")
    return pd.read_parquet(path)


def load_fpl_api_season_files(fpl_api_root: Path) -> dict[str, pd.DataFrame]:
    """Load available FPL API Vaastav-style season files."""
    if not fpl_api_root.exists():
        return {}
    frames: dict[str, pd.DataFrame] = {}
    for path in sorted(fpl_api_root.glob("*/merged_gw_api.parquet")):
        season = path.parent.name
        frame = pd.read_parquet(path)
        if "season" not in frame.columns:
            frame = frame.copy()
            frame["season"] = season
        frames[season] = frame
    return frames


def _row_counts(source_name: str, frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["source", "season", "rows"])
    counts = frame.groupby(frame["season"].astype(str), dropna=False).size().reset_index(name="rows")
    counts.insert(0, "source", source_name)
    return counts.rename(columns={"season": "season"})


def required_column_coverage(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in REQUIRED_COLUMNS:
        if column in frame.columns:
            non_missing = int(frame[column].notna().sum())
            coverage = round(float(frame[column].notna().mean() * 100), 2) if len(frame) else 0.0
        else:
            non_missing = 0
            coverage = 0.0
        rows.append(
            {
                "column": column,
                "present": column in frame.columns,
                "non_missing_rows": non_missing,
                "coverage_pct": coverage,
            }
        )
    return pd.DataFrame(rows)


def align_columns(frames: list[pd.DataFrame]) -> list[pd.DataFrame]:
    columns = sorted(set().union(*(set(frame.columns) for frame in frames)))
    return [frame.reindex(columns=columns) for frame in frames]


def _coerce_nullable_boolean(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype("boolean")
    normalized = series.astype("string").str.strip().str.lower()
    mapped = normalized.map(
        {
            "true": True,
            "false": False,
            "1": True,
            "0": False,
            "1.0": True,
            "0.0": False,
            "yes": True,
            "no": False,
            "y": True,
            "n": False,
        }
    )
    mapped = mapped.where(series.notna(), pd.NA)
    return mapped.astype("boolean")


def normalize_combined_schema(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Normalize mixed Vaastav/FPL API dtypes before parquet writing."""
    normalized = frame.copy()
    coercion_rows: list[dict[str, object]] = []
    for column in NUMERIC_COLUMNS:
        if column not in normalized.columns:
            continue
        before = normalized[column]
        before_non_missing = int(before.notna().sum())
        coerced = pd.to_numeric(before, errors="coerce")
        invalid_count = int(before.notna().sum() - coerced.notna().sum())
        normalized[column] = coerced
        coercion_rows.append(
            {
                "column": column,
                "non_missing_before": before_non_missing,
                "values_coerced_to_na": invalid_count,
            }
        )

    for column in BOOLEAN_COLUMNS:
        if column in normalized.columns:
            normalized[column] = _coerce_nullable_boolean(normalized[column])

    for column in STRING_COLUMNS:
        if column in normalized.columns:
            normalized[column] = normalized[column].astype("string")

    dtype_rows = [
        {"column": column, "dtype": str(normalized[column].dtype)}
        for column in KEY_DTYPE_COLUMNS
        if column in normalized.columns
    ]
    return normalized, pd.DataFrame(coercion_rows), pd.DataFrame(dtype_rows)


def combine_merged_gw_sources(
    vaastav: pd.DataFrame,
    fpl_api_frames: dict[str, pd.DataFrame],
    *,
    boundary_season: str = DEFAULT_BOUNDARY_SEASON,
) -> tuple[pd.DataFrame, CombineDiagnostics]:
    """Combine Vaastav before boundary with FPL API from boundary onward."""
    if "season" not in vaastav.columns:
        raise SeasonCombinerError("Vaastav input must contain `season`.")
    vaastav_seasons = vaastav["season"].astype(str)
    vaastav_keep = vaastav.loc[vaastav_seasons < boundary_season].copy()
    vaastav_dropped = vaastav.loc[vaastav_seasons >= boundary_season].copy()

    kept_fpl_frames = []
    skipped_fpl_api_seasons = []
    for season, frame in sorted(fpl_api_frames.items()):
        if season < boundary_season:
            skipped_fpl_api_seasons.append(season)
            continue
        data = frame.copy()
        if "season" not in data.columns:
            data["season"] = season
        data["season"] = data["season"].fillna(season)
        kept_fpl_frames.append(data)

    source_frames = [("vaastav", vaastav_keep), *[("fpl_api", frame) for frame in kept_fpl_frames]]
    non_empty_frames = [frame for _, frame in source_frames if not frame.empty]
    if not non_empty_frames:
        raise SeasonCombinerError("No rows available after applying season boundary.")

    combined = pd.concat(align_columns(non_empty_frames), ignore_index=True, sort=False)
    combined, numeric_coercions, final_key_dtypes = normalize_combined_schema(combined)
    sort_columns = [column for column in ("season", "gw", "element", "fixture") if column in combined.columns]
    if sort_columns:
        combined = combined.sort_values(sort_columns, na_position="last").reset_index(drop=True)

    row_count_frames = [_row_counts("vaastav_included", vaastav_keep)]
    if not vaastav_dropped.empty:
        row_count_frames.append(_row_counts("vaastav_dropped", vaastav_dropped))
    for frame in kept_fpl_frames:
        row_count_frames.append(_row_counts("fpl_api_included", frame))
    row_counts = pd.concat(row_count_frames, ignore_index=True, sort=False)

    seasons_by_source = (
        row_counts.loc[row_counts["source"].str.endswith("included"), ["source", "season"]]
        .drop_duplicates()
        .sort_values(["source", "season"])
        .reset_index(drop=True)
    )
    diagnostics = CombineDiagnostics(
        seasons_by_source=seasons_by_source,
        row_counts=row_counts,
        required_column_coverage=required_column_coverage(combined),
        dropped_vaastav_rows=len(vaastav_dropped),
        dropped_vaastav_seasons=tuple(sorted(vaastav_dropped["season"].dropna().astype(str).unique())),
        skipped_fpl_api_seasons=tuple(sorted(skipped_fpl_api_seasons)),
        numeric_coercions=numeric_coercions,
        final_key_dtypes=final_key_dtypes,
    )
    return combined, diagnostics


def write_combined_dataset(frame: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output_path, index=False)


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "None."
    lines = [
        "| " + " | ".join(frame.columns) + " |",
        "| " + " | ".join(["---"] * len(frame.columns)) + " |",
    ]
    for _, row in frame.iterrows():
        values = [str(value).replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_diagnostics_report(
    diagnostics: CombineDiagnostics,
    *,
    output_path: Path = DEFAULT_REPORT_PATH,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(
            [
                "# Combined merged_gw Report",
                "",
                "Vaastav rows are used before the boundary season. FPL API rows are used from "
                f"`{DEFAULT_BOUNDARY_SEASON}` onward. No season is mixed between sources.",
                "",
                f"Dropped Vaastav rows at or after boundary: {diagnostics.dropped_vaastav_rows}",
                f"Dropped Vaastav seasons: {list(diagnostics.dropped_vaastav_seasons)}",
                f"Skipped pre-boundary FPL API seasons: {list(diagnostics.skipped_fpl_api_seasons)}",
                "",
                "## Seasons By Source",
                "",
                _markdown_table(diagnostics.seasons_by_source),
                "",
                "## Row Counts By Source And Season",
                "",
                _markdown_table(diagnostics.row_counts),
                "",
                "## Required Column Coverage",
                "",
                _markdown_table(diagnostics.required_column_coverage),
                "",
                "## Schema Normalization",
                "",
                "Numeric columns are coerced with `pd.to_numeric(errors=\"coerce\")` before parquet writing.",
                "",
                "### Numeric Coercions",
                "",
                _markdown_table(diagnostics.numeric_coercions),
                "",
                "### Final Key Dtypes",
                "",
                _markdown_table(diagnostics.final_key_dtypes),
                "",
            ]
        ),
        encoding="utf-8",
    )


def combine_from_paths(
    *,
    vaastav_input: Path = DEFAULT_VAASTAV_INPUT,
    fpl_api_root: Path = DEFAULT_FPL_API_ROOT,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    boundary_season: str = DEFAULT_BOUNDARY_SEASON,
) -> tuple[pd.DataFrame, CombineDiagnostics]:
    vaastav = read_parquet(vaastav_input)
    fpl_api_frames = load_fpl_api_season_files(fpl_api_root)
    combined, diagnostics = combine_merged_gw_sources(
        vaastav,
        fpl_api_frames,
        boundary_season=boundary_season,
    )
    write_combined_dataset(combined, output_path)
    write_diagnostics_report(diagnostics, output_path=report_path)
    return combined, diagnostics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vaastav-input", type=Path, default=DEFAULT_VAASTAV_INPUT)
    parser.add_argument("--fpl-api-root", type=Path, default=DEFAULT_FPL_API_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--boundary-season", default=DEFAULT_BOUNDARY_SEASON)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    combined, diagnostics = combine_from_paths(
        vaastav_input=args.vaastav_input,
        fpl_api_root=args.fpl_api_root,
        output_path=args.output,
        report_path=args.report,
        boundary_season=args.boundary_season,
    )
    print(f"Rows: {len(combined)}")
    print(f"Wrote: {args.output}")
    print(f"Wrote report: {args.report}")
    if diagnostics.dropped_vaastav_rows:
        print(
            "Dropped Vaastav boundary/future seasons: "
            f"{list(diagnostics.dropped_vaastav_seasons)}"
        )


if __name__ == "__main__":
    main()
