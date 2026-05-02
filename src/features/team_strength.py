"""Leakage-safe team-strength source tables.

This module prepares team-gameweek rows from player-gameweek data. It does not
add raw team identifiers to model features; downstream code should use this as
an intermediate table for rolling, pre-match team-strength features.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


SEASON_COLUMN = "season"
GAMEWEEK_COLUMN = "gw"
TEAM_COLUMN_CANDIDATES = ("team", "team_id", "squad", "club")
OPPONENT_TEAM_COLUMN_CANDIDATES = ("opponent_team", "opp_team", "opponent_team_id")
HOME_COLUMN_CANDIDATES = ("was_home", "is_home")
FIXTURE_COLUMN = "fixture"
HOME_SCORE_COLUMN = "team_h_score"
AWAY_SCORE_COLUMN = "team_a_score"
GOALS_SCORED_COLUMN = "goals_scored"
GOALS_CONCEDED_COLUMN = "goals_conceded"
TEAM_ID_NORMALIZED_COLUMN = "team_id_normalized"
OPPONENT_TEAM_ID_NORMALIZED_COLUMN = "opponent_team_id_normalized"
TEAM_NAME_NORMALIZED_COLUMN = "team_name_normalized"
OPPONENT_TEAM_NAME_NORMALIZED_COLUMN = "opponent_team_name_normalized"
DEFAULT_BASE_ELO = 1500.0
DEFAULT_PROMOTED_ELO = 1450.0
DEFAULT_K_FACTOR = 20.0
DEFAULT_HOME_ADVANTAGE = 50.0
PROMOTED_RANK_PRIORS = {
    1: 1470.0,
    2: 1455.0,
    3: 1440.0,
}
POSITION_LABEL_MAP = {
    "GKP": "GK",
    "GK": "GK",
    "DEF": "DEF",
    "MID": "MID",
    "FWD": "FWD",
}


class TeamStrengthError(ValueError):
    """Raised when team-strength source tables cannot be created."""


@dataclass(frozen=True)
class TeamIdentifierColumns:
    team: str
    opponent_team: str | None
    was_home: str | None


@dataclass(frozen=True)
class TeamIdentifierDiagnostics:
    total_rows: int
    valid_team_id_rows: int
    valid_opponent_id_rows: int
    supported_seasons: tuple[str, ...]
    unsupported_season_reasons: dict[str, str] = field(default_factory=dict)

    @property
    def valid_team_id_rate(self) -> float:
        return self.valid_team_id_rows / self.total_rows if self.total_rows else 0.0

    @property
    def valid_opponent_id_rate(self) -> float:
        return self.valid_opponent_id_rows / self.total_rows if self.total_rows else 0.0


def normalize_position_label(value: Any) -> str | None:
    """Normalize known FPL position labels."""
    if pd.isna(value):
        return None
    return POSITION_LABEL_MAP.get(str(value).strip().upper())


def normalize_team_identifier(value: Any) -> str | None:
    """Normalize team identifiers for stable grouping without changing semantics."""
    if pd.isna(value):
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned.upper() if cleaned else None
    return str(value)


def _looks_numeric_identifier(series: pd.Series) -> bool:
    non_null = series.dropna()
    if non_null.empty:
        return False
    return pd.to_numeric(non_null, errors="coerce").notna().all()


def _looks_named_identifier(series: pd.Series) -> bool:
    non_null = series.dropna()
    if non_null.empty:
        return False
    return not _looks_numeric_identifier(non_null)


def _first_existing_column(frame: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    return next((column for column in candidates if column in frame.columns), None)


def detect_team_identifier_columns(frame: pd.DataFrame) -> TeamIdentifierColumns:
    """Detect team, opponent, and home/away columns in processed Vaastav data."""
    team_column = _first_existing_column(frame, TEAM_COLUMN_CANDIDATES)
    if team_column is None:
        raise TeamStrengthError(
            f"Could not detect team identifier column. Tried: {TEAM_COLUMN_CANDIDATES}"
        )
    return TeamIdentifierColumns(
        team=team_column,
        opponent_team=_first_existing_column(frame, OPPONENT_TEAM_COLUMN_CANDIDATES),
        was_home=_first_existing_column(frame, HOME_COLUMN_CANDIDATES),
    )


def _infer_team_code_mapping_from_fixtures(
    season_frame: pd.DataFrame,
    *,
    team_column: str,
    opponent_column: str,
) -> tuple[dict[str, str], dict[str, str], str | None]:
    if FIXTURE_COLUMN not in season_frame.columns:
        return {}, {}, "fixture column is unavailable"

    team_to_codes: dict[str, set[str]] = {}
    invalid_fixture_count = 0
    for _, fixture in season_frame.dropna(
        subset=[team_column, opponent_column, FIXTURE_COLUMN],
    ).groupby([GAMEWEEK_COLUMN, FIXTURE_COLUMN], sort=False):
        team_to_opponents = {
            normalize_team_identifier(team): {
                normalize_team_identifier(opponent)
                for opponent in team_rows[opponent_column].dropna()
            }
            for team, team_rows in fixture.groupby(team_column, sort=False)
        }
        team_to_opponents = {
            team: opponents
            for team, opponents in team_to_opponents.items()
            if team is not None and len(opponents) == 1
        }
        if len(team_to_opponents) != 2:
            invalid_fixture_count += 1
            continue

        teams = list(team_to_opponents)
        first_team, second_team = teams[0], teams[1]
        first_opponent_code = next(iter(team_to_opponents[first_team]))
        second_opponent_code = next(iter(team_to_opponents[second_team]))
        team_to_codes.setdefault(first_team, set()).add(second_opponent_code)
        team_to_codes.setdefault(second_team, set()).add(first_opponent_code)

    ambiguous = {team: codes for team, codes in team_to_codes.items() if len(codes) != 1}
    if ambiguous:
        return {}, {}, "team-name to numeric-code mapping is ambiguous within season"
    name_to_id = {team: next(iter(codes)) for team, codes in team_to_codes.items()}
    id_to_name = {team_id: team for team, team_id in name_to_id.items()}
    if not name_to_id:
        reason = "no paired fixture rows with two named teams and two opponent codes"
        if invalid_fixture_count:
            reason = f"{reason}; {invalid_fixture_count} fixtures were not inferable"
        return {}, {}, reason
    return name_to_id, id_to_name, None


def normalize_team_identifiers(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, TeamIdentifierDiagnostics]:
    """Create consistent normalized team and opponent identifiers.

    Modern Vaastav rows use team names in ``team`` and numeric FPL team IDs in
    ``opponent_team``. For those seasons, each fixture contains rows for both
    clubs, so the team's own numeric ID can be inferred from the opposing rows.
    Seasons without team names remain unsupported for team-strength joins.
    """
    required = [SEASON_COLUMN, GAMEWEEK_COLUMN]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise TeamStrengthError(f"Missing required columns: {missing}")

    identifiers = detect_team_identifier_columns(frame)
    data = frame.copy()
    data[TEAM_ID_NORMALIZED_COLUMN] = pd.NA
    data[OPPONENT_TEAM_ID_NORMALIZED_COLUMN] = pd.NA
    data[TEAM_NAME_NORMALIZED_COLUMN] = pd.NA
    data[OPPONENT_TEAM_NAME_NORMALIZED_COLUMN] = pd.NA

    unsupported: dict[str, str] = {}
    supported: list[str] = []
    if identifiers.opponent_team is None:
        unsupported = {
            str(season): "opponent team column is unavailable"
            for season in sorted(data[SEASON_COLUMN].dropna().astype(str).unique())
        }
    else:
        for season, season_frame in data.groupby(SEASON_COLUMN, sort=True):
            season_key = str(season)
            index = season_frame.index
            team_values = season_frame[identifiers.team]
            opponent_values = season_frame[identifiers.opponent_team]
            team_is_numeric = _looks_numeric_identifier(team_values)
            opponent_is_numeric = _looks_numeric_identifier(opponent_values)
            team_is_named = _looks_named_identifier(team_values)
            opponent_is_named = _looks_named_identifier(opponent_values)

            if team_is_numeric and opponent_is_numeric:
                data.loc[index, TEAM_ID_NORMALIZED_COLUMN] = team_values.map(
                    normalize_team_identifier
                )
                data.loc[index, OPPONENT_TEAM_ID_NORMALIZED_COLUMN] = opponent_values.map(
                    normalize_team_identifier
                )
                supported.append(season_key)
                continue

            if team_is_named and opponent_is_named:
                data.loc[index, TEAM_ID_NORMALIZED_COLUMN] = team_values.map(
                    normalize_team_identifier
                )
                data.loc[index, OPPONENT_TEAM_ID_NORMALIZED_COLUMN] = opponent_values.map(
                    normalize_team_identifier
                )
                data.loc[index, TEAM_NAME_NORMALIZED_COLUMN] = team_values.map(
                    normalize_team_identifier
                )
                data.loc[index, OPPONENT_TEAM_NAME_NORMALIZED_COLUMN] = opponent_values.map(
                    normalize_team_identifier
                )
                supported.append(season_key)
                continue

            if team_is_named and opponent_is_numeric:
                name_to_id, id_to_name, reason = _infer_team_code_mapping_from_fixtures(
                    season_frame,
                    team_column=identifiers.team,
                    opponent_column=identifiers.opponent_team,
                )
                if reason is not None:
                    unsupported[season_key] = reason
                    continue
                normalized_team_names = team_values.map(normalize_team_identifier)
                normalized_opponents = opponent_values.map(normalize_team_identifier)
                data.loc[index, TEAM_ID_NORMALIZED_COLUMN] = normalized_team_names.map(name_to_id)
                data.loc[index, OPPONENT_TEAM_ID_NORMALIZED_COLUMN] = normalized_opponents
                data.loc[index, TEAM_NAME_NORMALIZED_COLUMN] = normalized_team_names
                data.loc[index, OPPONENT_TEAM_NAME_NORMALIZED_COLUMN] = normalized_opponents.map(
                    id_to_name
                )
                if (
                    data.loc[index, TEAM_ID_NORMALIZED_COLUMN].notna().all()
                    and data.loc[index, OPPONENT_TEAM_ID_NORMALIZED_COLUMN].notna().all()
                ):
                    supported.append(season_key)
                else:
                    unsupported[season_key] = (
                        "some rows could not be mapped from team names to numeric IDs"
                    )
                continue

            unsupported[season_key] = (
                "team/opponent identifier types are unsupported or team names are missing"
            )

    diagnostics = TeamIdentifierDiagnostics(
        total_rows=len(data),
        valid_team_id_rows=int(data[TEAM_ID_NORMALIZED_COLUMN].notna().sum()),
        valid_opponent_id_rows=int(data[OPPONENT_TEAM_ID_NORMALIZED_COLUMN].notna().sum()),
        supported_seasons=tuple(sorted(set(supported))),
        unsupported_season_reasons=unsupported,
    )
    return data, diagnostics


def _derive_goals(frame: pd.DataFrame, was_home_column: str | None) -> pd.DataFrame:
    data = frame.copy()
    if (
        was_home_column is None
        or HOME_SCORE_COLUMN not in data.columns
        or AWAY_SCORE_COLUMN not in data.columns
    ):
        # Vaastav player rows expose team_h_score/team_a_score plus was_home in
        # modern processed exports. Without all three columns, a player row does
        # not reliably say which score belongs to the player's team.
        return data

    was_home = data[was_home_column].astype(bool)
    home_score = pd.to_numeric(data[HOME_SCORE_COLUMN], errors="coerce")
    away_score = pd.to_numeric(data[AWAY_SCORE_COLUMN], errors="coerce")
    data[GOALS_SCORED_COLUMN] = home_score.where(was_home, away_score)
    data[GOALS_CONCEDED_COLUMN] = away_score.where(was_home, home_score)
    return data


def create_team_gameweek_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Create one team-gameweek-opponent row from player-gameweek rows.

    The table is an intermediate source for future rolling team-strength
    features. It intentionally keeps team identifiers here, not in the model
    feature list.
    """
    required = [SEASON_COLUMN, GAMEWEEK_COLUMN]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise TeamStrengthError(f"Missing required columns: {missing}")

    identifiers = detect_team_identifier_columns(frame)
    normalized, _ = normalize_team_identifiers(frame)
    data = _derive_goals(normalized, identifiers.was_home)
    output = pd.DataFrame(
        {
            SEASON_COLUMN: data[SEASON_COLUMN],
            GAMEWEEK_COLUMN: data[GAMEWEEK_COLUMN],
            TEAM_ID_NORMALIZED_COLUMN: data[TEAM_ID_NORMALIZED_COLUMN],
            OPPONENT_TEAM_ID_NORMALIZED_COLUMN: data[OPPONENT_TEAM_ID_NORMALIZED_COLUMN],
        }
    )
    if data[TEAM_NAME_NORMALIZED_COLUMN].notna().any():
        output[TEAM_NAME_NORMALIZED_COLUMN] = data[TEAM_NAME_NORMALIZED_COLUMN]
    if data[OPPONENT_TEAM_NAME_NORMALIZED_COLUMN].notna().any():
        output[OPPONENT_TEAM_NAME_NORMALIZED_COLUMN] = data[OPPONENT_TEAM_NAME_NORMALIZED_COLUMN]
    if identifiers.was_home is not None:
        output["was_home"] = data[identifiers.was_home].astype(bool)
    for column in (GOALS_SCORED_COLUMN, GOALS_CONCEDED_COLUMN):
        if column in data.columns:
            output[column] = data[column]

    dedupe_columns = [
        SEASON_COLUMN,
        GAMEWEEK_COLUMN,
        TEAM_ID_NORMALIZED_COLUMN,
        OPPONENT_TEAM_ID_NORMALIZED_COLUMN,
    ]
    if "was_home" in output.columns:
        dedupe_columns.append("was_home")

    return (
        output.dropna(subset=[TEAM_ID_NORMALIZED_COLUMN, OPPONENT_TEAM_ID_NORMALIZED_COLUMN])
        .drop_duplicates(subset=dedupe_columns)
        .sort_values([SEASON_COLUMN, GAMEWEEK_COLUMN, TEAM_ID_NORMALIZED_COLUMN])
        .reset_index(drop=True)
    )


