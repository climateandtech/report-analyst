"""Writes a report's tags as an iXBRL report, with each value marked in the passage it was taken from."""

import re
from datetime import date
from decimal import Decimal
from typing import NamedTuple
from xml.sax.saxutils import escape

from report_analyst.core.xbrl.esrs_taxonomy import PERCENT
from report_analyst.core.xbrl.tagging import PURE, data_type
from report_analyst.core.xbrl.xbrl_report import (
    contexts,
    fact_attributes,
    fact_value,
    is_escaped,
    namespace_declarations,
    schema_ref,
    units,
)
from report_analyst.models.source_tag import SourceTag
from report_analyst.models.taxonomy import Taxonomy, TaxonomyConcept

XHTML = "http://www.w3.org/1999/xhtml"
IX = "http://www.xbrl.org/2013/inlineXBRL"
IXT = "http://www.xbrl.org/inlineXBRL/transformation/2022-02-16"
# How reports write numbers, by the iXBRL format that reads them: the thousands separators, then the decimal mark.
NUMBER_FORMATS = {
    "ixt:num-dot-decimal": (("", ",", " ", "\xa0"), "."),
    "ixt:num-comma-decimal": (("", ".", " ", "\xa0"), ","),
}


class Mark(NamedTuple):
    """Where a tag's value is in its passage, and how iXBRL reads it from there."""

    start: int
    end: int
    format: str | None = None
    scale: int | None = None


def inline_report(
    tags: list[SourceTag], sources: list[dict], taxonomy: Taxonomy, lei: str, start: date, end: date
) -> tuple[str, list[str]]:
    """An iXBRL report of the tagged passages, and the ids of the tags written below their passage.

    Every tag must use a concept of the taxonomy.
    """
    concepts = {concept.name: concept for concept in taxonomy.concepts}
    paragraphs, written_below = [], []
    for source in sorted(sources, key=lambda source: (source["page"], source["span_start"])):
        source_tags = [tag for tag in tags if tag.source_id == source["id"]]
        if not source_tags:
            continue
        passage = source["selected_text"]
        in_passage, lines_below = [], []
        for tag in source_tags:
            concept = concepts[tag.concept]
            mark = find_mark(tag, concept, passage)
            if mark and all(_fits(mark, concept, other, other_concept) for other, _, other_concept in in_passage):
                in_passage.append((mark, tag, concept))
            else:
                written_below.append(tag.id)
                lines_below.append(_line_below(tag, concept, taxonomy.namespaces))
        paragraphs.append(f"<p>{_passage_with_facts(passage, in_passage)}</p>" + "".join(lines_below))
    report = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<html xmlns="{XHTML}" xmlns:ix="{IX}" xmlns:ixt="{IXT}" {namespace_declarations(taxonomy)}>'
        "<head><title>Tagged facts</title></head><body>"
        # The taxonomy, contexts and units go in a header that is not shown.
        f'<div style="display:none"><ix:header><ix:references>{schema_ref(taxonomy)}</ix:references>'
        f"<ix:resources>{contexts(lei, start, end)}{units(tags, concepts)}</ix:resources></ix:header></div>"
        + "".join(paragraphs)
        + "</body></html>"
    )
    return report, written_below


def find_mark(tag: SourceTag, concept: TaxonomyConcept, passage: str) -> Mark | None:
    """Where the tag's value is in the passage, or None when the passage does not show it."""
    if concept.kind == "yes/no":
        return Mark(0, len(passage), "ixt:fixed-true" if tag.value == "true" else "ixt:fixed-false")
    if concept.kind == "menu":
        # A menu's value is the option's web address, which no report shows.
        return None
    if concept.kind == "number":
        return _find_number(tag, concept, passage)
    start = passage.find(tag.value)
    return Mark(start, start + len(tag.value)) if start >= 0 else None


