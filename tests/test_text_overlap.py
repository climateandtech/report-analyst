"""Unit tests for ClimRetrieve/OSA text overlap matching."""

from report_analyst.core.benchmark.text_overlap import (
    best_overlap,
    is_text_match,
    normalize_text,
    token_containment,
    token_jaccard,
)


def test_normalize_text_collapses_whitespace_and_case():
    assert normalize_text("  Scope   1\nEmissions ") == "scope 1 emissions"


def test_token_jaccard_identical_texts_is_one():
    assert token_jaccard("Net-zero by 2050", "net zero by 2050") == 1.0


def test_token_jaccard_empty_is_zero():
    assert token_jaccard("", "climate") == 0.0


def test_containment_expert_span_inside_larger_chunk():
    relevant = "We aim to reach net-zero emissions by 2050."
    retrieved = "Climate strategy. We aim to reach net-zero emissions by 2050. Further details follow."
    assert token_containment(relevant, retrieved) == 1.0
    assert is_text_match(retrieved, relevant)


def test_is_text_match_rejects_unrelated_chunks():
    assert not is_text_match(
        "Employee volunteering hours increased this year.",
        "Board oversight of climate-related risks.",
    )


def test_best_overlap_returns_matching_candidate():
    retrieved = "The board oversees climate-related risks through the sustainability committee."
    match, score = best_overlap(
        retrieved,
        [
            "Water usage declined 4%.",
            "Board oversight of climate-related risks.",
        ],
    )
    assert match == "Board oversight of climate-related risks."
    assert score > 0
