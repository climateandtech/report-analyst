# Streamlit Benchmarking Section - Workflow Documentation

## Overview

The Streamlit benchmarking section provides a **UI-based interface** for evaluating retrieval and extraction systems against reference datasets. It's designed to be a user-friendly alternative to command-line benchmarking scripts, allowing users to upload datasets, configure retrieval parameters, run evaluations, and view results through an interactive web interface.

## Location in Streamlit App

The benchmarking section is accessible via the **"Benchmarking"** tab in the Streamlit sidebar navigation (🎯 icon).

**File**: `report_analyst/streamlit_app.py` (lines 4357-4403)
**UI Component**: `report_analyst/ui/benchmarking.py`

## Architecture

The benchmarking section uses a modular architecture:

```
Streamlit App (streamlit_app.py)
    ↓
BenchmarkingUI (ui/benchmarking.py)
    ├── DatasetLoader (core/benchmark/dataset_loader.py)
    ├── EvaluationEngine (core/benchmark/evaluation_engine.py)
    └── BenchmarkStore (core/storage/benchmark_store.py)
```

## Four Main Tabs

The benchmarking interface is organized into **4 sub-tabs**:

### 1. 📊 Datasets Tab (`render_dataset_management()`)

**Purpose**: Manage benchmark datasets (ground truth data)

**Workflow**:
1. **Upload Dataset**
   - User uploads a YAML or JSON file containing ground truth chunk relevance data
   - File is temporarily saved
   - `DatasetLoader.load_dataset()` loads and validates the dataset
   - `DatasetLoader.validate_dataset_consistency()` checks for consistency issues
   - User sees validation results (warnings if any)
   - Dataset preview is shown (name, description, number of questions)
   - User confirms save → `BenchmarkStore.save_dataset()` stores it in SQLite database

2. **View Existing Datasets**
   - Lists all uploaded datasets in a table
   - Shows: Dataset ID, Name, Question Set, Version, Created date
   - User can select a dataset for actions

3. **Dataset Actions**
   - **View Details**: Shows dataset metadata and statistics (total questions, total chunks)
   - **Delete Dataset**: Removes dataset from database

**Data Format**:
- **Input**: YAML or JSON files
- **Required fields**: `dataset_id`, `name`, `description`, `version`, `question_set`, `questions`
- **Structure**: Each question contains ground truth chunks with relevance scores

**Storage**: SQLite database (`benchmark_datasets` and `ground_truth_chunks` tables)

---

### 2. 🎯 Evaluate Tab (`render_benchmarking_interface()`)

**Purpose**: Run benchmark evaluations with configurable retrieval parameters

**Workflow**:
1. **Select Dataset**
   - User selects from uploaded datasets (dropdown)
   - Must have at least one dataset uploaded

2. **Configure Evaluation**
   - **Evaluation Name**: Auto-generated or custom name
   - **Retrieval Configuration** (`_render_config_form()`):
     - **Chunk Size**: 100-2000 (default: 1000)
     - **Chunk Overlap**: 0-500 (default: 200)
     - **Top K**: 1-20 (default: 5)
     - **Use LLM Scoring**: Checkbox (default: False)
     - **Embedding Model**: Dropdown (default, openai, sentence-transformers)
     - **Similarity Threshold**: Slider 0.0-1.0 (default: 0.0)
     - **LLM Model** (if LLM scoring enabled): gpt-4o-mini, gpt-4o, gemini-1.5-flash

3. **Run Evaluation**
   - User clicks "Run Evaluation" button
   - `_run_evaluation()` is called with:
     - `dataset_id`: Selected dataset
     - `evaluation_name`: User-provided name
     - `config`: `RetrievalConfig` object with all parameters

4. **Evaluation Execution** (Currently Placeholder)
   - **Current Status**: `_run_evaluation()` creates placeholder metrics
   - **Intended Behavior**: Should integrate with `DocumentAnalyzer` to:
     - Load ground truth from selected dataset
     - Run retrieval with configured parameters
     - Compare retrieved chunks with ground truth
     - Calculate metrics using `EvaluationEngine`
   - **Metrics Calculated**:
     - Precision@K (for K=1, 3, 5)
     - Recall@K (for K=1, 3, 5)
     - F1@K (for K=1, 3, 5)
     - Mean Average Precision (MAP)
     - Mean Reciprocal Rank (MRR)
     - nDCG@K (for K=1, 3, 5)

5. **Save Results**
   - `BenchmarkEvaluation` object is created with:
     - Dataset ID
     - Evaluation name
     - Configuration hash
     - Retrieval config
     - Evaluation metrics
   - Saved to database via `BenchmarkStore.save_evaluation()`

**Note**: The actual evaluation logic is currently a placeholder. It needs to be integrated with `DocumentAnalyzer` to perform real retrieval and comparison.

---

### 3. 📈 Results Tab (`render_results_dashboard()`)

**Purpose**: View and analyze evaluation results

