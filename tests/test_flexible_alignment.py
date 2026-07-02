"""Unit tests for flexible benchmark dataset alignment."""

import pandas as pd
import pytest

from report_analyst.core.benchmark.dataset_mapper import generate_chunk_id, generate_query_id
from report_analyst.core.benchmark.flexible_alignment import (
    BenchmarkAlignConfig,
    GroundTruthAlignConfig,
    align_benchmark_flexible,
    align_ground_truth_flexible,
)


class TestAlignGroundTruthFlexible:
    """Tests for align_ground_truth_flexible."""

    @pytest.fixture
    def raw_ground_truth(self):
        return pd.DataFrame(
            {
                "report": ["doc_a", "doc_a"],
                "question": ["What is scope 1?", "What is scope 1?"],
                "chunk": ["Scope 1 emissions data", "Governance overview"],
                "relevance": [2, 0],
            }
        )

    def test_aligns_required_columns_and_derives_ids(self, raw_ground_truth):
        config = GroundTruthAlignConfig(
            document_col="report",
            question_col="question",
            chunk_text_col="chunk",
            relevant_part_col=None,
            label_cols=["relevance"],
        )

        aligned = align_ground_truth_flexible(raw_ground_truth, config)

        assert list(aligned.columns) == [
            "query_id",
            "chunk_id",
            "relevant_part_id",
            "question",
            "document",
            "chunk_text",
            "relevant_part_text",
            "relevance",
            "score",
        ]
        assert aligned.loc[0, "query_id"] == generate_query_id("doc_a", "What is scope 1?")
        assert aligned.loc[0, "chunk_id"] == generate_chunk_id("Scope 1 emissions data")
        assert aligned.loc[0, "relevant_part_id"] == aligned.loc[0, "chunk_id"]
        assert aligned.loc[0, "score"] == 2.0

    def test_raises_when_label_column_missing(self, raw_ground_truth):
        config = GroundTruthAlignConfig(
            document_col="report",
            question_col="question",
            chunk_text_col="chunk",
            relevant_part_col=None,
            label_cols=["missing_label"],
        )

        with pytest.raises(ValueError, match="Label column 'missing_label'"):
            align_ground_truth_flexible(raw_ground_truth, config)


class TestAlignBenchmarkFlexible:
    """Tests for align_benchmark_flexible."""

    @pytest.fixture
    def raw_benchmark(self):
        return pd.DataFrame(
            {
                "query_id": ["q1", "q1"],
                "chunk_text": ["Alpha chunk", "Beta chunk"],
                "pred_relevance": [2, 1],
                "relevant_text_sim": [0.9, 0.4],
            }
        )

    def test_reuses_existing_query_id_and_deduplicates_ranking_column(self, raw_benchmark):
        config = BenchmarkAlignConfig(
            document_col=None,
            question_col=None,
            query_id_col="query_id",
            chunk_text_col="chunk_text",
            relevant_part_col=None,
            prediction_cols=["pred_relevance", "relevant_text_sim"],
            ranking_score_col="relevant_text_sim",
        )

        aligned = align_benchmark_flexible(raw_benchmark, config)

        assert aligned["query_id"].tolist() == ["q1", "q1"]
        assert aligned["chunk_id"].tolist() == [
            generate_chunk_id("Alpha chunk"),
            generate_chunk_id("Beta chunk"),
        ]
        assert "relevant_text_sim" in aligned.columns
        assert aligned.columns.tolist().count("relevant_text_sim") == 1

    def test_builds_query_id_from_question_when_missing_query_id_column(self):
        raw = pd.DataFrame(
            {
                "report": ["doc_a"],
                "question": ["What is scope 1?"],
                "chunk_text": ["Scope 1 emissions data"],
                "pred_relevance": [2],
            }
        )
        config = BenchmarkAlignConfig(
            document_col="report",
            question_col="question",
            query_id_col=None,
            chunk_text_col="chunk_text",
            relevant_part_col=None,
            prediction_cols=["pred_relevance"],
            ranking_score_col=None,
        )

        aligned = align_benchmark_flexible(raw, config)

        assert aligned.loc[0, "query_id"] == generate_query_id("doc_a", "What is scope 1?")

    def test_raises_when_neither_query_id_nor_question_provided(self, raw_benchmark):
        config = BenchmarkAlignConfig(
            document_col=None,
            question_col=None,
            query_id_col=None,
            chunk_text_col="chunk_text",
            relevant_part_col=None,
            prediction_cols=["pred_relevance"],
            ranking_score_col=None,
        )

        with pytest.raises(ValueError, match="Either an explicit query_id_col"):
            align_benchmark_flexible(raw_benchmark.drop(columns=["query_id"]), config)
