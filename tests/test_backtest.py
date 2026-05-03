from pathlib import Path
import shutil
import subprocess
import sys

import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.dummy import DummyRegressor

import evaluation.backtest as backtest_module
from evaluation.backtest import (
    DEFAULT_SUPPORTED_RESULTS_PATH,
    DEFAULT_SUPPORTED_SUMMARY_PATH,
    RAW_CURRENT_GW_OUTCOME_COLUMNS,
    RAW_TEAM_COLUMNS,
    SklearnModelSpec,
    add_baseline_prediction_features,
    add_position_interactions,
    ablation_feature_configurations,
    assert_feature_configuration_safe,
    add_residual_target,
    build_preprocessor,
    collect_feature_selection_counts,
    feature_selection_candidate_columns,
    final_residual_prediction,
    minutes_adjusted_baseline_predictions,
    normalize_position_column,
    position_diagnostics,
    run_position_model_backtest,
    run_backtest,
    run_broad_feature_ablation,
    run_feature_selection_experiment,
    run_season_window_comparison,
    season_filtered_frame,
    season_window_definitions,
    season_window_fold_summary,
    season_window_frame,
    sklearn_model_specs,
    write_position_markdown_summary,
    write_position_results,
    write_supported_season_filter_report,
    write_markdown_summary,
    write_results,
    write_season_window_report,
    write_season_window_results,
    write_broad_feature_ablation_report,
    write_broad_feature_ablation_results,
    select_features_elasticnet,
)


class RecordingRegressor(BaseEstimator, RegressorMixin):
    fit_targets: list[list[float]] = []

    def fit(self, x: pd.DataFrame, y: pd.Series) -> "RecordingRegressor":
        self.fit_targets.append(list(y))
        self.prediction_ = float(pd.Series(y).mean())
        return self

    def predict(self, x: pd.DataFrame) -> list[float]:
        return [self.prediction_] * len(x)


def modeling_frame() -> pd.DataFrame:
    rows = []
    for season, offset in [("2022-23", 0), ("2023-24", 10)]:
        for element, position in [(1, "MID"), (2, "FWD")]:
            for gw in [1, 2, 3, 4]:
                points = offset + element + gw
                rows.append(
                    {
                        "element": element,
                        "season": season,
                        "gw": gw,
                        "position": position,
                        "total_points": points,
                        "minutes": 90 if gw % 2 == 0 else 30,
                        "points_last_1": points - 1 if gw > 1 else pd.NA,
                        "points_mean_last_3": points - 1 if gw > 1 else pd.NA,
                        "points_mean_last_5": points - 1 if gw > 1 else pd.NA,
                        "minutes_mean_last_5": 90,
                        "next_gw_points": points + 1 if gw < 4 else pd.NA,
                    }
                )
    return pd.DataFrame(rows)


