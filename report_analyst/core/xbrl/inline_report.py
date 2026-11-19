"""Writes a report's tags as an iXBRL report, with each value marked in the passage it was taken from."""

import re
from decimal import Decimal
from typing import NamedTuple

from report_analyst.core.xbrl.esrs_taxonomy import PERCENT
from report_analyst.core.xbrl.tagging import data_type
from report_analyst.models.source_tag import SourceTag
from report_analyst.models.taxonomy import TaxonomyConcept

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
    for text, ixt_format in _forms(shown).items():
        # Only a number on its own counts, so 1,240 is not found in 11,240.
        found = re.search(rf"(?<![\d.,]){re.escape(text)}(?!\d|[.,]\d)", passage)
        if found:
            return Mark(found.start(), found.end(), ixt_format, scale)
    return None


def _forms(number: Decimal) -> dict[str, str]:
    """The ways a report can write the number, each with its format, such as "1.240": "ixt:num-comma-decimal"."""
    whole, _, fraction = format(number, "f").partition(".")
    grouped = f"{int(whole):,}"
    forms: dict[str, str] = {}
    for ixt_format, (separators, decimal_mark) in NUMBER_FORMATS.items():
        for separator in separators:
            # The first format keeps a form both can read, such as 1240.
            forms.setdefault(grouped.replace(",", separator) + (decimal_mark + fraction if fraction else ""), ixt_format)
    return forms