def expected_score(team_elo: float, opponent_elo: float) -> float:
    """Expected Elo score against an opponent."""
    return 1 / (1 + 10 ** ((opponent_elo - team_elo) / 400))


def actual_score(goals_scored: float, goals_conceded: float) -> float:
    """Convert match goals into Elo result score."""
    if goals_scored > goals_conceded:
        return 1.0
    if goals_scored == goals_conceded:
        return 0.5
    return 0.0


def initial_team_elos(
    teams: pd.Series,
    *,
    season: str | None = None,
    base_elo: float = DEFAULT_BASE_ELO,
    promoted_teams: set[str] | None = None,
    promoted_elo: float = DEFAULT_PROMOTED_ELO,
    previous_season_final_elos: dict[str, float] | None = None,
    team_season_priors: pd.DataFrame | None = None,
) -> dict[str, float]:
    """Initialize teams with safe start-of-season priors."""
    promoted = promoted_teams or set()
    normalized_promoted = {normalize_team_identifier(team) for team in promoted}
    final_elos = previous_season_final_elos or {}
    normalized_final_elos = {
        normalize_team_identifier(team): elo for team, elo in final_elos.items()
    }
    prior_lookup = team_prior_lookup(team_season_priors, season=season)

    initial_elos = {}
    for team in sorted({team for team in teams.map(normalize_team_identifier).dropna()}):
        if team in prior_lookup:
            initial_elos[team] = start_elo_from_prior(
                prior_lookup[team],
                previous_season_final_elo=normalized_final_elos.get(team),
                base_elo=base_elo,
                promoted_elo=promoted_elo,
            )
        elif team in normalized_promoted:
            initial_elos[team] = promoted_elo
        else:
            initial_elos[team] = base_elo
    return initial_elos