def three_season_modeling_frame() -> pd.DataFrame:
    rows = []
    for season, offset in [("2020-21", 0), ("2021-22", 100), ("2022-23", 200)]:
        for element, position in [(1, "MID"), (2, "FWD")]:
            for gw in [1, 2, 3, 4]:
                points = offset + element + gw
                rows.append(
                    {
                        "element": element,
                        "season": season,
                        "gw": gw,
                        "position": position,
                        "total_points": points,
                        "minutes": 90,
                        "points_last_1": points - 1 if gw > 1 else pd.NA,
                        "points_mean_last_3": points - 1 if gw > 1 else pd.NA,
                        "points_mean_last_5": points - 1 if gw > 1 else pd.NA,
                        "minutes_mean_last_5": 90,
                        "team_elo_pre_gw": 1500.0,
                        "opponent_elo_pre_gw": 1500.0,
                        "elo_difference": 0.0,
                        "home_adjusted_elo_difference": 50.0,
                        "team_goals_scored_mean_last_5": 1.0,
                        "team_goals_conceded_mean_last_5": 1.0,
                        "opponent_goals_scored_mean_last_5": 1.0,
                        "opponent_goals_conceded_mean_last_5": 1.0,
                        "team_clean_sheet_rate_last_5": 0.5,
                        "opponent_clean_sheet_rate_last_5": 0.5,
                        "goals_scored_mean_last_3": 0.1,
                        "goals_scored_mean_last_5": 0.1,
                        "assists_mean_last_3": 0.1,
                        "assists_mean_last_5": 0.1,
                        "clean_sheets_mean_last_3": 0.1,
                        "clean_sheets_mean_last_5": 0.1,
                        "goals_conceded_mean_last_3": 0.1,
                        "goals_conceded_mean_last_5": 0.1,
                        "influence_mean_last_3": 1.0,
                        "influence_mean_last_5": 1.0,
                        "creativity_mean_last_3": 1.0,
                        "creativity_mean_last_5": 1.0,
                        "threat_mean_last_3": 1.0,
                        "threat_mean_last_5": 1.0,
                        "ict_index_mean_last_3": 1.0,
                        "ict_index_mean_last_5": 1.0,
                        "expected_goals_mean_last_3": 0.1,
                        "expected_goals_mean_last_5": 0.1,
                        "expected_assists_mean_last_3": 0.1,
                        "expected_assists_mean_last_5": 0.1,
                        "expected_goal_involvements_mean_last_3": 0.1,
                        "expected_goal_involvements_mean_last_5": 0.1,
                        "expected_goals_conceded_mean_last_3": 0.1,
                        "expected_goals_conceded_mean_last_5": 0.1,
                        "selected_lag_1": 100.0,
                        "transfers_in_lag_1": 1.0,
                        "transfers_out_lag_1": 1.0,
                        "transfers_balance_lag_1": 0.0,
                        "was_home": gw % 2 == 0,
                        "next_gw_points": points + 1 if gw < 4 else pd.NA,
                    }
                )
    return pd.DataFrame(rows)


def minimal_results_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "validation_season": ["2022-23"],
            "model": ["minutes_adjusted_rolling_mean"],
            "n_train": [6],
            "n_validation": [6],
            "mae": [1.0],
            "rmse": [1.0],
            "spearman": [0.0],
            "top_10_precision": [0.5],
            "top_10_avg_actual_points": [2.0],
            "top_20_precision": [0.5],
            "top_20_avg_actual_points": [2.0],
            "top_50_precision": [0.5],
            "top_50_avg_actual_points": [2.0],
        }
    )


