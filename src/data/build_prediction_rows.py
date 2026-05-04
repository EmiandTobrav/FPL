"""Build Vaastav-compatible prediction rows for upcoming FPL fixtures."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from data.fpl_api_to_vaastav import (
    OPTIONAL_COMPATIBILITY_COLUMNS,
    POSITION_LABELS,
    REQUIRED_VAASTAV_COLUMNS,
    UNAVAILABLE_OPTIONAL_COLUMNS,
)


DEFAULT_INPUT_ROOT = Path("data/interim/fpl_api")
DEFAULT_REPORT_PATH = Path("reports/prediction_row_builder_report.md")
OUTCOME_COLUMNS = ("total_points", "minutes", "starts", "bonus", "bps")
SNAPSHOT_COLUMNS = ("value", "selected", "transfers_in", "transfers_out")
REQUIRED_PREDICTION_COLUMNS = (
    "season",
    "gw",
    "element",
    "name",
    "team",
    "opponent_team",
    "was_home",
    "position",
    "value",
    "selected",
    "transfers_in",
    "transfers_out",
    *OUTCOME_COLUMNS,
    "fixture",
)


class PredictionRowBuildError(ValueError):
    """Raised when upcoming prediction rows cannot be built."""


@dataclass(frozen=True)
class PredictionRowSummary:
    season: str
    gw: int
    output_path: Path
    fixture_count: int
    player_fixture_rows: int
    blank_teams: tuple[str, ...]
    blank_player_count: int
    double_fixture_teams: tuple[str, ...]
    required_present: tuple[str, ...]
    required_missing: tuple[str, ...]
    outcome_columns_missing: tuple[str, ...]
    schema_missing_from_completed: tuple[str, ...]
    assumptions: tuple[str, ...]


def season_dir(input_root: Path, season: str) -> Path:
    return input_root / season


def read_optional_table(directory: Path, name: str) -> pd.DataFrame:
    path = directory / f"{name}.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def read_required_table(directory: Path, name: str) -> pd.DataFrame:
    path = directory / f"{name}.parquet"
    if not path.exists():
        raise PredictionRowBuildError(f"Missing required table: {path}")
    return pd.read_parquet(path)


def next_unfinished_gameweek(fixtures: pd.DataFrame) -> int:
    """Return the earliest fixture event that is not finished."""
    if "event" not in fixtures.columns:
        raise PredictionRowBuildError("fixtures.parquet must contain `event`.")
    data = fixtures.dropna(subset=["event"]).copy()
    if data.empty:
        raise PredictionRowBuildError("No fixture events are available.")
    if "finished" in data.columns:
        unfinished = data.loc[~data["finished"].fillna(False).astype(bool)]
    else:
        unfinished = data
    if unfinished.empty:
        raise PredictionRowBuildError("No unfinished fixture gameweeks are available.")
    return int(pd.to_numeric(unfinished["event"], errors="coerce").dropna().min())


def _name_series(elements: pd.DataFrame) -> pd.Series:
    if "web_name" in elements.columns:
        names = elements["web_name"].copy()
    else:
        names = pd.Series(pd.NA, index=elements.index)
    if {"first_name", "second_name"}.issubset(elements.columns):
        full = (
            elements["first_name"].fillna("").astype(str).str.strip()
            + " "
            + elements["second_name"].fillna("").astype(str).str.strip()
        ).str.strip()
        names = names.fillna(full)
    return names


def _team_name_lookup(teams: pd.DataFrame) -> dict[Any, Any]:
    if {"id", "name"}.issubset(teams.columns):
        return teams.set_index("id")["name"].to_dict()
    return {}


def normalize_elements(elements: pd.DataFrame, teams: pd.DataFrame) -> pd.DataFrame:
    if "id" not in elements.columns or "team" not in elements.columns:
        raise PredictionRowBuildError("elements.parquet must contain `id` and `team`.")
    team_lookup = _team_name_lookup(teams)
    data = pd.DataFrame(
        {
            "element": elements["id"],
            "name": _name_series(elements),
            "team_id": elements["team"],
            "team": elements["team"].map(team_lookup).fillna(elements["team"]),
            "position": elements.get("element_type", pd.Series(pd.NA, index=elements.index))
            .map(POSITION_LABELS)
            .fillna(elements.get("element_type", pd.Series(pd.NA, index=elements.index))),
            "value": elements.get("now_cost", pd.Series(pd.NA, index=elements.index)),
            "selected": elements.get("selected_by_percent", pd.Series(pd.NA, index=elements.index)),
            "transfers_in": elements.get("transfers_in", pd.Series(pd.NA, index=elements.index)),
            "transfers_out": elements.get("transfers_out", pd.Series(pd.NA, index=elements.index)),
        }
    )
    return data


def fixture_sides(fixtures: pd.DataFrame, gw: int) -> pd.DataFrame:
    required = {"id", "event", "team_h", "team_a"}
    missing = required.difference(fixtures.columns)
    if missing:
        raise PredictionRowBuildError(f"fixtures.parquet missing required columns: {sorted(missing)}")
    gameweek = fixtures.loc[pd.to_numeric(fixtures["event"], errors="coerce").eq(gw)].copy()
    if gameweek.empty:
        raise PredictionRowBuildError(f"No fixtures found for GW {gw}.")
    rows: list[dict[str, Any]] = []
    for fixture in gameweek.to_dict(orient="records"):
        common = {
            "gw": gw,
            "fixture": fixture.get("id"),
            "kickoff_time": fixture.get("kickoff_time", pd.NA),
            "finished": fixture.get("finished", pd.NA),
            "started": fixture.get("started", pd.NA),
        }
        rows.append(
            {
                **common,
                "team_id": fixture.get("team_h"),
                "opponent_team": fixture.get("team_a"),
                "was_home": True,
            }
        )
        rows.append(
            {
                **common,
                "team_id": fixture.get("team_a"),
                "opponent_team": fixture.get("team_h"),
                "was_home": False,
            }
        )
    return pd.DataFrame(rows)


def _overlay_upcoming_fixture_values(rows: pd.DataFrame, upcoming: pd.DataFrame) -> pd.DataFrame:
    if upcoming.empty or not {"element", "id"}.issubset(upcoming.columns):
        return rows
    overlay_columns = [
        column
        for column in ("kickoff_time", "is_home", "team_h", "team_a")
        if column in upcoming.columns
    ]
    if not overlay_columns:
        return rows
    overlay = upcoming[["element", "id", *overlay_columns]].rename(columns={"id": "fixture"})
    merged = rows.merge(overlay, on=["element", "fixture"], how="left", suffixes=("", "_upcoming"))
    if "kickoff_time_upcoming" in merged.columns:
        merged["kickoff_time"] = merged["kickoff_time"].fillna(merged["kickoff_time_upcoming"])
    if "is_home" in merged.columns:
        merged["was_home"] = merged["was_home"].where(merged["is_home"].isna(), merged["is_home"])
    return merged.drop(
        columns=[column for column in merged.columns if column.endswith("_upcoming") or column == "is_home"]
    )


def build_prediction_rows(
    *,
    season: str,
    fixtures: pd.DataFrame,
    elements: pd.DataFrame,
    teams: pd.DataFrame,
    upcoming_player_fixtures: pd.DataFrame | None = None,
    completed_schema: pd.DataFrame | None = None,
    gw: int | None = None,
) -> tuple[pd.DataFrame, PredictionRowSummary]:
    """Create one player-fixture prediction row for the requested unfinished GW."""
    target_gw = gw if gw is not None else next_unfinished_gameweek(fixtures)
    players = normalize_elements(elements, teams)
    sides = fixture_sides(fixtures, target_gw)
    rows = players.merge(sides, on="team_id", how="inner")
    upcoming = upcoming_player_fixtures if upcoming_player_fixtures is not None else pd.DataFrame()
    rows = _overlay_upcoming_fixture_values(rows, upcoming)
    rows["season"] = season
    rows["GW"] = target_gw
    rows["round"] = target_gw

    for column in OUTCOME_COLUMNS:
        rows[column] = pd.NA
    for column in ("expected_goals", "expected_assists", "expected_goal_involvements", "expected_goals_conceded"):
        rows[column] = pd.NA
    for column in OPTIONAL_COMPATIBILITY_COLUMNS:
        if column not in rows.columns:
            rows[column] = pd.NA
    for column in UNAVAILABLE_OPTIONAL_COLUMNS:
        if column not in rows.columns:
            rows[column] = pd.NA
    for column in REQUIRED_VAASTAV_COLUMNS:
        if column not in rows.columns:
            rows[column] = pd.NA

    team_counts = sides.groupby("team_id", dropna=False).size()
    all_team_ids = set(players["team_id"].dropna())
    fixture_team_ids = set(sides["team_id"].dropna())
    blank_team_ids = sorted(all_team_ids.difference(fixture_team_ids))
    team_name_lookup = players.drop_duplicates("team_id").set_index("team_id")["team"].to_dict()
    blank_teams = tuple(str(team_name_lookup.get(team_id, team_id)) for team_id in blank_team_ids)
    blank_player_count = int(players.loc[players["team_id"].isin(blank_team_ids)].shape[0])
    double_fixture_teams = tuple(
        str(team_name_lookup.get(team_id, team_id))
        for team_id in sorted(team_counts.loc[team_counts.gt(1)].index)
    )

    ordered = [
        *REQUIRED_VAASTAV_COLUMNS,
        *[column for column in OPTIONAL_COMPATIBILITY_COLUMNS if column not in REQUIRED_VAASTAV_COLUMNS],
        *UNAVAILABLE_OPTIONAL_COLUMNS,
        "finished",
        "started",
    ]
    remaining = [column for column in rows.columns if column not in ordered and column != "team_id"]
    output = rows[[*ordered, *remaining]].sort_values(["fixture", "element"]).reset_index(drop=True)

    required_present = tuple(column for column in REQUIRED_PREDICTION_COLUMNS if column in output.columns)
    required_missing = tuple(column for column in REQUIRED_PREDICTION_COLUMNS if column not in output.columns)
    outcome_missing = tuple(column for column in OUTCOME_COLUMNS if column in output.columns and output[column].isna().all())
    schema_missing: tuple[str, ...] = ()
    if completed_schema is not None:
        schema_missing = tuple(sorted(set(completed_schema.columns).difference(output.columns)))
    assumptions = (
        "Prediction rows contain known fixture/player context only.",
        "Actual outcome columns are present but set to NA.",
        "Players on teams without a fixture in the target GW are omitted.",
        "Double gameweeks naturally create multiple player-fixture rows.",
    )
    summary = PredictionRowSummary(
        season=season,
        gw=int(target_gw),
        output_path=Path(),
        fixture_count=int(fixtures.loc[pd.to_numeric(fixtures["event"], errors="coerce").eq(target_gw)].shape[0]),
        player_fixture_rows=len(output),
        blank_teams=blank_teams,
        blank_player_count=blank_player_count,
        double_fixture_teams=double_fixture_teams,
        required_present=required_present,
        required_missing=required_missing,
        outcome_columns_missing=outcome_missing,
        schema_missing_from_completed=schema_missing,
        assumptions=assumptions,
    )
    return output, summary


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "None."
    lines = [
        "| " + " | ".join(frame.columns) + " |",
        "| " + " | ".join(["---"] * len(frame.columns)) + " |",
    ]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def write_prediction_report(
    summary: PredictionRowSummary,
    *,
    output_path: Path = DEFAULT_REPORT_PATH,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    assumptions = [f"- {assumption}" for assumption in summary.assumptions]
    output_path.write_text(
        "\n".join(
            [
                "# Prediction Row Builder Report",
                "",
                f"Season: `{summary.season}`",
                f"Target prediction GW: `{summary.gw}`",
                f"Output: `{summary.output_path.as_posix()}`",
                "",
                "| diagnostic | value |",
                "| --- | ---: |",
                f"| fixtures | {summary.fixture_count} |",
                f"| player-fixture rows | {summary.player_fixture_rows} |",
                f"| blank affected players | {summary.blank_player_count} |",
                "",
                f"Teams with blanks: {', '.join(summary.blank_teams) or 'None'}",
                "",
                f"Teams with double fixtures: {', '.join(summary.double_fixture_teams) or 'None'}",
                "",
                f"Required columns present: {', '.join(summary.required_present) or 'None'}",
                "",
                f"Required columns missing: {', '.join(summary.required_missing) or 'None'}",
                "",
                f"Outcome columns set to missing: {', '.join(summary.outcome_columns_missing) or 'None'}",
                "",
                (
                    "Missing versus completed merged_gw_api schema: "
                    f"{', '.join(summary.schema_missing_from_completed) or 'None'}"
                ),
                "",
                "## Assumptions",
                "",
                *assumptions,
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_prediction_rows_from_files(
    *,
    season: str,
    input_root: Path = DEFAULT_INPUT_ROOT,
    gw: int | None = None,
    report_path: Path = DEFAULT_REPORT_PATH,
) -> tuple[pd.DataFrame, PredictionRowSummary]:
    directory = season_dir(input_root, season)
    fixtures = read_required_table(directory, "fixtures")
    elements = read_required_table(directory, "elements")
    teams = read_required_table(directory, "teams")
    upcoming = read_optional_table(directory, "upcoming_player_fixtures")
    completed = read_optional_table(directory, "merged_gw_api")
    rows, summary = build_prediction_rows(
        season=season,
        fixtures=fixtures,
        elements=elements,
        teams=teams,
        upcoming_player_fixtures=upcoming,
        completed_schema=completed,
        gw=gw,
    )
    output_path = directory / f"prediction_rows_gw{summary.gw}.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows.to_parquet(output_path, index=False)
    summary = PredictionRowSummary(
        **{**summary.__dict__, "output_path": output_path},
    )
    write_prediction_report(summary, output_path=report_path)
    return rows, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", required=True, help="FPL season label, e.g. 2025-26.")
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--gw", type=int, default=None, help="Prediction gameweek override.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _, summary = build_prediction_rows_from_files(
        season=args.season,
        input_root=args.input_root,
        gw=args.gw,
        report_path=args.report,
    )
    print(f"Prediction GW: {summary.gw}")
    print(f"Rows: {summary.player_fixture_rows}")
    print(f"Wrote: {summary.output_path}")
    print(f"Wrote report: {args.report}")


if __name__ == "__main__":
    main()
