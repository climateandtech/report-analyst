# Benchmark Dataset Flow

This document describes the flexible dataset flow for benchmarking, supporting both Information Retrieval (IR) and Information Extraction (IE) datasets.

## Overview

The benchmarking system supports comparing two datasets with flexible column names:
- **Reference Dataset**: Ground truth (e.g., "climretrieve" for IR, "chatreport" for IE)
- **Input Dataset**: Actual results to evaluate

### Dataset Types

1. **Information Retrieval (IR)**: Compare retrieved chunks
   - Example: climretrieve dataset
   - Compares: chunk_id, position, relevance scores

2. **Information Extraction (IE)**: Compare analysis/answers
   - Example: chatreport, climatefinancebench datasets
   - Compares: answers, categories, extracted values

## Data Format

The system is flexible and supports different column names. It automatically detects dataset type (IR vs IE) and maps columns.

### Information Retrieval (IR) CSV Format

```csv
query_id,report_id,chunk_id,chunk_text,position,score,similarity_score,llm_score
tcfd_1,report_001,chunk_001,"Climate risks include...",1,0.95,0.92,0.88
tcfd_1,report_001,chunk_015,"Risk assessment...",2,0.89,0.87,0.85
```

**Common column name variations (all supported):**
- Query ID: `query_id`, `question_id`, `qid`, `query`
- Chunk ID: `chunk_id`, `chunk`, `cid`
- Position: `position`, `rank`, `order`, `pos`
- Score: `score`, `relevance_score`, `confidence_score`, `similarity_score`
- Report ID: `report_id`, `document_id`, `doc_id`, `report`

### Information Extraction (IE) CSV Format

```csv
question_id,answer,category,confidence_score,extracted_value
tcfd_1,"The company identifies climate risks...","risk_identification",0.92,"High"
tcfd_2,"Strategy includes...","strategy",0.88,"Medium"
```

**Common column name variations (all supported):**
- Query ID: `query_id`, `question_id`, `qid`, `query`
- Answer: `answer`, `analysis`, `response`, `text`
- Category: `category`, `class`, `label`, `type`
- Score: `score`, `confidence_score`, `relevance_score`

### SQLite Format

Same structure as CSV, stored in a table (default: `retrieval_results`).

## Flow A: Export Our Retrieval Results

Export retrieval results from our internal tools to CSV/SQLite format.

### Example: Export to CSV

```python
<<<<<<< HEAD
from report_analyst.core.benchmark.retrieval_results_loader import export_retrieval_results_to_csv
from report_analyst.models.benchmark import RetrievalResultsDataset, RetrievalResultRow
=======
from app.core.benchmark.retrieval_results_loader import export_retrieval_results_to_csv
from app.models.benchmark import RetrievalResultsDataset, RetrievalResultRow
>>>>>>> 78285f2b (added s4m benchmark)

# Create dataset from our retrieval results
results = [
    RetrievalResultRow(
        query_id="tcfd_1",
        report_id="report_001",
        chunk_id="chunk_001",
        chunk_text="Climate risks...",
        position=1,
        score=0.95,
        similarity_score=0.92
    ),
    # ... more results
]

dataset = RetrievalResultsDataset(
    dataset_id="our_results_v1",
    name="Our Retrieval Results",
    source="internal",
    results=results
)

# Export to CSV
export_retrieval_results_to_csv(dataset, "our_results.csv")
```

## Flow B: Load User-Provided CSV (Webhook-Ready)

Load retrieval results from CSV file or content. This function is designed to be webhook-ready.

### Function: `load_retrieval_results_from_csv`

```python
<<<<<<< HEAD
from report_analyst.core.benchmark.retrieval_results_loader import load_retrieval_results_from_csv
=======
from app.core.benchmark.retrieval_results_loader import load_retrieval_results_from_csv
>>>>>>> 78285f2b (added s4m benchmark)

# Option 1: Load from file path
dataset = load_retrieval_results_from_csv(
    csv_path="user_results.csv",
    dataset_id="user_results_v1",
    dataset_name="User Uploaded Results"
)

# Option 2: Load from CSV content (webhook-ready)
csv_content = """query_id,chunk_id,position,score
tcfd_1,chunk_001,1,0.95
tcfd_1,chunk_015,2,0.89"""

dataset = load_retrieval_results_from_csv(
    csv_content=csv_content,
    dataset_id="webhook_results",
    dataset_name="Webhook Results"
)
```

### Webhook Example

