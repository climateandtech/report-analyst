from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class SourceRectangle(BaseModel):
    """A selected PDF region expressed in PDF-page coordinates."""

    x: float
    y: float
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class SourceAnchor(BaseModel):
    """The source text and location retained for a future structured fact."""

    id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    page: int = Field(ge=1)
    span_start: int = Field(ge=0)
    span_end: int
    selected_text: str = Field(min_length=1)
    rects: list[SourceRectangle] = Field(min_length=1)
    created_at: datetime | None = None

    @model_validator(mode="after")
    def validate_span(self) -> "SourceAnchor":
        if self.span_end <= self.span_start:
            raise ValueError("span_end must be greater than span_start")
        return self