def patch_fast_main_dependencies(monkeypatch, scratch: Path, argv: list[str]) -> dict[str, list[object]]:
    calls: dict[str, list[object]] = {
        "write_results": [],
        "broad_ablation": [],
        "feature_selection": [],
        "model_pruning_audit": [],
    }

    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(backtest_module, "DEFAULT_RESULTS_PATH", scratch / "model_results.csv")
    monkeypatch.setattr(backtest_module, "DEFAULT_SUMMARY_PATH", scratch / "model_comparison.md")
    monkeypatch.setattr(
        backtest_module,
        "DEFAULT_POSITION_RESULTS_PATH",
        scratch / "position_model_comparison.csv",
    )
    monkeypatch.setattr(
        backtest_module,
        "DEFAULT_POSITION_SUMMARY_PATH",
        scratch / "position_model_comparison.md",
    )
    monkeypatch.setattr(
        backtest_module,
        "DEFAULT_SUPPORTED_RESULTS_PATH",
        scratch / "model_results_supported_seasons.csv",
    )
    monkeypatch.setattr(
        backtest_module,
        "DEFAULT_SUPPORTED_SUMMARY_PATH",
        scratch / "model_comparison_supported_seasons.md",
    )
    monkeypatch.setattr(
        backtest_module,
        "DEFAULT_SUPPORTED_FILTER_REPORT_PATH",
        scratch / "supported_season_filter_report.md",
    )
    monkeypatch.setattr(
        backtest_module,
        "DEFAULT_TEAM_FORM_FEATURE_REPORT_PATH",
        scratch / "team_form_feature_report.md",
    )

    monkeypatch.setattr(backtest_module, "read_dataset", lambda path: three_season_modeling_frame())
    monkeypatch.setattr(backtest_module, "run_backtest", lambda *args, **kwargs: minimal_results_frame())
    monkeypatch.setattr(
        backtest_module,
        "run_position_model_backtest",
        lambda *args, **kwargs: minimal_results_frame().assign(position="ALL"),
    )
    monkeypatch.setattr(
        backtest_module,
        "write_results",
        lambda results, path: calls["write_results"].append(path),
    )
    monkeypatch.setattr(backtest_module, "write_markdown_summary", lambda *args, **kwargs: None)
    monkeypatch.setattr(backtest_module, "write_position_results", lambda *args, **kwargs: None)
    monkeypatch.setattr(backtest_module, "write_position_markdown_summary", lambda *args, **kwargs: None)
    monkeypatch.setattr(backtest_module, "write_supported_season_filter_report", lambda *args, **kwargs: None)
    monkeypatch.setattr(backtest_module, "write_team_form_feature_report", lambda *args, **kwargs: None)
    monkeypatch.setattr(backtest_module, "write_broad_feature_ablation_results", lambda *args, **kwargs: None)
    monkeypatch.setattr(backtest_module, "write_broad_feature_ablation_report", lambda *args, **kwargs: None)
    monkeypatch.setattr(backtest_module, "write_feature_selection_results", lambda *args, **kwargs: None)
    monkeypatch.setattr(backtest_module, "write_feature_selection_report", lambda *args, **kwargs: None)

    def record_broad_ablation(*args, **kwargs) -> pd.DataFrame:
        calls["broad_ablation"].append(kwargs.get("min_season"))
        return minimal_results_frame().assign(feature_config="current_stable")

    def record_feature_selection(*args, **kwargs) -> pd.DataFrame:
        calls["feature_selection"].append(kwargs.get("min_season"))
        return minimal_results_frame().assign(selection_strategy="global_selected_features")

    monkeypatch.setattr(backtest_module, "run_broad_feature_ablation", record_broad_ablation)
    monkeypatch.setattr(backtest_module, "run_feature_selection_experiment", record_feature_selection)
    monkeypatch.setattr(
        backtest_module,
        "run_model_pruning_audit_report",
        lambda *args, **kwargs: calls["model_pruning_audit"].append(kwargs.get("min_season")),
    )
    return calls


def test_run_backtest_uses_prior_seasons_for_validation() -> None:
    results = run_backtest(
        modeling_frame(),
        model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
        residual_specs=[],
    )

    assert set(results["validation_season"]) == {"2023-24"}
    assert "DummyMean" in set(results["model"])
    assert "two_stage_minutes_points" in set(results["model"])
    dummy_row = results.loc[results["model"] == "DummyMean"].iloc[0]
    assert dummy_row["n_train"] == 6
    assert dummy_row["n_validation"] == 6
    assert "top_10_precision" in results.columns
    assert "top_10_avg_actual_points" in results.columns
    assert "GK_top_10_precision" in results.columns
    assert "DEF_top_50_avg_actual_points" in results.columns


def test_write_backtest_reports() -> None:
    scratch = Path("tests/.tmp_backtest")
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        results = run_backtest(
            modeling_frame(),
            model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
            residual_specs=[],
        )
        results_path = scratch / "model_results.csv"
        summary_path = scratch / "model_comparison.md"

        write_results(results, results_path)
        write_markdown_summary(results, summary_path)

        assert results_path.exists()
        assert summary_path.exists()
        summary = summary_path.read_text(encoding="utf-8")
        assert "# Model Comparison" in summary
        assert "Two-Stage Versus Best Direct Model" in summary
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_backtest_module_has_command_line_help() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "evaluation.backtest", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "--input" in completed.stdout
    assert "--min-season" in completed.stdout
    assert "--run-broad-ablation" in completed.stdout
    assert "--run-feature-selection" in completed.stdout
    assert "--run-season-window-comparison" in completed.stdout
    assert "--run-model-pruning-audit" in completed.stdout


