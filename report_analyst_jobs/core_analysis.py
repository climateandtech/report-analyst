"""
Core Analysis Functions

Essential analysis functions that can be used across different deployment scenarios.
Clean, focused implementations without framework dependencies.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class AnalysisConfig:
    """Configuration for analysis operations"""

    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 2000
    use_centralized_llm: bool = False
    owner: str = "default"
    experiment_name: str = "analysis"
    deployment_type: str = "experiment"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisRequest:
    """Request for document analysis"""

    document_id: str
    question_set: str
    questions: List[str]
    chunks: List[Dict[str, Any]]
    config: AnalysisConfig
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "question_set": self.question_set,
            "questions": self.questions,
            "chunks": self.chunks,
            "config": self.config.to_dict(),
            "metadata": self.metadata or {},
        }


@dataclass
class AnalysisResult:
    """Result from document analysis"""

    request_id: str
    document_id: str
    question_set: str
    questions: List[str]
    answers: List[str]
    method: str
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "document_id": self.document_id,
            "question_set": self.question_set,
            "questions": self.questions,
            "answers": self.answers,
            "method": self.method,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata or {},
            "timestamp": self.timestamp,
        }


def analyze_document_core(request: AnalysisRequest) -> AnalysisResult:
    """
    Core analysis function that works with any LLM backend.

    Args:
        request: Analysis request with document and questions

    Returns:
        AnalysisResult: Complete analysis result
    """
    try:
        answers = []

        # Process each question
        for question in request.questions:
            # Get relevant context from chunks
            context = _extract_relevant_context(request.chunks, question)

            # Analyze question with context
            answer = _analyze_question(question, context, request.config)
            answers.append(answer)

        return AnalysisResult(
            request_id=request.document_id,
            document_id=request.document_id,
            question_set=request.question_set,
            questions=request.questions,
            answers=answers,
            method="core_analysis",
            success=True,
            metadata=request.metadata,
        )

    except Exception as e:
        logger.error(f"Core analysis failed: {e}")
        return AnalysisResult(
            request_id=request.document_id,
            document_id=request.document_id,
            question_set=request.question_set,
            questions=request.questions,
            answers=[],
            method="core_analysis",
            success=False,
            error=str(e),
            metadata=request.metadata,
        )


def _extract_relevant_context(chunks: List[Dict[str, Any]], question: str) -> str:
    """
    Extract relevant context from chunks for a question.

    Args:
        chunks: List of document chunks
        question: Question to find context for

    Returns:
        str: Relevant context text
    """
    # Simple implementation - use first few chunks
    # In production, this would use semantic similarity
    relevant_chunks = chunks[:3]

    context_parts = []
    for chunk in relevant_chunks:
        chunk_text = chunk.get("chunk_text", "")
        if chunk_text:
            context_parts.append(chunk_text)

    return " ".join(context_parts)


def _analyze_question(question: str, context: str, config: AnalysisConfig) -> str:
    """
    Analyze a single question with context.

    Args:
        question: Question to analyze
        context: Relevant context
        config: Analysis configuration

    Returns:
        str: Analysis answer
    """
    # This is a placeholder implementation
    # In production, this would call the actual LLM

    answer = f"""
    Question: {question}
    
    Analysis based on the document content:
    
    {context[:500]}...
    
    [This is a placeholder analysis. In production, this would use the configured LLM model ({config.model}) to provide a detailed analysis.]
    """

    return answer.strip()


def create_analysis_request(
    document_id: str,
    question_set: str,
    questions: List[str],
    chunks: List[Dict[str, Any]],
    config: Optional[AnalysisConfig] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AnalysisRequest:
    """
    Create an analysis request with defaults.

    Args:
        document_id: Unique document identifier
        question_set: Name of question set
        questions: List of questions to analyze
        chunks: Document chunks
        config: Optional analysis configuration
        metadata: Optional metadata

    Returns:
        AnalysisRequest: Complete request object
    """
    if config is None:
        config = AnalysisConfig()

    return AnalysisRequest(
        document_id=document_id,
        question_set=question_set,
        questions=questions,
        chunks=chunks,
        config=config,
        metadata=metadata,
    )


def format_analysis_for_display(result: AnalysisResult) -> Dict[str, Any]:
    """
    Format analysis result for display in UIs.

    Args:
        result: Analysis result

    Returns:
        Dict with formatted display data
    """
    return {
        "title": f"Analysis Results - {result.question_set.upper()}",
        "questions": result.questions,
        "answers": result.answers,
        "metadata": {
            "Method": result.method,
            "Success": "✅" if result.success else "❌",
            "Questions": len(result.questions),
            "Timestamp": result.timestamp,
            "Document ID": result.document_id,
        },
        "raw_result": result.to_dict(),
    }


def validate_analysis_request(request: AnalysisRequest) -> List[str]:
    """
    Validate analysis request.

    Args:
        request: Request to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if not request.document_id:
        errors.append("Document ID is required")

    if not request.questions:
        errors.append("At least one question is required")

    if not request.chunks:
        errors.append("Document chunks are required")

    if not request.question_set:
        errors.append("Question set name is required")

    for i, question in enumerate(request.questions):
        if not question.strip():
            errors.append(f"Question {i+1} is empty")

    return errors
