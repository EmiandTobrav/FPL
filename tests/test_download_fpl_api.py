from __future__ import annotations

from datetime import date
from pathlib import Path
import shutil

import pandas as pd

from data.download_fpl_api import (
    completed_gameweeks,
    detect_current_fpl_season,
    download_fpl_api_data,
    normalize_element_summaries,
    write_download_report,
)


def clean_scratch(name: str) -> Path:
    path = Path("tests") / f".tmp_{name}"
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


class FakeResponse:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> object:
        return self.payload


class FakeSession:
    def __init__(self) -> None:
        self.urls: list[str] = []

    def get(self, url: str, timeout: int) -> FakeResponse:
        self.urls.append(url)
        if url.endswith("/bootstrap-static/"):
            return FakeResponse(
                {
                    "events": [
                        {"id": 1, "finished": True, "data_checked": True},
                        {"id": 2, "finished": False, "data_checked": False},
                    ],
                    "teams": [{"id": 1, "name": "Arsenal"}],
                    "elements": [
                        {
                            "id": 11,
                            "web_name": "Player",
                            "element_type": 3,
                            "team": 1,
                            "now_cost": 75,
                        }
                    ],
                    "element_types": [{"id": 3, "singular_name_short": "MID"}],
                    "element_stats": [],
                    "chips": [],
                    "phases": [],
                    "game_settings": {},
                    "game_config": {},
                    "total_players": 1,
                }
            )
        if url.endswith("/fixtures/"):
            return FakeResponse(
                [
                    {
                        "id": 100,
                        "event": 1,
                        "team_h": 1,
                        "team_a": 2,
                        "team_h_score": 2,
                        "team_a_score": 1,
                    }
                ]
            )
        if url.endswith("/event/1/live/"):
            return FakeResponse(
                {
                    "elements": [
                        {
                            "id": 11,
                            "modified": False,
                            "stats": {"total_points": 6, "minutes": 90, "bonus": 1, "bps": 20},
                            "explain": [{"fixture": 100, "stats": []}],
                        }
                    ]
                }
            )
        if url.endswith("/element-summary/11/"):
            return FakeResponse(
                {
                    "history": [
                        {
                            "element": 11,
                            "round": 1,
                            "fixture": 100,
                            "opponent_team": 2,
                            "was_home": True,
                            "total_points": 6,
                            "minutes": 90,
                            "bonus": 1,
                            "bps": 20,
                            "selected": 1000,
                            "transfers_in": 100,
                            "transfers_out": 50,
                            "transfers_balance": 50,
                            "value": 75,
                        }
                    ],
                    "fixtures": [
                        {
                            "id": 101,
                            "event": 2,
                            "is_home": False,
                            "team_h": 2,
                            "team_a": 1,
                        }
                    ],
                    "history_past": [],
                }
            )
        raise AssertionError(f"Unexpected URL: {url}")


def test_detect_current_fpl_season_uses_july_boundary() -> None:
    assert detect_current_fpl_season(date(2026, 5, 4)) == "2025-26"
    assert detect_current_fpl_season(date(2026, 8, 1)) == "2026-27"


def test_completed_gameweeks_uses_finished_or_data_checked() -> None:
    bootstrap = {
        "events": [
            {"id": 1, "finished": True, "data_checked": False},
            {"id": 2, "finished": False, "data_checked": True},
            {"id": 3, "finished": False, "data_checked": False},
        ]
    }

    assert completed_gameweeks(bootstrap) == [1, 2]


def test_normalize_element_summaries_adds_season_and_gw() -> None:
    history, upcoming = normalize_element_summaries(
        {
            11: {
                "history": [{"element": 11, "round": 1, "total_points": 6}],
                "fixtures": [{"id": 101, "event": 2}],
            }
        },
        season="2025-26",
    )

    assert history.loc[0, "season"] == "2025-26"
    assert history.loc[0, "gw"] == 1
    assert history.loc[0, "GW"] == 1
    assert upcoming.loc[0, "element"] == 11
    assert upcoming.loc[0, "gw"] == 2


def test_download_fpl_api_data_writes_raw_and_normalized_tables() -> None:
    session = FakeSession()
    scratch = clean_scratch("download_fpl_api")

    try:
        summary = download_fpl_api_data(
            season="2025-26",
            output_dir=scratch,
            session=session,
            max_workers=1,
            force=True,
        )

        raw_root = scratch / "raw" / "fpl_api" / "2025-26"
        interim_root = scratch / "interim" / "fpl_api" / "2025-26"

        assert summary.player_count == 1
        assert summary.team_count == 1
        assert summary.fixture_count == 1
        assert summary.completed_gameweeks == [1]
        assert not summary.failed_requests
        assert (raw_root / "bootstrap_static.json").exists()
        assert (raw_root / "fixtures.json").exists()
        assert (raw_root / "event_live" / "1.json").exists()
        assert (raw_root / "element_summary" / "11.json").exists()
        assert (interim_root / "bootstrap_static.parquet").exists()
        assert (interim_root / "fixtures.parquet").exists()
        assert (interim_root / "events.parquet").exists()
        assert (interim_root / "teams.parquet").exists()
        assert (interim_root / "elements.parquet").exists()
        assert (interim_root / "live_gameweek_stats.parquet").exists()
        assert (interim_root / "player_gameweek_history.parquet").exists()
        assert (interim_root / "upcoming_player_fixtures.parquet").exists()

        history = pd.read_parquet(interim_root / "player_gameweek_history.parquet")
        assert history.loc[0, "season"] == "2025-26"
        assert history.loc[0, "gw"] == 1
        assert "event/2/live" not in "\n".join(session.urls)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_skip_element_summary_writes_empty_history_tables() -> None:
    session = FakeSession()
    scratch = clean_scratch("download_fpl_api_skip_summary")

    try:
        download_fpl_api_data(
            season="2025-26",
            output_dir=scratch,
            session=session,
            max_workers=1,
            force=True,
            skip_element_summary=True,
        )

        interim_root = scratch / "interim" / "fpl_api" / "2025-26"
        history = pd.read_parquet(interim_root / "player_gameweek_history.parquet")
        upcoming = pd.read_parquet(interim_root / "upcoming_player_fixtures.parquet")

        assert history.empty
        assert upcoming.empty
        assert "element-summary" not in "\n".join(session.urls)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_write_download_report_includes_summary() -> None:
    session = FakeSession()
    scratch = clean_scratch("download_fpl_api_report")
    try:
        summary = download_fpl_api_data(
            season="2025-26",
            output_dir=scratch,
            session=session,
            max_workers=1,
            force=True,
            skip_element_summary=True,
        )
        report_path = scratch / "report.md"

        write_download_report(summary, output_path=report_path)

        text = report_path.read_text(encoding="utf-8")
        assert "FPL API Download Report" in text
        assert "2025-26" in text
        assert "Completed gameweeks downloaded: 1" in text
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
