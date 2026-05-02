"""Download and combine Vaastav Fantasy Premier League gameweek data."""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests


LOGGER = logging.getLogger(__name__)

REPO = "vaastav/Fantasy-Premier-League"
BRANCH = "master"
GITHUB_CONTENTS_URL = f"https://api.github.com/repos/{REPO}/contents/data"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/data"
SEASON_PATTERN = re.compile(r"^\d{4}-\d{2}$")

DEFAULT_RAW_ROOT = Path("data/raw/vaastav")
DEFAULT_INTERIM_PATH = Path("data/interim/all_merged_gw.parquet")


class VaastavDownloadError(RuntimeError):
    """Raised when Vaastav data cannot be downloaded or combined."""


def discover_available_seasons(
    session: requests.Session | None = None,
    *,
    branch: str = BRANCH,
    timeout: int = 30,
) -> list[str]:
    """Return season directories available in the Vaastav repository."""
    client = session or requests.Session()
    response = client.get(GITHUB_CONTENTS_URL, params={"ref": branch}, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise VaastavDownloadError(
            f"Could not list seasons from {GITHUB_CONTENTS_URL}: {exc}"
        ) from exc

    contents = response.json()
    seasons = sorted(
        item["name"]
        for item in contents
        if item.get("type") == "dir" and SEASON_PATTERN.match(item.get("name", ""))
    )
    if not seasons:
        raise VaastavDownloadError(f"No season directories found in {GITHUB_CONTENTS_URL}")
    return seasons


def merged_gw_url(season: str, *, branch: str = BRANCH) -> str:
    """Build the raw GitHub URL for a season's merged gameweek CSV."""
    return f"https://raw.githubusercontent.com/{REPO}/{branch}/data/{season}/gws/merged_gw.csv"


def download_merged_gw(
    season: str,
    destination: Path,
    session: requests.Session | None = None,
    *,
    branch: str = BRANCH,
    timeout: int = 60,
) -> bool:
    """Download a season's merged_gw.csv.

    Returns False for missing files so historical gaps can be skipped with a
    warning. Other request failures are also reported and skipped, allowing the
    remaining seasons to continue.
    """
    client = session or requests.Session()
    url = merged_gw_url(season, branch=branch)
    response = client.get(url, timeout=timeout)

    if response.status_code == 404:
        LOGGER.warning("Skipping %s: merged_gw.csv not found at %s", season, url)
        return False

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        LOGGER.warning("Skipping %s: failed to download %s (%s)", season, url, exc)
        return False

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)
    LOGGER.info("Downloaded %s to %s", season, destination)
    return True


def add_required_columns(frame: pd.DataFrame, season: str) -> pd.DataFrame:
    """Add normalized season and gw columns to a Vaastav merged GW dataframe."""
    data = frame.copy()
    data["season"] = season

    if "gw" in data.columns:
        data["gw"] = data["gw"]
    elif "GW" in data.columns:
        data["gw"] = data["GW"]
    else:
        raise VaastavDownloadError(
            f"Season {season} does not contain a GW or gw column; cannot add gw."
        )

    return data


def player_key_column(frame: pd.DataFrame) -> str:
    """Choose the most stable available player identifier column."""
    for column in ("element", "id", "name"):
        if column in frame.columns:
            return column
    raise VaastavDownloadError(
        "Cannot validate player-season-gw duplicates: no element, id, or name column found."
    )


def duplicate_key_counts(frame: pd.DataFrame) -> pd.Series:
    """Count rows per player-season-gw key for duplicate validation."""
    player_col = player_key_column(frame)
    return frame.groupby([player_col, "season", "gw"], dropna=False).size()


def validate_no_introduced_duplicates(source_frames: Iterable[pd.DataFrame], combined: pd.DataFrame) -> None:
    """Ensure combining did not create duplicate player-season-gw rows.

    Duplicate rows are allowed only when they already exist in the source frames.
    """
    sources = list(source_frames)
    if not sources:
        raise VaastavDownloadError("Cannot validate duplicates without source data.")

    expected = duplicate_key_counts(pd.concat(sources, ignore_index=True)).sort_index()
    actual = duplicate_key_counts(combined).sort_index()

    if not actual.equals(expected):
        raise VaastavDownloadError(
            "Combined data contains player-season-gw duplicates that do not match source data."
        )


def load_season_file(path: Path, season: str) -> pd.DataFrame:
    """Load one downloaded merged_gw.csv and add required columns."""
    for encoding in ("utf-8", "latin1"):
        try:
            return add_required_columns(pd.read_csv(path, encoding=encoding), season)
        except UnicodeDecodeError:
            continue
    raise VaastavDownloadError(f"Could not decode {path} using supported encodings.")


def combine_season_files(
    seasons: Iterable[str],
    *,
    raw_root: Path = DEFAULT_RAW_ROOT,
    output_path: Path = DEFAULT_INTERIM_PATH,
) -> pd.DataFrame:
    """Combine downloaded season CSVs and write the parquet output."""
    frames: list[pd.DataFrame] = []
    for season in seasons:
        path = raw_root / season / "merged_gw.csv"
        if not path.exists():
            LOGGER.warning("Skipping %s: expected downloaded file is missing at %s", season, path)
            continue
        frames.append(load_season_file(path, season))

    if not frames:
        raise VaastavDownloadError("No merged_gw.csv files were available to combine.")

    combined = pd.concat(frames, ignore_index=True)
    validate_no_introduced_duplicates(frames, combined)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(output_path, index=False)
    LOGGER.info("Wrote %s rows to %s", len(combined), output_path)
    return combined


def download_all_available_seasons(
    *,
    raw_root: Path = DEFAULT_RAW_ROOT,
    output_path: Path = DEFAULT_INTERIM_PATH,
    session: requests.Session | None = None,
    branch: str = BRANCH,
) -> pd.DataFrame:
    """Download all available Vaastav merged_gw.csv files and combine them."""
    client = session or requests.Session()
    seasons = discover_available_seasons(client, branch=branch)
    downloaded: list[str] = []

    for season in seasons:
        destination = raw_root / season / "merged_gw.csv"
        if download_merged_gw(season, destination, client, branch=branch):
            downloaded.append(season)

    missing = sorted(set(seasons) - set(downloaded))
    if missing:
        LOGGER.warning("Skipped %d seasons without usable merged_gw.csv: %s", len(missing), missing)

    if not downloaded:
        raise VaastavDownloadError("No Vaastav merged_gw.csv files were downloaded.")

    return combine_season_files(downloaded, raw_root=raw_root, output_path=output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_INTERIM_PATH)
    parser.add_argument("--branch", default=BRANCH)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    args = parse_args()
    download_all_available_seasons(raw_root=args.raw_root, output_path=args.output, branch=args.branch)


if __name__ == "__main__":
    main()
