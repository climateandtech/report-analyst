"""Unit tests for benchmark dataset normalization helpers."""

import pandas as pd
import pytest

from report_analyst.core.benchmark.dataset_mapper import (
    generate_chunk_id,
    generate_query_id,
)
from report_analyst.core.benchmark.dataset_normalizer import (
    POSITION_MODE_ROW_ORDER,
    POSITION_MODE_SORT_BY_SCORE,
    make_chunk_id_from_text,
    make_query_id_from_columns,
    normalize_dataframe_for_benchmark,
)


class TestDatasetNormalizerHelpers:
    """Tests for small ID/score helper functions."""

    def test_make_query_id_from_columns_uses_document_when_present(self):
        query_id = make_query_id_from_columns("doc_a", "What is scope 1?")
        assert query_id == generate_query_id("doc_a", "What is scope 1?")

    def test_make_query_id_from_columns_falls_back_to_question_only(self):
        query_id = make_query_id_from_columns(None, "What is scope 1?")
        assert query_id == "What is scope 1?"

    def test_make_chunk_id_from_text_hashes_content(self):
        chunk_id = make_chunk_id_from_text("Scope 1 emissions data")
        assert chunk_id == generate_chunk_id("Scope 1 emissions data")


class TestNormalizeDataframeForBenchmark:
    """Tests for normalize_dataframe_for_benchmark."""

    @pytest.fixture
    def raw_df(self):
        return pd.DataFrame(
            {
                "description": ["q1", "q1", "q2"],
                "paragraph": ["chunk a", "chunk b", "chunk c"],
                "label": [2, "yes", "no"],
            }
        )

    def test_row_order_assigns_positions_per_query(self, raw_df):
        normalized = normalize_dataframe_for_benchmark(
            raw_df,
            query_column="description",
            chunk_text_column="paragraph",
            score_column="label",
            position_mode=POSITION_MODE_ROW_ORDER,
        )

        assert list(normalized.columns) == [
            "query_id",
            "chunk_id",
            "position",
            "score",
            "paragraph",
            "question",
        ]
        q1_rows = normalized[normalized["question"] == "q1"]
        assert q1_rows["position"].tolist() == [1, 2]
        assert q1_rows.iloc[0]["score"] == 2.0
        assert q1_rows.iloc[1]["score"] == 2.0

    def test_sort_by_score_orders_rows_within_query(self, raw_df):
        normalized = normalize_dataframe_for_benchmark(
            raw_df,
            query_column="description",
            chunk_text_column="paragraph",
            score_column="label",
            position_mode=POSITION_MODE_SORT_BY_SCORE,
        )

        q1_rows = normalized[normalized["question"] == "q1"]
        assert q1_rows.iloc[0]["paragraph"] == "chunk a"
        assert q1_rows.iloc[0]["position"] == 1
        assert q1_rows.iloc[1]["position"] == 2

    def test_document_column_builds_query_ids(self, raw_df):
        raw_with_doc = raw_df.assign(report=["doc_a", "doc_a", "doc_b"])
        normalized = normalize_dataframe_for_benchmark(
            raw_with_doc,
            query_column="description",
            chunk_text_column="paragraph",
            score_column="label",
            document_column="report",
            position_mode=POSITION_MODE_ROW_ORDER,
        )

        assert normalized.iloc[0]["query_id"] == generate_query_id("doc_a", "q1")
        assert normalized.iloc[2]["query_id"] == generate_query_id("doc_b", "q2")
        assert normalized.iloc[0]["chunk_id"] == generate_chunk_id("chunk a")

    def test_raises_when_required_column_missing(self, raw_df):
        with pytest.raises(ValueError, match="Query column 'missing'"):
            normalize_dataframe_for_benchmark(
                raw_df,
                query_column="missing",
                chunk_text_column="paragraph",
                score_column="label",
            )
