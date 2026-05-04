from pathlib import Path
import shutil

import pandas as pd

from data.sync_fpl_api import (
    detect_local_gameweeks,
    detect_sync_status,
    gameweeks_from_bootstrap,
    local_merged_gw_path,
    write_sync_report,
)


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


class FakeSession:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.urls: list[str] = []

    def get(self, url: str, timeout: int) -> FakeResponse:
        self.urls.append(url)
        return FakeResponse(self.payload)


def clean_scratch(name: str) -> Path:
    path = Path("tests") / f".tmp_{name}"
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


def bootstrap_payload() -> dict:
    return {
        "events": [
            {"id": 1, "finished": True, "data_checked": True},
            {"id": 2, "finished": False, "data_checked": True},
            {"id": 3, "finished": False, "data_checked": False},
            {"id": 4, "finished": False, "data_checked": False},
        ]
    }


def test_gameweeks_from_bootstrap_separates_completed_and_unfinished() -> None:
    completed, unfinished = gameweeks_from_bootstrap(bootstrap_payload())

    assert completed == (1, 2)
    assert unfinished == (3, 4)


def test_detect_local_gameweeks_returns_empty_when_file_missing() -> None:
    assert detect_local_gameweeks(Path("tests/.missing/merged_gw_api.parquet")) == ()


def test_detect_local_gameweeks_reads_unique_gw_values() -> None:
    scratch = clean_scratch("sync_fpl_api_local")
    try:
        path = scratch / "merged_gw_api.parquet"
        pd.DataFrame({"gw": [1, 1, 2]}).to_parquet(path, index=False)

        assert detect_local_gameweeks(path) == (1, 2)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_detect_sync_status_computes_missing_gameweeks() -> None:
    scratch = clean_scratch("sync_fpl_api_status")
    try:
        local_path = local_merged_gw_path(scratch, "2025-26")
        local_path.parent.mkdir(parents=True)
        pd.DataFrame({"gw": [1]}).to_parquet(local_path, index=False)
        session = FakeSession(bootstrap_payload())

        status = detect_sync_status(
            season="2025-26",
            data_root=scratch,
            session=session,
            retries=1,
        )

        assert status.season == "2025-26"
        assert status.completed_api_gameweeks == (1, 2)
        assert status.local_gameweeks == (1,)
        assert status.missing_gameweeks == (2,)
        assert status.unfinished_api_gameweeks == (3, 4)
        assert session.urls == ["https://fantasy.premierleague.com/api/bootstrap-static/"]
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_write_sync_report_contains_required_sections() -> None:
    scratch = clean_scratch("sync_fpl_api_report")
    try:
        status = detect_sync_status(
            season="2025-26",
            data_root=scratch,
            session=FakeSession(bootstrap_payload()),
            retries=1,
        )
        report_path = scratch / "report.md"

        write_sync_report(status, output_path=report_path)

        text = report_path.read_text(encoding="utf-8")
        assert "FPL API Sync Report" in text
        assert "completed API gameweeks" in text
        assert "missing gameweeks" in text
        assert "unfinished gameweeks ignored" in text
        assert "Dry-run sync detection only" in text
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
