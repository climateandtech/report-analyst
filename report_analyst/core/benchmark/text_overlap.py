"""Text overlap helpers for matching OSA chunks to ClimRetrieve labels."""

from __future__ import annotations

import re
from typing import Iterable

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize_text(value: str | None) -> str:
    """Lowercase, strip, and collapse whitespace."""
    if value is None:
        return ""
    return " ".join(str(value).lower().split())


def token_set(value: str | None) -> set[str]:
    """Alphanumeric tokens used for Jaccard / containment."""
    return set(_TOKEN_RE.findall(normalize_text(value)))


def token_jaccard(left: str | None, right: str | None) -> float:
    """Jaccard similarity of token sets. Empty inputs score 0."""
    left_tokens = token_set(left)
    right_tokens = token_set(right)
    if not left_tokens or not right_tokens:
        return 0.0
    union = left_tokens | right_tokens
    return len(left_tokens & right_tokens) / len(union)


def token_containment(needle: str | None, haystack: str | None) -> float:
    """Fraction of needle tokens found in haystack. Empty needle scores 0."""
    needle_tokens = token_set(needle)
    if not needle_tokens:
        return 0.0
    haystack_tokens = token_set(haystack)
    return len(needle_tokens & haystack_tokens) / len(needle_tokens)


def is_text_match(
    retrieved: str | None,
    relevant: str | None,
    *,
    jaccard_min: float = 0.25,
    containment_min: float = 0.6,
) -> bool:
    """True when retrieved text covers or overlaps an expert-relevant span."""
    if not normalize_text(retrieved) or not normalize_text(relevant):
        return False
    if token_jaccard(retrieved, relevant) >= jaccard_min:
        return True
    return token_containment(relevant, retrieved) >= containment_min


def best_overlap(
    retrieved: str | None,
    candidates: Iterable[str],
    *,
    jaccard_min: float = 0.25,
    containment_min: float = 0.6,
) -> tuple[str | None, float]:
    """Return the best-matching candidate text and its Jaccard score."""
    best_text: str | None = None
    best_score = 0.0
    for candidate in candidates:
        score = token_jaccard(retrieved, candidate)
        contained = token_containment(candidate, retrieved)
        if score > best_score:
            best_score = score
            best_text = candidate
        if is_text_match(
            retrieved,
            candidate,
            jaccard_min=jaccard_min,
            containment_min=containment_min,
        ) and contained > best_score:
            best_score = max(best_score, contained)
            best_text = candidate
    if best_text is None:
        return None, 0.0
    if not is_text_match(
        retrieved,
        best_text,
        jaccard_min=jaccard_min,
        containment_min=containment_min,
    ):
        return None, best_score
    return best_text, best_score
