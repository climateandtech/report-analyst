# Expected File Formats for Datasets

This document describes the structure expected for **ground truth** and **benchmark** datasets when using the Benchmarking / Evaluate features. Alignment (CSV/Excel only) maps your columns to these conventions.

---

## CSV and Excel (information retrieval)

Used for both ground truth and benchmark. Column names are **case-insensitive**; the loader accepts common variants.

### After alignment (evaluation engine expects)

| Role | Required columns | Optional / accepted variants |
|------|------------------|------------------------------|
| **Query** | `query_id` | `question_id`, `qid`, `query` |
| **Chunk** | `chunk_id` | `chunk`, `cid` |
| **Rank** | `position` | `rank`, `order`, `pos` |
| **Score** | `score` | `relevance_score`, `confidence_score`, `similarity_score` |
| **Document** | — | `report_id`, `document_id`, `doc_id`, `report` |

For **ground truth** alignment (e.g. ClimRetrieve mapper), your CSV/Excel should have:

- **document** (or `report`) — document/report identifier  
- **question** — question text  
- **context** or **relevant** — chunk/relevant text  
- **relevance_label** (or `Source Relevance Score`, `relevance`, `label`) — relevance score or label  

For **benchmark** alignment:

- **report** (or `document`) — report identifier  
- **question** — question text  
- **paragraph** (or `chunk`) — retrieved paragraph text  
- **relevant_text** (or `relevant`) — optional; used for matching to ground truth  
- **position** / **number** — optional; rank or paragraph number  
- **relevant_text_sim** — optional; similarity score for ranking  
- **label** / **relevance** — optional; relevance label  

If your file already has `query_id`, `chunk_id`, `position`, and `score` (or the accepted variants), it can be used without alignment. Otherwise use **Dataset Alignment** (CSV or Excel only) to convert to the expected structure.

---

## YAML and JSON (benchmark content schema)

Used for **benchmark datasets** that follow the internal content schema (e.g. question sets with ground truth chunks). **Not** used for alignment; alignment works only for CSV and Excel.

### Expected top-level structure

```yaml
dataset_id: string
name: string
description: string
version: string
question_set: string
questions: array
```

### Each item in `questions`

```yaml
question_id: string
question_text: string
ground_truth_chunks: array
```

### Each item in `ground_truth_chunks`

```yaml
chunk_id: string
relevance_score: number   # 0.0 to 1.0
is_evidence: boolean
evidence_order: number     # optional
annotation_notes: string  # optional
```

Example (YAML):

```yaml
dataset_id: my-benchmark
name: My Benchmark
description: Optional description
version: "1.0"
question_set: default
questions:
  - question_id: q1
    question_text: "What are the company's emissions targets?"
    ground_truth_chunks:
      - chunk_id: c1
        relevance_score: 1.0
        is_evidence: true
        evidence_order: 1
```

**Note:** Report-level YAML (e.g. ClimRetrieve with `reports` → `questions` → `paragraphs`) is handled by a separate loader and is converted to the same internal format when supported.

---

## Summary

| Format | Use case | Alignment |
|--------|----------|-----------|
| **CSV** | Ground truth or benchmark (IR) | Yes — use Dataset Alignment if your columns differ. |
| **Excel** | Ground truth or benchmark (IR) | Yes — same as CSV. |
| **YAML** | Benchmark (content schema) | No — must match the schema above. |
| **JSON** | Benchmark (content schema) | No — same structure as YAML. |

For column mapping (e.g. ClimRetrieve), see `report_analyst/config/datasets/climretrieve.yaml` and add configs under `report_analyst/config/datasets/` for other conventions.
