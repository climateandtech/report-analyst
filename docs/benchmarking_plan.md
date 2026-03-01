# Information Retrieval Benchmarking Plan

## Overview

This document outlines the plan for implementing dataset upload capabilities, benchmarking the information retrieval pipeline, and adding human annotation functionality to the report-analyst system.

## 1. Dataset Upload and Management

### Data Structure
Benchmark datasets will be stored in YAML format:

```yaml
dataset_id: "tcfd_climate_risks_v1"
name: "TCFD Climate Risks Benchmark Dataset"
description: "Ground truth chunk relevance for TCFD climate risk questions"
version: "1.0"
created_at: "2024-01-15"
question_set: "tcfd"
questions:
  - question_id: "tcfd_1"
    question_text: "What are the climate-related risks?"
    ground_truth_chunks:
      - chunk_id: "chunk_001"
        relevance_score: 1.0  # Ground truth relevance (0.0-1.0)
        is_evidence: true
        evidence_order: 1
        annotation_notes: "Contains specific climate risk metrics"
```

### Database Schema Extensions

```sql
-- Benchmark datasets table
CREATE TABLE benchmark_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT UNIQUE,
    name TEXT,
    description TEXT,
    version TEXT,
    question_set TEXT,
    file_path TEXT,  -- Path to the dataset file
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Ground truth chunk relevance
CREATE TABLE ground_truth_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT,
    question_id TEXT,
    chunk_id TEXT,
    relevance_score REAL,
    is_evidence BOOLEAN,
    evidence_order INTEGER,
    annotation_notes TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY(dataset_id) REFERENCES benchmark_datasets(dataset_id)
);

-- Benchmark evaluation results
CREATE TABLE benchmark_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT,
    evaluation_name TEXT,
    config_hash TEXT,  -- Hash of retrieval configuration
    retrieval_config TEXT,  -- JSON of retrieval parameters
    evaluation_metrics TEXT,  -- JSON of computed metrics
    created_at TIMESTAMP,
    FOREIGN KEY(dataset_id) REFERENCES benchmark_datasets(dataset_id)
);

-- Human annotations table
CREATE TABLE human_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_id INTEGER,
    question_id TEXT,
    chunk_id TEXT,
    human_relevance_score REAL,
    human_is_evidence BOOLEAN,
    human_evidence_order INTEGER,
    annotation_notes TEXT,
    annotator_id TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY(evaluation_id) REFERENCES benchmark_evaluations(id)
);
```

## 2. Benchmarking Engine

### Core Components

1. **Dataset Loader**: Parse and validate benchmark datasets
2. **Evaluation Engine**: Compare retrieval results against ground truth
3. **Metrics Calculator**: Compute various evaluation metrics
4. **Configuration Manager**: Track different retrieval configurations

### Evaluation Metrics

- **Precision@K**: Percentage of retrieved chunks that are relevant
- **Recall@K**: Percentage of relevant chunks that were retrieved
- **F1@K**: Harmonic mean of precision and recall
- **Mean Reciprocal Rank (MRR)**: Average of reciprocal ranks of first relevant chunk
- **Normalized Discounted Cumulative Gain (NDCG)**: Considers relevance scores and ranking
- **Mean Average Precision (MAP)**: Average precision across all questions

### Configuration Management

```python
class RetrievalConfig:
    chunk_size: int
    chunk_overlap: int
    top_k: int
    use_llm_scoring: bool
    embedding_model: str
    similarity_threshold: float
    llm_model: str
```

## 3. Human Annotation Interface

### Annotation Workflow

1. **Batch Annotation**: Annotate multiple chunks at once
2. **Individual Annotation**: Fine-tune individual chunk scores
3. **Evidence Assignment**: Mark chunks as evidence and assign order
4. **Notes and Comments**: Add contextual notes for annotations

### Interface Features

- Side-by-side comparison of retrieved vs. ground truth chunks
- Slider controls for relevance scores (0.0-1.0)
- Checkbox for evidence assignment
- Text areas for annotation notes
- Bulk operations for similar chunks
- Export/import annotation data

## 4. UI Integration

### New Streamlit Pages

1. **Dataset Management Page**
   - Upload benchmark datasets
   - View existing datasets
   - Dataset validation and preview
   - Dataset versioning

2. **Benchmarking Page**
   - Select dataset and retrieval configuration
   - Run benchmark evaluations
   - View evaluation results and metrics
   - Compare different configurations
   - Export evaluation reports

3. **Annotation Page**
   - Select evaluation results to annotate
   - Interactive annotation interface
   - Progress tracking
   - Annotation quality metrics

4. **Results Dashboard**
   - Historical evaluation trends
   - Configuration performance comparison
   - Annotation statistics
   - Model improvement tracking

## 5. API Extensions

### New Endpoints

```python
# Dataset management
POST /api/datasets/upload
GET /api/datasets
GET /api/datasets/{dataset_id}
DELETE /api/datasets/{dataset_id}

# Benchmarking
POST /api/benchmarks/evaluate
GET /api/benchmarks/results
GET /api/benchmarks/{evaluation_id}/metrics

# Annotations
POST /api/annotations/batch
GET /api/annotations/{evaluation_id}
PUT /api/annotations/{annotation_id}
```

## 6. File Structure

```
app/
├── core/
│   ├── benchmark/
│   │   ├── __init__.py
│   │   ├── dataset_loader.py
│   │   ├── evaluation_engine.py
│   │   ├── metrics_calculator.py
│   │   └── config_manager.py
│   ├── annotation/
│   │   ├── __init__.py
│   │   ├── annotation_manager.py
│   │   └── annotation_validator.py
│   └── storage/
│       ├── benchmark_store.py
│       └── annotation_store.py
├── models/
│   ├── benchmark.py
│   └── annotation.py
├── ui/
│   ├── dataset_management.py
│   ├── benchmarking.py
│   └── annotation_interface.py
└── api/
    ├── benchmark_routes.py
    └── annotation_routes.py
```

## 7. Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- Database schema extensions
- Dataset loader and validator
- Basic evaluation engine
- Core metrics calculation

### Phase 2: Benchmarking Engine (Week 3-4)
- Configuration management
- Evaluation workflow
- Results storage and retrieval
- Basic UI for running benchmarks

### Phase 3: Annotation System (Week 5-6)
- Annotation data model
- Annotation interface
- Batch annotation capabilities
- Annotation validation

### Phase 4: UI Integration (Week 7-8)
- Streamlit page integration
- Results visualization
- Configuration comparison
- Export/import functionality

### Phase 5: Advanced Features (Week 9-10)
- Advanced metrics (NDCG, MAP)
- Annotation quality assessment
- Automated improvement suggestions
- Performance optimization

## 8. Data Flow

1. **Dataset Upload**: User uploads benchmark dataset → Validation → Storage
2. **Benchmark Execution**: Select dataset + config → Run retrieval → Compare with ground truth → Calculate metrics → Store results
3. **Annotation Process**: Select evaluation results → Annotate chunks → Store annotations → Update evaluation metrics
4. **Analysis**: View historical trends → Compare configurations → Identify improvement opportunities

## 9. Configuration Management

### Retrieval Configurations
- Predefined configurations (fast, balanced, accurate)
- Custom configuration builder
- Configuration templates
- A/B testing framework

### Evaluation Settings
- Metrics to compute
- Evaluation thresholds
- Comparison baselines
- Export formats

## 10. Quality Assurance

### Dataset Validation
- Schema validation
- Data consistency checks
- Coverage analysis
- Duplicate detection

### Annotation Quality
- Inter-annotator agreement
- Annotation consistency checks
- Quality metrics
- Automated validation