```python
from fastapi import FastAPI, UploadFile, File
<<<<<<< HEAD
from report_analyst.core.benchmark.retrieval_results_loader import load_retrieval_results_from_csv
=======
from app.core.benchmark.retrieval_results_loader import load_retrieval_results_from_csv
>>>>>>> 78285f2b (added s4m benchmark)

app = FastAPI()

@app.post("/api/benchmark/upload-results")
async def upload_retrieval_results(file: UploadFile = File(...)):
    """Webhook endpoint to upload retrieval results CSV"""
    csv_content = await file.read()
    
    dataset = load_retrieval_results_from_csv(
        csv_content=csv_content,
        dataset_id=f"upload_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
        dataset_name=file.filename
    )
    
    return {"dataset_id": dataset.dataset_id, "num_results": len(dataset.results)}
```

## Flow C: Load from SQLite

```python
<<<<<<< HEAD
from report_analyst.core.benchmark.retrieval_results_loader import load_retrieval_results_from_sqlite
=======
from app.core.benchmark.retrieval_results_loader import load_retrieval_results_from_sqlite
>>>>>>> 78285f2b (added s4m benchmark)

dataset = load_retrieval_results_from_sqlite(
    db_path="retrieval_results.db",
    table_name="retrieval_results",
    dataset_id="sqlite_results",
    dataset_name="SQLite Results",
    query_filter="report_id = 'report_001'"  # Optional filter
)
```

## Comparing Datasets

Compare a reference dataset (ground truth) against an input dataset (actual results).

### Example

```python
<<<<<<< HEAD
from report_analyst.core.benchmark.evaluation_engine import EvaluationEngine
from report_analyst.core.benchmark.retrieval_results_loader import (
=======
from app.core.benchmark.evaluation_engine import EvaluationEngine
from app.core.benchmark.retrieval_results_loader import (
>>>>>>> 78285f2b (added s4m benchmark)
    load_retrieval_results_from_csv,
    load_retrieval_results_from_sqlite
)

# Load reference dataset (e.g., climretrieve)
reference = load_retrieval_results_from_csv(
    csv_path="climretrieve_reference.csv",
    dataset_id="climretrieve_v1",
    dataset_name="ClimRetrieve Reference"
)

# Load input dataset (our results or user upload)
input_dataset = load_retrieval_results_from_csv(
    csv_path="our_results.csv",
    dataset_id="our_results_v1",
    dataset_name="Our Results"
)

# Compare datasets
engine = EvaluationEngine()
metrics = engine.compare_datasets(
    reference_dataset=reference,
    input_dataset=input_dataset,
    k_values=[1, 3, 5, 10]
)

print(f"MAP: {metrics.mean_average_precision:.3f}")
print(f"MRR: {metrics.mean_reciprocal_rank:.3f}")
print(f"Precision@5: {metrics.precision_at_k[5]:.3f}")
```

## Models

### RetrievalResultRow

Single row in a retrieval results dataset.

```python
class RetrievalResultRow(BaseModel):
    query_id: str
    report_id: Optional[str]
    chunk_id: str
    chunk_text: Optional[str]
    position: int  # 1-indexed
    score: float
    similarity_score: Optional[float]
    llm_score: Optional[float]
    metadata: Dict[str, Any]
```

### RetrievalResultsDataset

Collection of retrieval results.

```python
class RetrievalResultsDataset(BaseModel):
    dataset_id: str
    name: str
    description: Optional[str]
    source: str  # 'csv', 'sqlite', 'internal'
    source_path: Optional[str]
    results: List[RetrievalResultRow]
    
    def get_results_by_query(self, query_id: str) -> List[RetrievalResultRow]
    def get_unique_queries(self) -> List[str]
    def get_unique_reports(self) -> List[str]
```

## Key Functions

### Loaders

- `load_retrieval_results_from_csv()` - Load from CSV file or content (webhook-ready)
- `load_retrieval_results_from_sqlite()` - Load from SQLite database

### Exporters

- `export_retrieval_results_to_csv()` - Export dataset to CSV file

### Evaluation

- `EvaluationEngine.compare_datasets()` - Compare reference vs input datasets

## Migration from Old Format

The old format (YAML with ground truth chunks) is still supported through `BenchmarkDatasetContent`. The new format (`RetrievalResultsDataset`) is for comparing two retrieval result sets directly.

## Next Steps

1. Update UI to support CSV upload
2. Add export functionality to convert our retrieval results to CSV
3. Integrate with existing analyzer to export results automatically