def team_prior_lookup(
    priors: pd.DataFrame | None,
    *,
    season: str | None,
) -> dict[str, dict[str, Any]]:
    """Build a team prior lookup for the requested season only."""
    if priors is None or season is None or priors.empty:
        return {}
    required_columns = {"season", "team"}
    missing = required_columns - set(priors.columns)
    if missing:
        raise TeamStrengthError(f"Missing team prior columns: {sorted(missing)}")

    season_priors = priors.loc[priors["season"].astype(str) == str(season)].copy()
    season_priors["team"] = season_priors["team"].map(normalize_team_identifier)
    return {
        row["team"]: row.to_dict()
        for _, row in season_priors.dropna(subset=["team"]).iterrows()
    }


def table_position_prior(
    previous_season_position: Any,
    *,
    base_elo: float = DEFAULT_BASE_ELO,
) -> float | None:
    """Convert previous-season final league position to a start Elo prior."""
    if pd.isna(previous_season_position):
        return None
    position = pd.to_numeric(pd.Series([previous_season_position]), errors="coerce").iloc[0]
    if pd.isna(position):
        return None
    return float(base_elo + (21 - int(position)) * 5)


def promoted_team_prior(
    promoted_rank: Any,
    *,
    promoted_elo: float = DEFAULT_PROMOTED_ELO,
) -> float:
    """Map promoted-team rank to a conservative start Elo prior."""
    if pd.isna(promoted_rank):
        return promoted_elo
    rank = pd.to_numeric(pd.Series([promoted_rank]), errors="coerce").iloc[0]
    if pd.isna(rank):
        return promoted_elo
    return PROMOTED_RANK_PRIORS.get(int(rank), promoted_elo)


