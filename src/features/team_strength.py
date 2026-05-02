"""Leakage-safe team-strength source tables.

This module prepares team-gameweek rows from player-gameweek data. It does not
add raw team identifiers to model features; downstream code should use this as
an intermediate table for rolling, pre-match team-strength features.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


SEASON_COLUMN = "season"
GAMEWEEK_COLUMN = "gw"
TEAM_COLUMN_CANDIDATES = ("team", "team_id", "squad", "club")
OPPONENT_TEAM_COLUMN_CANDIDATES = ("opponent_team", "opp_team", "opponent_team_id")
HOME_COLUMN_CANDIDATES = ("was_home", "is_home")
HOME_SCORE_COLUMN = "team_h_score"
AWAY_SCORE_COLUMN = "team_a_score"
GOALS_SCORED_COLUMN = "goals_scored"
GOALS_CONCEDED_COLUMN = "goals_conceded"
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
    data = _derive_goals(frame, identifiers.was_home)
    output = pd.DataFrame(
        {
            SEASON_COLUMN: data[SEASON_COLUMN],
            GAMEWEEK_COLUMN: data[GAMEWEEK_COLUMN],
            "team": data[identifiers.team].map(normalize_team_identifier),
        }
    )
    if identifiers.opponent_team is not None:
        output["opponent_team"] = data[identifiers.opponent_team].map(normalize_team_identifier)
    if identifiers.was_home is not None:
        output["was_home"] = data[identifiers.was_home].astype(bool)
    for column in (GOALS_SCORED_COLUMN, GOALS_CONCEDED_COLUMN):
        if column in data.columns:
            output[column] = data[column]

    dedupe_columns = [SEASON_COLUMN, GAMEWEEK_COLUMN, "team"]
    if "opponent_team" in output.columns:
        dedupe_columns.append("opponent_team")
    if "was_home" in output.columns:
        dedupe_columns.append("was_home")

    return (
        output.dropna(subset=["team"])
        .drop_duplicates(subset=dedupe_columns)
        .sort_values([SEASON_COLUMN, GAMEWEEK_COLUMN, "team"])
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
        "team",
        "opponent_team",
        "was_home",
        GOALS_SCORED_COLUMN,
        GOALS_CONCEDED_COLUMN,
    ]
    missing = [column for column in required if column not in team_gameweeks.columns]
    if missing:
        raise TeamStrengthError(f"Missing required Elo columns: {missing}")

    promoted_by_season = promoted_teams_by_season or {}
    data = team_gameweeks.copy()
    data["team"] = data["team"].map(normalize_team_identifier)
    data["opponent_team"] = data["opponent_team"].map(normalize_team_identifier)
    data = data.dropna(subset=["team", "opponent_team"]).sort_values(
        [SEASON_COLUMN, GAMEWEEK_COLUMN, "team"]
    )

    season_outputs: list[pd.DataFrame] = []
    previous_final_elos: dict[str, float] = {}
    for season, season_data in data.groupby(SEASON_COLUMN, sort=True):
        teams = pd.concat([season_data["team"], season_data["opponent_team"]], ignore_index=True)
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
            gameweek["pre_gw_team_elo"] = gameweek["team"].map(lambda team: elos.get(team, base_elo))
            gameweek["pre_gw_opponent_elo"] = gameweek["opponent_team"].map(
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
                team = getattr(row, "team")
                opponent = getattr(row, "opponent_team")
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
        [SEASON_COLUMN, GAMEWEEK_COLUMN, "team"]
    ).reset_index(drop=True)


def _previous_team_rolling_mean(
    frame: pd.DataFrame,
    *,
    source_column: str,
    window: int,
) -> pd.Series:
    shifted = frame.groupby(["team", SEASON_COLUMN], sort=False)[source_column].shift(1)
    rolling = shifted.groupby([frame["team"], frame[SEASON_COLUMN]], sort=False).rolling(
        window=window,
        min_periods=1,
    )
    return rolling.mean().reset_index(level=[0, 1], drop=True).sort_index()


def add_rolling_team_goal_features(team_gameweeks: pd.DataFrame, *, window: int = 5) -> pd.DataFrame:
    """Add previous-match rolling team goal-form features.

    These features are reliable only when goals_scored and goals_conceded are
    present in the team-gameweek table. They are shifted within team-season
    before rolling, so GW t never uses GW t goals.
    """
    required = [
        SEASON_COLUMN,
        GAMEWEEK_COLUMN,
        "team",
        "opponent_team",
        GOALS_SCORED_COLUMN,
        GOALS_CONCEDED_COLUMN,
    ]
    missing = [column for column in required if column not in team_gameweeks.columns]
    if missing:
        raise TeamStrengthError(f"Missing required rolling team-goal columns: {missing}")

    data = team_gameweeks.sort_values(["team", SEASON_COLUMN, GAMEWEEK_COLUMN]).copy()
    data["team_clean_sheet"] = (pd.to_numeric(data[GOALS_CONCEDED_COLUMN], errors="coerce") == 0).astype(
        float
    )
    data["team_goals_scored_mean_last_5"] = _previous_team_rolling_mean(
        data,
        source_column=GOALS_SCORED_COLUMN,
        window=window,
    )
    data["team_goals_conceded_mean_last_5"] = _previous_team_rolling_mean(
        data,
        source_column=GOALS_CONCEDED_COLUMN,
        window=window,
    )
    data["team_clean_sheet_rate_last_5"] = _previous_team_rolling_mean(
        data,
        source_column="team_clean_sheet",
        window=window,
    )

    opponent_form = data[
        [
            SEASON_COLUMN,
            GAMEWEEK_COLUMN,
            "team",
            "team_goals_scored_mean_last_5",
            "team_goals_conceded_mean_last_5",
            "team_clean_sheet_rate_last_5",
        ]
    ].rename(
        columns={
            "team": "opponent_team",
            "team_goals_scored_mean_last_5": "opponent_goals_scored_mean_last_5",
            "team_goals_conceded_mean_last_5": "opponent_goals_conceded_mean_last_5",
            "team_clean_sheet_rate_last_5": "opponent_clean_sheet_rate_last_5",
        }
    )
    data = data.merge(
        opponent_form,
        on=[SEASON_COLUMN, GAMEWEEK_COLUMN, "opponent_team"],
        how="left",
    )
    return data.drop(columns=["team_clean_sheet"]).sort_values(
        [SEASON_COLUMN, GAMEWEEK_COLUMN, "team"]
    ).reset_index(drop=True)


def build_team_strength_features(
    player_gameweeks: pd.DataFrame,
    *,
    team_season_priors: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build leakage-safe numeric team-strength features for player rows."""
    team_gameweeks = create_team_gameweek_table(player_gameweeks)
    with_elo = add_elo_features(team_gameweeks, team_season_priors=team_season_priors)

    feature_columns = [
        SEASON_COLUMN,
        GAMEWEEK_COLUMN,
        "team",
        "opponent_team",
        "pre_gw_team_elo",
        "pre_gw_opponent_elo",
        "elo_difference",
        "home_adjusted_elo_difference",
    ]
    features = with_elo[feature_columns].rename(
        columns={
            "pre_gw_team_elo": "team_elo_pre_gw",
            "pre_gw_opponent_elo": "opponent_elo_pre_gw",
        }
    )

    identifiers = detect_team_identifier_columns(player_gameweeks)
    player_keys = pd.DataFrame(
        {
            SEASON_COLUMN: player_gameweeks[SEASON_COLUMN],
            GAMEWEEK_COLUMN: player_gameweeks[GAMEWEEK_COLUMN],
            "team": player_gameweeks[identifiers.team].map(normalize_team_identifier),
        },
        index=player_gameweeks.index,
    )
    if identifiers.opponent_team is not None:
        player_keys["opponent_team"] = player_gameweeks[identifiers.opponent_team].map(
            normalize_team_identifier
        )
    else:
        player_keys["opponent_team"] = pd.NA

    merged = player_keys.merge(
        features,
        on=[SEASON_COLUMN, GAMEWEEK_COLUMN, "team", "opponent_team"],
        how="left",
    )
    return merged.drop(columns=[SEASON_COLUMN, GAMEWEEK_COLUMN, "team", "opponent_team"])
