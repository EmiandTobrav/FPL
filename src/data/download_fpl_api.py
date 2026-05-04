"""Download and normalize official Fantasy Premier League API data."""

from __future__ import annotations

import argparse
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import requests


LOGGER = logging.getLogger(__name__)

BASE_URL = "https://fantasy.premierleague.com/api"
DEFAULT_OUTPUT_DIR = Path("data")
DEFAULT_REPORT_PATH = Path("reports/fpl_api_download_report.md")
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_RETRIES = 3
DEFAULT_MAX_WORKERS = 8


class FplApiDownloadError(RuntimeError):
    """Raised when official FPL API data cannot be downloaded or normalized."""


@dataclass(frozen=True)
class FplApiPaths:
    raw_dir: Path
    interim_dir: Path


@dataclass
class FplApiDownloadSummary:
    season: str
    detected_season: str
    player_count: int = 0
    team_count: int = 0
    fixture_count: int = 0
    completed_gameweeks: list[int] = field(default_factory=list)
    raw_files_written: list[Path] = field(default_factory=list)
    normalized_tables_written: list[Path] = field(default_factory=list)
    failed_requests: list[str] = field(default_factory=list)


def detect_current_fpl_season(today: date | None = None) -> str:
    """Return the likely FPL season label for the current date."""
    current = today or date.today()
    start_year = current.year if current.month >= 7 else current.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def api_paths(output_dir: Path, season: str) -> FplApiPaths:
    return FplApiPaths(
        raw_dir=output_dir / "raw" / "fpl_api" / season,
        interim_dir=output_dir / "interim" / "fpl_api" / season,
    )


def _json_path_for_endpoint(raw_dir: Path, endpoint_name: str, identifier: int | None = None) -> Path:
    if identifier is None:
        return raw_dir / f"{endpoint_name}.json"
    subdir = raw_dir / endpoint_name
    return subdir / f"{identifier}.json"


def fetch_json(
    url: str,
    *,
    session: requests.Session | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    retries: int = DEFAULT_RETRIES,
) -> Any:
    """Fetch one JSON response with simple retry handling."""
    client = session or requests.Session()
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = client.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2 ** (attempt - 1), 5))
    raise FplApiDownloadError(f"Failed to fetch {url} after {retries} attempts: {last_error}")


def load_or_fetch_json(
    url: str,
    raw_path: Path,
    *,
    session: requests.Session | None = None,
    force: bool = False,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    retries: int = DEFAULT_RETRIES,
) -> tuple[Any, bool]:
    """Load cached raw JSON unless force is enabled; otherwise download it."""
    if raw_path.exists() and not force:
        return json.loads(raw_path.read_text(encoding="utf-8")), False

    data = fetch_json(url, session=session, timeout=timeout, retries=retries)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return data, True


def completed_gameweeks(bootstrap: dict[str, Any]) -> list[int]:
    """Return completed gameweek ids from bootstrap-static events."""
    events = bootstrap.get("events", [])
    return sorted(
        int(event["id"])
        for event in events
        if event.get("finished") or event.get("data_checked")
    )


