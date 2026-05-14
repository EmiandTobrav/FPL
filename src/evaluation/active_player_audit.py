"""Audit active versus inactive player rows in the modelling dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from evaluation.backtest import POSITION_COLUMN, TARGET_COLUMN, normalize_position_column


DEFAULT_INPUT_PATH = Path("data/processed/modeling_dataset.parquet")
DEFAULT_CSV_PATH = Path("reports/active_player_audit.csv")
DEFAULT_MARKDOWN_PATH = Path("reports/active_player_audit.md")
ACTIVE_FEATURE_COLUMNS = ("minutes_mean_last_3", "minutes_mean_last_5", "starts_last_5")
POSITIONS = ("GK", "DEF", "MID", "FWD")
TOP_K_VALUES = (10, 20, 50)


class ActivePlayerAuditError(ValueError):
    """Raised when active-player audit inputs are incomplete."""


def read_dataset(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def gw_bucket(gw: object) -> str:
    gameweek = pd.to_numeric(pd.Series([gw]), errors="coerce").iloc[0]
    if pd.isna(gameweek):
        return "unknown"
    if int(gameweek) <= 5:
        return "GW1-5"
    if int(gameweek) <= 10:
        return "GW6-10"
    return "GW11+"


def add_active_player_flag(frame: pd.DataFrame) -> pd.DataFrame:
    """Add leakage-safe active/inactive labels from rolling minutes and starts."""
    missing = [column for column in ACTIVE_FEATURE_COLUMNS if column not in frame.columns]
    if missing:
        raise ActivePlayerAuditError(f"Missing active-player feature columns: {missing}")

    data = normalize_position_column(frame).copy()
    minutes_3 = pd.to_numeric(data["minutes_mean_last_3"], errors="coerce").fillna(0)
    minutes_5 = pd.to_numeric(data["minutes_mean_last_5"], errors="coerce").fillna(0)
    starts_5 = pd.to_numeric(data["starts_last_5"], errors="coerce").fillna(0)
    data["is_active"] = minutes_3.gt(0) | minutes_5.ge(30) | starts_5.gt(0)
    data["active_status"] = data["is_active"].map({True: "active", False: "inactive"})
    if "gw" in data.columns:
        data["gw_bucket"] = data["gw"].map(gw_bucket)
    else:
        data["gw_bucket"] = "unknown"
    return data


def _segment_summary(data: pd.DataFrame, *, segment_type: str, segment: str) -> pd.DataFrame:
    rows = []
    for status in ("active", "inactive"):
        subset = data.loc[data["active_status"].eq(status)]
        target = pd.to_numeric(subset[TARGET_COLUMN], errors="coerce")
        non_missing_target = target.dropna()
        rows.append(
            {
                "section": "segment_summary",
                "segment_type": segment_type,
                "segment": segment,
                "active_status": status,
                "rows": int(len(subset)),
                "avg_next_gw_points": float(non_missing_target.mean())
                if not non_missing_target.empty
                else float("nan"),
                "nonzero_next_gw_points_rows": int(non_missing_target.gt(0).sum()),
                "nonzero_next_gw_points_share": float(non_missing_target.gt(0).mean())
                if not non_missing_target.empty
                else float("nan"),
                "top_k": pd.NA,
                "inactive_rows_in_top_k": pd.NA,
                "inactive_share_in_top_k": pd.NA,
            }
        )
    return pd.DataFrame(rows)


def summarize_active_rows(data: pd.DataFrame) -> pd.DataFrame:
    """Summarize active/inactive rows overall and by season/GW bucket/position."""
    summaries = [_segment_summary(data, segment_type="overall", segment="all")]
    if "season" in data.columns:
        for season, season_frame in data.groupby(data["season"].astype(str), sort=True):
            summaries.append(_segment_summary(season_frame, segment_type="season", segment=str(season)))
    for bucket, bucket_frame in data.groupby("gw_bucket", sort=True):
        summaries.append(_segment_summary(bucket_frame, segment_type="gw_bucket", segment=str(bucket)))
    if POSITION_COLUMN in data.columns:
        for position in POSITIONS:
            position_frame = data.loc[data[POSITION_COLUMN].astype(str).eq(position)]
            if not position_frame.empty:
                summaries.append(_segment_summary(position_frame, segment_type="position", segment=position))
    return pd.concat(summaries, ignore_index=True, sort=False)


def summarize_top_actual_scorers(data: pd.DataFrame) -> pd.DataFrame:
    """Count inactive rows that appear among top-k actual target scorers per season/GW."""
    required = {"season", "gw", TARGET_COLUMN, "active_status"}
    if not required.issubset(data.columns):
        return pd.DataFrame()
    rows = []
    scored = data.dropna(subset=[TARGET_COLUMN]).copy()
    scored[TARGET_COLUMN] = pd.to_numeric(scored[TARGET_COLUMN], errors="coerce")
    scored = scored.dropna(subset=[TARGET_COLUMN])
    for top_k in TOP_K_VALUES:
        top_frames = []
        for _, group in scored.groupby(["season", "gw"], sort=True):
            top_frames.append(group.nlargest(top_k, TARGET_COLUMN, keep="all"))
        if not top_frames:
            continue
        top = pd.concat(top_frames, ignore_index=True, sort=False)
        inactive_rows = int(top["active_status"].eq("inactive").sum())
        rows.append(
            {
                "section": "top_actual_scorers",
                "segment_type": "top_actual_by_season_gw",
                "segment": f"top_{top_k}",
                "active_status": "inactive",
                "rows": int(len(top)),
                "avg_next_gw_points": float(top[TARGET_COLUMN].mean()),
                "nonzero_next_gw_points_rows": pd.NA,
                "nonzero_next_gw_points_share": pd.NA,
                "top_k": top_k,
                "inactive_rows_in_top_k": inactive_rows,
                "inactive_share_in_top_k": float(inactive_rows / len(top)) if len(top) else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def build_active_player_audit(frame: pd.DataFrame) -> pd.DataFrame:
    data = add_active_player_flag(frame).dropna(subset=[TARGET_COLUMN]).copy()
    summary = summarize_active_rows(data)
    top_actual = summarize_top_actual_scorers(data)
    if top_actual.empty:
        return summary
    return pd.concat([summary, top_actual], ignore_index=True, sort=False)


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


def _pivot_counts(audit: pd.DataFrame, segment_type: str) -> pd.DataFrame:
    subset = audit.loc[
        audit["section"].eq("segment_summary") & audit["segment_type"].eq(segment_type)
    ]
    if subset.empty:
        return pd.DataFrame()
    return (
        subset.pivot_table(
            index="segment",
            columns="active_status",
            values="rows",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )


def _overall_table(audit: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "active_status",
        "rows",
        "avg_next_gw_points",
        "nonzero_next_gw_points_share",
    ]
    return audit.loc[
        audit["section"].eq("segment_summary")
        & audit["segment_type"].eq("overall")
        & audit["segment"].eq("all"),
        columns,
    ].copy()


def _top_actual_table(audit: pd.DataFrame) -> pd.DataFrame:
    columns = ["segment", "rows", "inactive_rows_in_top_k", "inactive_share_in_top_k"]
    return audit.loc[audit["section"].eq("top_actual_scorers"), columns].copy()


def _recommendation(audit: pd.DataFrame) -> str:
    overall = _overall_table(audit)
    if overall.empty:
        return "Investigate active-player filtering after confirming active feature coverage."
    inactive = overall.loc[overall["active_status"].eq("inactive")]
    active = overall.loc[overall["active_status"].eq("active")]
    inactive_share = (
        float(inactive["nonzero_next_gw_points_share"].iloc[0])
        if not inactive.empty and pd.notna(inactive["nonzero_next_gw_points_share"].iloc[0])
        else 0.0
    )
    inactive_avg = float(inactive["avg_next_gw_points"].iloc[0]) if not inactive.empty else 0.0
    active_avg = float(active["avg_next_gw_points"].iloc[0]) if not active.empty else 0.0
    if inactive_share < 0.10 and inactive_avg < active_avg * 0.35:
        return (
            "Test filtering training and weekly candidate rows to likely active players using "
            "`minutes_mean_last_3 > 0 OR minutes_mean_last_5 >= 30 OR starts_last_5 > 0`."
        )
    return (
        "Keep inactive rows in the next modelling experiment, but add the active flag as a "
        "diagnostic or feature candidate before filtering."
    )


def write_reports(audit: pd.DataFrame, csv_path: Path, markdown_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(csv_path, index=False)
    markdown_path.write_text(
        "\n".join(
            [
                "# Active Player Audit",
                "",
                "Active rule: `minutes_mean_last_3 > 0 OR minutes_mean_last_5 >= 30 OR starts_last_5 > 0`.",
                "",
                "## Overall Active Vs Inactive",
                "",
                _markdown_table(_overall_table(audit)),
                "",
                "## Counts By Season",
                "",
                _markdown_table(_pivot_counts(audit, "season")),
                "",
                "## Counts By GW Bucket",
                "",
                _markdown_table(_pivot_counts(audit, "gw_bucket")),
                "",
                "## Counts By Position",
                "",
                _markdown_table(_pivot_counts(audit, "position")),
                "",
                "## Inactive Rows In Top Actual Scorers",
                "",
                _markdown_table(_top_actual_table(audit)),
                "",
                "## Recommendation",
                "",
                _recommendation(audit),
                "",
            ]
        ),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audit = build_active_player_audit(read_dataset(args.input))
    write_reports(audit, args.csv_output, args.markdown_output)
    print(f"Wrote: {args.csv_output}")
    print(f"Wrote: {args.markdown_output}")


if __name__ == "__main__":
    main()
