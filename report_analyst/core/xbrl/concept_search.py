"""Search ESRS taxonomy concepts by words, standard and kind."""

import re

from report_analyst.models.taxonomy import ConceptKind, TaxonomyConcept

WORD = re.compile(r"\w[\w-]*")
# The reference parts a user may type. The Knowledge Hub link is left out, its words would match almost any query.
SEARCHED_REFERENCE_PARTS = ("section", "disclosure_requirement", "paragraph", "subparagraph", "clause", "datapoint_id")


def search_concepts(
    concepts: list[TaxonomyConcept],
    query: str = "",
    standard: str | None = None,
    kind: ConceptKind | None = None,
) -> list[TaxonomyConcept]:
    """Concepts that match every query word in the label, group or ESRS reference, in group order.

    A word matches the start of a word, so "emiss" finds "emissions". A number matches a whole number,
    so "scope 1" does not find paragraph 13.
    """
    query_words = _words(query)
    found = [
        concept
        for concept in concepts
        if (kind is None or concept.kind == kind)
        and (standard is None or standard in _standards_of(concept))
        and all(_matches(query_word, _searched_words(concept)) for query_word in query_words)
    ]
    return _in_group_order(found)


def _matches(query_word: str, words: set[str]) -> bool:
    if query_word.isdigit():
        return query_word in words
    return any(word.startswith(query_word) for word in words)


def standards(concepts: list[TaxonomyConcept]) -> list[str]:
    """The ESRS standards the concepts belong to, in group order."""
    return list(dict.fromkeys(section for concept in _in_group_order(concepts) for section in _standards_of(concept)))


def _in_group_order(concepts: list[TaxonomyConcept]) -> list[TaxonomyConcept]:
    # Group names start with their code, such as [210800], so sorting by name keeps the taxonomy's order.
    return sorted(concepts, key=lambda concept: (concept.group is None, concept.group or ""))


def _standards_of(concept: TaxonomyConcept) -> list[str]:
    return [reference.section for reference in concept.esrs_references if reference.section]


def _searched_words(concept: TaxonomyConcept) -> set[str]:
    parts = [concept.label, concept.group or ""]
    for reference in concept.esrs_references:
        parts.extend(getattr(reference, part) or "" for part in SEARCHED_REFERENCE_PARTS)
    return set(_words(" ".join(parts)))


def _words(text: str) -> list[str]:
    return WORD.findall(text.lower())
