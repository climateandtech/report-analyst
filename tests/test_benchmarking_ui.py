"""Unit tests for BenchmarkingUI with Streamlit mocked."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from report_analyst.models.benchmark import (
    BenchmarkDataset,
    BenchmarkEvaluation,
    DatasetType,
    EvaluationMetrics,
    FlexibleDatasetRow,
    RetrievalConfig,
)
from report_analyst.ui.benchmarking import BenchmarkingUI


class _SessionState(dict):
    """Minimal stand-in for streamlit.session_state attribute + item access."""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]


@pytest.fixture
def cache_manager(tmp_path):
    cm = MagicMock()
    cm.db_path = str(tmp_path / "bench.db")
    return cm


@pytest.fixture
def ui(cache_manager):
    with patch("report_analyst.ui.benchmarking.BenchmarkStore") as store_cls:
        store_cls.return_value = MagicMock()
        return BenchmarkingUI(cache_manager)


@pytest.fixture
def mock_st(monkeypatch):
    st = MagicMock()
    st.session_state = _SessionState()

    def _columns(n):
        cols = []
        for _ in range(n):
            col = MagicMock()
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=False)
            cols.append(col)
        return cols

    st.columns.side_effect = _columns

    def _tabs(labels):
        tabs = []
        for _ in labels:
            tab = MagicMock()
            tab.__enter__ = MagicMock(return_value=tab)
            tab.__exit__ = MagicMock(return_value=False)
            tabs.append(tab)
        return tabs

    st.tabs.side_effect = _tabs
    expander = MagicMock()
    expander.__enter__ = MagicMock(return_value=expander)
    expander.__exit__ = MagicMock(return_value=False)
    st.expander.return_value = expander
    spinner = MagicMock()
    spinner.__enter__ = MagicMock(return_value=spinner)
    spinner.__exit__ = MagicMock(return_value=False)
    st.spinner.return_value = spinner
    monkeypatch.setattr("report_analyst.ui.benchmarking.st", st)
    return st


def _sample_dataset(dataset_id="d1", n=2):
    rows = [
        FlexibleDatasetRow(data={"query_id": "q1", "chunk_id": f"c{i}", "position": i, "score": 0.9 - i * 0.1})
        for i in range(1, n + 1)
    ]
    return BenchmarkDataset(
        dataset_id=dataset_id,
        name="Sample",
        dataset_type=DatasetType.INFORMATION_RETRIEVAL,
        results=rows,
    )


def test_ui_init_wires_dependencies(ui, cache_manager):
    assert ui.cache_manager is cache_manager
    assert ui.evaluation_engine is not None
    assert ui.dataset_loader is not None


def test_render_csv_metrics_table_and_charts(ui, mock_st):
    metrics = EvaluationMetrics(
        precision_at_k={1: 0.5, 5: 0.4},
        recall_at_k={1: 0.5, 5: 0.4},
        f1_at_k={1: 0.5, 5: 0.4},
        mean_reciprocal_rank=0.5,
        mean_average_precision=0.4,
        ndcg_at_k={1: 0.5, 5: 0.4},
    )
    ui._render_csv_metrics_table(metrics, [1, 5])
    with patch("report_analyst.ui.benchmarking.px") as px:
        px.line.return_value = MagicMock()
        px.bar.return_value = MagicMock()
        ui._render_csv_metrics_charts(metrics, [1, 5], chart_key_prefix="t")
    assert mock_st.dataframe.called or mock_st.table.called or mock_st.write.called


def test_run_csv_evaluation_from_datasets_success(ui, mock_st):
    ref = _sample_dataset("ref")
    bench = _sample_dataset("bench")
    mock_st.session_state.uploaded_datasets = {"ref": ref, "bench": bench}

    with patch.object(ui.evaluation_engine, "compare_flexible_datasets") as compare:
        compare.return_value = EvaluationMetrics(precision_at_k={1: 1.0}, mean_average_precision=1.0)
        with patch.object(ui, "_render_csv_metrics_table"), patch.object(ui, "_render_csv_metrics_charts"):
            ui._run_csv_evaluation_from_datasets("upload", "ref", "upload", "bench", [1, 5], "eval1")

    assert "csv_evaluations" in mock_st.session_state
    assert mock_st.session_state["csv_evaluations"][0].evaluation_name == "eval1"
    assert mock_st.success.called


def test_run_csv_evaluation_db_source_errors(ui, mock_st):
    ui._run_csv_evaluation_from_datasets("db", "x", "upload", "y", [1], "e")
    assert mock_st.error.called


def test_run_csv_evaluation_missing_upload(ui, mock_st):
    mock_st.session_state.uploaded_datasets = {}
    ui._run_csv_evaluation_from_datasets("upload", "missing", "upload", "missing", [1], "e")
    assert mock_st.error.called


def test_render_confirmation_ui_confirm_and_cancel(ui, mock_st):
    dataset = _sample_dataset()
    mock_st.session_state.uploaded_datasets = {"tmp": dataset, "ground_truth_current": dataset}
    mock_st.button.side_effect = [True, False]  # confirm
    ui._render_confirmation_ui(dataset, "tmp", "ground_truth", "f.csv")
    assert "ground_truth_current" in mock_st.session_state.uploaded_datasets
    assert mock_st.rerun.called

    mock_st.button.side_effect = [False, True]  # cancel
    mock_st.session_state.uploaded_datasets = {"tmp": dataset}
    mock_st.rerun.reset_mock()
    ui._render_confirmation_ui(dataset, "tmp", "ground_truth", "f.csv")
    assert "tmp" not in mock_st.session_state.uploaded_datasets


def test_render_results_table_and_details(ui, mock_st):
    metrics = EvaluationMetrics(precision_at_k={1: 0.5}, mean_average_precision=0.5)
    evaluation = BenchmarkEvaluation(
        dataset_id="d1",
        evaluation_name="e1",
        config_hash="abc",
        retrieval_config=RetrievalConfig(top_k=5),
        evaluation_metrics=metrics,
    )
    ui._render_results_table([evaluation])
    ui._render_evaluation_details(evaluation)
    assert mock_st.write.called or mock_st.dataframe.called or mock_st.metric.called


def test_render_metrics_charts(ui, mock_st):
    metrics = EvaluationMetrics(
        precision_at_k={1: 0.5, 5: 0.4},
        recall_at_k={1: 0.5, 5: 0.4},
        f1_at_k={1: 0.5, 5: 0.4},
        ndcg_at_k={1: 0.5, 5: 0.4},
        mean_reciprocal_rank=0.5,
        mean_average_precision=0.4,
    )
    evaluation = BenchmarkEvaluation(
        dataset_id="d1",
        evaluation_name="e1",
        config_hash="abc",
        retrieval_config=RetrievalConfig(top_k=5),
        evaluation_metrics=metrics,
    )
    with patch("report_analyst.ui.benchmarking.px") as px:
        px.line.return_value = MagicMock()
        px.bar.return_value = MagicMock()
        ui._render_metrics_charts([evaluation])


def test_show_and_delete_dataset(ui, mock_st):
    ui.benchmark_store.get_dataset.return_value = MagicMock(name="n", dataset_id="d1", description="x", question_set="tcfd")
    ui.benchmark_store.get_dataset_content.return_value = MagicMock(questions=[1, 2, 3])
    ui._show_dataset_details("d1")
    ui.benchmark_store.delete_dataset.return_value = True
    ui._delete_dataset("d1")
    assert ui.benchmark_store.delete_dataset.called


def test_render_config_form(ui, mock_st):
    mock_st.number_input.side_effect = [1000, 200, 5, 0.0]
    mock_st.checkbox.return_value = False
    mock_st.selectbox.return_value = "default"
    mock_st.text_input.return_value = None
    cfg = ui._render_config_form()
    assert isinstance(cfg, RetrievalConfig)
    assert cfg.top_k == 5


def test_handle_dataset_upload_csv(ui, mock_st):
    mock_st.session_state.uploaded_datasets = {}
    uploaded = MagicMock()
    uploaded.name = "data.csv"
    uploaded.getvalue.return_value = b"query_id,chunk_id,position,score\nq1,c1,1,0.9\n"

    with patch(
        "report_analyst.ui.benchmarking.load_flexible_dataset_from_csv",
        return_value=_sample_dataset("up"),
    ):
        ui._handle_dataset_upload(uploaded, dataset_type="ground_truth")

    assert mock_st.session_state.get("uploaded_datasets") is not None or mock_st.success.called or mock_st.error.called


def test_render_annotation_interface_and_form(ui, mock_st):
    ui.render_annotation_interface()
    metrics = EvaluationMetrics()
    evaluation = BenchmarkEvaluation(
        dataset_id="d1",
        evaluation_name="e1",
        config_hash="abc",
        retrieval_config=RetrievalConfig(),
        evaluation_metrics=metrics,
    )
    ui._render_annotation_form(evaluation)


def test_render_dataset_management_smoke(ui, mock_st):
    mock_st.radio.return_value = "Ranking (retrieval)"
    mock_st.file_uploader.return_value = None
    mock_st.selectbox.return_value = None
    ui.benchmark_store.list_datasets.return_value = []
    ui.render_dataset_management()
    assert mock_st.subheader.called


def test_render_benchmarking_interface_smoke(ui, mock_st):
    mock_st.session_state.uploaded_datasets = {
        "ground_truth_current": _sample_dataset("gt"),
        "benchmark_current": _sample_dataset("bm"),
    }
    mock_st.selectbox.side_effect = ["upload", "ground_truth_current", "upload", "benchmark_current"]
    mock_st.text_input.side_effect = ["my eval", "1,5"]
    mock_st.button.return_value = False
    ui.render_benchmarking_interface()
    assert mock_st.subheader.called or mock_st.write.called


def test_render_results_dashboard_smoke(ui, mock_st):
    mock_st.session_state.csv_evaluations = []
    ui.benchmark_store.list_evaluations.return_value = []
    ui.render_results_dashboard()


def _csv_upload(name: str, content: str):
    uploaded = MagicMock()
    uploaded.name = name
    uploaded.getvalue.return_value = content.encode("utf-8")
    # file-like for pd.read_csv(gt_file)
    from io import StringIO

    buf = StringIO(content)
    uploaded.__iter__ = buf.__iter__
    # pandas read_csv can take file-like; attach read
    uploaded.read = lambda *a, **k: content.encode("utf-8")
    return uploaded


def test_handle_classification_upload(ui, mock_st):
    df = pd.DataFrame({"relevance": [0, 1, 2], "score_a": [0.1, 0.8, 0.9]})
    uploaded = MagicMock(name="cls.csv")
    uploaded.name = "cls.csv"
    ui._handle_classification_upload(df, uploaded, "classification")
    assert "classification_current" in mock_st.session_state.uploaded_datasets
    assert mock_st.success.called


def test_handle_classification_upload_empty(ui, mock_st):
    ui._handle_classification_upload(pd.DataFrame(), MagicMock(name="e.csv"), "classification")
    assert mock_st.error.called


def test_handle_dataset_upload_csv_confirm(ui, mock_st):
    mock_st.session_state.uploaded_datasets = {}
    mock_st.button.side_effect = [True, False]
    uploaded = MagicMock()
    uploaded.name = "ok.csv"
    uploaded.getvalue.return_value = b"query_id,chunk_id,position,score\nq1,c1,1,0.9\n"
    with patch(
        "report_analyst.ui.benchmarking.load_flexible_dataset_from_csv",
        return_value=_sample_dataset("up"),
    ):
        ui._handle_dataset_upload(uploaded, "ground_truth")
    assert "ground_truth_current" in mock_st.session_state.uploaded_datasets


def test_handle_dataset_upload_already_aligned(ui, mock_st):
    ds = _sample_dataset("aligned")
    mock_st.session_state["aligned_ground_truth_ok.csv"] = True
    mock_st.session_state.uploaded_datasets = {"ground_truth_current": ds}
    uploaded = MagicMock()
    uploaded.name = "ok.csv"
    uploaded.getvalue.return_value = b"query_id,chunk_id,position,score\nq1,c1,1,0.9\n"
    ui._handle_dataset_upload(uploaded, "ground_truth")
    assert mock_st.success.called


def test_render_classification_calibration_panel(ui, mock_st):
    rows = [
        FlexibleDatasetRow(data={"relevance": 1, "pred": 0.8, "query_id": "q1", "chunk_id": "c1"}),
        FlexibleDatasetRow(data={"relevance": 0, "pred": 0.2, "query_id": "q1", "chunk_id": "c2"}),
    ]
    ds = BenchmarkDataset(
        dataset_id="c",
        name="cls",
        dataset_type=DatasetType.INFORMATION_RETRIEVAL,
        results=rows,
        column_mapping={"classification_label_col": "relevance", "classification_prediction_cols": "pred"},
    )
    mock_st.session_state.uploaded_datasets = {"classification_current": ds}

    def _select(*args, **kwargs):
        options = kwargs.get("options") or []
        index = kwargs.get("index", 0)
        return options[index] if options else None

    mock_st.selectbox.side_effect = _select
    mock_st.multiselect.return_value = ["pred"]
    mock_st.slider.return_value = 10
    mock_st.button.return_value = True

    metrics_df = pd.DataFrame({"model": ["pred"], "ece": [0.1]})
    with patch("report_analyst.ui.benchmarking.compute_calibration_metrics", return_value=metrics_df), patch(
        "report_analyst.ui.benchmarking.compute_classification_report",
        return_value={"0": {"precision": 1.0}, "accuracy": 1.0},
    ):
        ui._render_classification_calibration_panel("t_")

    assert mock_st.session_state.get("csv_classification_evaluations")


def test_render_classification_model_comparison(ui, mock_st):
    mock_st.session_state.csv_classification_evaluations = [
        {
            "evaluation_name": "run1",
            "created_at": pd.Timestamp.now(),
            "metrics_df": pd.DataFrame({"m": [1]}),
        }
    ]
    mock_st.selectbox.side_effect = lambda *a, **k: 0
    ui._render_classification_model_comparison()
    assert mock_st.dataframe.called


def test_render_error_analysis_export(ui, mock_st):
    ref = _sample_dataset("ref")
    bench = _sample_dataset("bench")
    mock_st.session_state.uploaded_datasets = {"ref": ref, "bench": bench}
    mock_st.session_state.csv_evaluations = [
        type(
            "E",
            (),
            {
                "retrieval_config": RetrievalConfig(top_k=2),
                "ref_key": "ref",
                "bench_key": "bench",
                "dataset_id": "ref|||bench",
            },
        )()
    ]
    mock_st.button.return_value = True
    with patch(
        "report_analyst.ui.benchmarking.build_error_analysis_dataframe_from_flexible",
        return_value=pd.DataFrame({"a": [1]}),
    ):
        ui._render_error_analysis_export()
    assert mock_st.download_button.called


def test_run_evaluation_placeholder(ui, mock_st):
    ui.benchmark_store.save_evaluation.return_value = 42
    ui._run_evaluation("d1", "e1", RetrievalConfig())
    assert mock_st.success.called


def test_flexible_gt_wizard_aligns(ui, mock_st):
    content = "document,question,context,relevance\nR,Q,chunk text,1\n"
    uploaded = MagicMock()
    uploaded.name = "gt.csv"

    def _select(*args, **kwargs):
        options = kwargs.get("options") or []
        index = kwargs.get("index", 0)
        return options[index] if options else None

    mock_st.file_uploader.return_value = uploaded
    mock_st.selectbox.side_effect = _select
    mock_st.multiselect.return_value = ["relevance"]
    mock_st.button.return_value = True

    with patch("report_analyst.ui.benchmarking.pd.read_csv", return_value=pd.read_csv(__import__("io").StringIO(content))):
        with patch(
            "report_analyst.ui.benchmarking.align_ground_truth_flexible",
            return_value=pd.DataFrame(
                {
                    "query_id": ["R|||Q"],
                    "chunk_id": ["c1"],
                    "position": [1],
                    "score": [1.0],
                }
            ),
        ):
            ui._render_flexible_gt_wizard()

    assert "ground_truth_flexible_current" in mock_st.session_state.uploaded_datasets


def test_flexible_bm_wizard_no_file_returns(ui, mock_st):
    mock_st.file_uploader.return_value = None
    ui._render_flexible_bm_wizard()


def test_render_dataset_management_classification_mode(ui, mock_st):
    mock_st.radio.return_value = "Classification"
    mock_st.file_uploader.return_value = None
    ui.benchmark_store.list_datasets.return_value = []
    with patch.object(ui, "_render_flexible_bm_wizard") as wiz:
        ui.render_dataset_management()
        assert wiz.called


def test_annotation_with_evaluations(ui, mock_st):
    metrics = EvaluationMetrics()
    evaluation = BenchmarkEvaluation(
        dataset_id="d1",
        evaluation_name="e1",
        config_hash="abc",
        retrieval_config=RetrievalConfig(),
        evaluation_metrics=metrics,
    )
    ui.benchmark_store.list_evaluations.return_value = [evaluation]
    mock_st.selectbox.return_value = evaluation
    ui.render_annotation_interface()


def test_flexible_bm_wizard_aligns_ranking_mode(ui, mock_st):
    content = "report,question,paragraph,score\nR,Q,para text,0.9\n"
    uploaded = MagicMock()
    uploaded.name = "bm.csv"

    def _select(*args, **kwargs):
        options = kwargs.get("options") or []
        index = kwargs.get("index", 0)
        return options[index] if options else None

    mock_st.session_state.evaluation_mode = "Ranking (retrieval)"
    mock_st.file_uploader.return_value = uploaded
    mock_st.selectbox.side_effect = _select
    mock_st.multiselect.return_value = ["score"]
    mock_st.button.return_value = True

    aligned = pd.DataFrame(
        {
            "query_id": ["R|||Q"],
            "chunk_id": ["c1"],
            "position": [1],
            "score": [0.9],
            "paragraph": ["para text"],
        }
    )
    with patch(
        "report_analyst.ui.benchmarking.pd.read_csv",
        return_value=pd.read_csv(__import__("io").StringIO(content)),
    ), patch(
        "report_analyst.ui.benchmarking.align_benchmark_flexible",
        return_value=aligned,
    ):
        ui._render_flexible_bm_wizard()

    assert any("benchmark" in k for k in mock_st.session_state.uploaded_datasets)


def test_flexible_bm_wizard_classification_mode(ui, mock_st):
    content = "document,question,paragraph,relevance,pred\nR,Q,p,1,0.8\n"
    uploaded = MagicMock()
    uploaded.name = "bm.csv"

    def _select(*args, **kwargs):
        options = kwargs.get("options") or []
        index = kwargs.get("index", 0)
        return options[index] if options else None

    mock_st.session_state.evaluation_mode = "Classification"
    mock_st.file_uploader.return_value = uploaded
    mock_st.selectbox.side_effect = _select
    mock_st.multiselect.return_value = ["pred"]
    mock_st.button.return_value = True

    aligned = pd.DataFrame(
        {
            "query_id": ["R|||Q"],
            "chunk_id": ["c1"],
            "position": [1],
            "score": [0.8],
            "relevance": [1],
            "pred": [0.8],
        }
    )
    with patch(
        "report_analyst.ui.benchmarking.pd.read_csv",
        return_value=pd.read_csv(__import__("io").StringIO(content)),
    ), patch(
        "report_analyst.ui.benchmarking.align_benchmark_flexible",
        return_value=aligned,
    ):
        ui._render_flexible_bm_wizard()

    assert mock_st.success.called


def test_handle_yaml_dataset_upload(ui, mock_st):
    mock_st.session_state.uploaded_datasets = {}
    mock_st.button.return_value = True
    uploaded = MagicMock()
    uploaded.name = "ds.yaml"
    uploaded.getvalue.return_value = b"dataset: x\n"
    fake_ds = MagicMock()
    fake_ds.name = "Y"
    fake_ds.description = "d"
    fake_ds.questions = [1, 2]
    ui.dataset_loader = MagicMock()
    ui.dataset_loader.load_dataset.return_value = fake_ds
    ui.dataset_loader.validate_dataset_consistency.return_value = []
    ui._handle_dataset_upload(uploaded, "ground_truth")
    assert ui.benchmark_store.save_dataset.called


def test_render_benchmarking_interface_runs_eval(ui, mock_st):
    mock_st.session_state.uploaded_datasets = {
        "ground_truth_current": _sample_dataset("gt"),
        "benchmark_current": _sample_dataset("bm"),
    }

    def _select(*args, **kwargs):
        options = kwargs.get("options") or []
        index = kwargs.get("index", 0)
        return options[index] if options else None

    mock_st.radio.return_value = "Ranking (retrieval)"
    mock_st.selectbox.side_effect = _select
    mock_st.text_input.side_effect = ["eval-run", "1,5"]
    mock_st.number_input.return_value = 10
    mock_st.button.return_value = True
    with patch.object(ui, "_run_csv_evaluation_from_datasets") as run:
        ui.render_benchmarking_interface()
        assert run.called


def test_render_results_dashboard_with_evals(ui, mock_st):
    metrics = EvaluationMetrics(
        precision_at_k={1: 0.5, 5: 0.4},
        recall_at_k={1: 0.5, 5: 0.4},
        f1_at_k={1: 0.5, 5: 0.4},
        ndcg_at_k={1: 0.5, 5: 0.4},
        mean_reciprocal_rank=0.5,
        mean_average_precision=0.4,
    )
    evaluation = BenchmarkEvaluation(
        dataset_id="d1",
        evaluation_name="e1",
        config_hash="abc",
        retrieval_config=RetrievalConfig(top_k=5),
        evaluation_metrics=metrics,
    )
    ui.benchmark_store.list_evaluations.return_value = [evaluation]
    mock_st.session_state.csv_evaluations = []
    mock_st.multiselect.return_value = ["d1"]
    mock_st.radio.return_value = "Both"

    def _select(*args, **kwargs):
        options = kwargs.get("options") or []
        return options[0] if options else None

    mock_st.selectbox.side_effect = _select
    with patch.object(ui, "_render_results_table"), patch.object(ui, "_render_metrics_charts"), patch.object(
        ui, "_render_error_analysis_export"
    ), patch.object(ui, "_render_classification_model_comparison"), patch.object(
        ui, "_render_classification_calibration_panel"
    ), patch.object(
        ui, "_render_evaluation_details"
    ) as details:
        ui.render_results_dashboard()
        assert details.called
