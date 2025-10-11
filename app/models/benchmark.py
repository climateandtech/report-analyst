from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BenchmarkDataset(BaseModel):
    dataset_id: str = Field(..., description="Unique identifier for the dataset")
    name: str = Field(..., description="Human-readable name of the dataset")
    description: str = Field(..., description="Description of the dataset")
    version: str = Field(..., description="Version of the dataset")
    question_set: str = Field(..., description="Question set this dataset is for")
    file_path: Optional[str] = Field(None, description="Path to the dataset file")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

class GroundTruthChunk(BaseModel):
    chunk_id: str = Field(..., description="Identifier for the chunk")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Ground truth relevance score")
    is_evidence: bool = Field(..., description="Whether this chunk is evidence")
    evidence_order: Optional[int] = Field(None, description="Order of evidence if applicable")
    annotation_notes: Optional[str] = Field(None, description="Notes about this annotation")

class BenchmarkQuestion(BaseModel):
    question_id: str = Field(..., description="Question identifier")
    question_text: str = Field(..., description="The actual question text")
    ground_truth_chunks: List[GroundTruthChunk] = Field(..., description="Ground truth chunks for this question")

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
    use_llm_scoring: bool = Field(default=False, description="Whether to use LLM scoring")
    embedding_model: str = Field(default="default", description="Embedding model to use")
    similarity_threshold: float = Field(default=0.0, description="Minimum similarity threshold")
    llm_model: Optional[str] = Field(None, description="LLM model for scoring")

class EvaluationMetrics(BaseModel):
    precision_at_k: Dict[int, float] = Field(default_factory=dict, description="Precision at different K values")
    recall_at_k: Dict[int, float] = Field(default_factory=dict, description="Recall at different K values")
    f1_at_k: Dict[int, float] = Field(default_factory=dict, description="F1 score at different K values")
    mean_reciprocal_rank: float = Field(default=0.0, description="Mean reciprocal rank")
    mean_average_precision: float = Field(default=0.0, description="Mean average precision")
    ndcg_at_k: Dict[int, float] = Field(default_factory=dict, description="NDCG at different K values")

class BenchmarkEvaluation(BaseModel):
    id: Optional[int] = None
    dataset_id: str = Field(..., description="Dataset used for evaluation")
    evaluation_name: str = Field(..., description="Name of this evaluation")
    config_hash: str = Field(..., description="Hash of the retrieval configuration")
    retrieval_config: RetrievalConfig = Field(..., description="Configuration used for retrieval")
    evaluation_metrics: EvaluationMetrics = Field(..., description="Computed evaluation metrics")
    created_at: Optional[datetime] = None

class HumanAnnotation(BaseModel):
    id: Optional[int] = None
    evaluation_id: int = Field(..., description="Evaluation this annotation belongs to")
    question_id: str = Field(..., description="Question being annotated")
    chunk_id: str = Field(..., description="Chunk being annotated")
    human_relevance_score: float = Field(..., ge=0.0, le=1.0, description="Human-assigned relevance score")
    human_is_evidence: bool = Field(..., description="Human judgment on evidence")
    human_evidence_order: Optional[int] = Field(None, description="Human-assigned evidence order")
    annotation_notes: Optional[str] = Field(None, description="Notes from the annotator")
    annotator_id: str = Field(..., description="ID of the person making the annotation")
    created_at: Optional[datetime] = None