def _find_number(tag: SourceTag, concept: TaxonomyConcept, passage: str) -> Mark | None:
    number = abs(Decimal(tag.value))
    # A percent is stored as 0.25 but shown as 25 %.
    scale = -2 if data_type(concept) == PERCENT else None
    shown = number.scaleb(2) if scale else number
    for text, ixt_format in _number_forms(shown).items():
        # Only a number on its own counts, so 1,240 is not found in 11,240.
        found = re.search(rf"(?<![\d.,]){re.escape(text)}(?!\d|[.,]\d)", passage)
        if found:
            return Mark(found.start(), found.end(), ixt_format, scale)
    return None


def _number_forms(number: Decimal) -> dict[str, str]:
    """The ways a report can write the number, each with its format, such as "1.240": "ixt:num-comma-decimal"."""
    whole, _, fraction = format(number, "f").partition(".")
    grouped = f"{int(whole):,}"
    forms: dict[str, str] = {}
    for ixt_format, (separators, decimal_mark) in NUMBER_FORMATS.items():
        for separator in separators:
            # The first format keeps a form both can read, such as 1240.
            forms.setdefault(grouped.replace(",", separator) + (decimal_mark + fraction if fraction else ""), ixt_format)
    return forms


def _fits(mark: Mark, concept: TaxonomyConcept, other: Mark, other_concept: TaxonomyConcept) -> bool:
    """Marks fit when they don't overlap, or when one is a text fact around the other."""
    if mark.end <= other.start or other.end <= mark.start:
        return True
    return (_around(other, mark) and other_concept.kind != "number") or (_around(mark, other) and concept.kind != "number")


def _around(outer: Mark, inner: Mark) -> bool:
    """Whether the outer mark covers the inner one and more."""
    return outer.start <= inner.start and inner.end <= outer.end and (outer.start, outer.end) != (inner.start, inner.end)


def _passage_with_facts(passage: str, facts: list[tuple[Mark, SourceTag, TaxonomyConcept]]) -> str:
    """The passage, escaped, with each fact's element around its mark."""
    # Each opening and closing goes where its mark starts or ends. Where several meet at one place,
    # closings go first, and a longer fact opens before and closes after a shorter one inside it.
    CLOSING, OPENING = 0, 1
    insertions = []
    for mark, tag, concept in facts:
        opening, closing = _fact_element(tag, concept, mark)
        insertions += [(mark.start, OPENING, -mark.end, opening), (mark.end, CLOSING, -mark.start, closing)]
    parts, position = [], 0
    for place, _, _, element in sorted(insertions):
        parts += [escape(passage[position:place]), element]
        position = place
    return "".join(parts) + escape(passage[position:])


def _line_below(tag: SourceTag, concept: TaxonomyConcept, namespaces: dict[str, str]) -> str:
    """The tag on its own line below the passage, such as "Gross scope 1 GHG emissions: 1240 tCO2e"."""
    opening, closing = _fact_element(tag, concept)
    value = tag.value.lstrip("-") if concept.kind == "number" else fact_value(tag, concept, namespaces)
    unit = f" {tag.unit}" if tag.unit and tag.unit != PURE else ""
    return f"<p>{escape(concept.label)}: {opening}{escape(value)}{closing}{escape(unit)}</p>"


def _fact_element(tag: SourceTag, concept: TaxonomyConcept, mark: Mark | None = None) -> tuple[str, str]:
    """The opening and closing of the tag's iXBRL element, such as <ix:nonFraction ...> and </ix:nonFraction>."""
    name = "ix:nonFraction" if concept.kind == "number" else "ix:nonNumeric"
    attributes = f'name="{concept.name}" {fact_attributes(tag, concept)}'
    if mark and mark.format:
        attributes += f' format="{mark.format}"'
    if mark and mark.scale:
        attributes += f' scale="{mark.scale}"'
    if concept.kind == "number" and tag.value.startswith("-"):
        # iXBRL writes a number without its minus sign and marks it as negative.
        attributes += ' sign="-"'
    if is_escaped(tag, concept):
        attributes += ' escape="true"'
    return f"<{name} {attributes}>", f"</{name}>"