def _is_promoted_status(value: Any) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"promoted", "newly_promoted", "yes", "true", "1"}


def start_elo_from_prior(
    prior: dict[str, Any],
    *,
    previous_season_final_elo: float | None,
    base_elo: float = DEFAULT_BASE_ELO,
    promoted_elo: float = DEFAULT_PROMOTED_ELO,
) -> float:
    """Resolve one team's start Elo from manual priors and previous final Elo."""
    if _is_promoted_status(prior.get("promoted_status")):
        return promoted_team_prior(prior.get("promoted_rank"), promoted_elo=promoted_elo)

    position_prior = table_position_prior(
        prior.get("previous_season_position"),
        base_elo=base_elo,
    )
    if position_prior is None:
        return base_elo
    if previous_season_final_elo is None:
        return position_prior
    return 0.70 * previous_season_final_elo + 0.30 * position_prior


def add_elo_features(
    team_gameweeks: pd.DataFrame,
    *,
    base_elo: float = DEFAULT_BASE_ELO,
    k_factor: float = DEFAULT_K_FACTOR,
    home_advantage: float = DEFAULT_HOME_ADVANTAGE,
    promoted_teams_by_season: dict[str, set[str]] | None = None,
    team_season_priors: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Add pre-gameweek Elo features to a team-gameweek table.

    For GW t, emitted Elo values are captured before any GW t match updates are
    applied. Updates from GW t are only visible from GW t+1 onward.
    """
    required = [
        SEASON_COLUMN,
        GAMEWEEK_COLUMN,
        TEAM_ID_NORMALIZED_COLUMN,
        OPPONENT_TEAM_ID_NORMALIZED_COLUMN,
        "was_home",
        GOALS_SCORED_COLUMN,
        GOALS_CONCEDED_COLUMN,
    ]
    missing = [column for column in required if column not in team_gameweeks.columns]
    if missing:
        raise TeamStrengthError(f"Missing required Elo columns: {missing}")

    promoted_by_season = promoted_teams_by_season or {}
    data = team_gameweeks.copy()
    data[TEAM_ID_NORMALIZED_COLUMN] = data[TEAM_ID_NORMALIZED_COLUMN].map(normalize_team_identifier)
    data[OPPONENT_TEAM_ID_NORMALIZED_COLUMN] = data[OPPONENT_TEAM_ID_NORMALIZED_COLUMN].map(
        normalize_team_identifier
    )
    data = data.dropna(
        subset=[TEAM_ID_NORMALIZED_COLUMN, OPPONENT_TEAM_ID_NORMALIZED_COLUMN]
    ).sort_values(
        [SEASON_COLUMN, GAMEWEEK_COLUMN, TEAM_ID_NORMALIZED_COLUMN]
    )

    season_outputs: list[pd.DataFrame] = []
    previous_final_elos: dict[str, float] = {}
    for season, season_data in data.groupby(SEASON_COLUMN, sort=True):
        teams = pd.concat(
            [
                season_data[TEAM_ID_NORMALIZED_COLUMN],
                season_data[OPPONENT_TEAM_ID_NORMALIZED_COLUMN],
            ],
            ignore_index=True,
        )
        elos = initial_team_elos(
            teams,
            season=str(season),
            base_elo=base_elo,
            promoted_teams=promoted_by_season.get(str(season), set()),
            previous_season_final_elos=previous_final_elos,
            team_season_priors=team_season_priors,
        )
        gameweek_outputs: list[pd.DataFrame] = []
        for _, gameweek_data in season_data.groupby(GAMEWEEK_COLUMN, sort=True):
            gameweek = gameweek_data.copy()
            gameweek["pre_gw_team_elo"] = gameweek[TEAM_ID_NORMALIZED_COLUMN].map(
                lambda team: elos.get(team, base_elo)
            )
            gameweek["pre_gw_opponent_elo"] = gameweek[OPPONENT_TEAM_ID_NORMALIZED_COLUMN].map(
                lambda team: elos.get(team, base_elo)
            )
            gameweek["elo_difference"] = (
                gameweek["pre_gw_team_elo"] - gameweek["pre_gw_opponent_elo"]
            )
            home_adjustment = gameweek["was_home"].map(lambda is_home: home_advantage if is_home else -home_advantage)
            gameweek["home_adjusted_elo_difference"] = (
                gameweek["elo_difference"] + home_adjustment
            )
            gameweek_outputs.append(gameweek)

            next_elos = elos.copy()
            for row in gameweek.itertuples(index=False):
                team = getattr(row, TEAM_ID_NORMALIZED_COLUMN)
                opponent = getattr(row, OPPONENT_TEAM_ID_NORMALIZED_COLUMN)
                team_elo = elos.get(team, base_elo)
                opponent_elo = elos.get(opponent, base_elo)
                result = actual_score(
                    getattr(row, GOALS_SCORED_COLUMN),
                    getattr(row, GOALS_CONCEDED_COLUMN),
                )
                expectation = expected_score(team_elo, opponent_elo)
                next_elos[team] = team_elo + k_factor * (result - expectation)
            elos = next_elos
        season_outputs.append(pd.concat(gameweek_outputs, ignore_index=True))
        previous_final_elos = elos.copy()

    if not season_outputs:
        return data.assign(
            pre_gw_team_elo=pd.Series(dtype="float64"),
            pre_gw_opponent_elo=pd.Series(dtype="float64"),
            elo_difference=pd.Series(dtype="float64"),
            home_adjusted_elo_difference=pd.Series(dtype="float64"),
        )
    return pd.concat(season_outputs, ignore_index=True).sort_values(
        [SEASON_COLUMN, GAMEWEEK_COLUMN, TEAM_ID_NORMALIZED_COLUMN]
    ).reset_index(drop=True)


def _previous_team_gameweek_rolling_mean(
    frame: pd.DataFrame,
    *,
    source_column: str,
    window: int,
) -> pd.Series:
    gameweek_values = (
        frame.groupby([TEAM_ID_NORMALIZED_COLUMN, SEASON_COLUMN, GAMEWEEK_COLUMN], as_index=False)[
            source_column
        ]
        .mean()
        .sort_values([TEAM_ID_NORMALIZED_COLUMN, SEASON_COLUMN, GAMEWEEK_COLUMN])
    )
    shifted = gameweek_values.groupby(
        [TEAM_ID_NORMALIZED_COLUMN, SEASON_COLUMN],
        sort=False,
    )[source_column].shift(1)
    rolling = shifted.groupby(
        [
            gameweek_values[TEAM_ID_NORMALIZED_COLUMN],
            gameweek_values[SEASON_COLUMN],
        ],
        sort=False,
    ).rolling(window=window, min_periods=1)
    gameweek_values[f"__previous_{source_column}"] = rolling.mean().reset_index(
        level=[0, 1],
        drop=True,
    )
    return frame.merge(
        gameweek_values[
            [
                TEAM_ID_NORMALIZED_COLUMN,
                SEASON_COLUMN,
                GAMEWEEK_COLUMN,
                f"__previous_{source_column}",
            ]
        ],
        on=[TEAM_ID_NORMALIZED_COLUMN, SEASON_COLUMN, GAMEWEEK_COLUMN],
        how="left",
    )[f"__previous_{source_column}"]


def add_rolling_team_goal_features(team_gameweeks: pd.DataFrame, *, window: int = 5) -> pd.DataFrame:
    """Add previous-match rolling team goal-form features.

    These features are reliable only when goals_scored and goals_conceded are
    present in the team-gameweek table. They are shifted within team-season
    before rolling, so GW t never uses GW t goals.
    """
    required = [
        SEASON_COLUMN,
        GAMEWEEK_COLUMN,
        TEAM_ID_NORMALIZED_COLUMN,
        OPPONENT_TEAM_ID_NORMALIZED_COLUMN,
        GOALS_SCORED_COLUMN,
        GOALS_CONCEDED_COLUMN,
    ]
    missing = [column for column in required if column not in team_gameweeks.columns]
    if missing:
        raise TeamStrengthError(f"Missing required rolling team-goal columns: {missing}")

    data = team_gameweeks.sort_values(
        [TEAM_ID_NORMALIZED_COLUMN, SEASON_COLUMN, GAMEWEEK_COLUMN]
    ).reset_index(drop=True)
    data["team_clean_sheet"] = (pd.to_numeric(data[GOALS_CONCEDED_COLUMN], errors="coerce") == 0).astype(
        float
    )
    data["team_goals_scored_mean_last_5"] = _previous_team_gameweek_rolling_mean(
        data,
        source_column=GOALS_SCORED_COLUMN,
        window=window,
    )
    data["team_goals_conceded_mean_last_5"] = _previous_team_gameweek_rolling_mean(
        data,
        source_column=GOALS_CONCEDED_COLUMN,
        window=window,
    )
    data["team_clean_sheet_rate_last_5"] = _previous_team_gameweek_rolling_mean(
        data,
        source_column="team_clean_sheet",
        window=window,
    )

    opponent_form = data[
        [
            SEASON_COLUMN,
            GAMEWEEK_COLUMN,
            TEAM_ID_NORMALIZED_COLUMN,
            "team_goals_scored_mean_last_5",
            "team_goals_conceded_mean_last_5",
            "team_clean_sheet_rate_last_5",
        ]
    ].rename(
        columns={
            TEAM_ID_NORMALIZED_COLUMN: OPPONENT_TEAM_ID_NORMALIZED_COLUMN,
            "team_goals_scored_mean_last_5": "opponent_goals_scored_mean_last_5",
            "team_goals_conceded_mean_last_5": "opponent_goals_conceded_mean_last_5",
            "team_clean_sheet_rate_last_5": "opponent_clean_sheet_rate_last_5",
        }
    )
    opponent_form = opponent_form.drop_duplicates(
        subset=[SEASON_COLUMN, GAMEWEEK_COLUMN, OPPONENT_TEAM_ID_NORMALIZED_COLUMN]
    )
    data = data.merge(
        opponent_form,
        on=[SEASON_COLUMN, GAMEWEEK_COLUMN, OPPONENT_TEAM_ID_NORMALIZED_COLUMN],
        how="left",
    )
    return data.drop(columns=["team_clean_sheet"]).sort_values(
        [SEASON_COLUMN, GAMEWEEK_COLUMN, TEAM_ID_NORMALIZED_COLUMN]
    ).reset_index(drop=True)


def build_team_strength_features(
    player_gameweeks: pd.DataFrame,
    *,
    team_season_priors: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build leakage-safe numeric team-strength features for player rows."""
    team_gameweeks = create_team_gameweek_table(player_gameweeks)
    with_elo = add_elo_features(team_gameweeks, team_season_priors=team_season_priors)
    rolling_columns = [
        "team_goals_scored_mean_last_5",
        "team_goals_conceded_mean_last_5",
        "opponent_goals_scored_mean_last_5",
        "opponent_goals_conceded_mean_last_5",
        "team_clean_sheet_rate_last_5",
        "opponent_clean_sheet_rate_last_5",
    ]
    if {GOALS_SCORED_COLUMN, GOALS_CONCEDED_COLUMN}.issubset(team_gameweeks.columns):
        with_rolling = add_rolling_team_goal_features(team_gameweeks)
        with_elo = with_elo.merge(
            with_rolling[
                [
                    SEASON_COLUMN,
                    GAMEWEEK_COLUMN,
                    TEAM_ID_NORMALIZED_COLUMN,
                    OPPONENT_TEAM_ID_NORMALIZED_COLUMN,
                    *rolling_columns,
                ]
            ],
            on=[
                SEASON_COLUMN,
                GAMEWEEK_COLUMN,
                TEAM_ID_NORMALIZED_COLUMN,
                OPPONENT_TEAM_ID_NORMALIZED_COLUMN,
            ],
            how="left",
        )

    feature_columns = [
        SEASON_COLUMN,
        GAMEWEEK_COLUMN,
        TEAM_ID_NORMALIZED_COLUMN,
        OPPONENT_TEAM_ID_NORMALIZED_COLUMN,
        "pre_gw_team_elo",
        "pre_gw_opponent_elo",
        "elo_difference",
        "home_adjusted_elo_difference",
        *[column for column in rolling_columns if column in with_elo.columns],
    ]
    features = with_elo[feature_columns].rename(
        columns={
            "pre_gw_team_elo": "team_elo_pre_gw",
            "pre_gw_opponent_elo": "opponent_elo_pre_gw",
        }
    )

    player_keys, _ = normalize_team_identifiers(player_gameweeks)
    player_keys = pd.DataFrame(
        {
            SEASON_COLUMN: player_keys[SEASON_COLUMN],
            GAMEWEEK_COLUMN: player_keys[GAMEWEEK_COLUMN],
            TEAM_ID_NORMALIZED_COLUMN: player_keys[TEAM_ID_NORMALIZED_COLUMN],
            OPPONENT_TEAM_ID_NORMALIZED_COLUMN: player_keys[OPPONENT_TEAM_ID_NORMALIZED_COLUMN],
        },
        index=player_gameweeks.index,
    )

    merged = player_keys.merge(
        features,
        on=[
            SEASON_COLUMN,
            GAMEWEEK_COLUMN,
            TEAM_ID_NORMALIZED_COLUMN,
            OPPONENT_TEAM_ID_NORMALIZED_COLUMN,
        ],
        how="left",
    )
    return merged.drop(
        columns=[
            SEASON_COLUMN,
            GAMEWEEK_COLUMN,
            TEAM_ID_NORMALIZED_COLUMN,
            OPPONENT_TEAM_ID_NORMALIZED_COLUMN,
        ]
    )


def team_identifier_diagnostics(frame: pd.DataFrame) -> TeamIdentifierDiagnostics:
    """Return diagnostics for normalized team/opponent identifiers."""
    _, diagnostics = normalize_team_identifiers(frame)
    return diagnostics