def test_preprocessor_outputs_named_feature_dataframe() -> None:
    frame = modeling_frame().dropna(subset=["points_last_1"]).copy()
    columns = ["position", "points_last_1", "points_mean_last_3"]

    preprocessor = build_preprocessor(frame, columns, scale_numeric=True)
    transformed = preprocessor.fit_transform(frame[columns])

    assert isinstance(transformed, pd.DataFrame)
    assert all(isinstance(column, str) for column in transformed.columns)


def test_removed_non_working_models_are_not_in_active_specs() -> None:
    model_names = {spec.name for spec in sklearn_model_specs()}
    removed_model_names = {"Random" + "ForestRegressor", "Hist" + "GradientBoostingRegressor"}

    assert not removed_model_names.intersection(model_names)


def test_main_full_history_does_not_run_optional_experiments(monkeypatch) -> None:
    scratch = Path("tests/.tmp_cli_backtest/full_history")
    calls = patch_fast_main_dependencies(
        monkeypatch,
        scratch,
        ["evaluation.backtest", "--input", "dummy.parquet"],
    )

    backtest_module.main()

    assert calls["broad_ablation"] == []
    assert calls["feature_selection"] == []
    assert calls["model_pruning_audit"] == []
    assert calls["write_results"] == [scratch / "model_results.csv"]


def test_main_supported_default_does_not_run_optional_experiments(
    monkeypatch,
) -> None:
    scratch = Path("tests/.tmp_cli_backtest/supported_default")
    calls = patch_fast_main_dependencies(
        monkeypatch,
        scratch,
        ["evaluation.backtest", "--input", "dummy.parquet", "--min-season", "2020-21"],
    )

    backtest_module.main()

    assert calls["broad_ablation"] == []
    assert calls["feature_selection"] == []
    assert calls["model_pruning_audit"] == []
    assert calls["write_results"] == [scratch / "model_results_supported_seasons.csv"]


def test_main_broad_ablation_flag_runs_broad_ablation(monkeypatch) -> None:
    scratch = Path("tests/.tmp_cli_backtest/broad_flag")
    calls = patch_fast_main_dependencies(
        monkeypatch,
        scratch,
        [
            "evaluation.backtest",
            "--input",
            "dummy.parquet",
            "--min-season",
            "2020-21",
            "--run-broad-ablation",
        ],
    )

    backtest_module.main()

    assert calls["broad_ablation"] == ["2020-21"]
    assert calls["feature_selection"] == []
    assert calls["model_pruning_audit"] == []


def test_main_feature_selection_flag_runs_feature_selection(monkeypatch) -> None:
    scratch = Path("tests/.tmp_cli_backtest/feature_selection_flag")
    calls = patch_fast_main_dependencies(
        monkeypatch,
        scratch,
        [
            "evaluation.backtest",
            "--input",
            "dummy.parquet",
            "--min-season",
            "2020-21",
            "--run-feature-selection",
        ],
    )

    backtest_module.main()

    assert calls["broad_ablation"] == []
    assert calls["feature_selection"] == ["2020-21"]
    assert calls["model_pruning_audit"] == []


def test_main_model_pruning_audit_flag_runs_audit(monkeypatch) -> None:
    scratch = Path("tests/.tmp_cli_backtest/model_pruning_flag")
    calls = patch_fast_main_dependencies(
        monkeypatch,
        scratch,
        [
            "evaluation.backtest",
            "--input",
            "dummy.parquet",
            "--run-model-pruning-audit",
        ],
    )

    backtest_module.main()

    assert calls["broad_ablation"] == []
    assert calls["feature_selection"] == []
    assert calls["model_pruning_audit"] == ["2022-23"]


def test_min_season_filters_train_and_validation_data() -> None:
    results = run_backtest(
        three_season_modeling_frame(),
        model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
        residual_specs=[],
        min_season="2021-22",
    )

    assert set(results["validation_season"]) == {"2022-23"}
    dummy_row = results.loc[results["model"] == "DummyMean"].iloc[0]
    assert dummy_row["n_train"] == 6
    assert dummy_row["n_validation"] == 6
    assert results.attrs["diagnostics"]["season_filter"]["included_seasons"] == [
        "2021-22",
        "2022-23",
    ]
    assert results.attrs["diagnostics"]["season_filter"]["excluded_seasons"] == ["2020-21"]


