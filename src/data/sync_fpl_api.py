"""Detect completed FPL API gameweeks missing from local adapted data."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from data.download_fpl_api import (
    BASE_URL,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    detect_current_fpl_season,
    fetch_json,
)


DEFAULT_DATA_ROOT = Path("data")
DEFAULT_REPORT_PATH = Path("reports/fpl_api_sync_report.md")


@dataclass(frozen=True)
class FplApiSyncStatus:
    season: str
    detected_season: str
    completed_api_gameweeks: tuple[int, ...]
    unfinished_api_gameweeks: tuple[int, ...]
    local_gameweeks: tuple[int, ...]
    missing_gameweeks: tuple[int, ...]
    local_path: Path


def gameweeks_from_bootstrap(bootstrap: dict[str, Any]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Return completed and unfinished FPL gameweeks from bootstrap-static."""
    completed: list[int] = []
    unfinished: list[int] = []
    for event in bootstrap.get("events", []):
        if event.get("id") is None:
            continue
        gameweek = int(event["id"])
        if event.get("finished") or event.get("data_checked"):
            completed.append(gameweek)
        else:
            unfinished.append(gameweek)
    return tuple(sorted(completed)), tuple(sorted(unfinished))


def local_merged_gw_path(data_root: Path, season: str) -> Path:
    return data_root / "interim" / "fpl_api" / season / "merged_gw_api.parquet"


def detect_local_gameweeks(path: Path) -> tuple[int, ...]:
    """Return gameweeks present in local merged_gw_api parquet, or empty when missing."""
    if not path.exists():
        return ()
    frame = pd.read_parquet(path, columns=None)
    if "gw" not in frame.columns:
        return ()
    gameweeks = pd.to_numeric(frame["gw"], errors="coerce").dropna().astype(int)
    return tuple(sorted(gameweeks.unique()))


def detect_sync_status(
    *,
    season: str | None = None,
    data_root: Path = DEFAULT_DATA_ROOT,
    session: requests.Session | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    retries: int = DEFAULT_RETRIES,
) -> FplApiSyncStatus:
    """Detect API completed gameweeks that are not present locally."""
    detected_season = detect_current_fpl_season()
    season_label = season or detected_season
    bootstrap = fetch_json(
        f"{BASE_URL}/bootstrap-static/",
        session=session,
        timeout=timeout,
        retries=retries,
    )
    completed, unfinished = gameweeks_from_bootstrap(bootstrap)
    local_path = local_merged_gw_path(data_root, season_label)
    local = detect_local_gameweeks(local_path)
    missing = tuple(sorted(set(completed).difference(local)))
    return FplApiSyncStatus(
        season=season_label,
        detected_season=detected_season,
        completed_api_gameweeks=completed,
        unfinished_api_gameweeks=unfinished,
        local_gameweeks=local,
        missing_gameweeks=missing,
        local_path=local_path,
    )


def _gameweek_list(values: tuple[int, ...]) -> str:
    return ", ".join(map(str, values)) or "None"


def write_sync_report(
    status: FplApiSyncStatus,
    *,
    output_path: Path = DEFAULT_REPORT_PATH,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(
            [
                "# FPL API Sync Report",
                "",
                f"Detected season: `{status.detected_season}`",
                f"Sync season: `{status.season}`",
                f"Local merged_gw_api path: `{status.local_path.as_posix()}`",
                "",
                "| item | gameweeks | count |",
                "| --- | --- | ---: |",
                (
                    "| completed API gameweeks | "
                    f"{_gameweek_list(status.completed_api_gameweeks)} | "
                    f"{len(status.completed_api_gameweeks)} |"
                ),
                (
                    "| local gameweeks | "
                    f"{_gameweek_list(status.local_gameweeks)} | "
                    f"{len(status.local_gameweeks)} |"
                ),
                (
                    "| missing gameweeks | "
                    f"{_gameweek_list(status.missing_gameweeks)} | "
                    f"{len(status.missing_gameweeks)} |"
                ),
                (
                    "| unfinished gameweeks ignored | "
                    f"{_gameweek_list(status.unfinished_api_gameweeks)} | "
                    f"{len(status.unfinished_api_gameweeks)} |"
                ),
                "",
                "Dry-run sync detection only. No raw API data, adapter rows, combined "
                "datasets, or model outputs are written by this command.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default=None, help="FPL season label, e.g. 2025-26.")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect missing gameweeks and write only the sync report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    status = detect_sync_status(
        season=args.season,
        data_root=args.data_root,
        timeout=args.timeout,
        retries=args.retries,
    )
    write_sync_report(status, output_path=args.report)
    print(f"Season: {status.season}")
    print(f"Completed API gameweeks: {_gameweek_list(status.completed_api_gameweeks)}")
    print(f"Local gameweeks: {_gameweek_list(status.local_gameweeks)}")
    print(f"Missing gameweeks: {_gameweek_list(status.missing_gameweeks)}")
    print(f"Unfinished gameweeks ignored: {_gameweek_list(status.unfinished_api_gameweeks)}")
    print(f"Wrote report: {args.report}")


if __name__ == "__main__":
    main()
