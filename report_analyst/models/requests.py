from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    GENERAL = "general"
    SUSTAINABILITY = "sustainability"
    FINANCIAL = "financial"
    RISK = "risk"
    CUSTOM = "custom"


class AnalysisRequest(BaseModel):
    document_id: str = Field(..., description="The ID of the uploaded document")
    analysis_type: AnalysisType = Field(
        default=AnalysisType.GENERAL, description="The type of analysis to perform"
    )
    custom_instructions: Optional[str] = Field(
        None, description="Custom instructions for the analysis"
    )


class QuestionRequest(BaseModel):
    document_id: str = Field(..., description="The ID of the uploaded document")
    question: str = Field(..., description="The question to ask about the document")
    context: Optional[str] = Field(
        None, description="Additional context for the question"
    )


class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    num_pages: Optional[int] = None
    file_type: str
    file_size: int
