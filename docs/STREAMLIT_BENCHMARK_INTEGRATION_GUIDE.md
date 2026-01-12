# Guideline: Integrating ClimRetrieve Benchmarking Metrics into Streamlit

This guide explains how to integrate ClimRetrieve benchmarking metrics into the Streamlit frontend.

## Overview

The integration will add a new section to the existing benchmarking tab that allows users to:
1. Upload/select labels and results files
2. Run ClimRetrieve benchmark evaluation
3. Display metrics (Precision@K, Recall@K, F1@K, nDCG@K) with visualizations
4. Compare multiple strategies side-by-side

## Architecture

```
Streamlit App (app/streamlit_app.py)
    └─> Benchmarking Tab
        └─> ClimRetrieve Benchmarking Section (NEW)
            ├─> File Selection/Upload
            ├─> Evaluation Runner
            ├─> Metrics Display
            └─> Comparison View
```

## Implementation Steps

### Step 1: Create ClimRetrieve Benchmark UI Component

Create a new file: `app/ui/climretrieve_benchmarking.py`

```python
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from ..core.benchmark.climretrieve_io import load_inputs
from ..core.benchmark.climretrieve_metrics import evaluate_climretrieve, ClimRetrieveMetrics

logger = logging.getLogger(__name__)


class ClimRetrieveBenchmarkingUI:
    """Streamlit UI components for ClimRetrieve benchmarking"""
    
    def __init__(self):
        self.results_dir = Path("data/climretrieve/results")
        self.labels_dir = Path("data/climretrieve/labels")
    
    def render_file_selection(self) -> Tuple[Optional[Path], Optional[Path]]:
        """Render file selection interface"""
        st.subheader("📁 File Selection")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Labels File (Ground Truth)**")
            labels_option = st.radio(
                "Labels source:",
                ["Use existing file", "Upload file"],
                key="labels_source"
            )
            
            if labels_option == "Use existing file":
                # List available label files
                label_files = list(self.labels_dir.glob("*.csv")) if self.labels_dir.exists() else []
                if label_files:
                    selected_labels = st.selectbox(
                        "Select labels file:",
                        [f.name for f in label_files],
                        key="labels_select"
                    )
                    labels_path = self.labels_dir / selected_labels
                else:
                    st.warning("No label files found. Please upload one.")
                    labels_path = None
            else:
                uploaded_labels = st.file_uploader(
                    "Upload labels CSV",
                    type=["csv"],
                    key="labels_upload"
                )
                if uploaded_labels:
                    # Save to temp location
                    temp_path = Path("temp") / uploaded_labels.name
                    temp_path.parent.mkdir(exist_ok=True)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_labels.getbuffer())
                    labels_path = temp_path
                else:
                    labels_path = None
        
        with col2:
            st.write("**Results File (Model Output)**")
            results_option = st.radio(
                "Results source:",
                ["Use existing file", "Upload file"],
                key="results_source"
            )
            
            if results_option == "Use existing file":
                # List available result files
                result_files = list(self.results_dir.glob("*.csv")) if self.results_dir.exists() else []
                if result_files:
                    selected_results = st.selectbox(
                        "Select results file:",
                        [f.name for f in result_files],
                        key="results_select"
                    )
                    results_path = self.results_dir / selected_results
                else:
                    st.warning("No result files found. Please upload one.")
                    results_path = None
            else:
                uploaded_results = st.file_uploader(
                    "Upload results CSV",
                    type=["csv"],
                    key="results_upload"
                )
                if uploaded_results:
                    temp_path = Path("temp") / uploaded_results.name
                    temp_path.parent.mkdir(exist_ok=True)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_results.getbuffer())
                    results_path = temp_path
                else:
                    results_path = None
        
        return labels_path, results_path
    
    def render_evaluation_config(self) -> Dict:
        """Render evaluation configuration options"""
        st.subheader("⚙️ Evaluation Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            k_values_str = st.text_input(
                "K values (comma-separated):",
                value="1,3,5,10",
                key="k_values",
                help="K values for Precision@K, Recall@K, etc."
            )
            k_values = [int(k.strip()) for k in k_values_str.split(",") if k.strip().isdigit()]
        
        with col2:
            relevance_threshold = st.number_input(
                "Relevance threshold:",
                min_value=0,
                max_value=3,
                value=1,
                key="relevance_threshold",
                help="Minimum relevance score to be considered relevant"
            )
        
        with col3:
            gain_scheme = st.selectbox(
                "nDCG gain scheme:",
                ["exp", "linear"],
                key="gain_scheme",
                help="Gain scheme for nDCG calculation"
            )
        
        return {
            "k_values": k_values,
            "relevance_threshold": relevance_threshold,
            "gain_scheme": gain_scheme
        }
    
    def run_evaluation(
        self,
        labels_path: Path,
        results_path: Path,
        config: Dict
    ) -> Optional[ClimRetrieveMetrics]:
        """Run ClimRetrieve evaluation"""
        try:
            with st.spinner("Loading datasets and running evaluation..."):
                # Load inputs
                inputs = load_inputs(
                    labels_csv=labels_path,
                    results_csv=results_path,
                    score_col="score",
                    paragraph_col="paragraph"
                )
                
                # Run evaluation
                metrics = evaluate_climretrieve(
                    labels=inputs.labels,
                    results=inputs.results,
                    k_values=config["k_values"],
                    relevance_threshold=config["relevance_threshold"],
                    gain_scheme=config["gain_scheme"]
                )
                
                return metrics
        
        except Exception as e:
            st.error(f"Error running evaluation: {str(e)}")
            logger.exception(e)
            return None
    
    def render_metrics_table(self, metrics: ClimRetrieveMetrics, k_values: List[int]):
        """Render metrics in a table format"""
        st.subheader("📊 Evaluation Metrics")
        
        # Create DataFrame
        data = {
            "K": k_values,
            "Precision@K": [metrics.precision_at_k.get(k, 0.0) for k in k_values],
            "Recall@K": [metrics.recall_at_k.get(k, 0.0) for k in k_values],
            "F1@K": [metrics.f1_at_k.get(k, 0.0) for k in k_values],
            "nDCG@K": [metrics.ndcg_at_k.get(k, 0.0) for k in k_values],
        }
        df = pd.DataFrame(data)
        
        # Display table
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "K": st.column_config.NumberColumn("K", format="%d"),
                "Precision@K": st.column_config.NumberColumn("Precision@K", format="%.4f"),
                "Recall@K": st.column_config.NumberColumn("Recall@K", format="%.4f"),
                "F1@K": st.column_config.NumberColumn("F1@K", format="%.4f"),
                "nDCG@K": st.column_config.NumberColumn("nDCG@K", format="%.4f"),
            }
        )
        
        return df
    
    def render_metrics_charts(self, metrics: ClimRetrieveMetrics, k_values: List[int]):
        """Render metrics as charts"""
        st.subheader("📈 Metrics Visualization")
        
        # Create DataFrame
        data = {
            "K": k_values,
            "Precision@K": [metrics.precision_at_k.get(k, 0.0) for k in k_values],
            "Recall@K": [metrics.recall_at_k.get(k, 0.0) for k in k_values],
            "F1@K": [metrics.f1_at_k.get(k, 0.0) for k in k_values],
            "nDCG@K": [metrics.ndcg_at_k.get(k, 0.0) for k in k_values],
        }
        df = pd.DataFrame(data)
        
        # Create tabs for different chart types
        tab1, tab2, tab3 = st.tabs(["Line Chart", "Bar Chart", "Comparison"])
        
        with tab1:
            # Line chart
            fig = px.line(
                df,
                x="K",
                y=["Precision@K", "Recall@K", "F1@K", "nDCG@K"],
                title="Metrics vs K",
                markers=True
            )
            fig.update_layout(
                xaxis_title="K",
                yaxis_title="Score",
                yaxis_range=[0, 1],
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Bar chart
            fig = px.bar(
                df,
                x="K",
                y=["Precision@K", "Recall@K", "F1@K", "nDCG@K"],
                title="Metrics vs K (Bar Chart)",
                barmode="group"
            )
            fig.update_layout(
                xaxis_title="K",
                yaxis_title="Score",
                yaxis_range=[0, 1]
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Individual metric comparisons
            metric_type = st.selectbox("Select metric:", ["Precision@K", "Recall@K", "F1@K", "nDCG@K"])
            fig = px.bar(
                df,
                x="K",
                y=metric_type,
                title=f"{metric_type} vs K",
                color=metric_type,
                color_continuous_scale="Viridis"
            )
            fig.update_layout(
                xaxis_title="K",
                yaxis_title=metric_type,
                yaxis_range=[0, 1]
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_comparison_view(self, all_metrics: Dict[str, ClimRetrieveMetrics], k_values: List[int]):
        """Render comparison view for multiple strategies"""
        st.subheader("🔄 Strategy Comparison")
        
        if not all_metrics:
            st.info("Run evaluations for multiple strategies to see comparison.")
            return
        
        # Create comparison DataFrame
        comparison_data = []
        for strategy, metrics in all_metrics.items():
            for k in k_values:
                comparison_data.append({
                    "Strategy": strategy,
                    "K": k,
                    "Precision@K": metrics.precision_at_k.get(k, 0.0),
                    "Recall@K": metrics.recall_at_k.get(k, 0.0),
                    "F1@K": metrics.f1_at_k.get(k, 0.0),
                    "nDCG@K": metrics.ndcg_at_k.get(k, 0.0),
                })
        
        df_comparison = pd.DataFrame(comparison_data)
        
        # Display comparison table
        st.dataframe(df_comparison, use_container_width=True)
        
        # Comparison charts
        metric_type = st.selectbox("Select metric for comparison:", 
                                   ["Precision@K", "Recall@K", "F1@K", "nDCG@K"],
                                   key="comparison_metric")
        
        fig = px.line(
            df_comparison,
            x="K",
            y=metric_type,
            color="Strategy",
            title=f"{metric_type} Comparison Across Strategies",
            markers=True
        )
        fig.update_layout(
            xaxis_title="K",
            yaxis_title=metric_type,
            yaxis_range=[0, 1],
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def render_main_interface(self):
        """Render the main ClimRetrieve benchmarking interface"""
        st.header("🎯 ClimRetrieve Benchmarking")
        st.markdown("Evaluate your retrieval system against ClimRetrieve benchmark datasets.")
        
        # File selection
        labels_path, results_path = self.render_file_selection()
        
        # Evaluation config
        config = self.render_evaluation_config()
        
        # Run evaluation button
        if st.button("🚀 Run Evaluation", type="primary"):
            if labels_path and results_path:
                metrics = self.run_evaluation(labels_path, results_path, config)
                
                if metrics:
                    # Store in session state for comparison
                    if "climretrieve_metrics" not in st.session_state:
                        st.session_state.climretrieve_metrics = {}
                    
                    strategy_name = results_path.stem
                    st.session_state.climretrieve_metrics[strategy_name] = metrics
                    
                    # Display results
                    st.success("Evaluation completed successfully!")
                    
                    # Metrics table
                    df = self.render_metrics_table(metrics, config["k_values"])
                    
                    # Metrics charts
                    self.render_metrics_charts(metrics, config["k_values"])
                    
                    # Download results
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Metrics as CSV",
                        data=csv,
                        file_name=f"{strategy_name}_metrics.csv",
                        mime="text/csv"
                    )
            else:
                st.error("Please select both labels and results files.")
        
        # Comparison view (if multiple evaluations)
        if "climretrieve_metrics" in st.session_state and len(st.session_state.climretrieve_metrics) > 1:
            st.divider()
            self.render_comparison_view(st.session_state.climretrieve_metrics, config["k_values"])
        
        # Clear results button
        if "climretrieve_metrics" in st.session_state and st.session_state.climretrieve_metrics:
            if st.button("🗑️ Clear All Results"):
                st.session_state.climretrieve_metrics = {}
                st.rerun()
```

