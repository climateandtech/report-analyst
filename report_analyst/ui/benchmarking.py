import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import tempfile
import json
from typing import Dict, List, Optional
import logging

from ..core.benchmark.dataset_loader import DatasetLoader, DatasetValidationError
from ..core.benchmark.evaluation_engine import EvaluationEngine
from ..core.storage.benchmark_store import BenchmarkStore
from ..models.benchmark import RetrievalConfig, BenchmarkEvaluation, HumanAnnotation

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
        st.subheader("📊 Dataset Management")
        
        # Dataset upload
        with st.expander("Upload New Dataset", expanded=False):
            uploaded_file = st.file_uploader(
                "Choose a benchmark dataset file",
                type=['yaml', 'yml', 'json'],
                help="Upload a YAML or JSON file containing ground truth chunk relevance data"
            )
            
            if uploaded_file is not None:
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
            dataset_data.append({
                "Dataset ID": dataset.dataset_id,
                "Name": dataset.name,
                "Question Set": dataset.question_set,
                "Version": dataset.version,
                "Created": dataset.created_at.strftime("%Y-%m-%d %H:%M") if dataset.created_at else "Unknown"
            })
        
        df = pd.DataFrame(dataset_data)
        st.dataframe(df, use_container_width=True)
        
        # Dataset actions
        if datasets:
            selected_dataset = st.selectbox(
                "Select dataset for actions:",
                options=[d.dataset_id for d in datasets],
                format_func=lambda x: next(d.name for d in datasets if d.dataset_id == x)
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
        st.subheader("🎯 Run Benchmark Evaluation")
        
        datasets = self.benchmark_store.list_datasets()
        if not datasets:
            st.warning("No datasets available. Please upload a dataset first.")
            return
        
        # Configuration
        col1, col2 = st.columns(2)
        
        with col1:
            selected_dataset = st.selectbox(
                "Select Dataset:",
                options=[d.dataset_id for d in datasets],
                format_func=lambda x: next(d.name for d in datasets if d.dataset_id == x)
            )
        
        with col2:
            evaluation_name = st.text_input(
                "Evaluation Name:",
                value=f"eval_{selected_dataset}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}"
            )
        
        # Retrieval configuration
        st.subheader("Retrieval Configuration")
        config = self._render_config_form()
        
        # Run evaluation
        if st.button("Run Evaluation", type="primary"):
            if selected_dataset and evaluation_name:
                self._run_evaluation(selected_dataset, evaluation_name, config)
            else:
                st.error("Please select a dataset and provide an evaluation name")
    
    def render_results_dashboard(self):
        """Render evaluation results dashboard"""
        st.subheader("📈 Evaluation Results")
        
        evaluations = self.benchmark_store.list_evaluations()
        if not evaluations:
            st.info("No evaluations run yet. Run a benchmark evaluation to see results.")
            return
        
        # Filter controls
        col1, col2 = st.columns(2)
        with col1:
            datasets = list(set(e.dataset_id for e in evaluations))
            selected_datasets = st.multiselect("Filter by Dataset:", datasets, default=datasets)
        
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
        if st.selectbox("Select evaluation for details:", 
                       options=[f"{e.evaluation_name} ({e.dataset_id})" for e in filtered_evals]):
            selected_eval = filtered_evals[0]  # Simplified for demo
            self._render_evaluation_details(selected_eval)
    
    def render_annotation_interface(self):
        """Render human annotation interface"""
        st.subheader("✍️ Human Annotation")
        
        evaluations = self.benchmark_store.list_evaluations()
        if not evaluations:
            st.info("No evaluations available for annotation.")
            return
        
        selected_eval = st.selectbox(
            "Select Evaluation to Annotate:",
            options=evaluations,
            format_func=lambda x: f"{x.evaluation_name} ({x.dataset_id})"
        )
        
        if selected_eval:
            self._render_annotation_form(selected_eval)
    
    def _handle_dataset_upload(self, uploaded_file):
        """Handle dataset file upload"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
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
                    st.write(f"⚠️ {warning}")
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
            llm_model=llm_model
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
            ndcg_at_k={1: 0.8, 3: 0.72, 5: 0.68}
        )
        
        evaluation = BenchmarkEvaluation(
            dataset_id=dataset_id,
            evaluation_name=evaluation_name,
            config_hash="",
            retrieval_config=config,
            evaluation_metrics=placeholder_metrics
        )
        
        eval_id = self.benchmark_store.save_evaluation(evaluation)
        st.success(f"Evaluation '{evaluation_name}' completed and saved with ID {eval_id}")
    
    def _render_results_table(self, evaluations: List[BenchmarkEvaluation]):
        """Render evaluation results table"""
        results_data = []
        for eval in evaluations:
            metrics = eval.evaluation_metrics
            results_data.append({
                "Evaluation": eval.evaluation_name,
                "Dataset": eval.dataset_id,
                "MAP": f"{metrics.mean_average_precision:.3f}",
                "MRR": f"{metrics.mean_reciprocal_rank:.3f}",
                "P@5": f"{metrics.precision_at_k.get(5, 0):.3f}",
                "R@5": f"{metrics.recall_at_k.get(5, 0):.3f}",
                "F1@5": f"{metrics.f1_at_k.get(5, 0):.3f}",
                "NDCG@5": f"{metrics.ndcg_at_k.get(5, 0):.3f}",
                "Date": eval.created_at.strftime("%Y-%m-%d") if eval.created_at else "Unknown"
            })
        
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
                    chart_data.append({
                        "Evaluation": eval.evaluation_name,
                        "K": k,
                        "Precision": metrics.precision_at_k[k],
                        "Recall": metrics.recall_at_k[k],
                        "F1": metrics.f1_at_k[k],
                        "NDCG": metrics.ndcg_at_k[k]
                    })
        
        if not chart_data:
            return
        
        df = pd.DataFrame(chart_data)
        
        # Create charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(df, x="K", y="Precision", color="Evaluation", 
                         title="Precision@K Comparison")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.line(df, x="K", y="Recall", color="Evaluation", 
                         title="Recall@K Comparison")
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
        st.info("Annotation interface would show retrieved chunks here for human evaluation.")
        
        # Placeholder annotation form
        annotator_id = st.text_input("Annotator ID", value="annotator_1")
        
        if st.button("Save Annotations"):
            st.success("Annotations saved! (This is a placeholder)")
