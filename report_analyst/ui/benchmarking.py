import json
import logging
import sqlite3
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..core.benchmark.dataset_loader import DatasetLoader, DatasetValidationError
from ..core.benchmark.dataset_mapper import (
    DatasetMapperFactory,
    list_available_dataset_ids,
)
from ..core.benchmark.error_analysis import (
    build_error_analysis_dataframe,
    build_error_analysis_dataframe_from_flexible,
)
from ..core.benchmark.evaluation_engine import EvaluationEngine
from ..core.benchmark.retrieval_results_loader import (
    load_flexible_dataset_from_csv,
    load_retrieval_results_from_csv,
)
from ..core.storage.benchmark_store import BenchmarkStore
from ..models.benchmark import BenchmarkEvaluation, HumanAnnotation, RetrievalConfig

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

        # Expected file formats (expandable)
        with st.expander("Expected file formats (CSV, Excel, YAML, JSON)"):
            st.markdown(
                "**CSV / Excel (ground truth or benchmark)** — For evaluation, the app expects "
                "columns such as: `query_id` (or `question_id`), `chunk_id`, `position` (or `rank`), "
                "`score` (or `relevance_score`). Ground truth alignment expects: `document`, `question`, "
                "`context` or `relevant`, `relevance_label`. Benchmark alignment expects: `report`, "
                "`question`, `paragraph`, and optionally `relevant_text`, `relevant_text_sim`. "
                "Column names are case-insensitive; common variants are accepted. If your file does not "
                "match, use **Dataset Alignment** (CSV/Excel only) to convert it."
            )
            st.markdown(
                "**YAML / JSON** — Benchmark content schema: top-level `dataset_id`, `name`, "
                "`description`, `version`, `question_set`, and `questions` (array of `question_id`, "
                "`question_text`, `ground_truth_chunks` with `chunk_id`, `relevance_score`, `is_evidence`). "
                "Alignment is not available for YAML/JSON; use CSV/Excel for alignment."
            )
            st.caption(
                "Full details: see EXPECTED_FILE_FORMATS.md in the project root."
            )

        # Initialize session state for uploaded datasets if not exists
        if "uploaded_datasets" not in st.session_state:
            st.session_state.uploaded_datasets = {}

        # Dataset upload section with tabs for ground truth and benchmark
        upload_tab1, upload_tab2 = st.tabs(
            ["Upload Ground Truth Dataset", "Upload Benchmark Dataset"]
        )

        with upload_tab1:
            st.write("Upload a ground truth/reference dataset file")
            uploaded_ground_truth = st.file_uploader(
                "Choose a ground truth dataset file",
                type=["yaml", "yml", "json", "csv", "xlsx", "xls"],
                help="Upload a YAML, JSON, CSV, or Excel file containing ground truth data",
                key="ground_truth_uploader",
            )

            # Always handle the uploaded file on each rerun so that actions
            # like "Align dataset and use for evaluation" are processed.
            if uploaded_ground_truth is not None:
                self._handle_dataset_upload(
                    uploaded_ground_truth, dataset_type="ground_truth"
                )

        with upload_tab2:
            st.write("Upload a benchmark/results dataset file")
            uploaded_benchmark = st.file_uploader(
                "Choose a benchmark dataset file",
                type=["yaml", "yml", "json", "csv", "xlsx", "xls"],
                help="Upload a YAML, JSON, CSV, or Excel file containing benchmark results",
                key="benchmark_uploader",
            )

            if uploaded_benchmark is not None:
                self._handle_dataset_upload(
                    uploaded_benchmark, dataset_type="benchmark"
                )

        # Offer download of aligned datasets (when user previously aligned and used one)
        aligned_gt = st.session_state.get("aligned_csv_current_ground_truth")
        aligned_bm = st.session_state.get("aligned_csv_current_benchmark")
        if aligned_gt or aligned_bm:
            st.subheader("Download aligned datasets")
            st.caption(
                "You have aligned dataset(s) in use. Download the aligned CSV version below."
            )
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

        # List existing datasets
        st.subheader("Existing Datasets")
        try:
            datasets = self.benchmark_store.list_datasets()
        except sqlite3.OperationalError as e:
            st.warning("Database not initialized. Please restart the application.")
            logger.error(f"Database error: {e}")
            datasets = []

        if not datasets:
            st.info("No datasets uploaded yet. Upload a dataset to get started.")
            return

        # Display datasets in a table
        dataset_data = []
        for dataset in datasets:
            dataset_data.append(
                {
                    "Dataset ID": dataset.dataset_id,
                    "Name": dataset.name,
                    "Question Set": dataset.question_set,
                    "Version": dataset.version,
                    "Created": (
                        dataset.created_at.strftime("%Y-%m-%d %H:%M")
                        if dataset.created_at
                        else "Unknown"
                    ),
                }
            )

        df = pd.DataFrame(dataset_data)
        st.dataframe(df, use_container_width=True)

        # Dataset actions
        if datasets:
            selected_dataset = st.selectbox(
                "Select dataset for actions:",
                options=[d.dataset_id for d in datasets],
                format_func=lambda x: next(
                    d.name for d in datasets if d.dataset_id == x
                ),
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("View Details"):
                    self._show_dataset_details(selected_dataset)

            with col2:
                if st.button("Delete Dataset", type="secondary"):
                    self._delete_dataset(selected_dataset)

        # ------------------------------------------------------------------
        # Optional: On-the-fly alignment tools using DatasetMapper
        # ------------------------------------------------------------------
        st.subheader("Dataset Alignment (Experimental)")
        st.caption(
            "⚠️ Alignment works only for CSV or Excel files. YAML/JSON datasets are "
            "loaded as-is and cannot be aligned with this tool."
        )

        available_ids = list_available_dataset_ids()
        if not available_ids:
            st.info(
                "No dataset mapping configurations were found. "
                "Add YAML configs under `report_analyst/config/datasets/` to enable this feature."
            )
            return

        selected_mapping_id = st.selectbox(
            "Select dataset mapping configuration:",
            options=available_ids,
            index=(
                available_ids.index("climretrieve")
                if "climretrieve" in available_ids
                else 0
            ),
            help="Determines how raw CSV columns are mapped to the internal benchmark schema.",
        )

        mapper = DatasetMapperFactory.get_mapper(selected_mapping_id)

        align_tab_gt, align_tab_bm = st.tabs(
            ["Align Ground Truth CSV", "Align Benchmark CSV"]
        )

        with align_tab_gt:
            st.write(
                "Upload a **raw ground truth** CSV or Excel file and convert it to the "
                "aligned format used by the evaluation engine."
            )
            raw_gt_file = st.file_uploader(
                "Ground truth file (CSV or Excel)",
                type=["csv", "xlsx", "xls"],
                key="align_ground_truth_csv",
            )
            if raw_gt_file is not None:
                try:
                    ext = raw_gt_file.name.split(".")[-1].lower()
                    if ext in ["xlsx", "xls"]:
                        df_raw = pd.read_excel(raw_gt_file)
                    else:
                        df_raw = pd.read_csv(raw_gt_file)
                    df_aligned = mapper.align_ground_truth(df_raw)
                    st.success(
                        f"Aligned ground truth dataset "
                        f"({len(df_aligned)} rows, {df_aligned['query_id'].nunique()} queries)."
                    )
                    st.dataframe(df_aligned.head(), use_container_width=True)

                    csv_bytes = df_aligned.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Download aligned ground truth CSV",
                        data=csv_bytes,
                        file_name="ground_truth_aligned.csv",
                        mime="text/csv",
                    )
                except Exception as exc:  # pragma: no cover - UI feedback
                    st.error(f"Failed to align ground truth dataset: {exc}")
                    logger.error(
                        "Ground truth alignment failed: %s", exc, exc_info=True
                    )

        with align_tab_bm:
            st.write(
                "Upload a **raw benchmark results** CSV or Excel file and convert it to "
                "the aligned format used by the evaluation engine."
            )
            raw_bm_file = st.file_uploader(
                "Benchmark results file (CSV or Excel)",
                type=["csv", "xlsx", "xls"],
                key="align_benchmark_csv",
            )
            if raw_bm_file is not None:
                try:
                    ext = raw_bm_file.name.split(".")[-1].lower()
                    if ext in ["xlsx", "xls"]:
                        df_raw = pd.read_excel(raw_bm_file)
                    else:
                        df_raw = pd.read_csv(raw_bm_file)
                    df_aligned = mapper.align_benchmark(df_raw)
                    st.success(
                        f"Aligned benchmark results "
                        f"({len(df_aligned)} rows, {df_aligned['query_id'].nunique()} queries)."
                    )
                    st.dataframe(df_aligned.head(), use_container_width=True)

                    csv_bytes = df_aligned.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Download aligned benchmark CSV",
                        data=csv_bytes,
                        file_name="benchmark_aligned.csv",
                        mime="text/csv",
                    )
                except Exception as exc:  # pragma: no cover - UI feedback
                    st.error(f"Failed to align benchmark dataset: {exc}")
                    logger.error("Benchmark alignment failed: %s", exc, exc_info=True)

    def render_benchmarking_interface(self):
        """Render benchmarking interface"""
        st.subheader("Run Benchmark Evaluation")

        # Get datasets from both database and session state (uploaded files)
        db_datasets = []
        try:
            db_datasets = self.benchmark_store.list_datasets()
        except sqlite3.OperationalError:
            pass

        uploaded_datasets = st.session_state.get("uploaded_datasets", {})

        # Check for unconfirmed datasets and show helpful message
        temp_datasets = {
            k: v for k, v in uploaded_datasets.items() if k.startswith("temp_")
        }
        if (
            temp_datasets
            and not db_datasets
            and not any(not k.startswith("temp_") for k in uploaded_datasets.keys())
        ):
            st.warning(
                "⚠️ You have uploaded datasets but haven't confirmed them yet. "
                "Please go to the 'Datasets' tab and click 'Confirm and Use This Dataset' "
                "for each uploaded dataset to make them available for evaluation."
            )
            return

        if not db_datasets and not uploaded_datasets:
            st.warning("No datasets available. Please upload datasets first.")
            return

        # Configuration
        col1, col2 = st.columns(2)

        with col1:
            # Select reference/ground truth dataset
            reference_options = {}
            for d in db_datasets:
                reference_options[f"DB: {d.name}"] = ("db", d.dataset_id)

            for key, dataset in uploaded_datasets.items():
                # Only show confirmed datasets (not temporary ones)
                if "ground_truth" in key and not key.startswith("temp_"):
                    reference_options[f"Uploaded: {dataset.name}"] = ("uploaded", key)

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
                    benchmark_options[f"Uploaded: {dataset.name}"] = ("uploaded", key)

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
        st.subheader("Evaluation Configuration")
        col1, col2 = st.columns(2)
        with col1:
            top_k = st.number_input(
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
                k_values = [
                    int(k.strip()) for k in k_values_input.split(",") if k.strip()
                ]
                if not k_values:
                    k_values = None
            except ValueError:
                st.warning("Invalid K values format. Using default values.")
                k_values = None

        # Run evaluation
        if st.button("Run Evaluation", type="primary"):
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

    def render_results_dashboard(self):
        """Render evaluation results dashboard"""
        st.subheader("Evaluation Results")

        # Get evaluations from database
        evaluations = []
        try:
            evaluations = self.benchmark_store.list_evaluations()
        except sqlite3.OperationalError:
            pass

        # Get evaluations from session state (recent CSV evaluations)
        session_evals = st.session_state.get("csv_evaluations", [])

        all_evaluations = evaluations + session_evals

        if not all_evaluations:
            st.info(
                "No evaluations run yet. Run a benchmark evaluation to see results."
            )
            return

        # Filter controls
        col1, col2 = st.columns(2)
        with col1:
            datasets = list(
                set(e.dataset_id for e in all_evaluations if hasattr(e, "dataset_id"))
            )
            if datasets:
                selected_datasets = st.multiselect(
                    "Filter by Dataset:", datasets, default=datasets
                )
            else:
                selected_datasets = []

        with col2:
            # Show all evaluations by default
            pass

        # Filter evaluations
        if selected_datasets:
            filtered_evals = [
                e
                for e in all_evaluations
                if hasattr(e, "dataset_id") and e.dataset_id in selected_datasets
            ]
        else:
            filtered_evals = all_evaluations

        if not filtered_evals:
            st.warning("No evaluations match the selected filters.")
            return

        # Results table - show all results
        self._render_results_table(filtered_evals)

        # Metrics visualization
        self._render_metrics_charts(filtered_evals)

        # Error analysis export for the latest CSV evaluation (session-based)
        self._render_error_analysis_export()

        # Detailed evaluation view
        if filtered_evals:
            eval_options = [
                f"{e.evaluation_name} ({getattr(e, 'dataset_id', 'N/A')})"
                for e in filtered_evals
            ]
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
                    st.error(
                        "Cannot determine datasets for error analysis from evaluation metadata."
                    )
                    return

                uploaded_datasets = st.session_state.get("uploaded_datasets", {})
                ground_truth_ds = uploaded_datasets.get(ref_id)
                benchmark_ds = uploaded_datasets.get(bench_id)

                if not ground_truth_ds or not benchmark_ds:
                    st.error(
                        "Could not locate the ground truth and benchmark datasets used for this evaluation."
                    )
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
            except Exception as e:
                st.error(f"Failed to build error-analysis CSV: {str(e)}")

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

    def _run_csv_evaluation_from_datasets(
        self, ref_source, ref_id, bench_source, bench_id, k_values, evaluation_name
    ):
        """Run evaluation using selected datasets from database or uploaded files"""
        try:
            with st.spinner("Loading datasets and calculating metrics..."):
                # Load reference dataset
                if ref_source == "db":
                    # Load from database (would need to convert from BenchmarkDatasetContent)
                    st.error(
                        "Database dataset evaluation not yet implemented. Please use uploaded CSV/Excel files."
                    )
                    return
                else:
                    # Load from session state
                    reference_dataset = st.session_state.uploaded_datasets.get(ref_id)
                    if not reference_dataset:
                        st.error(f"Reference dataset {ref_id} not found.")
                        return

                # Load benchmark dataset
                if bench_source == "db":
                    st.error(
                        "Database dataset evaluation not yet implemented. Please use uploaded CSV/Excel files."
                    )
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

            from ..models.benchmark import BenchmarkEvaluation, RetrievalConfig

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
            st.error(f"Error loading datasets: {str(e)}")
            logger.exception("Dataset loading error")
        except Exception as e:
            st.error(f"Error during evaluation: {str(e)}")
            logger.exception("Evaluation error")

    def _render_confirmation_ui(
        self, dataset, temp_key: str, dataset_type: str, file_name: str
    ):
        """Render confirmation UI for an unconfirmed dataset"""
        st.info(
            f"📋 **{dataset.name}** ({len(dataset.results)} rows) - Pending confirmation"
        )

        # Show basic info
        st.write(f"**Dataset Name:** {dataset.name}")
        st.write(f"**Number of rows:** {len(dataset.results)}")

        # Confirm save - this will replace any existing dataset of the same type
        col1, col2 = st.columns(2)
        with col1:
            button_key = f"confirm_{dataset_type}_{file_name}"
            if st.button(
                "Confirm and Use This Dataset", key=button_key, type="primary"
            ):
                dataset_key = f"{dataset_type}_current"

                # Remove old dataset of the same type if it exists
                if dataset_key in st.session_state.uploaded_datasets:
                    old_dataset = st.session_state.uploaded_datasets[dataset_key]
                    st.info(
                        f"Replacing previous {dataset_type} dataset: {old_dataset.name}"
                    )

                # Save the new dataset
                st.session_state.uploaded_datasets[dataset_key] = dataset

                # Remove temporary key
                if temp_key in st.session_state.uploaded_datasets:
                    del st.session_state.uploaded_datasets[temp_key]

                st.success(
                    f"Dataset '{dataset.name}' confirmed and ready for evaluation!"
                )
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
            for i, result in enumerate(dataset.results[:5]):
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
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{file_ext}"
            ) as tmp_file:
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

                    # If this file has already been aligned and registered for this
                    # dataset_type, avoid re-showing the schema warning on rerun.
                    aligned_flag_key = f"aligned_{dataset_type}_{uploaded_file.name}"
                    dataset_key = f"{dataset_type}_current"
                    if (
                        st.session_state.get(aligned_flag_key)
                        and "uploaded_datasets" in st.session_state
                        and dataset_key in st.session_state.uploaded_datasets
                    ):
                        aligned_dataset = st.session_state.uploaded_datasets[
                            dataset_key
                        ]
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
                    except Exception as exc:  # pragma: no cover - UI fallback
                        load_error = exc

                    if dataset is not None:
                        st.success(
                            f"Dataset loaded successfully from {file_ext.upper()} file!"
                        )

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
                                    old_dataset = st.session_state.uploaded_datasets[
                                        dataset_key
                                    ]
                                    st.info(
                                        f"Replacing previous {dataset_type} dataset: {old_dataset.name}"
                                    )

                                # Save the new dataset
                                st.session_state.uploaded_datasets[dataset_key] = (
                                    dataset
                                )

                                # Remove temporary key
                                if temp_key in st.session_state.uploaded_datasets:
                                    del st.session_state.uploaded_datasets[temp_key]

                                # Clear any previously stored aligned CSV for this type
                                st.session_state.pop(
                                    f"aligned_csv_current_{dataset_type}", None
                                )

                                st.success(
                                    f"Dataset '{dataset.name}' confirmed and ready for evaluation!"
                                )
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
                            for i, result in enumerate(dataset.results[:5]):
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
                        st.warning(
                            "This file does not match the expected benchmark CSV schema "
                            "used by the evaluation engine."
                        )
                        st.caption(
                            "Alignment is available for CSV and Excel files only."
                        )
                        if load_error is not None:
                            st.caption(f"Details: {load_error}")

                        available_ids = list_available_dataset_ids()
                        if not available_ids:
                            st.info(
                                "No dataset mapping configurations were found. "
                                "Add YAML configs under "
                                "`report_analyst/config/datasets/` to enable alignment."
                            )
                        else:
                            selected_mapping_id = st.selectbox(
                                "Select mapping configuration to align this dataset:",
                                options=available_ids,
                                index=(
                                    available_ids.index("climretrieve")
                                    if "climretrieve" in available_ids
                                    else 0
                                ),
                                key=f"align_cfg_{dataset_type}_{uploaded_file.name}",
                            )

                            # If we just aligned for download, show the download button
                            download_key = f"aligned_csv_download_{dataset_type}_{uploaded_file.name}"
                            if st.session_state.get(download_key) is not None:
                                csv_bytes = st.session_state[download_key]
                                st.success("Aligned file is ready. Download it below.")
                                st.download_button(
                                    label="Download aligned CSV",
                                    data=csv_bytes,
                                    file_name=(
                                        "ground_truth_aligned.csv"
                                        if dataset_type == "ground_truth"
                                        else "benchmark_aligned.csv"
                                    ),
                                    mime="text/csv",
                                    key=f"dl_aligned_{dataset_type}_{uploaded_file.name}",
                                )
                                st.caption(
                                    "You can also 'Align and use for evaluation' to use "
                                    "this dataset for evaluation."
                                )

                            col_align_use, col_align_dl = st.columns(2)
                            with col_align_use:
                                if st.button(
                                    "Align dataset and use for evaluation",
                                    key=f"align_and_use_{dataset_type}_{uploaded_file.name}",
                                ):
                                    mapper = DatasetMapperFactory.get_mapper(
                                        selected_mapping_id
                                    )
                                    if dataset_type == "ground_truth":
                                        df_aligned = mapper.align_ground_truth(df_raw)
                                    else:
                                        df_aligned = mapper.align_benchmark(df_raw)

                                    csv_aligned = df_aligned.to_csv(index=False)
                                    csv_bytes = csv_aligned.encode("utf-8")
                                    aligned_dataset = load_flexible_dataset_from_csv(
                                        csv_content=csv_aligned,
                                        dataset_name=(
                                            f"{dataset_type}_aligned_{uploaded_file.name}"
                                        ),
                                    )

                                    temp_key = f"temp_{dataset_type}_aligned_{uploaded_file.name}"
                                    if "uploaded_datasets" not in st.session_state:
                                        st.session_state.uploaded_datasets = {}
                                    st.session_state.uploaded_datasets[temp_key] = (
                                        aligned_dataset
                                    )

                                    dataset_key = f"{dataset_type}_current"
                                    st.session_state.uploaded_datasets[dataset_key] = (
                                        aligned_dataset
                                    )

                                    if temp_key in st.session_state.uploaded_datasets:
                                        del st.session_state.uploaded_datasets[temp_key]

                                    aligned_flag_key = (
                                        f"aligned_{dataset_type}_{uploaded_file.name}"
                                    )
                                    st.session_state[aligned_flag_key] = True

                                    # Store aligned CSV so user can download it later
                                    st.session_state[
                                        f"aligned_csv_current_{dataset_type}"
                                    ] = (uploaded_file.name, csv_bytes)

                                    st.success(
                                        "Dataset was aligned to the expected structure and "
                                        "is now ready for evaluation."
                                    )
                                    st.rerun()

                            with col_align_dl:
                                if st.button(
                                    "Align and download CSV",
                                    key=f"align_and_download_{dataset_type}_{uploaded_file.name}",
                                ):
                                    mapper = DatasetMapperFactory.get_mapper(
                                        selected_mapping_id
                                    )
                                    if dataset_type == "ground_truth":
                                        df_aligned = mapper.align_ground_truth(df_raw)
                                    else:
                                        df_aligned = mapper.align_benchmark(df_raw)
                                    csv_bytes = df_aligned.to_csv(index=False).encode(
                                        "utf-8"
                                    )
                                    st.session_state[download_key] = csv_bytes
                                    st.rerun()

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
            st.error(f"Failed to load dataset: {str(e)}")
            logger.exception("Dataset loading error")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            logger.exception("Unexpected error during dataset upload")

        finally:
            # Clean up temp file
            if tmp_path:
                try:
                    Path(tmp_path).unlink()
                except:
                    pass

    def _render_config_form(self) -> RetrievalConfig:
        """Render retrieval configuration form"""
        col1, col2, col3 = st.columns(3)

        with col1:
            chunk_size = st.number_input(
                "Chunk Size", min_value=100, max_value=2000, value=1000
            )
            chunk_overlap = st.number_input(
                "Chunk Overlap", min_value=0, max_value=500, value=200
            )

        with col2:
            top_k = st.number_input("Top K", min_value=1, max_value=20, value=5)
            use_llm_scoring = st.checkbox("Use LLM Scoring", value=False)

        with col3:
            embedding_model = st.selectbox(
                "Embedding Model", ["default", "openai", "sentence-transformers"]
            )
            similarity_threshold = st.slider("Similarity Threshold", 0.0, 1.0, 0.0, 0.1)

        llm_model = None
        if use_llm_scoring:
            llm_model = st.selectbox(
                "LLM Model", ["gpt-4o-mini", "gpt-4o", "gemini-1.5-flash"]
            )

        return RetrievalConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            use_llm_scoring=use_llm_scoring,
            embedding_model=embedding_model,
            similarity_threshold=similarity_threshold,
            llm_model=llm_model,
        )

    def _run_evaluation(
        self, dataset_id: str, evaluation_name: str, config: RetrievalConfig
    ):
        """Run benchmark evaluation"""
        # This would integrate with the existing analyzer
        st.info(
            "Evaluation functionality would integrate with the existing DocumentAnalyzer here."
        )
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
        st.success(
            f"Evaluation '{evaluation_name}' completed and saved with ID {eval_id}"
        )

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
                    "Evaluation": eval_name,
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
                        "Evaluation": eval_name,
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
                color="Evaluation",
                title="Precision@K Comparison",
                markers=True,
            )
            st.plotly_chart(
                fig, use_container_width=True, key="results_precision_chart"
            )

        with col2:
            fig = px.line(
                df,
                x="K",
                y="Recall",
                color="Evaluation",
                title="Recall@K Comparison",
                markers=True,
            )
            st.plotly_chart(fig, use_container_width=True, key="results_recall_chart")

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
        st.info(
            "Annotation interface would show retrieved chunks here for human evaluation."
        )

        # Placeholder annotation form
        annotator_id = st.text_input("Annotator ID", value="annotator_1")

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

    def _render_csv_metrics_charts(
        self, metrics, k_values: Optional[List[int]], chart_key_prefix: str = "csv"
    ):
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