### Step 2: Integrate into Streamlit App

Modify `app/streamlit_app.py` to add ClimRetrieve benchmarking section:

```python
# Around line 1569, in the benchmarking tab section:

with benchmark_tab:
    try:
        from app.ui.benchmarking import BenchmarkingUI
        from app.ui.climretrieve_benchmarking import ClimRetrieveBenchmarkingUI
        
        benchmark_ui = BenchmarkingUI(analyzer.cache_manager)
        climretrieve_ui = ClimRetrieveBenchmarkingUI()
        
        # Sub-tabs for benchmarking features
        dataset_tab, eval_tab, results_tab, annotation_tab, climretrieve_tab = st.tabs([
            "📊 Datasets", "🎯 Evaluate", "📈 Results", "✍️ Annotate", "🎯 ClimRetrieve"
        ])
        
        with dataset_tab:
            benchmark_ui.render_dataset_management()
        
        with eval_tab:
            benchmark_ui.render_benchmarking_interface()
        
        with results_tab:
            benchmark_ui.render_results_dashboard()
        
        with annotation_tab:
            benchmark_ui.render_annotation_interface()
        
        with climretrieve_tab:
            climretrieve_ui.render_main_interface()
            
    except ImportError as e:
        st.error(f"Benchmarking functionality not available: {e}")
    except Exception as e:
        st.error(f"Error loading benchmarking interface: {e}")
        st.exception(e)
```

