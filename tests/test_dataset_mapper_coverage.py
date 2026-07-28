"""Additional coverage for dataset mapper edge cases."""

import pandas as pd
import pytest

from report_analyst.core.benchmark.dataset_mapper import (
    DatasetMapperFactory,
    generate_chunk_id,
    generate_query_id,
    list_available_dataset_ids,
    transform_benchmark_results,
    transform_ground_truth,
)


def test_generate_query_id_strips_ends():
    assert generate_query_id("  Doc A ", " What? ") == "Doc A|||What?"


def test_generate_chunk_id_stable_and_empty():
    assert generate_chunk_id("hello") == generate_chunk_id("hello")
    assert generate_chunk_id("") != ""
    assert generate_chunk_id("x", prefix="p_").startswith("p_")


def test_transform_ground_truth_string_labels_and_missing_label():
    df = pd.DataFrame(
        {
            "Document": ["A", "A", "A"],
            "Question": ["Q", "Q", "Q"],
            "Relevant": ["r1", "r2", "r3"],
            "Label": ["yes", "maybe", "no"],
        }
    )
    out = transform_ground_truth(df, relevance_label_col="Label")
    assert set(out["score"].tolist()) == {2.0, 1.0, 0.0}

    df2 = pd.DataFrame({"document": ["A"], "question": ["Q"], "context": ["ctx only"]})
    out2 = transform_ground_truth(df2)
    assert out2.iloc[0]["score"] == 1.0


def test_transform_ground_truth_raises_without_required_columns():
    with pytest.raises(ValueError, match="document"):
        transform_ground_truth(pd.DataFrame({"question": ["Q"], "relevant": ["r"]}))
    with pytest.raises(ValueError, match="question"):
        transform_ground_truth(pd.DataFrame({"document": ["D"], "relevant": ["r"]}))
    with pytest.raises(ValueError, match="context or relevant"):
        transform_ground_truth(pd.DataFrame({"document": ["D"], "question": ["Q"]}))


def test_transform_benchmark_results_number_col_and_no_relevant_text():
    df = pd.DataFrame(
        {
            "report": ["R"],
            "question": ["Q"],
            "paragraph": ["para text"],
            "number": [0],
            "label": ["high"],
        }
    )
    out = transform_benchmark_results(df)
    assert out.iloc[0]["position"] == 1
    assert out.iloc[0]["relevant_part_id"] == out.iloc[0]["chunk_id"]
    assert out.iloc[0]["score"] == 2.0


def test_transform_benchmark_results_raises_without_paragraph():
    with pytest.raises(ValueError, match="paragraph"):
        transform_benchmark_results(pd.DataFrame({"report": ["R"], "question": ["Q"]}))


def test_factory_unknown_dataset_falls_back_to_default():
    mapper = DatasetMapperFactory.get_mapper("unknown_dataset_xyz")
    assert mapper.dataset_id == "unknown_dataset_xyz"
    ids = list_available_dataset_ids()
    assert isinstance(ids, list)
