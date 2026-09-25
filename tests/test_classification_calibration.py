"""Unit tests for classification and calibration benchmark metrics."""

import numpy as np
import pandas as pd
import pytest

from report_analyst.core.benchmark.classification_calibration import (
    compute_calibration_metrics,
    compute_classification_report,
    expected_calibration_error,
    minmax_normalize,
)


class TestMinmaxNormalize:
    """Tests for minmax_normalize."""

    def test_returns_half_when_all_values_identical(self):
        series = pd.Series([3, 3, 3])
        normalized = minmax_normalize(series)
        np.testing.assert_array_equal(normalized, np.array([0.5, 0.5, 0.5]))

    def test_scales_values_to_unit_interval(self):
        series = pd.Series([0, 5, 10])
        normalized = minmax_normalize(series)
        np.testing.assert_allclose(normalized, np.array([0.0, 0.5, 1.0]))


class TestExpectedCalibrationError:
    """Tests for expected_calibration_error."""

    def test_returns_zero_for_empty_input(self):
        assert expected_calibration_error(np.array([]), np.array([])) == 0.0

    def test_perfect_calibration_has_low_error(self):
        y_true = np.array([0, 0, 1, 1])
        y_prob = np.array([0.1, 0.2, 0.8, 0.9])
        ece = expected_calibration_error(y_true, y_prob, n_bins=2)
        assert ece < 0.2


class TestComputeCalibrationMetrics:
    """Tests for compute_calibration_metrics."""

    @pytest.fixture
    def labeled_df(self):
        return pd.DataFrame(
            {
                "ground_truth": [0, 1, 2, 0, 2],
                "model_a": [0, 1, 2, 0, 2],
                "model_b": [0, 0, 1, 0, 1],
            }
        )

    def test_returns_one_row_per_prediction_column(self, labeled_df):
        metrics = compute_calibration_metrics(
            labeled_df,
            ground_truth_col="ground_truth",
            score_cols=["model_a", "model_b"],
            n_bins=10,
        )

        assert len(metrics) == 2
        assert set(metrics["prediction"]) == {"model_a", "model_b"}
        assert metrics.loc[metrics["prediction"] == "model_a", "f1_1"].iloc[0] == 1.0

    def test_returns_nan_metrics_when_no_overlap(self):
        df = pd.DataFrame({"ground_truth": [np.nan], "model_a": [1]})
        metrics = compute_calibration_metrics(
            df,
            ground_truth_col="ground_truth",
            score_cols=["model_a"],
        )

        assert metrics.iloc[0]["ece"] != metrics.iloc[0]["ece"]  # NaN


class TestComputeClassificationReport:
    """Tests for compute_classification_report."""

    def test_builds_three_class_report(self):
        df = pd.DataFrame(
            {
                "relevance": [0, 1, 2, 0, 2],
                "pred": [0, 1, 2, 1, 2],
            }
        )

        report = compute_classification_report(
            df,
            ground_truth_col="relevance",
            score_col="pred",
        )

        assert report["accuracy"] == pytest.approx(0.8)
        assert "irrelevant (0)" in report

    def test_raises_when_columns_missing(self):
        df = pd.DataFrame({"relevance": [0, 1]})
        with pytest.raises(ValueError, match="Columns 'relevance' and/or 'pred'"):
            compute_classification_report(
                df,
                ground_truth_col="relevance",
                score_col="pred",
            )
