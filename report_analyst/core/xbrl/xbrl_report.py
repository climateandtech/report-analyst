"""Writes a report's tags as an XBRL report, so Arelle can check them."""

from datetime import date
from xml.sax.saxutils import escape, quoteattr

from report_analyst.core.xbrl.esrs_taxonomy import MONEY
from report_analyst.core.xbrl.tagging import PURE, data_type
from report_analyst.models.source_tag import SourceTag
from report_analyst.models.taxonomy import Taxonomy, TaxonomyConcept

# Each fact's id is this prefix and its tag's id, so Arelle's messages can be traced back to their tag.
FACT_ID = "tag-"
# The scheme for companies identified by their Legal Entity Identifier (LEI).
LEI_SCHEME = "http://standards.iso.org/iso/17442"
NAMESPACES = {
    "xbrli": "http://www.xbrl.org/2003/instance",
    "link": "http://www.xbrl.org/2003/linkbase",
    "xlink": "http://www.w3.org/1999/xlink",
    "iso4217": "http://www.xbrl.org/2003/iso4217",
    "utr": "http://www.xbrl.org/2009/utr",
}


def xbrl_report(tags: list[SourceTag], taxonomy: Taxonomy, lei: str, start: date, end: date) -> str:
    """An XBRL report with one fact per tag. Every tag must use a concept of the taxonomy."""
    concepts = {concept.name: concept for concept in taxonomy.concepts}
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n<xbrli:xbrl {namespace_declarations(taxonomy)}>'
        f"{schema_ref(taxonomy)}{contexts(lei, start, end)}{units(tags, concepts)}"
        + "".join(_fact(tag, concepts[tag.concept], taxonomy.namespaces) for tag in tags)
        + "</xbrli:xbrl>"
    )


def namespace_declarations(taxonomy: Taxonomy) -> str:
    return " ".join(f"xmlns:{prefix}={quoteattr(uri)}" for prefix, uri in {**NAMESPACES, **taxonomy.namespaces}.items())


def schema_ref(taxonomy: Taxonomy) -> str:
    return f'<link:schemaRef xlink:type="simple" xlink:href={quoteattr(taxonomy.entry_point)}/>'


def contexts(lei: str, start: date, end: date) -> str:
    entity = f"<xbrli:entity><xbrli:identifier scheme={quoteattr(LEI_SCHEME)}>{escape(lei)}</xbrli:identifier></xbrli:entity>"
    # Duration concepts report the whole period, instant concepts the state at its end.
    # Each context is named after its period type, so a fact refers to it by its concept's period type.
    return (
        f'<xbrli:context id="duration">{entity}<xbrli:period><xbrli:startDate>{start.isoformat()}</xbrli:startDate>'
        f"<xbrli:endDate>{end.isoformat()}</xbrli:endDate></xbrli:period></xbrli:context>"
        f'<xbrli:context id="instant">{entity}<xbrli:period><xbrli:instant>{end.isoformat()}</xbrli:instant>'
        "</xbrli:period></xbrli:context>"
    )


def units(tags: list[SourceTag], concepts: dict[str, TaxonomyConcept]) -> str:
    measures = {tag.unit: _measure(tag.unit, concepts[tag.concept]) for tag in tags if tag.unit}
    return "".join(
        f'<xbrli:unit id="{unit}"><xbrli:measure>{measure}</xbrli:measure></xbrli:unit>' for unit, measure in measures.items()
    )


def fact_attributes(tag: SourceTag, concept: TaxonomyConcept) -> str:
    attributes = f'id="{FACT_ID}{tag.id}" contextRef="{concept.period_type}"'
    if tag.unit:
        attributes += f' unitRef="{tag.unit}" decimals="{tag.decimals}"'
    return attributes


def fact_value(tag: SourceTag, concept: TaxonomyConcept, namespaces: dict[str, str]) -> str:
    """The value to write, not escaped. Menu options get their namespace, such as https://...#OwnWorkforceMember."""
    return " ".join(_expanded(name, namespaces) for name in tag.value.split()) if concept.options else tag.value


def _measure(unit: str, concept: TaxonomyConcept) -> str:
    if unit == PURE:
        return "xbrli:pure"
    return f"iso4217:{unit}" if data_type(concept) == MONEY else f"utr:{unit}"


def _fact(tag: SourceTag, concept: TaxonomyConcept, namespaces: dict[str, str]) -> str:
    return f"<{concept.name} {fact_attributes(tag, concept)}>{escape(fact_value(tag, concept, namespaces))}</{concept.name}>"


def _expanded(name: str, namespaces: dict[str, str]) -> str:
    prefix, local_name = name.split(":", 1)
    return f"{namespaces[prefix]}#{local_name}"