def test_default_backtest_still_uses_full_available_dataset() -> None:
    results = run_backtest(
        three_season_modeling_frame(),
        model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
        residual_specs=[],
    )

    assert set(results["validation_season"]) == {"2021-22", "2022-23"}
    assert "season_filter" not in results.attrs["diagnostics"]


def test_min_season_does_not_leak_future_validation_seasons_into_training() -> None:
    data = three_season_modeling_frame()
    data.loc[data["season"] == "2022-23", "next_gw_points"] = 999
    RecordingRegressor.fit_targets = []

    run_backtest(
        data,
        model_specs=[SklearnModelSpec("RecordingRegressor", RecordingRegressor())],
        residual_specs=[],
        min_season="2021-22",
    )

    assert RecordingRegressor.fit_targets
    assert all(max(targets) < 999 for targets in RecordingRegressor.fit_targets if targets)


def test_filtered_reports_are_written_to_separate_files() -> None:
    scratch = Path("tests/.tmp_backtest")
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        data = three_season_modeling_frame()
        full_results = run_backtest(
            data,
            model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
            residual_specs=[],
        )
        filtered_results = run_backtest(
            data,
            model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
            residual_specs=[],
            min_season="2021-22",
        )
        filtered_path = scratch / DEFAULT_SUPPORTED_RESULTS_PATH.name
        filtered_summary_path = scratch / DEFAULT_SUPPORTED_SUMMARY_PATH.name
        report_path = scratch / "supported_season_filter_report.md"

        write_results(filtered_results, filtered_path)
        write_markdown_summary(filtered_results, filtered_summary_path)
        write_supported_season_filter_report(
            source=data,
            full_results=full_results,
            filtered_results=filtered_results,
            full_position_results=None,
            filtered_position_results=None,
            min_season="2021-22",
            path=report_path,
        )

        assert filtered_path.exists()
        assert filtered_summary_path.exists()
        assert report_path.exists()
        assert "Supported-Season Filter Report" in report_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_season_filtered_frame_keeps_only_supported_seasons() -> None:
    filtered = season_filtered_frame(three_season_modeling_frame(), "2021-22")

    assert sorted(filtered["season"].unique()) == ["2021-22", "2022-23"]


def test_season_window_definitions_include_intended_seasons() -> None:
    data = three_season_modeling_frame()

    assert sorted(season_window_frame(data, "full_history")["season"].unique()) == [
        "2020-21",
        "2021-22",
        "2022-23",
    ]
    assert sorted(season_window_frame(data, "supported_seasons")["season"].unique()) == [
        "2020-21",
        "2021-22",
        "2022-23",
    ]
    assert sorted(season_window_frame(data, "rich_feature_seasons")["season"].unique()) == [
        "2022-23"
    ]
    assert season_window_definitions()["rich_feature_seasons"] == "2022-23"


def test_season_window_training_seasons_are_earlier_than_validation() -> None:
    folds = season_window_fold_summary(three_season_modeling_frame(), "full_history")

    for _, row in folds.iterrows():
        train_seasons = [season for season in str(row["train_seasons"]).split(", ") if season]
        assert train_seasons
        assert all(train_season < row["validation_season"] for train_season in train_seasons)


def test_season_window_comparison_skips_windows_with_too_little_data() -> None:
    results = run_season_window_comparison(
        three_season_modeling_frame(),
        model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
        residual_specs=[],
    )

    assert "rich_feature_seasons" not in set(results["window"])
    assert {"full_history", "supported_seasons"}.issubset(set(results["window"]))
    fold_tables = results.attrs["diagnostics"]["folds"]
    assert fold_tables["rich_feature_seasons"].iloc[0]["note"].startswith("skipped:")


