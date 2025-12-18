import pytest
from app.core.benchmark.evaluation_engine import EvaluationEngine
from app.core.benchmark.retrieval_results_loader import load_flexible_dataset_from_csv
from app.models.benchmark import BenchmarkDataset, FlexibleDatasetRow, DatasetType


class TestFlexibleDatasetEvaluation:
    """Test suite for evaluating flexible datasets"""
    
    @pytest.fixture
    def engine(self):
        return EvaluationEngine()
    
    def test_compare_ir_datasets_basic(self, engine):
        """Test comparing two IR datasets with matching chunks"""
        reference_csv = """query_id,chunk_id,position,score
tcfd_1,chunk_001,1,1.0
tcfd_1,chunk_015,2,0.9
tcfd_2,chunk_023,1,1.0"""
        
        input_csv = """query_id,chunk_id,position,score
tcfd_1,chunk_001,1,0.95
tcfd_1,chunk_015,2,0.89
tcfd_2,chunk_023,1,0.93"""
        
        reference = load_flexible_dataset_from_csv(csv_content=reference_csv)
        input_dataset = load_flexible_dataset_from_csv(csv_content=input_csv)
        
        metrics = engine.compare_flexible_datasets(reference, input_dataset)
        
        assert metrics is not None
        assert 1 in metrics.precision_at_k
        assert metrics.precision_at_k[1] > 0
    
    def test_compare_ir_datasets_partial_match(self, engine):
        """Test comparing IR datasets with partial chunk matches"""
        reference_csv = """query_id,chunk_id,position,score
tcfd_1,chunk_001,1,1.0
tcfd_1,chunk_015,2,0.9
tcfd_1,chunk_042,3,0.8"""
        
        input_csv = """query_id,chunk_id,position,score
tcfd_1,chunk_001,1,0.95
tcfd_1,chunk_999,2,0.89
tcfd_1,chunk_015,3,0.87"""
        
        reference = load_flexible_dataset_from_csv(csv_content=reference_csv)
        input_dataset = load_flexible_dataset_from_csv(csv_content=input_csv)
        
        metrics = engine.compare_flexible_datasets(reference, input_dataset, k_values=[1, 2, 3])
        
        assert metrics.precision_at_k[1] == 1.0
        assert metrics.precision_at_k[2] < 1.0
        assert metrics.precision_at_k[3] < 1.0
    
    def test_compare_ir_datasets_no_common_queries(self, engine):
        """Test comparing datasets with no common queries"""
        reference_csv = """query_id,chunk_id,position,score
tcfd_1,chunk_001,1,1.0"""
        
        input_csv = """query_id,chunk_id,position,score
tcfd_99,chunk_001,1,0.95"""
        
        reference = load_flexible_dataset_from_csv(csv_content=reference_csv)
        input_dataset = load_flexible_dataset_from_csv(csv_content=input_csv)
        
        metrics = engine.compare_flexible_datasets(reference, input_dataset)
        
        assert metrics.mean_average_precision == 0.0
        assert metrics.mean_reciprocal_rank == 0.0
    
    def test_compare_ie_datasets_exact_match(self, engine):
        """Test comparing IE datasets with exact answer matches"""
        reference_csv = """question_id,answer,category
tcfd_1,"The company identifies climate risks","risk_identification"
tcfd_2,"Strategy includes climate considerations","strategy" """
        
        input_csv = """question_id,answer,category
tcfd_1,"The company identifies climate risks","risk_identification"
tcfd_2,"Strategy includes climate considerations","strategy" """
        
        reference = load_flexible_dataset_from_csv(csv_content=reference_csv)
        input_dataset = load_flexible_dataset_from_csv(csv_content=input_csv)
        
        metrics = engine.compare_flexible_datasets(reference, input_dataset)
        
        assert metrics.precision_at_k[1] == 1.0
        assert metrics.mean_average_precision == 1.0
    
    def test_compare_ie_datasets_partial_match(self, engine):
        """Test comparing IE datasets with partial matches"""
        reference_csv = """question_id,answer
tcfd_1,"The company identifies climate risks"
tcfd_2,"Strategy includes climate considerations" """
        
        input_csv = """question_id,answer
tcfd_1,"The company identifies climate risks"
tcfd_2,"Different answer here" """
        
        reference = load_flexible_dataset_from_csv(csv_content=reference_csv)
        input_dataset = load_flexible_dataset_from_csv(csv_content=input_csv)
        
        metrics = engine.compare_flexible_datasets(reference, input_dataset)
        
        assert metrics.precision_at_k[1] == 0.5
        assert metrics.mean_average_precision == 0.5
    
    def test_compare_datasets_with_variant_column_names(self, engine):
        """Test comparing datasets with different column name variations"""
        reference_csv = """query_id,chunk_id,position,relevance_score
tcfd_1,chunk_001,1,1.0
tcfd_1,chunk_015,2,0.9"""
        
        input_csv = """question_id,chunk,rank,score
tcfd_1,chunk_001,1,0.95
tcfd_1,chunk_015,2,0.89"""
        
        reference = load_flexible_dataset_from_csv(csv_content=reference_csv)
        input_dataset = load_flexible_dataset_from_csv(csv_content=input_csv)
        
        metrics = engine.compare_flexible_datasets(reference, input_dataset)
        
        assert metrics is not None
        assert len(reference.get_unique_queries()) == 1
        assert len(input_dataset.get_unique_queries()) == 1
    
    def test_compare_datasets_different_types_warning(self, engine):
        """Test that comparing different dataset types shows warning but still works"""
        reference_csv = """query_id,chunk_id,position,score
tcfd_1,chunk_001,1,1.0"""
        
        input_csv = """question_id,answer
tcfd_1,"Some answer" """
        
        reference = load_flexible_dataset_from_csv(csv_content=reference_csv)
        input_dataset = load_flexible_dataset_from_csv(csv_content=input_csv)
        
        # Should not raise, but may show warning
        metrics = engine.compare_flexible_datasets(reference, input_dataset)
        assert metrics is not None