**Workflow**:
1. **Filter Evaluations**
   - User can filter by dataset (multiselect)
   - Shows all evaluations by default
   - Date range filter (placeholder for future)

2. **Results Table** (`_render_results_table()`)
   - Displays evaluation results in a table
   - Columns:
     - Evaluation name
     - Dataset ID
     - MAP (Mean Average Precision)
     - MRR (Mean Reciprocal Rank)
     - P@5, R@5, F1@5, NDCG@5
     - Date

3. **Metrics Visualization** (`_render_metrics_charts()`)
   - **Precision@K Comparison**: Line chart showing Precision@K for K=1,3,5 across evaluations
   - **Recall@K Comparison**: Line chart showing Recall@K for K=1,3,5 across evaluations
   - Uses Plotly for interactive charts
   - Only shows if 2+ evaluations exist

4. **Detailed Evaluation View**
   - User selects an evaluation from dropdown
   - `_render_evaluation_details()` shows:
     - Full configuration (JSON)
     - Full metrics (JSON)

**Use Cases**:
- Compare different retrieval configurations
- Track performance over time
- Identify best-performing configurations

---

### 4. ✍️ Annotate Tab (`render_annotation_interface()`)

**Purpose**: Human annotation interface for evaluation results (Currently Placeholder)

**Workflow**:
1. **Select Evaluation**
   - User selects an evaluation from dropdown
   - Must have at least one evaluation run

2. **Annotation Form** (`_render_annotation_form()`)
   - **Current Status**: Placeholder interface
   - **Intended Behavior**: Should show:
     - Retrieved chunks for each question
     - Side-by-side comparison with ground truth
     - Relevance score sliders (0.0-1.0)
     - Evidence assignment checkboxes
     - Annotation notes text areas
     - Bulk operations for similar chunks

3. **Save Annotations**
   - Annotator ID input
   - Save button (currently placeholder)
   - Should store annotations in database

**Note**: This is a planned feature and currently shows placeholder UI.

---

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT BENCHMARKING                   │
└─────────────────────────────────────────────────────────────┘

1. DATASET UPLOAD (📊 Datasets Tab)
   ┌─────────────────────────────────────┐
   │ Upload YAML/JSON                    │
   │ ↓                                   │
   │ DatasetLoader.load_dataset()        │
   │ ↓                                   │
   │ DatasetLoader.validate_dataset()   │
   │ ↓                                   │
   │ BenchmarkStore.save_dataset()       │
   │ ↓                                   │
   │ Stored in SQLite DB                │
   └─────────────────────────────────────┘

2. RUN EVALUATION (🎯 Evaluate Tab)
   ┌─────────────────────────────────────┐
   │ Select Dataset                     │
   │ ↓                                   │
   │ Configure Retrieval Parameters     │
   │ (chunk_size, overlap, top_k, etc.) │
   │ ↓                                   │
   │ Click "Run Evaluation"              │
   │ ↓                                   │
   │ [PLACEHOLDER]                      │
   │ Should:                             │
   │ - Load ground truth                 │
   │ - Run DocumentAnalyzer              │
   │ - Compare with ground truth        │
   │ - Calculate metrics                 │
   │ ↓                                   │
   │ BenchmarkStore.save_evaluation()   │
   │ ↓                                   │
   │ Results stored in DB               │
   └─────────────────────────────────────┘

3. VIEW RESULTS (📈 Results Tab)
   ┌─────────────────────────────────────┐
   │ Filter by Dataset                   │
   │ ↓                                   │
   │ View Results Table                  │
   │ (MAP, MRR, P@K, R@K, F1@K, NDCG@K) │
   │ ↓                                   │
   │ View Metrics Charts                 │
   │ (Precision@K, Recall@K over K)      │
   │ ↓                                   │
   │ View Detailed Evaluation            │
   │ (Config + Metrics JSON)            │
   └─────────────────────────────────────┘

4. ANNOTATE (✍️ Annotate Tab) [PLACEHOLDER]
   ┌─────────────────────────────────────┐
   │ Select Evaluation                   │
   │ ↓                                   │
   │ View Retrieved Chunks               │
   │ ↓                                   │
   │ Annotate Relevance Scores           │
   │ ↓                                   │
   │ Save Annotations                    │
   └─────────────────────────────────────┘
