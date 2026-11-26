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
    "xbrldi": "http://xbrl.org/2006/xbrldi",
}


def xbrl_report(tags: list[SourceTag], taxonomy: Taxonomy, lei: str, start: date, end: date) -> str:
    """An XBRL report with one fact per tag. Every tag must use a concept of the taxonomy."""
    concepts = {concept.name: concept for concept in taxonomy.concepts}
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n<xbrli:xbrl {namespace_declarations(taxonomy)}>'
        f"{schema_ref(taxonomy)}{contexts(tags, concepts, lei, start, end)}{units(tags, concepts)}"
        + "".join(_fact(tag, concepts[tag.concept], taxonomy.namespaces) for tag in tags)
        + "</xbrli:xbrl>"
    )


def namespace_declarations(taxonomy: Taxonomy) -> str:
    return " ".join(f"xmlns:{prefix}={quoteattr(uri)}" for prefix, uri in {**NAMESPACES, **taxonomy.namespaces}.items())


def schema_ref(taxonomy: Taxonomy) -> str:
    return f'<link:schemaRef xlink:type="simple" xlink:href={quoteattr(taxonomy.entry_point)}/>'


def contexts(tags: list[SourceTag], concepts: dict[str, TaxonomyConcept], lei: str, start: date, end: date) -> str:
    entity = f"<xbrli:entity><xbrli:identifier scheme={quoteattr(LEI_SCHEME)}>{escape(lei)}</xbrli:identifier></xbrli:entity>"
    # Duration concepts report the whole period, instant concepts the state at its end.
    periods = {
        "duration": f"<xbrli:startDate>{start.isoformat()}</xbrli:startDate><xbrli:endDate>{end.isoformat()}</xbrli:endDate>",
        "instant": f"<xbrli:instant>{end.isoformat()}</xbrli:instant>",
    }
    # Each context is named after its period type, so a fact refers to it by its concept's period type.
    written = "".join(_context(period_type, entity, period) for period_type, period in periods.items())
    for tag in tags:
        concept = concepts[tag.concept]
        if concept.identifier and tag.identifier:
            element = concept.identifier.element
            scenario = (
                f'<xbrli:scenario><xbrldi:typedMember dimension="{concept.identifier.dimension}">'
                f"<{element}>{escape(tag.identifier)}</{element}></xbrldi:typedMember></xbrli:scenario>"
            )
            written += _context(_context_id(tag, concept), entity, periods[concept.period_type], scenario)
    return written


def units(tags: list[SourceTag], concepts: dict[str, TaxonomyConcept]) -> str:
    measures = {tag.unit: _measure(tag.unit, concepts[tag.concept]) for tag in tags if tag.unit}
    return "".join(
        f'<xbrli:unit id="{unit}"><xbrli:measure>{measure}</xbrli:measure></xbrli:unit>' for unit, measure in measures.items()
    )


def fact_attributes(tag: SourceTag, concept: TaxonomyConcept) -> str:
    attributes = f'id="{FACT_ID}{tag.id}" contextRef="{_context_id(tag, concept)}"'
    if tag.unit:
        attributes += f' unitRef="{tag.unit}" decimals="{tag.decimals}"'
    return attributes


def fact_value(tag: SourceTag, concept: TaxonomyConcept, namespaces: dict[str, str]) -> str:
    """The value to write, not escaped. Menu options get their namespace, such as https://...#OwnWorkforceMember."""
    return " ".join(_expanded(name, namespaces) for name in tag.value.split()) if concept.options else tag.value


def _context_id(tag: SourceTag, concept: TaxonomyConcept) -> str:
    """A tag with the identifier its concept needs has its own context, which holds the identifier."""
    if concept.identifier and tag.identifier:
        return f"{concept.period_type}-{tag.id}"
    return concept.period_type


def _context(context_id: str, entity: str, period: str, scenario: str = "") -> str:
    return f'<xbrli:context id="{context_id}">{entity}<xbrli:period>{period}</xbrli:period>{scenario}</xbrli:context>'


def _measure(unit: str, concept: TaxonomyConcept) -> str:
    if unit == PURE:
        return "xbrli:pure"
    return f"iso4217:{unit}" if data_type(concept) == MONEY else f"utr:{unit}"


def _fact(tag: SourceTag, concept: TaxonomyConcept, namespaces: dict[str, str]) -> str:
    return f"<{concept.name} {fact_attributes(tag, concept)}>{escape(fact_value(tag, concept, namespaces))}</{concept.name}>"


def _expanded(name: str, namespaces: dict[str, str]) -> str:
    prefix, local_name = name.split(":", 1)
    return f"{namespaces[prefix]}#{local_name}"
