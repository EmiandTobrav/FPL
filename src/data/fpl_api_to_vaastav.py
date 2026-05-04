"""Adapt normalized official FPL API tables to Vaastav-style merged_gw rows."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_INPUT_ROOT = Path("data/interim/fpl_api")
DEFAULT_REPORT_PATH = Path("reports/fpl_api_vaastav_adapter_report.md")
DEFAULT_OUTPUT_FILENAME = "merged_gw_api.parquet"
MIN_FPL_API_SEASON = "2025-26"

REQUIRED_VAASTAV_COLUMNS = (
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
    "starts",
    "bonus",
    "bps",
    "selected",
    "transfers_in",
    "transfers_out",
    "value",
    "expected_goals",
    "expected_assists",
    "expected_goal_involvements",
    "expected_goals_conceded",
)
OPTIONAL_COMPATIBILITY_COLUMNS = (
    "assists",
    "clean_sheets",
    "creativity",
    "defensive_contribution",
    "fixture",
    "goals_conceded",
    "goals_scored",
    "ict_index",
    "influence",
    "kickoff_time",
    "modified",
    "own_goals",
    "penalties_missed",
    "penalties_saved",
    "recoveries",
    "red_cards",
    "round",
    "saves",
    "tackles",
    "team_a_score",
    "team_h_score",
    "threat",
    "transfers_balance",
    "yellow_cards",
    "GW",
)
UNAVAILABLE_OPTIONAL_COLUMNS = (
    "attempted_passes",
    "big_chances_created",
    "big_chances_missed",
    "clearances_blocks_interceptions",
    "completed_passes",
    "dribbles",
    "ea_index",
    "errors_leading_to_goal",
    "errors_leading_to_goal_attempt",
    "fouls",
    "id",
    "key_passes",
    "kickoff_time_formatted",
    "loaned_in",
    "loaned_out",
    "offside",
    "open_play_crosses",
    "penalties_conceded",
    "tackled",
    "target_missed",
    "winning_goals",
    "xP",
    "mng_clean_sheets",
    "mng_draw",
    "mng_goals_scored",
    "mng_loss",
    "mng_underdog_draw",
    "mng_underdog_win",
    "mng_win",
)
POSITION_LABELS = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
    "1": "GK",
    "2": "DEF",
    "3": "MID",
    "4": "FWD",
}


class FplApiVaastavAdapterError(ValueError):
    """Raised when normalized FPL API tables cannot be adapted."""


@dataclass(frozen=True)
class AdapterSummary:
    season: str
    output_path: Path
    rows_produced: int
    required_present: tuple[str, ...]
    required_missing: tuple[str, ...]
    optional_present: tuple[str, ...]
    optional_missing: tuple[str, ...]
    columns_filled_na: tuple[str, ...]
    schema_extra_columns: tuple[str, ...]


def season_is_supported(season: str) -> bool:
    """Return true when a season belongs to the FPL API era for this project."""
    return str(season) >= MIN_FPL_API_SEASON


def season_dir(input_root: Path, season: str) -> Path:
    return input_root / season


def read_table(directory: Path, name: str) -> pd.DataFrame:
    path = directory / f"{name}.parquet"
    if not path.exists():
        raise FplApiVaastavAdapterError(f"Missing normalized FPL API table: {path}")
    return pd.read_parquet(path)


def _first_available(row: pd.Series, columns: tuple[str, ...]) -> Any:
    for column in columns:
        if column in row.index and pd.notna(row[column]):
            return row[column]
    return pd.NA


def _name_lookup(elements: pd.DataFrame) -> pd.Series:
    if "web_name" in elements.columns:
        names = elements["web_name"].copy()
    else:
        names = pd.Series(pd.NA, index=elements.index)
    if {"first_name", "second_name"}.issubset(elements.columns):
        full_name = (
            elements["first_name"].fillna("").astype(str).str.strip()
            + " "
            + elements["second_name"].fillna("").astype(str).str.strip()
        ).str.strip()
        names = names.fillna(full_name)
    return names


def _position_lookup(elements: pd.DataFrame) -> pd.Series:
    if "element_type" not in elements.columns:
        return pd.Series(pd.NA, index=elements.index)
    return elements["element_type"].map(POSITION_LABELS).fillna(elements["element_type"])


def _team_lookup(elements: pd.DataFrame, teams: pd.DataFrame) -> pd.Series:
    if "team" not in elements.columns:
        return pd.Series(pd.NA, index=elements.index)
    if {"id", "name"}.issubset(teams.columns):
        team_names = teams.set_index("id")["name"]
        return elements["team"].map(team_names).fillna(elements["team"])
    return elements["team"]


def player_metadata(elements: pd.DataFrame, teams: pd.DataFrame) -> pd.DataFrame:
    if "id" not in elements.columns:
        raise FplApiVaastavAdapterError("elements.parquet must contain player id column `id`.")
    metadata = pd.DataFrame(
        {
            "element": elements["id"],
            "name": _name_lookup(elements),
            "position": _position_lookup(elements),
            "team": _team_lookup(elements, teams),
        }
    )
    return metadata.drop_duplicates(subset=["element"])


def adapt_fpl_api_tables(
    *,
    season: str,
    history: pd.DataFrame,
    elements: pd.DataFrame,
    teams: pd.DataFrame,
) -> pd.DataFrame:
    """Return Vaastav-compatible rows from normalized FPL API tables."""
    if not season_is_supported(season):
        raise FplApiVaastavAdapterError(
            f"FPL API adapter only supports seasons >= {MIN_FPL_API_SEASON}; got {season}."
        )
    if history.empty:
        return pd.DataFrame(columns=[*REQUIRED_VAASTAV_COLUMNS, *OPTIONAL_COMPATIBILITY_COLUMNS])
    if "element" not in history.columns:
        raise FplApiVaastavAdapterError("player_gameweek_history.parquet must contain `element`.")

    data = history.copy()
    if "season" not in data.columns:
        data["season"] = season
    else:
        data["season"] = data["season"].fillna(season)
    if "gw" not in data.columns:
        data["gw"] = data["round"] if "round" in data.columns else pd.NA
    if "GW" not in data.columns:
        data["GW"] = data["gw"]

    data = data.merge(player_metadata(elements, teams), on="element", how="left", suffixes=("", "_meta"))
    for column in ("name", "position", "team"):
        meta_column = f"{column}_meta"
        if meta_column in data.columns:
            data[column] = data[column].fillna(data[meta_column]) if column in data.columns else data[meta_column]
            data = data.drop(columns=[meta_column])

    for column in REQUIRED_VAASTAV_COLUMNS:
        if column not in data.columns:
            data[column] = pd.NA
    for column in OPTIONAL_COMPATIBILITY_COLUMNS:
        if column not in data.columns:
            data[column] = pd.NA
    for column in UNAVAILABLE_OPTIONAL_COLUMNS:
        if column not in data.columns:
            data[column] = pd.NA

    ordered_columns = [
        *REQUIRED_VAASTAV_COLUMNS,
        *[column for column in OPTIONAL_COMPATIBILITY_COLUMNS if column not in REQUIRED_VAASTAV_COLUMNS],
        *UNAVAILABLE_OPTIONAL_COLUMNS,
    ]
    remaining_columns = [column for column in data.columns if column not in ordered_columns]
    return data[[*ordered_columns, *remaining_columns]].sort_values(
        ["season", "gw", "element", "fixture"],
        na_position="last",
    ).reset_index(drop=True)


def load_mapping_report_columns(path: Path = Path("reports/fpl_api_schema_mapping.csv")) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def adapt_fpl_api_season(
    *,
    season: str,
    input_root: Path = DEFAULT_INPUT_ROOT,
    output_filename: str = DEFAULT_OUTPUT_FILENAME,
    mapping_report_path: Path = Path("reports/fpl_api_schema_mapping.csv"),
) -> tuple[pd.DataFrame, AdapterSummary]:
    directory = season_dir(input_root, season)
    history = read_table(directory, "player_gameweek_history")
    elements = read_table(directory, "elements")
    teams = read_table(directory, "teams")
    merged = adapt_fpl_api_tables(season=season, history=history, elements=elements, teams=teams)

    output_path = directory / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(output_path, index=False)

    mapping = load_mapping_report_columns(mapping_report_path)
    required_from_mapping = set()
    if not mapping.empty and {"vaastav_column", "current_pipeline_importance"}.issubset(mapping.columns):
        required_from_mapping = set(
            mapping.loc[
                mapping["current_pipeline_importance"].eq("essential"),
                "vaastav_column",
            ].dropna()
        )
    expected_required = set(REQUIRED_VAASTAV_COLUMNS) | required_from_mapping
    required_present = tuple(sorted(column for column in expected_required if column in merged.columns))
    required_missing = tuple(sorted(expected_required.difference(merged.columns)))
    optional_columns = set(OPTIONAL_COMPATIBILITY_COLUMNS) | set(UNAVAILABLE_OPTIONAL_COLUMNS)
    optional_present = tuple(sorted(column for column in optional_columns if column in merged.columns))
    optional_missing = tuple(sorted(optional_columns.difference(merged.columns)))
    columns_filled_na = tuple(sorted(column for column in merged.columns if merged[column].isna().all()))
    schema_extra_columns = tuple(
        sorted(
            column
            for column in merged.columns
            if column
            not in set(REQUIRED_VAASTAV_COLUMNS)
            | set(OPTIONAL_COMPATIBILITY_COLUMNS)
            | set(UNAVAILABLE_OPTIONAL_COLUMNS)
        )
    )
    summary = AdapterSummary(
        season=season,
        output_path=output_path,
        rows_produced=len(merged),
        required_present=required_present,
        required_missing=required_missing,
        optional_present=optional_present,
        optional_missing=optional_missing,
        columns_filled_na=columns_filled_na,
        schema_extra_columns=schema_extra_columns,
    )
    return merged, summary


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


def write_adapter_report(
    merged: pd.DataFrame,
    summary: AdapterSummary,
    *,
    output_path: Path = DEFAULT_REPORT_PATH,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows_by_gw = (
        merged.groupby("gw", dropna=False).size().rename("rows").reset_index()
        if "gw" in merged.columns
        else pd.DataFrame(columns=["gw", "rows"])
    )
    assumptions = [
        "Only seasons >= 2025-26 are accepted.",
        "`name`, `position`, and `team` are joined from `elements` and `teams`.",
        "`gw` and `GW` come from history `round` when missing.",
        "Unavailable compatibility columns are filled with NA instead of being fabricated.",
        "This command does not merge FPL API rows with Vaastav history.",
    ]
    output_path.write_text(
        "\n".join(
            [
                "# FPL API Vaastav Adapter Report",
                "",
                f"Season: `{summary.season}`",
                f"Output: `{summary.output_path.as_posix()}`",
                f"Rows produced: {summary.rows_produced}",
                "",
                "## Rows Produced By GW",
                "",
                _markdown_table(rows_by_gw),
                "",
                "## Required Columns",
                "",
                f"Present: {', '.join(summary.required_present) or 'None'}",
                "",
                f"Missing: {', '.join(summary.required_missing) or 'None'}",
                "",
                "## Optional Columns",
                "",
                f"Present: {', '.join(summary.optional_present) or 'None'}",
                "",
                f"Missing: {', '.join(summary.optional_missing) or 'None'}",
                "",
                "## Columns Filled As NA",
                "",
                ", ".join(summary.columns_filled_na) or "None",
                "",
                "## Schema Differences From Vaastav merged_gw",
                "",
                (
                    "Extra normalized API columns retained: "
                    + (", ".join(summary.schema_extra_columns) or "None")
                ),
                "",
                "Some older Vaastav pass/chance/manager fields may be present only as all-NA "
                "compatibility columns because they are not available in the sampled official API.",
                "",
                "## Assumptions",
                "",
                *[f"- {assumption}" for assumption in assumptions],
                "",
            ]
        ),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", required=True, help="FPL API season label, e.g. 2025-26.")
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-filename", default=DEFAULT_OUTPUT_FILENAME)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument(
        "--mapping-report",
        type=Path,
        default=Path("reports/fpl_api_schema_mapping.csv"),
        help="Optional schema mapping CSV used for validation.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    merged, summary = adapt_fpl_api_season(
        season=args.season,
        input_root=args.input_root,
        output_filename=args.output_filename,
        mapping_report_path=args.mapping_report,
    )
    write_adapter_report(merged, summary, output_path=args.report)
    print(f"Rows produced: {summary.rows_produced}")
    print(f"Wrote: {summary.output_path}")
    print(f"Wrote report: {args.report}")


if __name__ == "__main__":
    main()
