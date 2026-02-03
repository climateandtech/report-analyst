import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..core.benchmark.dataset_loader import DatasetLoader, DatasetValidationError
from ..core.benchmark.evaluation_engine import EvaluationEngine
from ..core.storage.benchmark_store import BenchmarkStore
from ..models.benchmark import BenchmarkEvaluation, HumanAnnotation, RetrievalConfig
from ..core.benchmark.benchmark_registry import BenchmarkRegistry
from ..core.benchmark.dataset_validator import DatasetValidator, ValidationResult

logger = logging.getLogger(__name__)


class BenchmarkingUI:
    """Streamlit UI components for benchmarking functionality"""

    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.dataset_loader = DatasetLoader()
        self.evaluation_engine = EvaluationEngine()
        self.benchmark_store = BenchmarkStore(cache_manager.db_path)
        # NEW: Add benchmark registry and validator
        self.benchmark_registry = BenchmarkRegistry()
        self.validator = DatasetValidator()

    def render_dataset_management(self):
        """Render dataset management interface"""

        st.subheader("📊 Dataset Management")
        
        # Info about CSV uploads
        st.info("💡 **Note:** To upload CSV files with your retrieval results for evaluation, go to the **🎯 Evaluate** tab.")

        # Dataset upload
        with st.expander("Upload New Dataset", expanded=False):
            uploaded_file = st.file_uploader(
                "Choose a benchmark dataset file",
                type=["yaml", "yml", "json", "csv"],
                help="Upload a YAML, JSON, or CSV file containing ground truth chunk relevance data. CSV format: report, question, paragraph, relevance. For CSV results evaluation, use the Evaluate tab.",
            )

            if uploaded_file is not None:
                # Check if CSV file - need metadata
                is_csv = uploaded_file.name.lower().endswith('.csv')
                
                if is_csv:
                    st.info("📋 **CSV Dataset Detected** - Please provide dataset metadata:")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        dataset_id = st.text_input(
                            "Dataset ID:",
                            value=f"csv_{uploaded_file.name.replace('.csv', '').replace(' ', '_').lower()}",
                            help="Unique identifier for this dataset",
                            key="csv_dataset_id"
                        )
                        dataset_name = st.text_input(
                            "Dataset Name:",
                            value=f"CSV Dataset: {uploaded_file.name}",
                            help="Display name for the dataset",
                            key="csv_dataset_name"
                        )
                    with col2:
                        question_set = st.text_input(
                            "Question Set:",
                            value="custom",
                            help="Question set identifier (e.g., 'tcfd', 'custom')",
                            key="csv_question_set"
                        )
                        dataset_version = st.text_input(
                            "Version:",
                            value="1.0",
                            help="Dataset version",
                            key="csv_dataset_version"
                        )
                    
                    dataset_description = st.text_area(
                        "Description:",
                        value=f"Ground truth dataset loaded from CSV file: {uploaded_file.name}",
                        help="Description of the dataset",
                        key="csv_dataset_description"
                    )
                    
                    if st.button("Load CSV Dataset", type="primary", key="load_csv_btn"):
                        self._handle_csv_dataset_upload(
                            uploaded_file, 
                            dataset_id, 
                            dataset_name, 
                            dataset_description,
                            question_set
                        )
                else:
                    # YAML/JSON file - handle normally
                    self._handle_dataset_upload(uploaded_file)

        # List existing datasets
        st.subheader("Existing Datasets")
        datasets = self.benchmark_store.list_datasets()

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

    def render_benchmarking_interface(self):

        """Render benchmarking interface for uploading results and selecting benchmarks"""
        st.subheader("Run Benchmark Evaluation")

        # Step 1: Upload user's results dataset
        st.subheader("Upload Your Results")
        
        # Provide instructions
        st.info("📄 Upload a CSV file with your retrieval results. Required columns: `report`, `question`, `paragraph`, `score`")
        
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=["csv"],
            accept_multiple_files=False,
            key="benchmark_results_upload",
            help="CSV file with columns: report, question, paragraph, score",
        )

        user_df = None
        if uploaded_file is not None:
            try:
                # Show file info
                st.write(f"📎 **File:** {uploaded_file.name} ({uploaded_file.size:,} bytes)")
                
                # Read CSV with error handling
                user_df = pd.read_csv(uploaded_file)
                st.success(f"✅ Loaded {len(user_df)} rows")

                # Show preview
                with st.expander("Preview your dataset", expanded=True):
                    st.dataframe(user_df.head(10))
                    st.write(f"**Columns:** {', '.join(list(user_df.columns))}")
                    
                    # Validate required columns
                    required_cols = ["report", "question", "paragraph"]
                    missing_cols = [col for col in required_cols if col not in user_df.columns]
                    if missing_cols:
                        st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                        st.stop()
                    
                    # Check for score column
                    if "score" not in user_df.columns:
                        score_cols = [col for col in user_df.columns if "score" in col.lower()]
                        if score_cols:
                            st.warning(f"⚠️ Using column '{score_cols[0]}' as score column")
                        else:
                            st.error("❌ No 'score' column found. Please include a score column in your CSV.")
                            st.stop()
            except pd.errors.EmptyDataError:
                st.error("❌ The CSV file is empty. Please upload a file with data.")
                st.stop()
            except pd.errors.ParserError as e:
                st.error(f"❌ Error parsing CSV file: {e}")
                st.info("💡 Make sure your CSV file is properly formatted and uses commas as delimiters.")
                st.stop()
            except Exception as e:
                st.error(f"❌ Error loading CSV: {e}")
                logger.exception("Error loading uploaded CSV file")
                st.stop()

        # Step 2: Select benchmark
        st.subheader("Select Benchmark")
        available_benchmarks = self.benchmark_registry.list_benchmarks()

        if not available_benchmarks:
            st.warning("No benchmarks available. Please configure benchmarks.")
            return

        selected_benchmark = st.selectbox(
            "Choose benchmark to evaluate against:",
            options=[b.benchmark_id for b in available_benchmarks],
            format_func=lambda x: next(
                b.name for b in available_benchmarks if b.benchmark_id == x
            ),
            help="Select the ground truth benchmark to compare against",
        )

        benchmark_info = self.benchmark_registry.get_benchmark(selected_benchmark)

        # Show benchmark info
        if benchmark_info:
            with st.expander("Benchmark Information"):
                st.write(f"**Name:** {benchmark_info.name}")
                st.write(f"**Description:** {benchmark_info.description}")
                st.write(f"**Format:** {benchmark_info.format}")
                st.write(f"**Version:** {benchmark_info.version}")

        # Step 3: Validation (if dataset uploaded)
        validation_result = None
        if user_df is not None and selected_benchmark:
            st.subheader("Validation")

            # Strict mode toggle
            strict_mode = st.checkbox(
                "Strict mode (for competition)",
                value=False,
                help="If enabled, requires perfect match. If disabled, allows partial matches.",
            )

            # Load benchmark labels
            try:
                with st.spinner("Loading benchmark labels..."):
                    benchmark_df = self.benchmark_registry.load_benchmark_labels(
                        selected_benchmark
                    )

                # Perform validation
                validation_result = self.validator.validate_dataset_match(
                    user_df=user_df,
                    benchmark_df=benchmark_df,
                    strict_mode=strict_mode,
                )

                # Display validation results
                if validation_result.is_valid:
                    st.success(validation_result.message)
                else:
                    if strict_mode:
                        st.error(validation_result.message)
                        # Show details
                        if validation_result.missing_pairs:
                            with st.expander("Missing pairs (first 10)"):
                                st.write(list(validation_result.missing_pairs)[:10])
                        if validation_result.extra_pairs:
                            with st.expander("Extra pairs (first 10)"):
                                st.write(list(validation_result.extra_pairs)[:10])
                    else:
                        st.warning(validation_result.message)
                        st.info(
                            f"Will evaluate {len(validation_result.matching_pairs)} matching pairs"
                        )

            except Exception as e:
                st.error(f"Error during validation: {e}")
                return

        # Step 4: Run evaluation
        st.subheader("Run Evaluation")

        evaluation_name = st.text_input(
            "Evaluation Name:",
            value=(
                f"eval_{selected_benchmark}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}"
                if selected_benchmark
                else ""
            ),
            help="Name for this evaluation run",
        )

        # K values configuration
        k_values_input = st.text_input(
            "K values (comma-separated):",
            value="1,3,5,10",
            help="K values for Precision@K, Recall@K, etc.",
        )

        if st.button(
            "Run Evaluation",
            type="primary",
            disabled=(user_df is None or not selected_benchmark),
        ):
            if user_df is None or not selected_benchmark:
                st.error("Please upload a dataset and select a benchmark")
                return

            if validation_result and not validation_result.can_proceed:
                st.error("Cannot proceed due to validation errors")
                return

            # Parse K values
            try:
                k_values = [int(k.strip()) for k in k_values_input.split(",")]
            except:
                k_values = [1, 3, 5, 10]
                st.warning(f"Invalid K values, using default: {k_values}")

            # Run evaluation
            self._run_evaluation(
                user_df=user_df,
                benchmark_id=selected_benchmark,
                evaluation_name=evaluation_name,
                k_values=k_values,
                validation_result=validation_result,
            )

    def render_results_dashboard(self):
        """Render evaluation results dashboard"""
        st.subheader("Evaluation Results")

        evaluations = self.benchmark_store.list_evaluations()
        if not evaluations:
            st.info(
                "No evaluations run yet. Run a benchmark evaluation to see results."
            )
            return

        # Filter controls
        col1, col2 = st.columns(2)
        with col1:
            datasets = list(set(e.dataset_id for e in evaluations))
            selected_datasets = st.multiselect(
                "Filter by Dataset:", datasets, default=datasets
            )

        with col2:
            # Date range filter could be added here
            pass

        # Filter evaluations
        filtered_evals = [e for e in evaluations if e.dataset_id in selected_datasets]

        if not filtered_evals:
            st.warning("No evaluations match the selected filters.")
            return

        # Results table
        self._render_results_table(filtered_evals)

        # Metrics visualization
        self._render_metrics_charts(filtered_evals)

        # Detailed evaluation view
        if st.selectbox(
            "Select evaluation for details:",
            options=[f"{e.evaluation_name} ({e.dataset_id})" for e in filtered_evals],
        ):
            selected_eval = filtered_evals[0]  # Simplified for demo
            self._render_evaluation_details(selected_eval)

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

    def _handle_dataset_upload(self, uploaded_file):
        """Handle dataset file upload (YAML/JSON)"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}"
            ) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            # Load and validate dataset
            with st.spinner("Loading and validating dataset..."):
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
            if st.button("Save Dataset"):
                self.benchmark_store.save_dataset(dataset, uploaded_file.name)
                st.success(f"Dataset '{dataset.name}' saved successfully!")
                st.rerun()

        except (DatasetValidationError, Exception) as e:
            st.error(f"Failed to load dataset: {str(e)}")

        finally:
            # Clean up temp file
            try:
                Path(tmp_path).unlink()
            except:
                pass

    def _handle_csv_dataset_upload(self, uploaded_file, dataset_id: str, 
                                   dataset_name: str, dataset_description: str,
                                   question_set: str):
        """Handle CSV dataset file upload"""
        tmp_path = None
        try:
            # Validate inputs
            if not dataset_id or not dataset_id.strip():
                st.error("Dataset ID is required")
                return
            if not dataset_name or not dataset_name.strip():
                st.error("Dataset name is required")
                return
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".csv"
            ) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            # Load and validate CSV dataset
            with st.spinner("Loading and validating CSV dataset..."):
                dataset = self.dataset_loader.load_dataset(
                    tmp_path,
                    dataset_id=dataset_id.strip(),
                    dataset_name=dataset_name.strip(),
                    dataset_description=dataset_description.strip() if dataset_description else None,
                    question_set=question_set.strip() if question_set else "custom"
                )
                warnings = self.dataset_loader.validate_dataset_consistency(dataset)

            # Show validation results
            if warnings:
                st.warning(f"Dataset loaded with {len(warnings)} warnings:")
                for warning in warnings:
                    st.write(f"⚠️ {warning}")
            else:
                st.success("✅ CSV dataset validation passed!")

            # Show dataset preview
            st.write(f"**Dataset ID:** {dataset.dataset_id}")
            st.write(f"**Dataset Name:** {dataset.name}")
            st.write(f"**Description:** {dataset.description}")
            st.write(f"**Question Set:** {dataset.question_set}")
            st.write(f"**Questions:** {len(dataset.questions)}")
            
            # Show sample questions
            with st.expander("Preview Questions (first 5)"):
                for i, q in enumerate(dataset.questions[:5]):
                    st.write(f"**{q.question_id}:** {q.question_text[:100]}...")
                    st.write(f"  - {len(q.ground_truth_chunks)} chunks, "
                            f"{sum(1 for c in q.ground_truth_chunks if c.is_evidence)} relevant")

            # Confirm save
            if st.button("Save CSV Dataset", type="primary", key="save_csv_btn"):
                self.benchmark_store.save_dataset(dataset, uploaded_file.name)
                st.success(f"✅ Dataset '{dataset.name}' saved successfully!")
                st.balloons()
                st.rerun()

        except (DatasetValidationError, Exception) as e:
            st.error(f"❌ Failed to load CSV dataset: {str(e)}")
            logger.exception("Error loading CSV dataset")

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
        self,
        user_df: pd.DataFrame,
        benchmark_id: str,
        evaluation_name: str,
        k_values: List[int],
        validation_result: Optional[ValidationResult] = None,
    ):
        """Run benchmark evaluation using real evaluation services"""

        try:
            with st.spinner("Running evaluation..."):
                # Load benchmark labels
                benchmark_df = self.benchmark_registry.load_benchmark_labels(
                    benchmark_id
                )
                benchmark_info = self.benchmark_registry.get_benchmark(benchmark_id)

                # Filter to matching pairs if validation was done
                if validation_result and validation_result.matching_pairs:
                    # Filter both datasets to matching pairs only
                    user_df = user_df[
                        user_df.apply(
                            lambda row: (str(row["report"]), str(row["question"]))
                            in validation_result.matching_pairs,
                            axis=1,
                        )
                    ]
                    benchmark_df = benchmark_df[
                        benchmark_df.apply(
                            lambda row: (str(row["report"]), str(row["question"]))
                            in validation_result.matching_pairs,
                            axis=1,
                        )
                    ]
                    st.info(
                        f"Evaluating {len(validation_result.matching_pairs)} matching pairs"
                    )

                # Prepare user results DataFrame
                # Ensure required columns exist
                required_cols = ["report", "question", "paragraph"]
                missing_cols = [
                    col for col in required_cols if col not in user_df.columns
                ]
                if missing_cols:
                    st.error(f"Missing required columns: {missing_cols}")
                    return

                # Ensure score column exists (or create default)
                if "score" not in user_df.columns:
                    # Try to find score column
                    score_cols = [
                        col for col in user_df.columns if "score" in col.lower()
                    ]
                    if score_cols:
                        user_df = user_df.rename(columns={score_cols[0]: "score"})
                    else:
                        st.error(
                            "No score column found. Please include a 'score' column in your CSV."
                        )
                        return

                # Rename to standard format
                user_results = user_df[["report", "question", "paragraph", "score"]].copy()

                # Run evaluation based on benchmark format
                if benchmark_info.format == "climretrieve":
                    from ..core.benchmark.climretrieve_metrics import (
                        evaluate_climretrieve,
                    )

                    metrics_result = evaluate_climretrieve(
                        labels=benchmark_df,
                        results=user_results,
                        k_values=k_values,
                    )

                    # Convert to EvaluationMetrics format
                    from ..models.benchmark import EvaluationMetrics

                    evaluation_metrics = EvaluationMetrics(
                        precision_at_k=metrics_result.precision_at_k,
                        recall_at_k=metrics_result.recall_at_k,
                        f1_at_k=metrics_result.f1_at_k,
                        ndcg_at_k=metrics_result.ndcg_at_k,
                        mean_reciprocal_rank=0.0,  # Not calculated by evaluate_climretrieve
                        mean_average_precision=0.0,  # Not calculated by evaluate_climretrieve
                    )

                elif benchmark_info.format == "s4m":
                    # For S4M, would use evaluate_s4m_classification
                    # Implementation depends on S4M format requirements
                    st.error("S4M format evaluation not yet implemented in UI")
                    return
                else:
                    st.error(f"Unsupported benchmark format: {benchmark_info.format}")
                    return

                # Save evaluation
                from ..models.benchmark import BenchmarkEvaluation, RetrievalConfig

                evaluation = BenchmarkEvaluation(
                    dataset_id=benchmark_id,
                    evaluation_name=evaluation_name,
                    config_hash="",  # Not using retrieval config for this workflow
                    retrieval_config=RetrievalConfig(),  # Empty config
                    evaluation_metrics=evaluation_metrics,
                )

                eval_id = self.benchmark_store.save_evaluation(evaluation)

                st.success(
                    f"Evaluation '{evaluation_name}' completed and saved with ID {eval_id}"
                )
                st.balloons()

                # Display metrics immediately
                st.subheader("Results")
                self._display_metrics_summary(evaluation_metrics)

                # Auto-refresh to show in results tab
                st.rerun()

        except Exception as e:
            st.error(f"Error during evaluation: {e}")
            logger.exception(e)
            raise

    def _render_results_table(self, evaluations: List[BenchmarkEvaluation]):
        """Render evaluation results table"""
        results_data = []
        for eval in evaluations:
            metrics = eval.evaluation_metrics
            results_data.append(
                {
                    "Evaluation": eval.evaluation_name,
                    "Dataset": eval.dataset_id,
                    "MAP": f"{metrics.mean_average_precision:.3f}",
                    "MRR": f"{metrics.mean_reciprocal_rank:.3f}",
                    "P@5": f"{metrics.precision_at_k.get(5, 0):.3f}",
                    "R@5": f"{metrics.recall_at_k.get(5, 0):.3f}",
                    "F1@5": f"{metrics.f1_at_k.get(5, 0):.3f}",
                    "NDCG@5": f"{metrics.ndcg_at_k.get(5, 0):.3f}",
                    "Date": (
                        eval.created_at.strftime("%Y-%m-%d")
                        if eval.created_at
                        else "Unknown"
                    ),
                }
            )

        df = pd.DataFrame(results_data)
        st.dataframe(df, use_container_width=True)

    def _render_metrics_charts(self, evaluations: List[BenchmarkEvaluation]):
        """Render metrics visualization charts"""
        if len(evaluations) < 2:
            return

        # Prepare data for plotting
        chart_data = []
        for eval in evaluations:
            metrics = eval.evaluation_metrics
            for k in [1, 3, 5]:
                if k in metrics.precision_at_k:
                    chart_data.append(
                        {
                            "Evaluation": eval.evaluation_name,
                            "K": k,
                            "Precision": metrics.precision_at_k[k],
                            "Recall": metrics.recall_at_k[k],
                            "F1": metrics.f1_at_k[k],
                            "NDCG": metrics.ndcg_at_k[k],
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
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.line(
                df, x="K", y="Recall", color="Evaluation", title="Recall@K Comparison"
            )
            st.plotly_chart(fig, use_container_width=True)

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

    def _display_metrics_summary(self, metrics):
        """Display metrics summary in a nice format"""
        from ..models.benchmark import EvaluationMetrics

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("MAP", f"{metrics.mean_average_precision:.3f}")
        with col2:
            st.metric("MRR", f"{metrics.mean_reciprocal_rank:.3f}")
        with col3:
            if 5 in metrics.precision_at_k:
                st.metric("Precision@5", f"{metrics.precision_at_k[5]:.3f}")
        with col4:
            if 5 in metrics.recall_at_k:
                st.metric("Recall@5", f"{metrics.recall_at_k[5]:.3f}")

        # Detailed table
        st.subheader("Detailed Metrics")
        metrics_data = []
        for k in sorted(metrics.precision_at_k.keys()):
            metrics_data.append(
                {
                    "K": k,
                    "Precision@K": f"{metrics.precision_at_k.get(k, 0):.3f}",
                    "Recall@K": f"{metrics.recall_at_k.get(k, 0):.3f}",
                    "F1@K": f"{metrics.f1_at_k.get(k, 0):.3f}",
                    "nDCG@K": f"{metrics.ndcg_at_k.get(k, 0):.3f}",
                }
            )

        st.dataframe(pd.DataFrame(metrics_data), use_container_width=True)

    def _render_evaluation_details(self, evaluation: BenchmarkEvaluation):
        """Render detailed evaluation information"""
        st.subheader(f"Evaluation: {evaluation.evaluation_name}")

        # Configuration
        config = evaluation.retrieval_config
        st.write("**Configuration:**")
        config_dict = config.model_dump()
        st.json(config_dict)

        # Metrics
        st.write("**Metrics:**")
        metrics_dict = evaluation.evaluation_metrics.model_dump()
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