def test_season_window_outputs_are_written_separately() -> None:
    scratch = Path("tests/.tmp_season_window")
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        results = run_season_window_comparison(
            three_season_modeling_frame(),
            model_specs=[SklearnModelSpec("DummyMean", DummyRegressor(strategy="mean"))],
            residual_specs=[],
        )
        results_path = scratch / "season_window_results.csv"
        report_path = scratch / "season_window_comparison.md"

        write_season_window_results(results, results_path)
        write_season_window_report(results, report_path)

        assert results_path.exists()
        assert report_path.exists()
        assert not (scratch / "model_results.csv").exists()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_ablation_feature_configurations_include_and_exclude_expected_features() -> None:
    configs = ablation_feature_configurations()

    assert "team_elo_pre_gw" in configs["current_stable"]
    assert "team_goals_scored_mean_last_5" in configs["current_stable"]
    assert "team_elo_pre_gw" not in configs["no_team_strength"]
    assert "team_goals_scored_mean_last_5" not in configs["no_team_strength"]
    assert "team_elo_pre_gw" in configs["elo_only"]
    assert "team_goals_scored_mean_last_5" not in configs["elo_only"]
    assert "team_elo_pre_gw" not in configs["team_form_only"]
    assert "team_goals_scored_mean_last_5" in configs["team_form_only"]
    assert "goals_scored_mean_last_3" in configs["player_returns_rolling"]
    assert "influence_mean_last_3" in configs["ict_rolling"]
    assert "expected_goals_mean_last_3" in configs["expected_stats_rolling"]
    assert "selected_lag_1" in configs["ownership_transfers_lagged"]
    assert "was_home" in configs["fixture_home"]
    assert "selected_lag_1" in configs["all_safe_candidates"]


def test_ablation_feature_configurations_exclude_raw_leakage_and_team_columns() -> None:
    forbidden = {*RAW_CURRENT_GW_OUTCOME_COLUMNS, *RAW_TEAM_COLUMNS}

    for columns in ablation_feature_configurations().values():
        assert not forbidden.intersection(columns)
        assert_feature_configuration_safe(columns)


def test_broad_ablation_respects_supported_season_filter() -> None:
    results = run_broad_feature_ablation(
        three_season_modeling_frame(),
        min_season="2021-22",
        model_specs=[SklearnModelSpec("Ridge", DummyRegressor(strategy="mean"))],
        residual_specs=[],
    )

    assert set(results["validation_season"]) == {"2022-23"}
    assert set(results["feature_group"]) == set(ablation_feature_configurations())
    assert "global_plus_position_interactions" in set(results["model"])


def test_broad_ablation_outputs_are_written_separately() -> None:
    scratch = Path("tests/.tmp_backtest")
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        results = run_broad_feature_ablation(
            three_season_modeling_frame(),
            min_season="2021-22",
            model_specs=[SklearnModelSpec("Ridge", DummyRegressor(strategy="mean"))],
            residual_specs=[],
        )
        results_path = scratch / "broad_feature_ablation_results.csv"
        report_path = scratch / "broad_feature_ablation_report.md"

        write_broad_feature_ablation_results(results, results_path)
        write_broad_feature_ablation_report(results, report_path)

        assert results_path.exists()
        assert report_path.exists()
        assert not (scratch / DEFAULT_SUPPORTED_RESULTS_PATH.name).exists()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_feature_selection_uses_training_seasons_only() -> None:
    data = three_season_modeling_frame()
    data.loc[data["season"] == "2022-23", "goals_scored_mean_last_3"] = 999999
    train = data.loc[data["season"].isin(["2020-21", "2021-22"])].copy()

    selected_with_future_changed = select_features_elasticnet(
        train,
        feature_selection_candidate_columns(train),
        random_state=7,
    )
    selected_without_future = select_features_elasticnet(
        train,
        feature_selection_candidate_columns(train),
        random_state=7,
    )

    assert selected_with_future_changed == selected_without_future


