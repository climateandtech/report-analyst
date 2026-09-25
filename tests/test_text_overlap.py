"""Unit tests for ClimRetrieve/OSA text overlap matching."""

import json
from pathlib import Path

import pytest

from report_analyst.core.benchmark.text_overlap import (
    MatchRelation,
    best_overlap,
    classify_chunk_group_match,
    classify_text_match,
    find_ground_truth_window,
    is_ground_truth_hit,
    is_text_match,
    normalize_text,
    token_containment,
    token_jaccard,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ct_reit_chunk_matching.json"


@pytest.fixture(scope="module")
def ct_reit_fixture():
    return json.loads(FIXTURE_PATH.read_text())


def fixture_chunk(fixture, chunk_size: int, chunk_index: int) -> str:
    chunks = fixture["chunks"][str(chunk_size)]
    return next(chunk["text"] for chunk in chunks if chunk["document_chunk_index"] == chunk_index)


def test_normalize_text_collapses_whitespace_and_case():
    assert normalize_text("  Scope   1\nEmissions ") == "scope 1 emissions"


def test_token_jaccard_identical_texts_is_one():
    assert token_jaccard("Net-zero by 2050", "net zero by 2050") == 1.0


def test_token_jaccard_empty_is_zero():
    assert token_jaccard("", "climate") == 0.0


def test_containment_expert_span_inside_larger_chunk(ct_reit_fixture):
    relevant = ct_reit_fixture["ground_truth"]["text"]
    retrieved = fixture_chunk(ct_reit_fixture, 200, 77)

    assert token_containment(relevant, retrieved) == 1.0


def test_is_text_match_rejects_unrelated_chunks(ct_reit_fixture):
    retrieved = fixture_chunk(ct_reit_fixture, 200, 4)
    relevant = ct_reit_fixture["ground_truth"]["text"]

    assert not is_text_match(retrieved, relevant)


def test_is_text_match_rejects_partial_overlap_on_both_sides(ct_reit_fixture):
    retrieved = fixture_chunk(ct_reit_fixture, 200, 49)
    relevant = ct_reit_fixture["ground_truth"]["text"]

    assert not is_text_match(retrieved, relevant)


def test_ground_truth_containing_only_part_of_retrieved_is_not_a_hit(ct_reit_fixture):
    retrieved = fixture_chunk(ct_reit_fixture, 200, 77)
    ground_truth = fixture_chunk(ct_reit_fixture, 400, 45)

    assert not is_ground_truth_hit(classify_text_match(retrieved, ground_truth))


def test_best_overlap_returns_matching_candidate(ct_reit_fixture):
    retrieved = fixture_chunk(ct_reit_fixture, 200, 77)
    relevant = ct_reit_fixture["ground_truth"]["text"]
    match, score = best_overlap(
        retrieved,
        [
            fixture_chunk(ct_reit_fixture, 200, 4),
            relevant,
        ],
    )
    assert match == relevant
    assert score > 0


def test_real_climretrieve_text_is_an_exact_self_match(ct_reit_fixture):
    ground_truth = ct_reit_fixture["ground_truth"]["text"]

    assert classify_text_match(ground_truth, ground_truth).relation is MatchRelation.EXACT


def test_real_fixture_records_openai_embedding_mapping(ct_reit_fixture):
    assert ct_reit_fixture["generation"]["embedding_model"] == "text-embedding-ada-002"


def test_real_200_chunk_contains_climretrieve_text(ct_reit_fixture):
    retrieved = fixture_chunk(ct_reit_fixture, 200, 77)
    ground_truth = ct_reit_fixture["ground_truth"]["text"]

    assert classify_text_match(retrieved, ground_truth).relation is MatchRelation.RETRIEVED_CONTAINS_GROUND_TRUTH


def test_real_400_chunk_contains_200_chunk(ct_reit_fixture):
    retrieved = fixture_chunk(ct_reit_fixture, 400, 45)
    ground_truth = fixture_chunk(ct_reit_fixture, 200, 77)

    assert classify_text_match(retrieved, ground_truth).relation is MatchRelation.RETRIEVED_CONTAINS_GROUND_TRUTH


def test_real_200_chunk_is_contained_by_400_chunk(ct_reit_fixture):
    retrieved = fixture_chunk(ct_reit_fixture, 200, 77)
    ground_truth = fixture_chunk(ct_reit_fixture, 400, 45)

    assert classify_text_match(retrieved, ground_truth).relation is MatchRelation.GROUND_TRUTH_CONTAINS_RETRIEVED


def test_real_400_chunk_is_split_across_two_200_chunks(ct_reit_fixture):
    retrieved = [
        fixture_chunk(ct_reit_fixture, 200, 76),
        fixture_chunk(ct_reit_fixture, 200, 77),
    ]
    ground_truth = [fixture_chunk(ct_reit_fixture, 400, 45)]

    assert classify_chunk_group_match(retrieved, ground_truth).relation is MatchRelation.GROUND_TRUTH_SPLIT_ACROSS_RETRIEVED


def test_real_400_chunk_merges_two_200_chunks(ct_reit_fixture):
    retrieved = [fixture_chunk(ct_reit_fixture, 400, 45)]
    ground_truth = [
        fixture_chunk(ct_reit_fixture, 200, 76),
        fixture_chunk(ct_reit_fixture, 200, 77),
    ]

    assert classify_chunk_group_match(retrieved, ground_truth).relation is MatchRelation.RETRIEVED_MERGES_GROUND_TRUTH


def test_real_reversed_200_chunks_do_not_reconstruct_400_chunk(ct_reit_fixture):
    retrieved = [
        fixture_chunk(ct_reit_fixture, 200, 77),
        fixture_chunk(ct_reit_fixture, 200, 76),
    ]
    ground_truth = [fixture_chunk(ct_reit_fixture, 400, 45)]

    assert (
        classify_chunk_group_match(retrieved, ground_truth).relation is not MatchRelation.GROUND_TRUTH_SPLIT_ACROSS_RETRIEVED
    )


def test_real_matcher_finds_two_chunk_window_that_reconstructs_ground_truth(ct_reit_fixture):
    retrieved = [
        fixture_chunk(ct_reit_fixture, 200, 76),
        fixture_chunk(ct_reit_fixture, 200, 77),
    ]
    ground_truth = fixture_chunk(ct_reit_fixture, 400, 45)

    assert find_ground_truth_window(retrieved, ground_truth, max_chunks=2).chunk_indices == (0, 1)


def test_real_unrelated_chunk_is_not_a_match(ct_reit_fixture):
    retrieved = fixture_chunk(ct_reit_fixture, 200, 4)
    ground_truth = ct_reit_fixture["ground_truth"]["text"]

    assert classify_text_match(retrieved, ground_truth).relation is MatchRelation.NO_MATCH