### Step 3: Add Required Dependencies

Ensure `requirements.txt` includes:
```
plotly>=5.0.0
streamlit>=1.28.0
pandas>=1.5.0
```

### Step 4: Create Directory Structure

Ensure directories exist:
```bash
mkdir -p data/climretrieve/labels
mkdir -p data/climretrieve/results
mkdir -p temp
```

## Alternative: Simpler Integration

If you want a simpler integration without creating a new class, you can add directly to the benchmarking tab:

```python
# In app/streamlit_app.py, in the benchmark_tab section:

with climretrieve_tab:
    st.header("🎯 ClimRetrieve Benchmarking")
    
    # File selection
    col1, col2 = st.columns(2)
    with col1:
        labels_file = st.file_uploader("Upload Labels CSV", type=["csv"])
    with col2:
        results_file = st.file_uploader("Upload Results CSV", type=["csv"])
    
    # Config
    k_values = st.text_input("K values:", "1,3,5,10")
    threshold = st.number_input("Threshold:", 1, min_value=0, max_value=3)
    
    if st.button("Run Evaluation") and labels_file and results_file:
        # Run evaluation and display results
        # ... (similar logic as above)
```

## Features to Include

1. **File Selection**
   - Upload files or select from existing files
   - Validate file format
   - Show file preview