def normalize_bootstrap_static(bootstrap: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Normalize bootstrap-static into stable tables."""
    element_stats = bootstrap.get("element_stats", [])
    chips = bootstrap.get("chips", [])
    phases = bootstrap.get("phases", [])
    game_settings = bootstrap.get("game_settings", {})
    game_config = bootstrap.get("game_config", {})
    return {
        "bootstrap_static": pd.DataFrame(
            [
                {
                    "total_players": bootstrap.get("total_players"),
                    "element_stats_count": len(element_stats),
                    "chips_count": len(chips),
                    "phases_count": len(phases),
                    "game_settings_json": json.dumps(game_settings, sort_keys=True),
                    "game_config_json": json.dumps(game_config, sort_keys=True),
                }
            ]
        ),
        "events": pd.json_normalize(bootstrap.get("events", [])),
        "teams": pd.json_normalize(bootstrap.get("teams", [])),
        "elements": pd.json_normalize(bootstrap.get("elements", [])),
    }


def normalize_fixtures(fixtures: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.json_normalize(fixtures)


def normalize_live_gameweek_stats(live_by_gameweek: dict[int, dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for gameweek, payload in sorted(live_by_gameweek.items()):
        for element in payload.get("elements", []):
            row = {"gw": gameweek, "element": element.get("id"), "modified": element.get("modified")}
            stats = element.get("stats", {})
            row.update(stats)
            if "explain" in element:
                row["explain_json"] = json.dumps(element["explain"], sort_keys=True)
            rows.append(row)
    return pd.DataFrame(rows)


def normalize_element_summaries(
    summaries: dict[int, dict[str, Any]],
    *,
    season: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    history_rows: list[dict[str, Any]] = []
    fixture_rows: list[dict[str, Any]] = []
    for player_id, payload in sorted(summaries.items()):
        for row in payload.get("history", []):
            normalized = dict(row)
            normalized["season"] = season
            normalized["gw"] = normalized.get("round")
            normalized["GW"] = normalized.get("round")
            history_rows.append(normalized)
        for row in payload.get("fixtures", []):
            normalized = dict(row)
            normalized["season"] = season
            normalized["element"] = player_id
            normalized["gw"] = normalized.get("event")
            normalized["GW"] = normalized.get("event")
            fixture_rows.append(normalized)
    return pd.DataFrame(history_rows), pd.DataFrame(fixture_rows)


def write_normalized_tables(
    tables: dict[str, pd.DataFrame],
    interim_dir: Path,
) -> list[Path]:
    interim_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, table in tables.items():
        path = interim_dir / f"{name}.parquet"
        table.to_parquet(path, index=False)
        written.append(path)
    return written


def _fetch_live_payload(
    gameweek: int,
    *,
    paths: FplApiPaths,
    session: requests.Session | None,
    force: bool,
    timeout: int,
    retries: int,
) -> tuple[int, dict[str, Any], Path | None]:
    path = _json_path_for_endpoint(paths.raw_dir, "event_live", gameweek)
    payload, wrote = load_or_fetch_json(
        f"{BASE_URL}/event/{gameweek}/live/",
        path,
        session=session,
        force=force,
        timeout=timeout,
        retries=retries,
    )
    return gameweek, payload, path if wrote else None


def _fetch_element_summary_payload(
    player_id: int,
    *,
    paths: FplApiPaths,
    session: requests.Session | None,
    force: bool,
    timeout: int,
    retries: int,
) -> tuple[int, dict[str, Any], Path | None]:
    path = _json_path_for_endpoint(paths.raw_dir, "element_summary", player_id)
    payload, wrote = load_or_fetch_json(
        f"{BASE_URL}/element-summary/{player_id}/",
        path,
        session=session,
        force=force,
        timeout=timeout,
        retries=retries,
    )
    return player_id, payload, path if wrote else None


def fetch_many(
    items: list[int],
    worker,
    *,
    max_workers: int,
) -> tuple[dict[int, dict[str, Any]], list[Path], list[str]]:
    """Fetch many integer-keyed payloads with isolated failures."""
    payloads: dict[int, dict[str, Any]] = {}
    raw_written: list[Path] = []
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, item): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                key, payload, raw_path = future.result()
                payloads[key] = payload
                if raw_path is not None:
                    raw_written.append(raw_path)
            except Exception as exc:  # noqa: BLE001 - report all per-request failures
                failures.append(f"{item}: {exc}")
    return payloads, raw_written, failures


def download_fpl_api_data(
    *,
    season: str | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    force: bool = False,
    max_workers: int = DEFAULT_MAX_WORKERS,
    skip_element_summary: bool = False,
    session: requests.Session | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    retries: int = DEFAULT_RETRIES,
) -> FplApiDownloadSummary:
    """Download raw FPL API responses and write normalized parquet tables."""
    detected_season = detect_current_fpl_season()
    season_label = season or detected_season
    paths = api_paths(output_dir, season_label)
    raw_written: list[Path] = []

    bootstrap, wrote = load_or_fetch_json(
        f"{BASE_URL}/bootstrap-static/",
        _json_path_for_endpoint(paths.raw_dir, "bootstrap_static"),
        session=session,
        force=force,
        timeout=timeout,
        retries=retries,
    )
    if wrote:
        raw_written.append(_json_path_for_endpoint(paths.raw_dir, "bootstrap_static"))

    fixtures, wrote = load_or_fetch_json(
        f"{BASE_URL}/fixtures/",
        _json_path_for_endpoint(paths.raw_dir, "fixtures"),
        session=session,
        force=force,
        timeout=timeout,
        retries=retries,
    )
    if wrote:
        raw_written.append(_json_path_for_endpoint(paths.raw_dir, "fixtures"))

    gameweeks = completed_gameweeks(bootstrap)
    live_payloads, live_written, live_failures = fetch_many(
        gameweeks,
        lambda gameweek: _fetch_live_payload(
            gameweek,
            paths=paths,
            session=session,
            force=force,
            timeout=timeout,
            retries=retries,
        ),
        max_workers=max_workers,
    )
    raw_written.extend(live_written)

    elements = bootstrap.get("elements", [])
    player_ids = sorted(int(element["id"]) for element in elements if element.get("id") is not None)
    summaries: dict[int, dict[str, Any]] = {}
    summary_failures: list[str] = []
    if not skip_element_summary:
        summaries, summary_written, summary_failures = fetch_many(
            player_ids,
            lambda player_id: _fetch_element_summary_payload(
                player_id,
                paths=paths,
                session=session,
                force=force,
                timeout=timeout,
                retries=retries,
            ),
            max_workers=max_workers,
        )
        raw_written.extend(summary_written)

    bootstrap_tables = normalize_bootstrap_static(bootstrap)
    history, upcoming = normalize_element_summaries(summaries, season=season_label)
    normalized_tables = {
        **bootstrap_tables,
        "fixtures": normalize_fixtures(fixtures),
        "live_gameweek_stats": normalize_live_gameweek_stats(live_payloads),
        "player_gameweek_history": history,
        "upcoming_player_fixtures": upcoming,
    }
    normalized_written = write_normalized_tables(normalized_tables, paths.interim_dir)

    summary = FplApiDownloadSummary(
        season=season_label,
        detected_season=detected_season,
        player_count=len(elements),
        team_count=len(bootstrap.get("teams", [])),
        fixture_count=len(fixtures),
        completed_gameweeks=gameweeks,
        raw_files_written=sorted(raw_written),
        normalized_tables_written=sorted(normalized_written),
        failed_requests=[*live_failures, *summary_failures],
    )
    return summary


def write_download_report(
    summary: FplApiDownloadSummary,
    *,
    output_path: Path = DEFAULT_REPORT_PATH,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = ", ".join(map(str, summary.completed_gameweeks)) or "None"
    raw_files = [f"- `{path.as_posix()}`" for path in summary.raw_files_written] or ["- None"]
    tables = [f"- `{path.as_posix()}`" for path in summary.normalized_tables_written] or ["- None"]
    failures = [f"- {failure}" for failure in summary.failed_requests] or ["- None"]
    output_path.write_text(
        "\n".join(
            [
                "# FPL API Download Report",
                "",
                f"Detected season: `{summary.detected_season}`",
                f"Requested season: `{summary.season}`",
                "",
                "| item | count |",
                "| --- | ---: |",
                f"| players | {summary.player_count} |",
                f"| teams | {summary.team_count} |",
                f"| fixtures | {summary.fixture_count} |",
                f"| completed gameweeks | {len(summary.completed_gameweeks)} |",
                f"| failed requests | {len(summary.failed_requests)} |",
                "",
                f"Completed gameweeks downloaded: {completed}",
                "",
                "## Raw Files Written",
                "",
                *raw_files,
                "",
                "## Normalized Tables Written",
                "",
                *tables,
                "",
                "## Failed Requests",
                "",
                *failures,
                "",
            ]
        ),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default=None, help="FPL season label, e.g. 2025-26.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Redownload even when raw JSON exists.")
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS)
    parser.add_argument(
        "--skip-element-summary",
        action="store_true",
        help="Skip element-summary calls for faster bootstrap/fixtures/live downloads.",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    args = parse_args()
    summary = download_fpl_api_data(
        season=args.season,
        output_dir=args.output_dir,
        force=args.force,
        max_workers=args.max_workers,
        skip_element_summary=args.skip_element_summary,
        timeout=args.timeout,
        retries=args.retries,
    )
    write_download_report(summary, output_path=args.report)
    print(f"Season: {summary.season}")
    print(f"Players: {summary.player_count}")
    print(f"Teams: {summary.team_count}")
    print(f"Fixtures: {summary.fixture_count}")
    print(f"Completed gameweeks: {summary.completed_gameweeks}")
    print(f"Failed requests: {len(summary.failed_requests)}")
    print(f"Wrote report: {args.report}")


if __name__ == "__main__":
    main()
