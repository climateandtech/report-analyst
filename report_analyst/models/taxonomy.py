from typing import Literal

from pydantic import BaseModel, ConfigDict

ConceptKind = Literal["narrative", "number", "yes/no", "menu", "text", "date"]


class EsrsReference(BaseModel):
    """Where a concept is required in the ESRS."""

    model_config = ConfigDict(frozen=True)

    section: str | None = None
    disclosure_requirement: str | None = None
    paragraph: str | None = None
    subparagraph: str | None = None
    clause: str | None = None
    datapoint_id: str | None = None
    url: str | None = None


class TaxonomyOption(BaseModel):
    """An allowed value of a menu concept."""

    name: str
    label: str


class TaxonomyConcept(BaseModel):
    """A taxonomy concept that can carry a reported fact."""

    name: str
    label: str
    kind: ConceptKind
    data_type: str
    period_type: str
    group: str | None = None
    esrs_references: list[EsrsReference] = []
    options_domain: str | None = None
    options: list[TaxonomyOption] = []


class Taxonomy(BaseModel):
    identifier: str
    name: str
    version: str
    concepts: list[TaxonomyConcept]
