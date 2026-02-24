"""
Pydantic Schemas for Report Analyst API

This module defines the data models used by the FastAPI endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalysisStatus(str, Enum):
    """Status of an analysis job"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUpload(BaseModel):
    """Request model for document upload"""

    file_path: str = Field(..., description="Path to the document file")
    source_type: Optional[str] = Field("local", description="Document source type (local or search_backend)")

    class Config:
        schema_extra = {"example": {"file_path": "/path/to/document.pdf", "source_type": "local"}}


class AnalysisConfiguration(BaseModel):
    """Configuration for analysis processing"""

    model_name: str = Field("gpt-4o-mini", description="LLM model to use")
    chunk_size: int = Field(500, description="Text chunk size")
    chunk_overlap: int = Field(20, description="Chunk overlap")
    top_k: int = Field(5, description="Top K chunks for retrieval")
    use_llm_scoring: bool = Field(False, description="Use LLM for chunk relevance scoring")
    single_call: bool = Field(True, description="Use single LLM call for analysis")
    force_recompute: bool = Field(False, description="Force recomputation of cached results")


class AnalysisJobRequest(BaseModel):
    """Request model for job-based analysis (document_id + selected_questions). Reserved for future use."""

    document_id: str = Field(..., description="ID of the uploaded document")
    question_set_id: str = Field(..., description="ID of the question set to use")
    selected_questions: List[str] = Field(..., description="List of question IDs to analyze")
    configuration: Optional[AnalysisConfiguration] = Field(default_factory=AnalysisConfiguration)

    class Config:
        schema_extra = {
            "example": {
                "document_id": "doc_123",
                "question_set_id": "tcfd",
                "selected_questions": ["tcfd_1", "tcfd_2"],
                "configuration": {
                    "model_name": "gpt-4o-mini",
                    "use_llm_scoring": False,
                },
            }
        }


class AnalysisJob(BaseModel):
    """Response model for analysis job"""

    job_id: str = Field(..., description="Unique job identifier")
    document_id: str = Field(..., description="Document being analyzed")
    question_set_id: str = Field(..., description="Question set being used")
    selected_questions: List[str] = Field(..., description="Questions being analyzed")
    status: AnalysisStatus = Field(..., description="Current job status")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Progress percentage")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ChunkRelevance(BaseModel):
    """Chunk relevance score for a question"""

    chunk_id: str = Field(..., description="Chunk identifier")
    question_id: str = Field(..., description="Question identifier")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    llm_explanation: Optional[str] = Field(None, description="LLM explanation of relevance")


class AnalysisResult(BaseModel):
    """Result of analyzing a single question"""

    job_id: str = Field(..., description="Job identifier")
    question_id: str = Field(..., description="Question identifier")
    question_text: str = Field(..., description="Full question text")
    answer: str = Field(..., description="Analysis answer")
    evidence_chunks: List[Dict[str, Any]] = Field(..., description="Supporting evidence chunks")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in the answer")
    model_used: str = Field(..., description="LLM model used for analysis")
    processing_time: float = Field(..., description="Time taken in seconds")


class Question(BaseModel):
    """Individual question model"""

    id: str = Field(..., description="Question identifier")
    text: str = Field(..., description="Question text")
    guidelines: Optional[str] = Field(None, description="Analysis guidelines")


class QuestionSet(BaseModel):
    """Question set model"""

    id: str = Field(..., description="Question set identifier")
    name: str = Field(..., description="Question set name")
    description: str = Field(..., description="Question set description")
    questions: Optional[Dict[str, Question]] = Field(None, description="Questions in the set")


class QuestionSetResponse(BaseModel):
    """Response model for question sets"""

    question_sets: Dict[str, Dict[str, Any]] = Field(..., description="Available question sets")


class DocumentChunkResponse(BaseModel):
    """Response model for document chunks"""

    chunk_id: str = Field(..., description="Chunk identifier")
    chunk_text: str = Field(..., description="Chunk text content")
    chunk_metadata: Dict[str, Any] = Field(..., description="Chunk metadata")
    relevance_scores: List[ChunkRelevance] = Field(default_factory=list, description="Relevance scores")


class IntegrationsResponse(BaseModel):
    """Response model for available integrations"""

    available_integrations: Dict[str, bool] = Field(..., description="Available integration modules")
    document_sources: List[str] = Field(..., description="Available document sources")


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str = Field(..., description="Health status")
    version: Optional[str] = Field(None, description="API version")
    core_package: Optional[bool] = Field(None, description="Core package availability")
    question_loader: Optional[bool] = Field(None, description="Question loader status")
    analyzer: Optional[bool] = Field(None, description="Analyzer status")
    available_integrations: Optional[Dict[str, bool]] = Field(None, description="Integration status")
    document_sources: Optional[List[str]] = Field(None, description="Available document sources")


class AnalysisRequest(BaseModel):
    """Request for document analysis"""

    filename: str = Field(..., description="Name of the uploaded file")
    question_set: str = Field("tcfd", description="Question set to use")
    chunk_size: int = Field(500, description="Text chunk size")
    chunk_overlap: int = Field(20, description="Overlap between chunks")
    top_k: int = Field(5, description="Number of top chunks to consider")
    model: str = Field("gpt-4o-mini", description="LLM model to use")


class AnalysisResponse(BaseModel):
    """Response from document analysis"""

    filename: str = Field(..., description="Name of the analyzed file")
    question_set: str = Field(..., description="Question set used")
    results: List[Dict[str, Any]] = Field(..., description="Analysis results")
    configuration: Dict[str, Any] = Field(..., description="Analysis configuration")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


class AsyncJobResponse(BaseModel):
    """Async job response"""

    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Job status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Job creation timestamp")


class JobStatus(BaseModel):
    """Job status information"""

    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Current job status")
    progress: float = Field(0.0, description="Job progress percentage")
    error: Optional[str] = Field(None, description="Error message if failed")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Analysis results if completed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Status timestamp")
