from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class SourceTag(BaseModel):
    """A fact taken from a saved PDF source: an ESRS concept and its value."""

    id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    concept: str = Field(min_length=1)
    # Stored the way XBRL writes it, such as 0.25 for 25 % or true for yes.
    value: str = Field(min_length=1)
    unit: str | None = None
    decimals: int | None = None
    created_at: datetime | None = None

    @model_validator(mode="after")
    def validate_number(self) -> "SourceTag":
        if (self.unit is None) != (self.decimals is None):
            raise ValueError("A number needs both a unit and decimals")
        return self
