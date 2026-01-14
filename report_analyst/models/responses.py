from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .requests import DocumentMetadata


class AnalysisResponse(BaseModel):
    document_id: str
    analysis_type: str
    summary: str
    key_points: List[str]
    topics: List[Dict[str, float]]
    metadata: DocumentMetadata
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score of the analysis"
    )


class QuestionResponse(BaseModel):
    document_id: str
    question: str
    answer: str
    context_used: Optional[str] = None
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score of the answer"
    )
    relevant_quotes: List[str] = Field(
        default_factory=list,
        description="Relevant quotes from the document supporting the answer",
    )


class ErrorResponse(BaseModel):
    detail: str
    error_code: str
    additional_info: Optional[Dict] = None