```

## Key Components

### BenchmarkingUI Class

**Location**: `report_analyst/ui/benchmarking.py`

**Initialization**:
- Takes `cache_manager` as parameter (for database access)
- Initializes:
  - `DatasetLoader`: Loads and validates datasets
  - `EvaluationEngine`: Calculates metrics (currently not fully integrated)
  - `BenchmarkStore`: Database operations

**Main Methods**:
- `render_dataset_management()`: Dataset upload and management
- `render_benchmarking_interface()`: Run evaluations
- `render_results_dashboard()`: View results and charts
- `render_annotation_interface()`: Human annotation (placeholder)

### DatasetLoader

**Location**: `report_analyst/core/benchmark/dataset_loader.py`

**Purpose**: Load and validate benchmark datasets from YAML/JSON files

**Key Methods**:
- `load_dataset(file_path)`: Load dataset from file
- `validate_dataset_consistency(dataset)`: Check for consistency issues

**Supported Format**:
```yaml
dataset_id: "my_dataset"
name: "My Benchmark Dataset"
description: "Description"
version: "1.0"
question_set: "tcfd"
questions:
  - question_id: "tcfd_1"
    question_text: "What are the climate risks?"
    ground_truth_chunks:
      - chunk_id: "chunk_001"
        relevance_score: 0.9
        is_evidence: true
        evidence_order: 1
```

### EvaluationEngine

**Location**: `report_analyst/core/benchmark/evaluation_engine.py`

**Purpose**: Calculate evaluation metrics by comparing retrieved chunks with ground truth

**Note**: Currently initialized but not fully integrated into the evaluation workflow.

### BenchmarkStore

**Location**: `report_analyst/core/storage/benchmark_store.py`

**Purpose**: Database operations for storing datasets and evaluations

**Key Methods**:
- `save_dataset(dataset, file_path)`: Save dataset to database
- `list_datasets()`: List all datasets
- `get_dataset(dataset_id)`: Retrieve dataset
- `save_evaluation(evaluation)`: Save evaluation results
- `list_evaluations()`: List all evaluations
- `get_ground_truth(dataset_id)`: Get ground truth chunks

**Database Tables**:
- `benchmark_datasets`: Dataset metadata
- `ground_truth_chunks`: Ground truth chunk relevance data
- `benchmark_evaluations`: Evaluation results and metrics

## Current Limitations

1. **Evaluation Logic is Placeholder**
   - `_run_evaluation()` creates fake metrics instead of running real evaluation
   - Needs integration with `DocumentAnalyzer` to:
     - Process documents with configured parameters
     - Retrieve chunks
     - Compare with ground truth
     - Calculate real metrics

2. **Annotation Interface is Placeholder**
   - `_render_annotation_form()` shows placeholder UI
   - No actual annotation functionality implemented

3. **No Document Upload in Evaluation**
   - Currently assumes ground truth dataset contains all necessary data
   - Doesn't allow uploading documents to evaluate against

4. **Limited Configuration Options**
   - Only basic retrieval parameters exposed
   - Doesn't expose all `DocumentAnalyzer` configuration options

## Intended Complete Workflow

The intended complete workflow should be:

1. **Upload Ground Truth Dataset** → Store in database
2. **Upload Document(s) to Evaluate** → Process with `DocumentAnalyzer`
3. **Configure Retrieval** → Set chunk size, overlap, top_k, embedding model, etc.
4. **Run Evaluation** → 
   - Process document with `DocumentAnalyzer`
   - Retrieve top-K chunks for each question
   - Compare retrieved chunks with ground truth
   - Calculate metrics (Precision@K, Recall@K, F1@K, MAP, MRR, nDCG@K)
5. **View Results** → Compare metrics across different configurations
6. **Annotate** → Manually adjust relevance scores and add annotations

## Comparison with Command-Line Scripts

| Feature | Streamlit UI | Command-Line Scripts |
|---------|-------------|----------------------|
| **Dataset Upload** | ✅ Interactive upload | ❌ Manual file placement |
| **Configuration** | ✅ UI forms | ✅ Command-line arguments |
| **Results Visualization** | ✅ Interactive charts | ❌ Text output only |
| **Historical Comparison** | ✅ Dashboard | ❌ Manual comparison |
| **Annotation** | ⚠️ Planned | ❌ Not available |
| **Batch Processing** | ❌ One at a time | ✅ Script automation |
| **Integration** | ⚠️ Partial | ✅ Full integration |

## Future Enhancements

1. **Complete Evaluation Integration**
   - Integrate `DocumentAnalyzer` into `_run_evaluation()`
   - Support document upload in evaluation tab
   - Real-time progress indicators

2. **Annotation System**
   - Full annotation interface
   - Batch annotation capabilities
   - Annotation quality metrics

3. **Advanced Features**
   - A/B testing framework
   - Configuration templates
   - Export/import evaluation results
   - Automated improvement suggestions

4. **Better Visualization**
   - More chart types (confusion matrices, ROC curves)
   - Interactive result exploration
   - Performance trend analysis

## Summary

The Streamlit benchmarking section provides a **user-friendly UI** for benchmarking retrieval systems, but currently has **placeholder implementations** for the core evaluation logic. It's designed to:

- **Upload and manage** benchmark datasets (ground truth)
- **Configure and run** evaluations with various retrieval parameters
- **View and compare** evaluation results through interactive dashboards
- **Annotate** evaluation results (planned feature)

The workflow is **modular and extensible**, making it easy to integrate with the existing `DocumentAnalyzer` and evaluation infrastructure once the placeholder code is replaced with real implementations.