2. **Configuration**
   - K values (default: 1,3,5,10)
   - Relevance threshold (default: 1)
   - nDCG gain scheme (exp/linear)

3. **Metrics Display**
   - Table view with all metrics
   - Interactive charts (line, bar, comparison)
   - Export to CSV

4. **Comparison View**
   - Compare multiple strategies
   - Side-by-side metrics
   - Comparison charts

5. **Error Handling**
   - Validate file formats
   - Show helpful error messages
   - Handle missing columns

## UI/UX Best Practices

1. **Progressive Disclosure**: Show configuration options in expanders
2. **Feedback**: Use spinners for long operations
3. **Visualization**: Use Plotly for interactive charts
4. **Responsive**: Use columns for layout
5. **Clear Labels**: Use descriptive headers and help text

## Testing

1. Test with different file formats
2. Test error handling (missing files, invalid formats)
3. Test comparison view with multiple strategies
4. Test file upload vs file selection
5. Test with different K values and thresholds

## Example Usage Flow

1. User selects/uploads labels file
2. User selects/uploads results file
3. User configures evaluation parameters
4. User clicks "Run Evaluation"
5. System loads files, runs evaluation
6. System displays metrics in table and charts
7. User can download results
8. User can run another evaluation for comparison
9. System shows comparison view

## Next Steps

1. Implement the UI component
2. Integrate into Streamlit app
3. Test with real data
4. Add error handling
5. Add documentation/tooltips
6. Consider adding caching for repeated evaluations


