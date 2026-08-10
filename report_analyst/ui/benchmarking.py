import logging
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from ..core.benchmark.classification_calibration import (
    compute_calibration_metrics,
    compute_classification_report,
)
from ..core.benchmark.dataset_loader import DatasetLoader, DatasetValidationError
from ..core.benchmark.error_analysis import (
    build_error_analysis_dataframe_from_flexible,
)
from ..core.benchmark.evaluation_engine import EvaluationEngine
from ..core.benchmark.flexible_alignment import (
    BenchmarkAlignConfig,
    GroundTruthAlignConfig,
    align_benchmark_flexible,
    align_ground_truth_flexible,
)
from ..core.benchmark.retrieval_results_loader import (
    load_flexible_dataset_from_csv,
)
from ..core.storage.benchmark_store import BenchmarkStore
from ..models.benchmark import (
    BenchmarkDataset,
    BenchmarkEvaluation,
    DatasetType,
    FlexibleDatasetRow,
    RetrievalConfig,
)

logger = logging.getLogger(__name__)


class BenchmarkingUI:
    """Streamlit UI components for benchmarking functionality"""

    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.dataset_loader = DatasetLoader()
        self.evaluation_engine = EvaluationEngine()
        self.benchmark_store = BenchmarkStore(cache_manager.db_path)

    def render_dataset_management(self):
        """Render dataset management interface"""
        st.subheader("Dataset Management")

        # Global evaluation mode: determines how many datasets are needed
        eval_mode = st.radio(
            "Select evaluation mode:",
            options=["Ranking (retrieval)", "Classification"],
            index=0,
            key="evaluation_mode",
            help=(
                "Ranking (retrieval) expects separate ground truth and benchmark datasets. "
                "Classification expects a single dataset that already contains both labels "
                "and model prediction/score columns."
            ),
        )

        # Expected file formats (expandable)
        with st.expander("Expected file formats (CSV, Excel, YAML, JSON)"):
            st.markdown(
                "**Supported files**"
            )
            st.markdown(
                "**CSV / Excel** — "
                "Recommended for new evaluations."
                "Your file should contain the information needed to identify `questions`, "
                "`relevant text`, `labels`, or `model scores`. You can map the columns after upload."
            )

            st.markdown(
                "**YAML / JSON** — "
                "Supported for existing benchmark datasets, but cannot be aligned in the wizard. "
            )
            st.markdown(
                "**Tip:** "
                "If you are unsure whether your file matches the expected structure, "
                "upload a CSV or Excel file and use the alignment step."
            )
            st.caption("Full details: see EXPECTED_FILE_FORMATS.md in the project root.")

        # Initialize session state for uploaded datasets if not exists
        if "uploaded_datasets" not in st.session_state:
            st.session_state.uploaded_datasets = {}

        # ------------------------------------------------------------------
        # Flexible alignment wizard (experimental)
        # ------------------------------------------------------------------
        
        if eval_mode == "Classification":
            st.subheader(
                "Upload & Align Dataset for Classification",
                help=(
                    "Classification requires one dataset containing both the expected labels "
                    "and the model prediction or score columns."
                ),
            )
            st.caption(
                "Upload one dataset containing both the expected labels and your model predictions. " \
                "Match the required columns, then continue to Evaluate."
            )
            # For classification we only need a single (results-style) dataset,
            # so we reuse the benchmark wizard.
            self._render_flexible_bm_wizard()
        else:
            st.subheader(
                "Upload & Align Datasets for Ranking",
                help=(
                    "Ranking requires two datasets: a ground-truth dataset with the expected "
                    "relevance information and a benchmark dataset containing the model results."
                ),
            )
            st.caption(
                "Upload your reference dataset first, then your benchmark results. " \
                "Match the required columns in each step. Once both datasets are ready, continue to Evaluate."
            )

            gt_wizard, bm_wizard = st.tabs(["1. Ground Truth", "2. Benchmark"])

            with gt_wizard:
                self._render_flexible_gt_wizard()

            with bm_wizard:
                self._render_flexible_bm_wizard()

        # Offer download of aligned datasets (when user previously aligned and used one)
        aligned_gt = st.session_state.get("aligned_csv_current_ground_truth")
        aligned_bm = st.session_state.get("aligned_csv_current_benchmark")
        if aligned_gt or aligned_bm:
            st.subheader("Download aligned datasets")
            st.caption("You have aligned dataset(s) in use. Download the aligned CSV version below.")
            dl_col1, dl_col2 = st.columns(2)
            if aligned_gt:
                with dl_col1:
                    _name, _bytes = aligned_gt
                    st.download_button(
                        label="Download aligned ground truth CSV",
                        data=_bytes,
                        file_name="ground_truth_aligned.csv",
                        mime="text/csv",
                        key="download_aligned_gt_current",
                    )
            if aligned_bm:
                with dl_col2:
                    _name, _bytes = aligned_bm
                    st.download_button(
                        label="Download aligned benchmark CSV",
                        data=_bytes,
                        file_name="benchmark_aligned.csv",
                        mime="text/csv",
                        key="download_aligned_bm_current",
                    )

        # List existing datasets (optional; alignment should still be available even if empty)
        st.subheader("Existing Datasets")
        try:
            datasets = self.benchmark_store.list_datasets()
        except sqlite3.OperationalError as e:
            st.warning("Database not initialized. Please restart the application.")
            logger.error(f"Database error: {e}")
            datasets = []

        if not datasets:
            st.info(
                "No datasets have been saved to the database yet. "
                "You can still upload CSV/Excel files above and/or use Dataset Alignment below."
            )
        else:
            # Display datasets in a table
            dataset_data = []
            for dataset in datasets:
                dataset_data.append(
                    {
                        "Dataset ID": dataset.dataset_id,
                        "Name": dataset.name,
                        "Question Set": dataset.question_set,
                        "Version": dataset.version,
                        "Created": (dataset.created_at.strftime("%Y-%m-%d %H:%M") if dataset.created_at else "Unknown"),
                    }
                )

            df = pd.DataFrame(dataset_data)
            st.dataframe(df, use_container_width=True)

            # Dataset actions
            selected_dataset = st.selectbox(
                "Select dataset for actions:",
                options=[d.dataset_id for d in datasets],
                format_func=lambda x: next(d.name for d in datasets if d.dataset_id == x),
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("View Details"):
                    self._show_dataset_details(selected_dataset)

            with col2:
                if st.button("Delete Dataset", type="secondary"):
                    self._delete_dataset(selected_dataset)

    def render_benchmarking_interface(self):
        """Render benchmarking interface"""
        st.subheader("Run Benchmark Evaluation")

        # Get datasets from both database and session state (uploaded files)
        db_datasets = []
        try:
            db_datasets = self.benchmark_store.list_datasets()
        except sqlite3.OperationalError:
            # DB may not be initialized yet on first Benchmarking visit.
            db_datasets = []

        uploaded_datasets = st.session_state.get("uploaded_datasets", {})

        # Check for unconfirmed datasets and show helpful message
        temp_datasets = {k: v for k, v in uploaded_datasets.items() if k.startswith("temp_")}
        if temp_datasets and not db_datasets and not any(not k.startswith("temp_") for k in uploaded_datasets.keys()):
            st.warning(
                "⚠️ You have uploaded datasets but haven't confirmed them yet. "
                "Please go to the 'Datasets' tab and click 'Confirm and Use This Dataset' "
                "for each uploaded dataset to make them available for evaluation."
            )
            return

        if not db_datasets and not uploaded_datasets:
            st.warning("No datasets available. Please upload datasets first.")
            return

        # Choose evaluation type: ranking, classification, or both
        eval_mode = st.radio(
            "Evaluation type",
            options=["Ranking (retrieval)", "Classification", "Both"],
            index=0,
            key="evaluation_type",
        )

        # Ranking / retrieval evaluation configuration
        if eval_mode in ("Ranking (retrieval)", "Both"):
            st.subheader("Ranking evaluation (retrieval)")

            col1, col2 = st.columns(2)

            with col1:
                # Select reference/ground truth dataset
                reference_options = {}
                for d in db_datasets:
                    reference_options[f"DB: {d.name}"] = ("db", d.dataset_id)

                for key, dataset in uploaded_datasets.items():
                    # Only show confirmed datasets (not temporary ones)
                    if "ground_truth" in key and not key.startswith("temp_"):
                        reference_options[f"Uploaded: {dataset.name}"] = (
                            "uploaded",
                            key,
                        )

                if reference_options:
                    selected_ref_label = st.selectbox(
                        "Select Reference (Ground Truth) Dataset:",
                        options=list(reference_options.keys()),
                    )
                    ref_source, ref_id = reference_options[selected_ref_label]
                else:
                    st.error("No reference datasets available")
                    return

            with col2:
                # Select benchmark dataset
                benchmark_options = {}
                for d in db_datasets:
                    benchmark_options[f"DB: {d.name}"] = ("db", d.dataset_id)
                for key, dataset in uploaded_datasets.items():
                    # Only show confirmed datasets (not temporary ones)
                    if "benchmark" in key and not key.startswith("temp_"):
                        benchmark_options[f"Uploaded: {dataset.name}"] = (
                            "uploaded",
                            key,
                        )

                if benchmark_options:
                    selected_bench_label = st.selectbox(
                        "Select Benchmark (Results) Dataset:",
                        options=list(benchmark_options.keys()),
                    )
                    bench_source, bench_id = benchmark_options[selected_bench_label]
                else:
                    st.error("No benchmark datasets available")
                    return

            # Evaluation name
            evaluation_name = st.text_input(
                "Evaluation Name:",
                value=f"eval_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}",
            )

            # Top K configuration
            st.subheader("Ranking configuration")
            col1, col2 = st.columns(2)
            with col1:
                st.number_input(
                    "Top K",
                    min_value=1,
                    max_value=50,
                    value=10,
                    help="Number of top results to consider for evaluation",
                )
            with col2:
                k_values_input = st.text_input(
                    "K values for metrics (comma-separated)",
                    value="1,3,5,10",
                    help="K values for Precision@K, Recall@K, etc. (e.g., 1,3,5,10)",
                )

            # Parse K values
            k_values = None
            if k_values_input:
                try:
                    k_values = [int(k.strip()) for k in k_values_input.split(",") if k.strip()]
                    if not k_values:
                        k_values = None
                except ValueError:
                    st.warning("Invalid K values format. Using default values.")
                    k_values = None

            # Run ranking evaluation
            if st.button("Run Ranking Evaluation", type="primary"):
                if evaluation_name:
                    self._run_csv_evaluation_from_datasets(
                        ref_source,
                        ref_id,
                        bench_source,
                        bench_id,
                        k_values,
                        evaluation_name,
                    )
                else:
                    st.error("Please provide an evaluation name")

        # Classification evaluation configuration
        if eval_mode in ("Classification", "Both"):
            st.subheader("Classification evaluation (per-chunk labels and scores)")
            st.caption(
                "Use this section when your dataset has ground-truth labels (e.g. relevance/usefulness) "
                "and one or more numeric prediction/score columns."
            )
            # Reuse the classification calibration panel so you can configure and run it here
            self._render_classification_calibration_panel("evaluate")

    def render_results_dashboard(self):
        """Render evaluation results dashboard"""
        st.subheader("Evaluation Results")

        # Get evaluations from database
        evaluations = []
        try:
            evaluations = self.benchmark_store.list_evaluations()
        except sqlite3.OperationalError:
            # DB may not be initialized yet; fall back to session evaluations only.
            evaluations = []

        # Get evaluations from session state (recent CSV evaluations)
        session_evals = st.session_state.get("csv_evaluations", [])

        all_evaluations = evaluations + session_evals

        if not all_evaluations:
            st.info("No evaluations run yet. Run a benchmark evaluation to see results.")
            return

        # Filter controls
        col1, col2 = st.columns(2)
        with col1:
            datasets = list(set(e.dataset_id for e in all_evaluations if hasattr(e, "dataset_id")))
            if datasets:
                selected_datasets = st.multiselect("Filter by Dataset:", datasets, default=datasets)
            else:
                selected_datasets = []

        with col2:
            # Show all evaluations by default
            pass

        # Filter evaluations
        if selected_datasets:
            filtered_evals = [e for e in all_evaluations if hasattr(e, "dataset_id") and e.dataset_id in selected_datasets]
        else:
            filtered_evals = all_evaluations

        if not filtered_evals:
            st.warning("No evaluations match the selected filters.")
            return

        # Let the user choose which metrics to focus on
        metrics_mode = st.radio(
            "Select metrics view:",
            ["Retrieval", "Classification", "Both"],
            index=0,
            key="metrics_view_mode",
        )

        if metrics_mode in ("Retrieval", "Both"):
            # Results table - show all results
            self._render_results_table(filtered_evals)

            # Metrics visualization
            self._render_metrics_charts(filtered_evals)

            # Error analysis export for the latest CSV evaluation (session-based)
            self._render_error_analysis_export()

        if metrics_mode in ("Classification", "Both"):
            # Model comparison from stored classification calibration runs
            self._render_classification_model_comparison()
            # Classification calibration for datasets with labels/scores
            self._render_classification_calibration_panel("result")

        # Detailed evaluation view
        if filtered_evals:
            eval_options = [f"{e.evaluation_name} ({getattr(e, 'dataset_id', 'N/A')})" for e in filtered_evals]
            selected_eval_name = st.selectbox(
                "Select evaluation for details:",
                options=eval_options,
            )
            if selected_eval_name:
                selected_idx = eval_options.index(selected_eval_name)
                selected_eval = filtered_evals[selected_idx]
                self._render_evaluation_details(selected_eval)

    def _render_error_analysis_export(self):
        """Render download button for error-analysis CSV based on current CSV evaluation context."""
        # Use the most recent CSV evaluation from session state
        session_evals = st.session_state.get("csv_evaluations", [])
        if not session_evals:
            return

        latest_eval = session_evals[-1]
        retrieval_config = getattr(latest_eval, "retrieval_config", None)
        if not retrieval_config:
            return

        top_k = getattr(retrieval_config, "top_k", None)
        if not top_k:
            return

        st.subheader("Error analysis export")
        st.caption(
            "Download a CSV with, for each retrieved chunk, the report, question, expert relevant part, "
            "retrieved chunk text, its position in top-K, expert relevance label, and whether it is really relevant "
            "(expert label > 0)."
        )

        if st.button("Build error-analysis CSV"):
            try:
                # Get current ground-truth and benchmark datasets used for the last CSV evaluation
                # Prefer explicit keys stored on the evaluation object
                ref_id = getattr(latest_eval, "ref_key", None)
                bench_id = getattr(latest_eval, "bench_key", None)

                dataset_id = getattr(latest_eval, "dataset_id", "")
                # Fallback to parsing dataset_id for legacy evaluations
                if (ref_id is None or bench_id is None) and dataset_id:
                    if "|||" in dataset_id:
                        ref_id, bench_id = dataset_id.split("|||", 1)
                    elif "_" in dataset_id:
                        ref_id, bench_id = dataset_id.split("_", 1)

                if not ref_id or not bench_id:
                    st.error("Cannot determine datasets for error analysis from evaluation metadata.")
                    return

                uploaded_datasets = st.session_state.get("uploaded_datasets", {})
                ground_truth_ds = uploaded_datasets.get(ref_id)
                benchmark_ds = uploaded_datasets.get(bench_id)

                if not ground_truth_ds or not benchmark_ds:
                    st.error("Could not locate the ground truth and benchmark datasets used for this evaluation.")
                    return

                df_error = build_error_analysis_dataframe_from_flexible(
                    ground_truth_dataset=ground_truth_ds,
                    benchmark_dataset=benchmark_ds,
                    top_k=top_k,
                )

                if df_error.empty:
                    st.warning("No rows generated for error analysis.")
                    return

                csv_bytes = df_error.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download error-analysis CSV",
                    data=csv_bytes,
                    file_name="benchmark_error_analysis.csv",
                    mime="text/csv",
                    key="download_error_analysis_csv",
                )
            except Exception as e:  # noqa: BLE001
                st.error(f"Failed to build error-analysis CSV: {e!s}")

    def render_annotation_interface(self):
        """Render human annotation interface"""
        st.subheader("Human Annotation")

        evaluations = self.benchmark_store.list_evaluations()
        if not evaluations:
            st.info("No evaluations available for annotation.")
            return

        selected_eval = st.selectbox(
            "Select Evaluation to Annotate:",
            options=evaluations,
            format_func=lambda x: f"{x.evaluation_name} ({x.dataset_id})",
        )

        if selected_eval:
            self._render_annotation_form(selected_eval)

    def _render_classification_model_comparison(self):
        """Render stored classification calibration runs as model comparison table and charts."""
        runs = st.session_state.get("csv_classification_evaluations", [])
        if not runs:
            st.info(
                "Run classification calibration in the **Evaluate** tab (select multiple "
                "prediction/score columns) to compare models here."
            )
            return

        st.subheader("Classification model comparison")
        options = [f"{r['evaluation_name']} ({r['created_at'].strftime('%Y-%m-%d %H:%M')})" for r in runs]
        selected_idx = st.selectbox(
            "Select calibration run:",
            range(len(runs)),
            format_func=lambda i: options[i],
            key="results_classification_run_select",
        )
        run = runs[selected_idx]
        metrics_df = run["metrics_df"]
        if metrics_df.empty:
            st.warning("No metrics for this run.")
            return

        st.caption(f"Run: **{run['evaluation_name']}** — one row per model (prediction column).")
        st.dataframe(metrics_df, use_container_width=True)

    def _render_classification_calibration_panel(self, key_prefix: str):
        """Render classification calibration metrics for datasets with relevance/usefulness scores."""
        uploaded_datasets = st.session_state.get("uploaded_datasets", {})
        if not uploaded_datasets:
            return

        # Build list of datasets that have at least some numeric columns
        candidates = []
        for key, dataset in uploaded_datasets.items():
            results = getattr(dataset, "results", [])
            if not results:
                continue
            first = results[0]
            data = getattr(first, "data", {}) or {}
            if not data:
                continue
            df_sample = pd.DataFrame([data])
            numeric_cols = df_sample.select_dtypes(include=["number"]).columns.tolist()
            if numeric_cols:
                candidates.append((key, dataset))

        if not candidates:
            return

        st.subheader("Classification calibration")
        st.caption(
            "Analyze calibration and classification performance for any dataset with "
            "a label column and one or more numeric prediction/score columns."
        )

        # Dataset selector
        labels = [f"{ds.name} ({key})" for key, ds in candidates]
        selected_label = st.selectbox(
            "Select dataset for calibration analysis:",
            options=labels,
            key=f"{key_prefix}_calibration_dataset_select",
        )
        idx = labels.index(selected_label)
        selected_key, selected_dataset = candidates[idx]

        # Build DataFrame from FlexibleDatasetRow objects
        df_rows = [row.data for row in selected_dataset.results]
        df = pd.DataFrame(df_rows)
        if df.empty:
            st.info("Selected dataset has no rows to analyze.")
            return

        all_cols = df.columns.tolist()

        # Try to load defaults from dataset metadata (set by the flexible wizard
        # when running in classification mode). Falls back to heuristics if not set.
        mapping = getattr(selected_dataset, "column_mapping", {}) or {}
        default_label_name = mapping.get("classification_label_col")
        raw_pred_cols = mapping.get("classification_prediction_cols") or ""
        # Stored as a comma-separated string to keep column_mapping values simple.
        default_pred_cols = (
            [c.strip() for c in raw_pred_cols.split(",") if c.strip()] if isinstance(raw_pred_cols, str) else []
        )

        # Ground-truth label: let the user pick from **all** columns.
        label_candidates = all_cols

        if default_label_name and default_label_name in label_candidates:
            default_label_index = label_candidates.index(default_label_name)
        else:
            # Prefer relevance/usefulness as default if present; otherwise first column.
            default_label_index = 0
            for preferred in ("relevance", "usefulness"):
                for i, col in enumerate(label_candidates):
                    if col.lower() == preferred:
                        default_label_index = i
                        break
                else:
                    continue
                break

        label_col = st.selectbox(
            "Ground-truth label column (e.g. relevance or usefulness):",
            options=label_candidates,
            index=default_label_index,
            key=f"{key_prefix}calibration_label_select",
        )

        # Prediction / score columns: show **all** columns and let the user decide.
        score_candidates = all_cols

        # Default predictions: use stored configuration if available; otherwise none.
        default_score_selection = [c for c in default_pred_cols if c in score_candidates]

        # Let the user choose one or more prediction columns (models) to analyze.
        selected_score_cols = st.multiselect(
            "Prediction / score columns (models):",
            options=score_candidates,
            default=default_score_selection,
            key=f"{key_prefix}calibration_score_multiselect",
        )
        if not selected_score_cols:
            st.info("Select at least one prediction/score column to compute metrics.")
            return

        n_bins = st.slider(
            "Number of bins for Expected Calibration Error (ECE):",
            min_value=10,
            max_value=200,
            value=100,
            step=10,
            key=f"{key_prefix}calibration_ece_bins",
        )

        if st.button("Compute classification calibration", key=f"{key_prefix}calibration_compute"):
            with st.spinner("Computing calibration metrics..."):
                try:
                    metrics_df = compute_calibration_metrics(
                        df,
                        ground_truth_col=label_col,
                        score_cols=selected_score_cols,
                        n_bins=n_bins,
                    )
                except Exception as exc:
                    st.error(f"Failed to compute calibration metrics: {exc}")
                    logger.exception("Calibration metrics error")
                    return

                st.markdown("**Calibration and discrimination metrics**")
                st.dataframe(metrics_df, use_container_width=True)

                # Store for model comparison in Results tab
                if "csv_classification_evaluations" not in st.session_state:
                    st.session_state.csv_classification_evaluations = []
                eval_name = f"Classification: {selected_key} ({label_col})"
                st.session_state.csv_classification_evaluations.append(
                    {
                        "evaluation_name": eval_name,
                        "dataset_id": selected_key,
                        "label_col": label_col,
                        "metrics_df": metrics_df,
                        "created_at": pd.Timestamp.now(),
                    }
                )
                st.success("Saved for model comparison in the **Results** tab.")

                # Classification report for every selected model
                for score_col in selected_score_cols:
                    try:
                        report_dict = compute_classification_report(
                            df,
                            ground_truth_col=label_col,
                            score_col=score_col,
                        )
                    except Exception as exc:
                        st.error(f"Failed to compute classification report for `{score_col}`: {exc}")
                        logger.exception("Classification report error")
                        continue

                    if report_dict:
                        st.markdown(f"**Classification report for `{score_col}` (labels 0, 1, 2)**")
                        report_df = pd.DataFrame(report_dict).T
                        st.dataframe(report_df, use_container_width=True)
                    else:
                        st.info(f"Not enough non-missing data to compute a classification report for `{score_col}`.")

    def _run_csv_evaluation_from_datasets(self, ref_source, ref_id, bench_source, bench_id, k_values, evaluation_name):
        """Run evaluation using selected datasets from database or uploaded files"""
        try:
            with st.spinner("Loading datasets and calculating metrics..."):
                # Load reference dataset
                if ref_source == "db":
                    # Load from database (would need to convert from BenchmarkDatasetContent)
                    st.error("Database dataset evaluation not yet implemented. Please use uploaded CSV/Excel files.")
                    return
                else:
                    # Load from session state
                    reference_dataset = st.session_state.uploaded_datasets.get(ref_id)
                    if not reference_dataset:
                        st.error(f"Reference dataset {ref_id} not found.")
                        return

                # Load benchmark dataset
                if bench_source == "db":
                    st.error("Database dataset evaluation not yet implemented. Please use uploaded CSV/Excel files.")
                    return
                else:
                    # Load from session state
                    benchmark_dataset = st.session_state.uploaded_datasets.get(bench_id)
                    if not benchmark_dataset:
                        st.error(f"Benchmark dataset {bench_id} not found.")
                        return

                # Run evaluation
                metrics = self.evaluation_engine.compare_flexible_datasets(
                    reference_dataset, benchmark_dataset, k_values=k_values
                )

            # Display results
            st.success("Evaluation completed successfully!")
            st.subheader("Results")

            # Display metrics table
            self._render_csv_metrics_table(metrics, k_values)

            # Display charts
            self._render_csv_metrics_charts(metrics, k_values)

            # Store evaluation in session state for results tab
            if "csv_evaluations" not in st.session_state:
                st.session_state.csv_evaluations = []

            from ..models.benchmark import RetrievalConfig

            # Use the maximum k value for error analysis export (to show all top-K chunks)
            max_k = max(k_values) if k_values else 10
            eval_obj = type(
                "Evaluation",
                (),
                {
                    "evaluation_name": evaluation_name,
                    "dataset_id": f"{ref_id}|||{bench_id}",
                    "evaluation_metrics": metrics,
                    "retrieval_config": RetrievalConfig(top_k=max_k),
                    "created_at": pd.Timestamp.now(),
                    # Explicit references to the dataset keys used for this evaluation
                    "ref_key": ref_id,
                    "bench_key": bench_id,
                },
            )()
            st.session_state.csv_evaluations.append(eval_obj)

        except ValueError as e:
            st.error(f"Error loading datasets: {e!s}")
            logger.exception("Dataset loading error")
        except Exception as e:
            st.error(f"Error during evaluation: {e!s}")
            logger.exception("Evaluation error")

    def _render_confirmation_ui(self, dataset, temp_key: str, dataset_type: str, file_name: str):
        """Render confirmation UI for an unconfirmed dataset"""
        st.info(f"📋 **{dataset.name}** ({len(dataset.results)} rows) - Pending confirmation")

        # Show basic info
        st.write(f"**Dataset Name:** {dataset.name}")
        st.write(f"**Number of rows:** {len(dataset.results)}")

        # Confirm save - this will replace any existing dataset of the same type
        col1, col2 = st.columns(2)
        with col1:
            button_key = f"confirm_{dataset_type}_{file_name}"
            if st.button("Confirm and Use This Dataset", key=button_key, type="primary"):
                dataset_key = f"{dataset_type}_current"

                # Remove old dataset of the same type if it exists
                if dataset_key in st.session_state.uploaded_datasets:
                    old_dataset = st.session_state.uploaded_datasets[dataset_key]
                    st.info(f"Replacing previous {dataset_type} dataset: {old_dataset.name}")

                # Save the new dataset
                st.session_state.uploaded_datasets[dataset_key] = dataset

                # Remove temporary key
                if temp_key in st.session_state.uploaded_datasets:
                    del st.session_state.uploaded_datasets[temp_key]

                st.success(f"Dataset '{dataset.name}' confirmed and ready for evaluation!")
                st.rerun()

        with col2:
            if st.button("Cancel", key=f"cancel_{dataset_type}_{file_name}"):
                # Remove temporary dataset
                if temp_key in st.session_state.uploaded_datasets:
                    del st.session_state.uploaded_datasets[temp_key]
                st.info("Upload cancelled. Dataset not saved.")
                st.rerun()

        # Show detailed preview
        st.divider()
        st.write("**Dataset Details:**")
        st.write(f"**Dataset ID:** {dataset.dataset_id}")
        st.write(f"**Dataset Type:** {dataset.dataset_type.value}")

        # Show sample data
        if dataset.results:
            st.write("**Sample data (first 5 rows):**")
            sample_data = []
            for _i, result in enumerate(dataset.results[:5]):
                row_data = result.data.copy()
                sample_data.append(row_data)
            if sample_data:
                st.dataframe(pd.DataFrame(sample_data), use_container_width=True)

    def _handle_dataset_upload(self, uploaded_file, dataset_type: str = "ground_truth"):
        """Handle dataset file upload - supports YAML, JSON, CSV, and Excel files"""
        tmp_path = None
        try:
            # Determine file extension
            file_ext = uploaded_file.name.split(".")[-1].lower()

            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            # Load dataset based on file type
            with st.spinner("Loading and validating dataset..."):
                if file_ext in ["csv", "xlsx", "xls"]:
                    # ------------------------------------------------------------------
                    # Step 1: Read raw tabular data
                    # ------------------------------------------------------------------
                    if file_ext in ["xlsx", "xls"]:
                        df_raw = pd.read_excel(tmp_path)
                        csv_string = df_raw.to_csv(index=False)
                        csv_kwargs = {"csv_content": csv_string}
                    else:
                        df_raw = pd.read_csv(tmp_path)
                        csv_kwargs = {"csv_path": tmp_path}

                    # ------------------------------------------------------------------
                    # Special path: classification mode.
                    # In this mode we want to preserve all label/prediction columns and
                    # only add IDs (query_id, chunk_id) via classification alignment,
                    # without forcing the strict retrieval schema.
                    # ------------------------------------------------------------------
                    if dataset_type == "classification":
                        self._handle_classification_upload(
                            df_raw=df_raw,
                            uploaded_file=uploaded_file,
                            dataset_type=dataset_type,
                        )
                        return

                    # If this file has already been aligned and registered for this
                    # dataset_type, avoid re-showing the schema warning on rerun.
                    aligned_flag_key = f"aligned_{dataset_type}_{uploaded_file.name}"
                    dataset_key = f"{dataset_type}_current"
                    if (
                        st.session_state.get(aligned_flag_key)
                        and "uploaded_datasets" in st.session_state
                        and dataset_key in st.session_state.uploaded_datasets
                    ):
                        aligned_dataset = st.session_state.uploaded_datasets[dataset_key]
                        st.success(
                            f"Using previously aligned dataset '{aligned_dataset.name}' "
                            f"({len(aligned_dataset.results)} rows) for evaluation."
                        )
                        return

                    # ------------------------------------------------------------------
                    # Step 2: Try to load as a flexible benchmark dataset
                    # If this fails (missing key columns, etc.), offer alignment.
                    # ------------------------------------------------------------------
                    dataset = None
                    load_error: Optional[Exception] = None
                    try:
                        dataset = load_flexible_dataset_from_csv(
                            dataset_name=f"{dataset_type}_{uploaded_file.name}",
                            **csv_kwargs,
                        )
                    except Exception as exc:  # noqa: BLE001  # pragma: no cover - UI fallback
                        load_error = exc

                    if dataset is not None:
                        st.success(f"Dataset loaded successfully from {file_ext.upper()} file!")

                        # Store dataset temporarily in session state for preview
                        # Use a temporary key that will be replaced on confirmation
                        temp_key = f"temp_{dataset_type}_{uploaded_file.name}"
                        if "uploaded_datasets" not in st.session_state:
                            st.session_state.uploaded_datasets = {}

                        st.session_state.uploaded_datasets[temp_key] = dataset

                        # Show basic info and confirmation buttons immediately after upload
                        st.write(f"**Dataset Name:** {dataset.name}")
                        st.write(f"**Number of rows:** {len(dataset.results)}")

                        # Confirm save - this will replace any existing dataset of the same type
                        col1, col2 = st.columns(2)
                        with col1:
                            button_key = f"confirm_{dataset_type}_{uploaded_file.name}"
                            if st.button(
                                "Confirm and Use This Dataset",
                                key=button_key,
                                type="primary",
                            ):
                                dataset_key = f"{dataset_type}_current"

                                # Remove old dataset of the same type if it exists
                                if dataset_key in st.session_state.uploaded_datasets:
                                    old_dataset = st.session_state.uploaded_datasets[dataset_key]
                                    st.info(f"Replacing previous {dataset_type} dataset: {old_dataset.name}")

                                # Save the new dataset
                                st.session_state.uploaded_datasets[dataset_key] = dataset

                                # Remove temporary key
                                if temp_key in st.session_state.uploaded_datasets:
                                    del st.session_state.uploaded_datasets[temp_key]

                                # Clear any previously stored aligned CSV for this type
                                st.session_state.pop(f"aligned_csv_current_{dataset_type}", None)

                                st.success(f"Dataset '{dataset.name}' confirmed and ready for evaluation!")
                                st.rerun()

                        with col2:
                            if st.button(
                                "Cancel",
                                key=f"cancel_{dataset_type}_{uploaded_file.name}",
                            ):
                                # Remove temporary dataset
                                if temp_key in st.session_state.uploaded_datasets:
                                    del st.session_state.uploaded_datasets[temp_key]
                                st.info("Upload cancelled. Dataset not saved.")
                                st.rerun()

                        # Show detailed preview below the buttons
                        st.divider()
                        st.write("**Dataset Details:**")
                        st.write(f"**Dataset ID:** {dataset.dataset_id}")
                        st.write(f"**Dataset Type:** {dataset.dataset_type.value}")

                        if dataset.results:
                            st.write("**Sample data (first 5 rows):**")
                            sample_data = []
                            for _i, result in enumerate(dataset.results[:5]):
                                row_data = result.data.copy()
                                sample_data.append(row_data)
                            if sample_data:
                                st.dataframe(
                                    pd.DataFrame(sample_data),
                                    use_container_width=True,
                                )
                    else:
                        # ------------------------------------------------------------------
                        # Dataset is not in the expected benchmark schema.
                        # Offer alignment using DatasetMapper.
                        # ------------------------------------------------------------------
                        st.warning("This file does not match the expected benchmark CSV schema used by the evaluation engine.")
                        st.caption(
                            "For new or custom CSV/Excel files, please use the "
                            "**Flexible Dataset Alignment (Wizard)** section below to "
                            "map your columns to the internal schema. The older "
                            "preset/manual alignment UI has been removed."
                        )
                        if load_error is not None:
                            st.caption(f"Details: {load_error}")
                        return
                else:
                    # Use traditional YAML/JSON loader
                    dataset = self.dataset_loader.load_dataset(tmp_path)
                    warnings = self.dataset_loader.validate_dataset_consistency(dataset)

                    # Show validation results
                    if warnings:
                        st.warning(f"Dataset loaded with {len(warnings)} warnings:")
                        for warning in warnings:
                            st.write(f"Warning: {warning}")
                    else:
                        st.success("Dataset validation passed!")

                    # Show dataset preview
                    st.write(f"**Dataset:** {dataset.name}")
                    st.write(f"**Description:** {dataset.description}")
                    st.write(f"**Questions:** {len(dataset.questions)}")

                    # Confirm save
                    if st.button("Save Dataset", key=f"save_{dataset_type}"):
                        self.benchmark_store.save_dataset(dataset, uploaded_file.name)
                        st.success(f"Dataset '{dataset.name}' saved successfully!")
                        st.rerun()

        except (DatasetValidationError, ValueError) as e:
            st.error(f"Failed to load dataset: {e!s}")
            logger.exception("Dataset loading error")
        except Exception as e:
            st.error(f"Unexpected error: {e!s}")
            logger.exception("Unexpected error during dataset upload")

        finally:
            # Clean up temp file
            if tmp_path:
                try:
                    Path(tmp_path).unlink()
                except OSError as exc:
                    logger.debug("Temp file cleanup failed: %s", exc)

    def _handle_classification_upload(self, df_raw: pd.DataFrame, uploaded_file, dataset_type: str):
        """Handle upload of a classification-style dataset (single file with labels and predictions).

        In this simplified path we do **no special alignment** - we just wrap the
        raw DataFrame rows as `FlexibleDatasetRow` objects so that the calibration
        panel can let the user pick any label and prediction columns manually.
        """
        if df_raw.empty:
            st.error("Uploaded classification dataset is empty.")
            return

        # Build BenchmarkDataset directly from the raw DataFrame, preserving all columns
        results = []
        for _, row in df_raw.iterrows():
            row_dict = {}
            for col in df_raw.columns:
                val = row[col]
                row_dict[col] = None if pd.isna(val) else val
            results.append(FlexibleDatasetRow(data=row_dict))

        dataset = BenchmarkDataset(
            dataset_id=f"{dataset_type}_{uploaded_file.name}",
            name=uploaded_file.name,
            description="Classification dataset (raw; no alignment)",
            version="1.0",
            dataset_type=DatasetType.INFORMATION_RETRIEVAL,
            source="csv",
            source_path=None,
            column_mapping={},
            results=results,
        )

        if "uploaded_datasets" not in st.session_state:
            st.session_state.uploaded_datasets = {}

        dataset_key = f"{dataset_type}_current"
        st.session_state.uploaded_datasets[dataset_key] = dataset

        # Store a copy of the original CSV for download convenience
        csv_bytes = df_raw.to_csv(index=False).encode("utf-8")
        st.session_state[f"aligned_csv_current_{dataset_type}"] = (
            uploaded_file.name,
            csv_bytes,
        )

        st.success(
            f"Classification dataset '{uploaded_file.name}' loaded and ready for "
            "manual column selection in the classification calibration panel."
        )

    def _render_flexible_gt_wizard(self):
        """Guided wizard for aligning a ground truth dataset to the flexible schema."""
        gt_file = st.file_uploader(
            "Ground truth CSV/Excel for flexible alignment",
            type=["csv", "xlsx", "xls"],
            key="flex_gt_file",
        )
        if gt_file is None:
            return

        ext = gt_file.name.split(".")[-1].lower()
        if ext in ["xlsx", "xls"]:
            df_raw = pd.read_excel(gt_file)
        else:
            df_raw = pd.read_csv(gt_file)

        if df_raw.empty:
            st.warning("Uploaded ground truth file is empty.")
            return

        st.write("Preview of uploaded ground truth data:")
        st.dataframe(df_raw.head(), use_container_width=True)

        cols = list(df_raw.columns)
        cols_lower = {c.lower(): c for c in cols}

        # Query definition
        st.markdown("**Step 1 – Identify the question**")
        doc_options = ["<none>", *cols]
        default_doc_idx = 0
        for cand in ("document", "report", "report_name", "doc_id"):
            if cand in cols_lower:
                default_doc_idx = doc_options.index(cols_lower[cand])
                break
        document_sel = st.selectbox(
            "Report / document (used to build query ID):",
            options=doc_options,
            index=default_doc_idx,
            key="flex_gt_document_col",
        )
        document_col = None if document_sel == "<none>" else document_sel

        # Choose question/description column
        default_q = cols[0]
        for cand in ("description", "question", "criteria", "prompt"):
            if cand in cols_lower:
                default_q = cols_lower[cand]
                break
        question_col = st.selectbox(
            "Question:",
            options=cols,
            index=cols.index(default_q) if default_q in cols else 0,
            key="flex_gt_question_col",
        )

        default_chunk = cols[0]
        for cand in ("chunk_text", "paragraph", "context", "text"):
            if cand in cols_lower:
                default_chunk = cols_lower[cand]
                break
        # Chunk & relevant part
        st.markdown("**Step 2 – Select the relevant text**")
        chunk_text_col = st.selectbox(
            "Full text / paragraph (or the expert relevant text if no full chunk is stored):",
            options=cols,
            index=cols.index(default_chunk) if default_chunk in cols else 0,
            key="flex_gt_chunk_col",
        )

        rel_options = ["<none>", *cols]
        default_rel_idx = 0
        for cand in ("relevant_part_text", "relevant", "relevant_text"):
            if cand in cols_lower:
                default_rel_idx = rel_options.index(cols_lower[cand])
                break
        rel_sel = st.selectbox(
            (
                "Relevant excerpt"
                "(optional - if you only have relevant text, you can reuse the "
                "same column as above):"
            ),
            options=rel_options,
            index=default_rel_idx,
            key="flex_gt_relevant_col",
        )
        relevant_part_col = None if rel_sel == "<none>" else rel_sel

        # Label columns
        st.markdown("**Step 3 – Select the ground-truth label**")
        # Suggest numeric or name-based label columns
        df_sample = df_raw.head(50)
        numeric_cols = df_sample.select_dtypes(include=["number"]).columns.tolist()
        label_suggestions = set()
        for c in cols:
            cl = c.lower()
            if any(x in cl for x in ("relevance", "usefulness", "label", "class")):
                label_suggestions.add(c)
        if not label_suggestions:
            label_suggestions.update(numeric_cols)
        default_labels = sorted(label_suggestions)

        label_cols = st.multiselect(
            "Relevance label (e.g. relevance, usefulness):",
            options=cols,
            default=default_labels,
            key="flex_gt_label_cols",
        )

        if st.button(
            "Align ground truth (flexible) and use for evaluation",
            key="flex_gt_align_button",
        ):
            try:
                gt_config = GroundTruthAlignConfig(
                    document_col=document_col,
                    question_col=question_col,
                    chunk_text_col=chunk_text_col,
                    relevant_part_col=relevant_part_col,
                    label_cols=label_cols,
                )
                df_aligned = align_ground_truth_flexible(df_raw, gt_config)

                st.success(
                    f"Aligned flexible ground truth: {len(df_aligned)} rows, {df_aligned['query_id'].nunique()} queries."
                )
                st.dataframe(df_aligned.head(), use_container_width=True)

                # Build BenchmarkDataset from aligned DataFrame
                results: List[FlexibleDatasetRow] = []
                for _, row in df_aligned.iterrows():
                    row_dict: Dict[str, Any] = {}
                    for col in df_aligned.columns:
                        val = row[col]
                        row_dict[col] = None if pd.isna(val) else val
                    results.append(FlexibleDatasetRow(data=row_dict))

                dataset = BenchmarkDataset(
                    dataset_id=f"ground_truth_flexible_{gt_file.name}",
                    name=f"GT flexible ({gt_file.name})",
                    description="Ground truth dataset aligned via flexible wizard",
                    version="1.0",
                    dataset_type=DatasetType.INFORMATION_RETRIEVAL,
                    source="csv",
                    source_path=None,
                    column_mapping={},
                    results=results,
                )

                if "uploaded_datasets" not in st.session_state:
                    st.session_state.uploaded_datasets = {}

                # Use a key that still matches 'ground_truth' for the evaluation UI
                dataset_key = "ground_truth_flexible_current"
                st.session_state.uploaded_datasets[dataset_key] = dataset

                csv_bytes = df_aligned.to_csv(index=False).encode("utf-8")
                st.session_state["aligned_csv_current_ground_truth"] = (
                    gt_file.name,
                    csv_bytes,
                )

                st.success("Flexible ground truth dataset is now registered for evaluation.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Flexible GT alignment failed: {exc}")

    def _render_flexible_bm_wizard(self):
        """Guided wizard for aligning a benchmark/results dataset to the flexible schema."""
        bm_file = st.file_uploader(
            "Benchmark results CSV/Excel for flexible alignment",
            type=["csv", "xlsx", "xls"],
            key="flex_bm_file",
        )
        if bm_file is None:
            return

        ext = bm_file.name.split(".")[-1].lower()
        if ext in ["xlsx", "xls"]:
            df_raw = pd.read_excel(bm_file)
        else:
            df_raw = pd.read_csv(bm_file)

        if df_raw.empty:
            st.warning("Uploaded benchmark file is empty.")
            return

        st.write("Preview of uploaded benchmark data:")
        st.dataframe(df_raw.head(), use_container_width=True)

        cols = list(df_raw.columns)
        cols_lower = {c.lower(): c for c in cols}

        # Query linkage
        has_query_id_col = any(c.lower() == "query_id" for c in cols)
        eval_mode = st.session_state.get("evaluation_mode")
        if eval_mode == "Classification":
            # Classification mode: query_id is not used for metrics, but we still
            # let the user label report and criteria columns for context and
            # for potential grouping in future analyses.
            st.markdown("Step 1 – Add context (optional)**")
            doc_options = ["<none>", *cols]
            default_doc_idx = 0
            for cand in ("document", "report", "report_name", "doc_id", "company"):
                if cand in cols_lower:
                    default_doc_idx = doc_options.index(cols_lower[cand])
                    break
            document_sel = st.selectbox(
                "Report or document:",
                options=doc_options,
                index=default_doc_idx,
                key="flex_bm_document_col",
            )
            document_col = None if document_sel == "<none>" else document_sel

            default_q = cols[0]
            for cand in ("description", "question", "criteria", "prompt"):
                if cand in cols_lower:
                    default_q = cols_lower[cand]
                    break
            question_col = st.selectbox(
                "Question or criteria:",
                options=cols,
                index=cols.index(default_q) if default_q in cols else 0,
                key="flex_bm_question_col",
            )
            # We don't configure qid_col explicitly; align_benchmark_flexible will
            # derive query_id from document/question as needed.
            qid_col = None
        else:
            st.markdown("**Step 1 – Identify the query**")
            query_id_options = ["<compute from document/question>", *cols]
            default_qid_idx = 0
            if has_query_id_col:
                default_qid_idx = query_id_options.index(next(c for c in cols if c.lower() == "query_id"))
            query_id_sel = st.selectbox(
                "How should the query be identified?",
                options=query_id_options,
                index=default_qid_idx,
                key="flex_bm_query_id_strategy",
            )
            if query_id_sel == "<compute from document/question>":
                qid_col = None
                # Need document and question/description columns
                doc_options = ["<none>", *cols]
                default_doc_idx = 0
                for cand in ("document", "report", "report_name", "doc_id"):
                    if cand in cols_lower:
                        default_doc_idx = doc_options.index(cols_lower[cand])
                        break
                document_sel = st.selectbox(
                    "Report or document ",
                    help=("must match the ground-truth file"),
                    options=doc_options,
                    index=default_doc_idx,
                    key="flex_bm_document_col",
                )
                document_col = None if document_sel == "<none>" else document_sel

                default_q = cols[0]
                for cand in ("description", "question", "criteria", "prompt"):
                    if cand in cols_lower:
                        default_q = cols_lower[cand]
                        break
                question_col = st.selectbox(
                    "Question or criteria ",
                    help=("must match the ground-truth file"),
                    options=cols,
                    index=cols.index(default_q) if default_q in cols else 0,
                    key="flex_bm_question_col",
                )
            else:
                qid_col = query_id_sel
                document_col = None
                question_col = None

        # Chunk & optional relevant part
        st.markdown("**Step 2 – Select the retrieved text**")
        default_chunk = cols[0]
        for cand in ("chunk_text", "paragraph", "context", "text"):
            if cand in cols_lower:
                default_chunk = cols_lower[cand]
                break
        chunk_text_col = st.selectbox(
            "Retrieved text or paragraph",
            options=cols,
            index=cols.index(default_chunk) if default_chunk in cols else 0,
            key="flex_bm_chunk_col",
        )

        rel_options = ["<none>", *cols]
        default_rel_idx = 0
        for cand in ("relevant_part_text_pred", "relevant_text_pred", "relevant_text"):
            if cand in cols_lower:
                default_rel_idx = rel_options.index(cols_lower[cand])
                break
        rel_sel = st.selectbox(
            "Relevant text span (optional)",
            help=(
                "Select this when your benchmark contains the specific text span "
                "that should match the relevant part in the ground-truth dataset."
            ),
            options=rel_options,
            index=default_rel_idx,
            key="flex_bm_relevant_col",
        )
        relevant_part_col = None if rel_sel == "<none>" else rel_sel

        # Detect if we are in classification mode. In that case, we want the
        # wizard to also capture which column is the ground-truth label and
        # which columns are model predictions so that the evaluation tab can
        # pre-populate the calibration UI.
        is_classification_mode = st.session_state.get("evaluation_mode") == "Classification"

        # Prediction & similarity columns
        st.markdown("**Step 3 - Model scores and ranking signal**")
        df_sample = df_raw.head(50)
        numeric_cols = df_sample.select_dtypes(include=["number"]).columns.tolist()
        pred_suggestions = set()
        for c in cols:
            cl = c.lower()
            if any(
                x in cl
                for x in (
                    "score",
                    "sim",
                    "prob",
                    "logit",
                    "confidence",
                    "relevance",
                    "usefulness",
                )
            ):
                pred_suggestions.add(c)
        if not pred_suggestions:
            pred_suggestions.update(numeric_cols)

        sorted(pred_suggestions)

        classification_label_col = None
        if is_classification_mode:
            st.markdown("**Step 3a - Ground-truth label used for classification metrics**")
            # Heuristic: prefer 'relevance' or 'usefulness' as label.
            default_label = cols[0]
            for cand in ("relevance", "usefulness", "label", "class"):
                for c in cols:
                    if c.lower() == cand:
                        default_label = c
                        break
                else:
                    continue
                break
            classification_label_col = st.selectbox(
                "Column with expert labels (e.g. relevance or usefulness):",
                options=cols,
                index=cols.index(default_label) if default_label in cols else 0,
                key="flex_bm_classification_label_col",
            )

        st.markdown("**Step 3b - Prediction / score columns from your models**")
        prediction_cols = st.multiselect(
            "Select model prediction / score column(s) (e.g. similarity, relevance_score_*):",
            options=cols,
            default=[],
            key="flex_bm_prediction_cols",
        )

        ranking_score_col = None
        if prediction_cols:
            ranking_score_col = st.selectbox(
                "Which score should be used to rank chunks and decide top-K relevance?",
                options=prediction_cols,
                index=0,
                key="flex_bm_ranking_score_col",
            )

        if st.button(
            "Align benchmark (flexible) and use for evaluation",
            key="flex_bm_align_button",
        ):
            try:
                bm_config = BenchmarkAlignConfig(
                    document_col=document_col,
                    question_col=question_col,
                    query_id_col=qid_col,
                    chunk_text_col=chunk_text_col,
                    relevant_part_col=relevant_part_col,
                    prediction_cols=prediction_cols,
                    ranking_score_col=ranking_score_col,
                )
                df_aligned = align_benchmark_flexible(df_raw, bm_config)

                # In classification mode, ensure the chosen ground-truth label
                # column is preserved in the aligned DataFrame so that the
                # evaluation tab can see and use it.
                if is_classification_mode and classification_label_col:
                    if classification_label_col in df_raw.columns:
                        df_aligned[classification_label_col] = df_raw[classification_label_col].values

                st.success(f"Aligned flexible benchmark: {len(df_aligned)} rows, {df_aligned['query_id'].nunique()} queries.")
                st.dataframe(df_aligned.head(), use_container_width=True)

                results: List[FlexibleDatasetRow] = []
                for _, row in df_aligned.iterrows():
                    row_dict: Dict[str, Any] = {}
                    for col in df_aligned.columns:
                        val = row[col]
                        row_dict[col] = None if pd.isna(val) else val
                    results.append(FlexibleDatasetRow(data=row_dict))

                dataset = BenchmarkDataset(
                    dataset_id=f"benchmark_flexible_{bm_file.name}",
                    name=f"BM flexible ({bm_file.name})",
                    description="Benchmark dataset aligned via flexible wizard",
                    version="1.0",
                    dataset_type=DatasetType.INFORMATION_RETRIEVAL,
                    source="csv",
                    source_path=None,
                    column_mapping={
                        # Remember classification defaults (if any) so that the
                        # calibration panel can pre-populate label/prediction
                        # selections without forcing the user to configure them again.
                        "classification_label_col": (classification_label_col if is_classification_mode else ""),
                        # Store prediction columns as a single comma-separated string
                        # to keep column_mapping values as simple scalars.
                        "classification_prediction_cols": (",".join(prediction_cols) if is_classification_mode else ""),
                    },
                    results=results,
                )

                if "uploaded_datasets" not in st.session_state:
                    st.session_state.uploaded_datasets = {}

                dataset_key = "benchmark_flexible_current"
                st.session_state.uploaded_datasets[dataset_key] = dataset

                csv_bytes = df_aligned.to_csv(index=False).encode("utf-8")
                st.session_state["aligned_csv_current_benchmark"] = (
                    bm_file.name,
                    csv_bytes,
                )

                st.success("Flexible benchmark dataset is now registered for evaluation.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Flexible benchmark alignment failed: {exc}")

    def _render_config_form(self) -> RetrievalConfig:
        """Render retrieval configuration form"""
        col1, col2, col3 = st.columns(3)

        with col1:
            chunk_size = st.number_input("Chunk Size", min_value=100, max_value=2000, value=1000)
            chunk_overlap = st.number_input("Chunk Overlap", min_value=0, max_value=500, value=200)

        with col2:
            top_k = st.number_input("Top K", min_value=1, max_value=20, value=5)
            use_llm_scoring = st.checkbox("Use LLM Scoring", value=False)

        with col3:
            embedding_model = st.selectbox("Embedding Model", ["default", "openai", "sentence-transformers"])
            similarity_threshold = st.slider("Similarity Threshold", 0.0, 1.0, 0.0, 0.1)

        llm_model = None
        if use_llm_scoring:
            llm_model = st.selectbox("LLM Model", ["gpt-4o-mini", "gpt-4o", "gemini-1.5-flash"])

        return RetrievalConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            use_llm_scoring=use_llm_scoring,
            embedding_model=embedding_model,
            similarity_threshold=similarity_threshold,
            llm_model=llm_model,
        )

    def _run_evaluation(self, dataset_id: str, evaluation_name: str, config: RetrievalConfig):
        """Run benchmark evaluation"""
        # This would integrate with the existing analyzer
        st.info("Evaluation functionality would integrate with the existing DocumentAnalyzer here.")
        # For now, create a placeholder evaluation

        # Save evaluation (placeholder)
        from ..models.benchmark import EvaluationMetrics

        placeholder_metrics = EvaluationMetrics(
            precision_at_k={1: 0.8, 3: 0.7, 5: 0.6},
            recall_at_k={1: 0.2, 3: 0.4, 5: 0.6},
            f1_at_k={1: 0.32, 3: 0.51, 5: 0.6},
            mean_reciprocal_rank=0.75,
            mean_average_precision=0.65,
            ndcg_at_k={1: 0.8, 3: 0.72, 5: 0.68},
        )

        evaluation = BenchmarkEvaluation(
            dataset_id=dataset_id,
            evaluation_name=evaluation_name,
            config_hash="",
            retrieval_config=config,
            evaluation_metrics=placeholder_metrics,
        )

        eval_id = self.benchmark_store.save_evaluation(evaluation)
        st.success(f"Evaluation '{evaluation_name}' completed and saved with ID {eval_id}")

    def _render_results_table(self, evaluations):
        """Render evaluation results table"""
        results_data = []
        for eval in evaluations:
            metrics = getattr(eval, "evaluation_metrics", None)
            if not metrics:
                continue

            eval_name = getattr(eval, "evaluation_name", "Unknown")
            dataset_id = getattr(eval, "dataset_id", "N/A")
            created_at = getattr(eval, "created_at", None)

            results_data.append(
                {
                    "Model": eval_name,
                    "Dataset": dataset_id,
                    "MAP": f"{metrics.mean_average_precision:.3f}",
                    "MRR": f"{metrics.mean_reciprocal_rank:.3f}",
                    "P@5": f"{metrics.precision_at_k.get(5, 0):.3f}",
                    "R@5": f"{metrics.recall_at_k.get(5, 0):.3f}",
                    "F1@5": f"{metrics.f1_at_k.get(5, 0):.3f}",
                    "NDCG@5": f"{metrics.ndcg_at_k.get(5, 0):.3f}",
                    "Date": (
                        created_at.strftime("%Y-%m-%d")
                        if created_at and hasattr(created_at, "strftime")
                        else (str(created_at) if created_at else "Unknown")
                    ),
                }
            )

        if results_data:
            df = pd.DataFrame(results_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No evaluation results to display.")

    def _render_metrics_charts(self, evaluations):
        """Render metrics visualization charts"""
        if len(evaluations) < 1:
            return

        # Prepare data for plotting
        chart_data = []
        for eval in evaluations:
            metrics = getattr(eval, "evaluation_metrics", None)
            if not metrics:
                continue

            eval_name = getattr(eval, "evaluation_name", "Unknown")

            # Get all available K values
            k_values = sorted(metrics.precision_at_k.keys())
            for k in k_values:
                chart_data.append(
                    {
                        "Model": eval_name,
                        "K": k,
                        "Precision": metrics.precision_at_k.get(k, 0.0),
                        "Recall": metrics.recall_at_k.get(k, 0.0),
                        "F1": metrics.f1_at_k.get(k, 0.0),
                        "NDCG": metrics.ndcg_at_k.get(k, 0.0),
                    }
                )

        if not chart_data:
            return

        df = pd.DataFrame(chart_data)

        # Create charts
        col1, col2 = st.columns(2)

        with col1:
            fig = px.line(
                df,
                x="K",
                y="Precision",
                color="Model",
                title="Precision@K by Model",
                markers=True,
            )
            st.plotly_chart(fig, use_container_width=True, key="results_precision_chart")

        with col2:
            fig = px.line(
                df,
                x="K",
                y="Recall",
                color="Model",
                title="Recall@K by Model",
                markers=True,
            )
            st.plotly_chart(fig, use_container_width=True, key="results_recall_chart")

        col3, col4 = st.columns(2)
        with col3:
            fig = px.line(
                df,
                x="K",
                y="F1",
                color="Model",
                title="F1@K by Model",
                markers=True,
            )
            st.plotly_chart(fig, use_container_width=True, key="results_f1_chart")
        with col4:
            fig = px.line(
                df,
                x="K",
                y="NDCG",
                color="Model",
                title="NDCG@K by Model",
                markers=True,
            )
            st.plotly_chart(fig, use_container_width=True, key="results_ndcg_chart")

    def _show_dataset_details(self, dataset_id: str):
        """Show detailed dataset information"""
        dataset = self.benchmark_store.get_dataset(dataset_id)
        if dataset:
            st.write(f"**Name:** {dataset.name}")
            st.write(f"**Description:** {dataset.description}")
            st.write(f"**Version:** {dataset.version}")
            st.write(f"**Question Set:** {dataset.question_set}")

            # Show ground truth statistics
            ground_truth = self.benchmark_store.get_ground_truth(dataset_id)
            total_questions = len(ground_truth)
            total_chunks = sum(len(chunks) for chunks in ground_truth.values())
            st.write(f"**Questions:** {total_questions}")
            st.write(f"**Total Chunks:** {total_chunks}")

    def _delete_dataset(self, dataset_id: str):
        """Delete a dataset"""
        if st.button(f"Confirm deletion of {dataset_id}", type="secondary"):
            if self.benchmark_store.delete_dataset(dataset_id):
                st.success(f"Dataset {dataset_id} deleted successfully!")
                st.rerun()
            else:
                st.error("Failed to delete dataset")

    def _render_evaluation_details(self, evaluation):
        """Render detailed evaluation information"""
        eval_name = getattr(evaluation, "evaluation_name", "Unknown")
        st.subheader(f"Evaluation: {eval_name}")

        # Configuration (if available)
        if hasattr(evaluation, "retrieval_config") and evaluation.retrieval_config:
            config = evaluation.retrieval_config
            st.write("**Configuration:**")
            if hasattr(config, "model_dump"):
                config_dict = config.model_dump()
            else:
                config_dict = dict(config) if isinstance(config, dict) else {}
            st.json(config_dict)

        # Metrics - show only JSON format in details, tables and charts are already shown above
        if hasattr(evaluation, "evaluation_metrics") and evaluation.evaluation_metrics:
            metrics = evaluation.evaluation_metrics
            st.write("**Metrics (JSON):**")
            if hasattr(metrics, "model_dump"):
                metrics_dict = metrics.model_dump()
            else:
                metrics_dict = dict(metrics) if isinstance(metrics, dict) else {}
            st.json(metrics_dict)

    def _render_annotation_form(self, evaluation: BenchmarkEvaluation):
        """Render annotation form for an evaluation"""
        st.write(f"Annotating evaluation: **{evaluation.evaluation_name}**")

        # This would show the retrieved chunks for annotation
        st.info("Annotation interface would show retrieved chunks here for human evaluation.")

        # Placeholder annotation form
        st.text_input("Annotator ID", value="annotator_1")

        if st.button("Save Annotations"):
            st.success("Annotations saved! (This is a placeholder)")

    def _render_csv_metrics_table(self, metrics, k_values: Optional[List[int]]):
        """Render metrics table for CSV evaluation results"""
        st.subheader("Metrics Summary")

        if k_values is None or not k_values:
            k_values = sorted(metrics.precision_at_k.keys())

        # Prepare table data
        table_data = {
            "Metric": ["MAP", "MRR"],
            "Value": [
                f"{metrics.mean_average_precision:.4f}",
                f"{metrics.mean_reciprocal_rank:.4f}",
            ],
        }

        # Add metrics at K
        for k in sorted(k_values):
            table_data[f"K={k}"] = [
                f"{metrics.precision_at_k.get(k, 0.0):.4f}",
                f"{metrics.recall_at_k.get(k, 0.0):.4f}",
            ]

        df_summary = pd.DataFrame(table_data)

        # Create detailed metrics table
        detailed_data = []
        for k in sorted(k_values):
            detailed_data.append(
                {
                    "K": k,
                    "Precision@K": f"{metrics.precision_at_k.get(k, 0.0):.4f}",
                    "Recall@K": f"{metrics.recall_at_k.get(k, 0.0):.4f}",
                    "F1@K": f"{metrics.f1_at_k.get(k, 0.0):.4f}",
                    "NDCG@K": f"{metrics.ndcg_at_k.get(k, 0.0):.4f}",
                }
            )

        df_detailed = pd.DataFrame(detailed_data)

        # Display tables
        st.write("**Overall Metrics:**")
        st.dataframe(df_summary, use_container_width=True, hide_index=True)

        st.write("**Metrics at K:**")
        st.dataframe(df_detailed, use_container_width=True, hide_index=True)

    def _render_csv_metrics_charts(self, metrics, k_values: Optional[List[int]], chart_key_prefix: str = "csv"):
        """Render Plotly charts for CSV evaluation results"""
        st.subheader("Visualization")

        if k_values is None or not k_values:
            k_values = sorted(metrics.precision_at_k.keys())

        if not k_values:
            st.warning("No K values available for plotting.")
            return

        # Prepare data for plotting
        chart_data = []
        for k in sorted(k_values):
            chart_data.append(
                {
                    "K": k,
                    "Precision": metrics.precision_at_k.get(k, 0.0),
                    "Recall": metrics.recall_at_k.get(k, 0.0),
                    "F1": metrics.f1_at_k.get(k, 0.0),
                    "NDCG": metrics.ndcg_at_k.get(k, 0.0),
                }
            )

        df_chart = pd.DataFrame(chart_data)

        # Create charts side by side
        col1, col2 = st.columns(2)

        with col1:
            fig_precision = px.line(
                df_chart,
                x="K",
                y="Precision",
                title="Precision@K",
                markers=True,
            )
            fig_precision.update_layout(
                xaxis_title="K",
                yaxis_title="Precision",
                yaxis_range=[0, 1.1],
            )
            st.plotly_chart(
                fig_precision,
                use_container_width=True,
                key=f"{chart_key_prefix}_precision_{id(metrics)}",
            )

        with col2:
            fig_recall = px.line(
                df_chart,
                x="K",
                y="Recall",
                title="Recall@K",
                markers=True,
            )
            fig_recall.update_layout(
                xaxis_title="K",
                yaxis_title="Recall",
                yaxis_range=[0, 1.1],
            )
            st.plotly_chart(
                fig_recall,
                use_container_width=True,
                key=f"{chart_key_prefix}_recall_{id(metrics)}",
            )