def test_feature_selection_does_not_select_raw_leakage_or_team_columns() -> None:
    results = run_feature_selection_experiment(
        three_season_modeling_frame(),
        min_season="2021-22",
        random_state=7,
    )
    counts = collect_feature_selection_counts(results)
    forbidden = {*RAW_CURRENT_GW_OUTCOME_COLUMNS, *RAW_TEAM_COLUMNS}

    assert not forbidden.intersection(counts)


def test_position_feature_selection_falls_back_when_position_rows_are_low() -> None:
    results = run_feature_selection_experiment(
        three_season_modeling_frame(),
        min_season="2021-22",
        random_state=7,
        min_position_rows=999,
    )
    position_row = results.loc[results["model"] == "position_selected_features"].iloc[0]
    global_row = results.loc[results["model"] == "global_selected_features"].iloc[0]

    assert "MID" in position_row["selected_features"]
    assert global_row["selected_features"].split(",")[0] in position_row["selected_features"]


def test_feature_selection_is_reproducible_with_fixed_seed() -> None:
    first = run_feature_selection_experiment(
        three_season_modeling_frame(),
        min_season="2021-22",
        random_state=123,
    )
    second = run_feature_selection_experiment(
        three_season_modeling_frame(),
        min_season="2021-22",
        random_state=123,
    )

    assert list(first["selected_features"]) == list(second["selected_features"])


def test_residual_target_is_actual_minus_minutes_adjusted_baseline() -> None:
    frame = pd.DataFrame(
        {
            "next_gw_points": [8.0, 2.0],
            "points_mean_last_5": [6.0, 9.0],
            "minutes_mean_last_5": [45.0, 90.0],
        }
    )
    baseline = minutes_adjusted_baseline_predictions(frame)

    with_residual = add_residual_target(frame, baseline)

    assert list(baseline) == [3.0, 9.0]
    assert list(with_residual["__residual_target"]) == [5.0, -7.0]


def test_validation_baseline_predictions_do_not_use_other_validation_rows() -> None:
    validation = pd.DataFrame(
        {
            "next_gw_points": [8.0, 999.0],
            "points_mean_last_5": [6.0, 1000.0],
            "minutes_mean_last_5": [45.0, 90.0],
        }
    )

    first_row_prediction = minutes_adjusted_baseline_predictions(validation.iloc[[0]]).iloc[0]
    full_frame_prediction = minutes_adjusted_baseline_predictions(validation).iloc[0]

    assert first_row_prediction == full_frame_prediction == 3.0


def test_residual_final_prediction_adds_baseline_and_predicted_residual() -> None:
    baseline = pd.Series([3.0, 9.0], index=[10, 11])
    predicted_residual = pd.Series([5.0, -7.0], index=[10, 11])

    prediction = final_residual_prediction(baseline, predicted_residual)

    assert list(prediction) == [8.0, 2.0]


def test_baseline_prediction_features_are_row_local() -> None:
    frame = pd.DataFrame(
        {
            "next_gw_points": [8.0, 999.0],
            "points_last_1": [4.0, 1000.0],
            "points_mean_last_3": [5.0, 1000.0],
            "points_mean_last_5": [6.0, 1000.0],
            "minutes_mean_last_5": [45.0, 90.0],
        }
    )

    first_row_features = add_baseline_prediction_features(frame.iloc[[0]])
    full_frame_features = add_baseline_prediction_features(frame)

    feature_columns = [
        "pred_rolling_3_gameweek_mean",
        "pred_rolling_5_gameweek_mean",
        "pred_minutes_adjusted_rolling_mean",
    ]
    pd.testing.assert_series_equal(
        first_row_features.iloc[0][feature_columns],
        full_frame_features.iloc[0][feature_columns],
        check_names=False,
    )
    assert list(full_frame_features.loc[0, feature_columns]) == [5.0, 6.0, 3.0]


