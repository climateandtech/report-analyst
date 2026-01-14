from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# Define enums first
class DatasetType(str, Enum):
    """Types of benchmark datasets"""

    INFORMATION_RETRIEVAL = "information_retrieval"  # IR: Compare retrieved chunks
    INFORMATION_EXTRACTION = "information_extraction"  # IE: Compare analysis/answers


class FlexibleDatasetRow(BaseModel):
    """
    Flexible row model that can handle different column names and structures.
    All fields are stored in a flexible data dictionary.
    """

    data: Dict[str, Any] = Field(
        ..., description="Flexible data dictionary containing all row fields"
    )

    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key (case-insensitive)"""
        key_lower = key.lower()
        for k, v in self.data.items():
            if k.lower() == key_lower:
                return v
        return default

    def get_query_id(self) -> Optional[str]:
        """Get query/question ID using common column name variations"""
        return self.get("query_id") or self.get("question_id") or self.get("qid")

    def get_chunk_id(self) -> Optional[str]:
        """Get chunk ID using common column name variations"""
        return self.get("chunk_id") or self.get("chunk") or self.get("cid")

    def get_score(self) -> Optional[float]:
        """Get score using common column name variations"""
        score = (
            self.get("score")
            or self.get("relevance_score")
            or self.get("confidence_score")
            or self.get("similarity_score")
        )
        if score is not None:
            try:
                return float(score)
            except (ValueError, TypeError):
                return None
        return None

    def get_position(self) -> Optional[int]:
        """Get position/rank using common column name variations"""
        pos = self.get("position") or self.get("rank") or self.get("order")
        if pos is not None:
            try:
                return int(pos)
            except (ValueError, TypeError):
                return None
        return None

    def get_answer(self) -> Optional[str]:
        """Get answer/analysis text for IE datasets"""
        return (
            self.get("answer")
            or self.get("analysis")
            or self.get("text")
            or self.get("response")
        )

    def get_category(self) -> Optional[str]:
        """Get category/classification"""
        return (
            self.get("category")
            or self.get("class")
            or self.get("label")
            or self.get("type")
        )


class BenchmarkDataset(BaseModel):
    """
    Unified flexible benchmark dataset model that handles different formats, column names, and dataset types.
    Supports both Information Retrieval (IR) and Information Extraction (IE) datasets.
    Can be used for metadata-only (database storage) or with full results (CSV/SQLite loaded).
    """

    # Core identifiers
    dataset_id: str = Field(..., description="Unique identifier for this dataset")
    name: str = Field(..., description="Name of the dataset")
    description: Optional[str] = Field(None, description="Description of the dataset")

    # Metadata fields
    version: Optional[str] = Field(None, description="Version of the dataset")
    question_set: Optional[str] = Field(
        None, description="Question set this dataset is for"
    )
    file_path: Optional[str] = Field(None, description="Path to the dataset file")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    # Dataset type and source (for loaded datasets)
    dataset_type: Optional[DatasetType] = Field(
        None, description="Type of dataset: IR or IE (None for metadata-only)"
    )
    source: Optional[str] = Field(
        None, description="Source: 'csv', 'sqlite', 'internal', 'database'"
    )
    source_path: Optional[str] = Field(None, description="Path to source file/database")

    # Data and mapping (for loaded datasets)
    column_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of standard names to actual column names",
    )
    results: List[FlexibleDatasetRow] = Field(
        default_factory=list,
        description="List of dataset rows (empty for metadata-only)",
    )

    def get_results_by_query(self, query_id: str) -> List[FlexibleDatasetRow]:
        """Get all results for a specific query/question"""
        return [r for r in self.results if r.get_query_id() == query_id]

    def get_unique_queries(self) -> List[str]:
        """Get list of unique query/question IDs"""
        query_ids = [r.get_query_id() for r in self.results if r.get_query_id()]
        return sorted(list(set(query_ids)))

    def get_unique_reports(self) -> List[str]:
        """Get list of unique report/document IDs"""
        report_ids = [
            r.get("report_id") or r.get("document_id") or r.get("doc_id")
            for r in self.results
        ]
        report_ids = [r for r in report_ids if r]
        return sorted(list(set(report_ids)))

    def is_metadata_only(self) -> bool:
        """Check if this is a metadata-only dataset (no results loaded)"""
        return len(self.results) == 0

    def has_results(self) -> bool:
        """Check if this dataset has results loaded"""
        return len(self.results) > 0


class GroundTruthChunk(BaseModel):
    chunk_id: str = Field(..., description="Identifier for the chunk")
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Ground truth relevance score"
    )
    is_evidence: bool = Field(..., description="Whether this chunk is evidence")
    evidence_order: Optional[int] = Field(
        None, description="Order of evidence if applicable"
    )
    annotation_notes: Optional[str] = Field(
        None, description="Notes about this annotation"
    )


class BenchmarkQuestion(BaseModel):
    question_id: str = Field(..., description="Question identifier")
    question_text: str = Field(..., description="The actual question text")
    ground_truth_chunks: List[GroundTruthChunk] = Field(
        ..., description="Ground truth chunks for this question"
    )


class BenchmarkDatasetContent(BaseModel):
    dataset_id: str
    name: str
    description: str
    version: str
    question_set: str
    created_at: str
    questions: List[BenchmarkQuestion]


class RetrievalConfig(BaseModel):
    chunk_size: int = Field(default=1000, description="Size of text chunks")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    top_k: int = Field(default=5, description="Number of chunks to retrieve")
    use_llm_scoring: bool = Field(
        default=False, description="Whether to use LLM scoring"
    )
    embedding_model: str = Field(
        default="default", description="Embedding model to use"
    )
    similarity_threshold: float = Field(
        default=0.0, description="Minimum similarity threshold"
    )
    llm_model: Optional[str] = Field(None, description="LLM model for scoring")


class EvaluationMetrics(BaseModel):
    precision_at_k: Dict[int, float] = Field(
        default_factory=dict, description="Precision at different K values"
    )
    recall_at_k: Dict[int, float] = Field(
        default_factory=dict, description="Recall at different K values"
    )
    f1_at_k: Dict[int, float] = Field(
        default_factory=dict, description="F1 score at different K values"
    )
    mean_reciprocal_rank: float = Field(default=0.0, description="Mean reciprocal rank")
    mean_average_precision: float = Field(
        default=0.0, description="Mean average precision"
    )
    ndcg_at_k: Dict[int, float] = Field(
        default_factory=dict, description="NDCG at different K values"
    )


class BenchmarkEvaluation(BaseModel):
    id: Optional[int] = None
    dataset_id: str = Field(..., description="Dataset used for evaluation")
    evaluation_name: str = Field(..., description="Name of this evaluation")
    config_hash: str = Field(..., description="Hash of the retrieval configuration")
    retrieval_config: RetrievalConfig = Field(
        ..., description="Configuration used for retrieval"
    )
    evaluation_metrics: EvaluationMetrics = Field(
        ..., description="Computed evaluation metrics"
    )
    created_at: Optional[datetime] = None


class HumanAnnotation(BaseModel):
    id: Optional[int] = None
    evaluation_id: int = Field(..., description="Evaluation this annotation belongs to")
    question_id: str = Field(..., description="Question being annotated")
    chunk_id: str = Field(..., description="Chunk being annotated")
    human_relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Human-assigned relevance score"
    )
    human_is_evidence: bool = Field(..., description="Human judgment on evidence")
    human_evidence_order: Optional[int] = Field(
        None, description="Human-assigned evidence order"
    )
    annotation_notes: Optional[str] = Field(
        None, description="Notes from the annotator"
    )
    annotator_id: str = Field(..., description="ID of the person making the annotation")
    created_at: Optional[datetime] = None


# Legacy models for backward compatibility


class RetrievalResultRow(BaseModel):
    """Single row in a retrieval results dataset (CSV format) - Legacy model"""

    query_id: str = Field(..., description="Question/query identifier")
    report_id: Optional[str] = Field(None, description="Report/document identifier")
    chunk_id: str = Field(..., description="Chunk identifier")
    chunk_text: Optional[str] = Field(None, description="Chunk text content")
    position: int = Field(
        ..., ge=1, description="Position/rank in retrieval results (1-indexed)"
    )
    score: float = Field(
        ..., description="Retrieval score (similarity, relevance, etc.)"
    )
    similarity_score: Optional[float] = Field(
        None, description="Vector similarity score"
    )
    llm_score: Optional[float] = Field(None, description="LLM-based relevance score")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class RetrievalResultsDataset(BaseModel):
    """Dataset containing retrieval results (from CSV or SQLite) - Legacy model"""

    dataset_id: str = Field(..., description="Unique identifier for this dataset")
    name: str = Field(..., description="Name of the dataset")
    description: Optional[str] = Field(None, description="Description of the dataset")
    source: str = Field(..., description="Source: 'csv', 'sqlite', 'internal'")
    source_path: Optional[str] = Field(None, description="Path to source file/database")
    results: List[RetrievalResultRow] = Field(
        ..., description="List of retrieval results"
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

    def get_results_by_query(self, query_id: str) -> List[RetrievalResultRow]:
        """Get all retrieval results for a specific query"""
        return [r for r in self.results if r.query_id == query_id]

    def get_unique_queries(self) -> List[str]:
        """Get list of unique query IDs"""
        return sorted(list(set(r.query_id for r in self.results)))

    def get_unique_reports(self) -> List[str]:
        """Get list of unique report IDs"""
        return sorted(list(set(r.report_id for r in self.results if r.report_id)))
