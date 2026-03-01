from unittest.mock import Mock

import numpy as np
import pytest

from report_analyst.core.benchmark.evaluation_engine import EvaluationEngine
from report_analyst.models.benchmark import (
    BenchmarkDatasetContent,
    BenchmarkQuestion,
    EvaluationMetrics,
    GroundTruthChunk,
    RetrievalConfig,
)


class TestEvaluationEngine:
    """Test suite for evaluation engine metrics calculation"""

    @pytest.fixture
    def engine(self):
        return EvaluationEngine()

    @pytest.fixture
    def sample_dataset(self):
        """Create a sample dataset for testing"""
        chunks_q1 = [
            GroundTruthChunk(
                chunk_id="chunk_1",
                relevance_score=1.0,
                is_evidence=True,
                evidence_order=1,
            ),
            GroundTruthChunk(
                chunk_id="chunk_2",
                relevance_score=0.8,
                is_evidence=True,
                evidence_order=2,
            ),
            GroundTruthChunk(
                chunk_id="chunk_3", relevance_score=0.0, is_evidence=False
            ),
        ]

        chunks_q2 = [
            GroundTruthChunk(
                chunk_id="chunk_4",
                relevance_score=0.9,
                is_evidence=True,
                evidence_order=1,
            ),
            GroundTruthChunk(
                chunk_id="chunk_5", relevance_score=0.0, is_evidence=False
            ),
        ]

        questions = [
            BenchmarkQuestion(
                question_id="q1",
                question_text="Question 1",
                ground_truth_chunks=chunks_q1,
            ),
            BenchmarkQuestion(
                question_id="q2",
                question_text="Question 2",
                ground_truth_chunks=chunks_q2,
            ),
        ]

        return BenchmarkDatasetContent(
            dataset_id="test_dataset",
            name="Test Dataset",
            description="Test",
            version="1.0",
            question_set="tcfd",
            created_at="2024-01-01",
            questions=questions,
        )

    @pytest.fixture
    def sample_retrieval_results(self):
        """Sample retrieval results for testing"""
        return {
            "q1": [
                {"id": "chunk_1", "score": 0.95},  # Relevant, rank 1
                {"id": "chunk_3", "score": 0.85},  # Not relevant, rank 2
                {"id": "chunk_2", "score": 0.75},  # Relevant, rank 3
                {"id": "chunk_unknown", "score": 0.65},  # Unknown chunk, rank 4
            ],
            "q2": [
                {"id": "chunk_5", "score": 0.90},  # Not relevant, rank 1
                {"id": "chunk_4", "score": 0.80},  # Relevant, rank 2
            ],
        }

    def test_precision_at_k(self, engine):
        """Test precision@K calculation"""
        binary_relevance = [1, 0, 1, 0, 1]  # 3 relevant out of 5

        assert engine._precision_at_k(binary_relevance, 1) == 1.0  # 1/1
        assert engine._precision_at_k(binary_relevance, 2) == 0.5  # 1/2
        assert engine._precision_at_k(binary_relevance, 3) == 2 / 3  # 2/3
        assert engine._precision_at_k(binary_relevance, 5) == 0.6  # 3/5
        assert engine._precision_at_k(binary_relevance, 0) == 0.0  # Edge case

    def test_recall_at_k(self, engine):
        """Test recall@K calculation"""
        binary_relevance = [1, 0, 1, 0, 1]  # 3 relevant out of 5
        total_relevant = 4  # Assume 4 total relevant chunks exist

        assert engine._recall_at_k(binary_relevance, total_relevant, 1) == 0.25  # 1/4
        assert engine._recall_at_k(binary_relevance, total_relevant, 3) == 0.5  # 2/4
        assert engine._recall_at_k(binary_relevance, total_relevant, 5) == 0.75  # 3/4
        assert engine._recall_at_k(binary_relevance, 0, 5) == 0.0  # No relevant chunks

    def test_f1_at_k(self, engine):
        """Test F1@K calculation"""
        assert engine._f1_at_k(1.0, 1.0) == 1.0  # Perfect
        assert engine._f1_at_k(0.5, 0.5) == 0.5  # Equal precision and recall
        assert engine._f1_at_k(0.0, 0.0) == 0.0  # No relevant results

        # Test harmonic mean calculation
        precision, recall = 0.8, 0.6
        expected_f1 = 2 * (precision * recall) / (precision + recall)
        assert abs(engine._f1_at_k(precision, recall) - expected_f1) < 1e-10

    def test_reciprocal_rank(self, engine):
        """Test reciprocal rank calculation"""
        assert engine._reciprocal_rank([1, 0, 0, 0]) == 1.0  # First position
        assert engine._reciprocal_rank([0, 1, 0, 0]) == 0.5  # Second position
        assert engine._reciprocal_rank([0, 0, 1, 0]) == 1 / 3  # Third position
        assert engine._reciprocal_rank([0, 0, 0, 0]) == 0.0  # No relevant results

    def test_average_precision(self, engine):
        """Test average precision calculation"""
        # Perfect ranking: all relevant first
        binary_relevance = [1, 1, 1, 0, 0]
        ap = engine._average_precision(binary_relevance)
        expected = (1.0 + 1.0 + 1.0) / 3  # (1/1 + 2/2 + 3/3) / 3
        assert abs(ap - expected) < 1e-10

        # Mixed ranking
        binary_relevance = [1, 0, 1, 0, 1]
        ap = engine._average_precision(binary_relevance)
        expected = (1.0 + 2 / 3 + 3 / 5) / 3  # (1/1 + 2/3 + 3/5) / 3
        assert abs(ap - expected) < 1e-10

        # No relevant documents
        assert engine._average_precision([0, 0, 0, 0]) == 0.0

    def test_ndcg_at_k(self, engine):
        """Test NDCG@K calculation"""
        retrieved_relevance = [1.0, 0.8, 0.0, 0.6]
        ground_truth = {"chunk_1": 1.0, "chunk_2": 0.8, "chunk_3": 0.6, "chunk_4": 0.0}

        # Test NDCG@1
        ndcg_1 = engine._ndcg_at_k(retrieved_relevance, ground_truth, 1)
        assert ndcg_1 == 1.0  # Perfect first result

        # Test NDCG@3
        ndcg_3 = engine._ndcg_at_k(retrieved_relevance, ground_truth, 3)

        # Calculate expected DCG@3
        dcg = 1.0 + 0.8 / np.log2(2) + 0.0 / np.log2(3)

        # Calculate expected IDCG@3 (ideal ranking: [1.0, 0.8, 0.6])
        idcg = 1.0 + 0.8 / np.log2(2) + 0.6 / np.log2(3)

        expected_ndcg = dcg / idcg
        assert abs(ndcg_3 - expected_ndcg) < 1e-10

    def test_evaluate_single_question(self, engine):
        """Test evaluation of a single question"""
        retrieved_chunks = [
            {"id": "chunk_1", "score": 0.9},
            {"id": "chunk_2", "score": 0.8},
            {"id": "chunk_3", "score": 0.7},
        ]

        ground_truth = {
            "chunk_1": 1.0,  # Relevant
            "chunk_2": 0.0,  # Not relevant
            "chunk_3": 0.8,  # Relevant
        }

        result = engine._evaluate_single_question(
            retrieved_chunks, ground_truth, [1, 2, 3]
        )

        # Check binary relevance
        expected_binary = [
            1,
            0,
            1,
        ]  # chunk_1: relevant, chunk_2: not relevant, chunk_3: relevant
        assert result["binary_relevance"] == expected_binary

        # Check precision@K
        assert result["precision_at_k"][1] == 1.0  # 1/1
        assert result["precision_at_k"][2] == 0.5  # 1/2
        assert result["precision_at_k"][3] == 2 / 3  # 2/3

        # Check reciprocal rank (first relevant at position 1)
        assert result["reciprocal_rank"] == 1.0

    def test_evaluate_retrieval_full(
        self, engine, sample_dataset, sample_retrieval_results
    ):
        """Test full retrieval evaluation"""
        config = RetrievalConfig(top_k=5)

        metrics = engine.evaluate_retrieval(
            sample_dataset, sample_retrieval_results, config, k_values=[1, 2, 3]
        )

        # Verify metrics structure
        assert isinstance(metrics, EvaluationMetrics)
        assert 1 in metrics.precision_at_k
        assert 2 in metrics.precision_at_k
        assert 3 in metrics.precision_at_k

        # Verify metrics are reasonable (between 0 and 1)
        assert 0 <= metrics.mean_average_precision <= 1
        assert 0 <= metrics.mean_reciprocal_rank <= 1

        for k in [1, 2, 3]:
            assert 0 <= metrics.precision_at_k[k] <= 1
            assert 0 <= metrics.recall_at_k[k] <= 1
            assert 0 <= metrics.f1_at_k[k] <= 1
            assert 0 <= metrics.ndcg_at_k[k] <= 1

    def test_evaluate_retrieval_missing_results(self, engine, sample_dataset):
        """Test evaluation with missing retrieval results"""
        incomplete_results = {
            "q1": [{"id": "chunk_1", "score": 0.9}]
            # Missing q2 results
        }

        config = RetrievalConfig(top_k=5)

        # Should not crash, should handle missing results gracefully
        metrics = engine.evaluate_retrieval(sample_dataset, incomplete_results, config)

        # Should still return valid metrics structure
        assert isinstance(metrics, EvaluationMetrics)

    def test_compare_evaluations(self, engine):
        """Test evaluation comparison"""
        eval1 = EvaluationMetrics(
            precision_at_k={5: 0.6},
            recall_at_k={5: 0.5},
            f1_at_k={5: 0.55},
            mean_reciprocal_rank=0.7,
            mean_average_precision=0.6,
            ndcg_at_k={5: 0.65},
        )

        eval2 = EvaluationMetrics(
            precision_at_k={5: 0.8},
            recall_at_k={5: 0.7},
            f1_at_k={5: 0.75},
            mean_reciprocal_rank=0.9,
            mean_average_precision=0.8,
            ndcg_at_k={5: 0.85},
        )

        comparison = engine.compare_evaluations(eval1, eval2)

        # Check improvements (with floating point tolerance)
        assert abs(comparison["map_improvement"] - 0.2) < 1e-10
        assert abs(comparison["mrr_improvement"] - 0.2) < 1e-10
        assert abs(comparison["precision_at_5_improvement"] - 0.2) < 1e-10
        assert abs(comparison["recall_at_5_improvement"] - 0.2) < 1e-10
        assert abs(comparison["f1_at_5_improvement"] - 0.2) < 1e-10
        assert abs(comparison["ndcg_at_5_improvement"] - 0.2) < 1e-10

    def test_empty_evaluation(self, engine):
        """Test evaluation with empty dataset"""
        empty_dataset = BenchmarkDatasetContent(
            dataset_id="empty",
            name="Empty Dataset",
            description="Empty",
            version="1.0",
            question_set="tcfd",
            created_at="2024-01-01",
            questions=[],
        )

        metrics = engine.evaluate_retrieval(empty_dataset, {}, RetrievalConfig())

        # Should return empty metrics
        assert isinstance(metrics, EvaluationMetrics)
        assert metrics.mean_average_precision == 0.0
        assert metrics.mean_reciprocal_rank == 0.0