def test_position_normalization_maps_known_labels_and_excludes_unknowns() -> None:
    frame = pd.DataFrame(
        {
            "season": ["2023-24", "2023-24", "2023-24", "2023-24", "2023-24"],
            "gw": [1, 1, 1, 1, 1],
            "position": ["GKP", "GK", "DEF", "MID", "AM"],
            "next_gw_points": [1, 2, 3, 4, 5],
        }
    )

    normalized = normalize_position_column(frame)
    diagnostics = position_diagnostics(frame)

    assert list(normalized["position"][:4]) == ["GK", "GK", "DEF", "MID"]
    assert pd.isna(normalized.loc[4, "position"])
    assert diagnostics["unknown_positions"] == {"AM": 1}


def test_write_results_overwrites_stale_model_rows() -> None:
    scratch = Path("tests/.tmp_backtest")
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        results_path = scratch / "model_results.csv"
        stale = pd.DataFrame(
            {
                "validation_season": ["2023-24"],
                "model": ["stale_model"],
                "mae": [99.0],
            }
        )
        fresh = pd.DataFrame(
            {
                "validation_season": ["2023-24"],
                "model": ["fresh_model"],
                "mae": [1.0],
            }
        )

        write_results(stale, results_path)
        write_results(fresh, results_path)

        saved = pd.read_csv(results_path)
        assert list(saved["model"]) == ["fresh_model"]
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_position_model_backtest_does_not_fit_on_validation_targets() -> None:
    data = modeling_frame()
    data.loc[data["season"] == "2023-24", "next_gw_points"] = 999
    RecordingRegressor.fit_targets = []

    results = run_position_model_backtest(
        data,
        estimator=RecordingRegressor(),
        min_position_train_rows=1,
    )

    assert {"global_model", "position_wise_models", "global_plus_position_interactions"}.issubset(
        set(results["strategy"])
    )
    assert RecordingRegressor.fit_targets
    assert all(max(targets) < 999 for targets in RecordingRegressor.fit_targets if targets)


def test_position_interactions_are_based_on_training_positions_only() -> None:
    train = modeling_frame().loc[lambda frame: frame["season"] == "2022-23"].copy()
    validation = pd.DataFrame(
        {
            "position": ["GK"],
            "points_last_1": [10],
            "points_mean_last_3": [10],
            "points_mean_last_5": [10],
            "minutes_mean_last_5": [90],
        }
    )
    columns = ["position", "points_last_1", "points_mean_last_3"]
    train_positions = sorted(train["position"].dropna().astype(str).unique())

    _, train_columns = add_position_interactions(train, columns, positions=train_positions)
    validation_with_interactions, validation_columns = add_position_interactions(
        validation,
        columns,
        positions=train_positions,
    )

    assert train_columns == validation_columns
    assert "points_last_1__position_GK" not in validation_columns
    assert validation_with_interactions.filter(like="__position_").eq(0).all().all()


def test_position_wise_models_fall_back_to_global_model_when_training_rows_are_low() -> None:
    results = run_position_model_backtest(
        modeling_frame(),
        estimator=DummyRegressor(strategy="mean"),
        min_position_train_rows=999,
    )

    metric_columns = [
        "mae",
        "rmse",
        "spearman",
        "top_10_precision",
        "top_20_precision",
        "top_50_precision",
    ]
    global_rows = results.loc[results["strategy"] == "global_model"].set_index(
        ["validation_season", "position"]
    )
    fallback_rows = results.loc[results["strategy"] == "position_wise_models"].set_index(
        ["validation_season", "position"]
    )

    pd.testing.assert_frame_equal(
        global_rows[metric_columns].sort_index(),
        fallback_rows[metric_columns].sort_index(),
    )


def test_write_position_model_reports() -> None:
    scratch = Path("tests/.tmp_backtest")
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        results = run_position_model_backtest(
            modeling_frame(),
            estimator=DummyRegressor(strategy="mean"),
            min_position_train_rows=1,
        )
        results_path = scratch / "position_model_comparison.csv"
        summary_path = scratch / "position_model_comparison.md"

        write_position_results(results, results_path)
        write_position_markdown_summary(results, summary_path)

        assert results_path.exists()
        assert summary_path.exists()
        summary = summary_path.read_text(encoding="utf-8")
        assert "Position Model Comparison" in summary
        assert "top_10_precision" in results.columns
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
