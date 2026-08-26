"""Text overlap helpers for matching OSA chunks to ClimRetrieve labels."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class MatchRelation(str, Enum):
    """Directional relationship between retrieved and ground-truth text."""

    EXACT = "exact"
    RETRIEVED_CONTAINS_GROUND_TRUTH = "retrieved_contains_ground_truth"
    GROUND_TRUTH_CONTAINS_RETRIEVED = "ground_truth_contains_retrieved"
    GROUND_TRUTH_SPLIT_ACROSS_RETRIEVED = "ground_truth_split_across_retrieved"
    RETRIEVED_MERGES_GROUND_TRUTH = "retrieved_merges_ground_truth"
    MANY_TO_MANY_OVERLAP = "many_to_many_overlap"
    PARTIAL_OVERLAP = "partial_overlap"
    NO_MATCH = "no_match"


@dataclass(frozen=True)
class TextMatch:
    """Scores and directional classification for a text or chunk-group match."""

    relation: MatchRelation
    jaccard: float
    retrieved_coverage: float
    ground_truth_coverage: float


@dataclass(frozen=True)
class ChunkWindowMatch:
    """A contiguous retrieved-chunk window that fully covers ground truth."""

    chunk_indices: tuple[int, ...]
    match: TextMatch


def normalize_text(value: str | None) -> str:
    """Lowercase, strip, and collapse whitespace."""
    if value is None:
        return ""
    return " ".join(str(value).lower().split())


def _tokens(value: str | None) -> list[str]:
    return _TOKEN_RE.findall(normalize_text(value))


def token_set(value: str | None) -> set[str]:
    """Alphanumeric tokens used for Jaccard / containment."""
    return set(_tokens(value))


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


def _contains_sequence(haystack: Sequence[str], needle: Sequence[str]) -> bool:
    if not needle or len(needle) > len(haystack):
        return False
    return any(haystack[index : index + len(needle)] == list(needle) for index in range(len(haystack) - len(needle) + 1))


def _merge_overlapping_token_sequences(chunks: Sequence[str]) -> list[str]:
    merged: list[str] = []
    for chunk in chunks:
        tokens = _tokens(chunk)
        overlap = 0
        for size in range(min(len(merged), len(tokens)), 0, -1):
            if merged[-size:] == tokens[:size]:
                overlap = size
                break
        merged.extend(tokens[overlap:])
    return merged


def classify_text_match(
    retrieved: str | None,
    ground_truth: str | None,
    *,
    jaccard_min: float = 0.25,
    containment_min: float = 0.6,
) -> TextMatch:
    """Classify exact, directional containment, partial overlap, or no match."""
    retrieved_tokens = _tokens(retrieved)
    ground_truth_tokens = _tokens(ground_truth)
    jaccard = token_jaccard(retrieved, ground_truth)
    retrieved_coverage = token_containment(retrieved, ground_truth)
    ground_truth_coverage = token_containment(ground_truth, retrieved)
    scores = (jaccard, retrieved_coverage, ground_truth_coverage)
    if not retrieved_tokens or not ground_truth_tokens:
        return TextMatch(MatchRelation.NO_MATCH, *scores)
    if retrieved_tokens == ground_truth_tokens:
        return TextMatch(MatchRelation.EXACT, *scores)
    if _contains_sequence(retrieved_tokens, ground_truth_tokens):
        return TextMatch(MatchRelation.RETRIEVED_CONTAINS_GROUND_TRUTH, *scores)
    if _contains_sequence(ground_truth_tokens, retrieved_tokens):
        return TextMatch(MatchRelation.GROUND_TRUTH_CONTAINS_RETRIEVED, *scores)
    if jaccard >= jaccard_min or max(retrieved_coverage, ground_truth_coverage) >= containment_min:
        return TextMatch(MatchRelation.PARTIAL_OVERLAP, *scores)
    return TextMatch(MatchRelation.NO_MATCH, *scores)


def classify_chunk_group_match(
    retrieved_chunks: Sequence[str],
    ground_truth_chunks: Sequence[str],
    *,
    coverage_min: float = 0.9,
) -> TextMatch:
    """Classify split, merged, or many-to-many chunk boundary differences."""
    if len(retrieved_chunks) == 1 and len(ground_truth_chunks) == 1:
        return classify_text_match(retrieved_chunks[0], ground_truth_chunks[0])
    retrieved_text = " ".join(_merge_overlapping_token_sequences(retrieved_chunks))
    ground_truth_text = " ".join(_merge_overlapping_token_sequences(ground_truth_chunks))
    base_match = classify_text_match(
        retrieved_text,
        ground_truth_text,
        containment_min=coverage_min,
    )
    covers_ground_truth = base_match.relation in {
        MatchRelation.EXACT,
        MatchRelation.RETRIEVED_CONTAINS_GROUND_TRUTH,
    }
    scores = (
        base_match.jaccard,
        base_match.retrieved_coverage,
        base_match.ground_truth_coverage,
    )
    if len(retrieved_chunks) > 1 and len(ground_truth_chunks) == 1 and covers_ground_truth:
        return TextMatch(MatchRelation.GROUND_TRUTH_SPLIT_ACROSS_RETRIEVED, *scores)
    if len(retrieved_chunks) == 1 and len(ground_truth_chunks) > 1 and covers_ground_truth:
        return TextMatch(MatchRelation.RETRIEVED_MERGES_GROUND_TRUTH, *scores)
    if len(retrieved_chunks) > 1 and len(ground_truth_chunks) > 1 and covers_ground_truth:
        return TextMatch(MatchRelation.MANY_TO_MANY_OVERLAP, *scores)
    return base_match


def is_ground_truth_hit(match: TextMatch) -> bool:
    """Whether retrieved text fully covers the ground truth in order."""
    return match.relation in {
        MatchRelation.EXACT,
        MatchRelation.RETRIEVED_CONTAINS_GROUND_TRUTH,
        MatchRelation.GROUND_TRUTH_SPLIT_ACROSS_RETRIEVED,
        MatchRelation.RETRIEVED_MERGES_GROUND_TRUTH,
        MatchRelation.MANY_TO_MANY_OVERLAP,
    }


def find_ground_truth_window(
    retrieved_chunks: Sequence[str],
    ground_truth: str,
    *,
    max_chunks: int = 2,
) -> ChunkWindowMatch | None:
    """Find the shortest contiguous retrieved window that fully covers ground truth."""
    for window_size in range(1, min(max_chunks, len(retrieved_chunks)) + 1):
        for start in range(len(retrieved_chunks) - window_size + 1):
            stop = start + window_size
            match = classify_chunk_group_match(retrieved_chunks[start:stop], [ground_truth])
            if is_ground_truth_hit(match):
                return ChunkWindowMatch(tuple(range(start, stop)), match)
    return None


def is_text_match(
    retrieved: str | None,
    relevant: str | None,
    *,
    jaccard_min: float = 0.25,
    containment_min: float = 0.6,
) -> bool:
    """True when retrieved text covers or overlaps an expert-relevant span."""
    match = classify_text_match(
        retrieved,
        relevant,
        jaccard_min=jaccard_min,
        containment_min=containment_min,
    )
    return match.relation in {
        MatchRelation.EXACT,
        MatchRelation.RETRIEVED_CONTAINS_GROUND_TRUTH,
        MatchRelation.GROUND_TRUTH_CONTAINS_RETRIEVED,
    }


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
