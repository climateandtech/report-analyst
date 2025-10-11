import pytest
import tempfile
import sqlite3
import json
from pathlib import Path
from datetime import datetime

from app.core.storage.benchmark_store import BenchmarkStore
from app.models.benchmark import (
    BenchmarkDataset, 
    BenchmarkDatasetContent, 
    BenchmarkQuestion,
    GroundTruthChunk,
    BenchmarkEvaluation,
    RetrievalConfig,
    EvaluationMetrics,
    HumanAnnotation
)

class TestBenchmarkStore:
    """Test suite for benchmark data storage"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        # Initialize database schema
        store = BenchmarkStore(db_path)
        with sqlite3.connect(db_path) as conn:
            # Create the benchmark tables (simplified version for testing)
            conn.execute("""
                CREATE TABLE benchmark_datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT UNIQUE,
                    name TEXT,
                    description TEXT,
                    version TEXT,
                    question_set TEXT,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE ground_truth_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT,
                    question_id TEXT,
                    chunk_id TEXT,
                    relevance_score REAL,
                    is_evidence BOOLEAN,
                    evidence_order INTEGER,
                    annotation_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(dataset_id) REFERENCES benchmark_datasets(dataset_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE benchmark_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT,
                    evaluation_name TEXT,
                    config_hash TEXT,
                    retrieval_config TEXT,
                    evaluation_metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(dataset_id) REFERENCES benchmark_datasets(dataset_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE human_annotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evaluation_id INTEGER,
                    question_id TEXT,
                    chunk_id TEXT,
                    human_relevance_score REAL,
                    human_is_evidence BOOLEAN,
                    human_evidence_order INTEGER,
                    annotation_notes TEXT,
                    annotator_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(evaluation_id) REFERENCES benchmark_evaluations(id)
                )
            """)
            
            conn.commit()
        
        yield db_path
        
        # Cleanup
        try:
            Path(db_path).unlink()
        except:
            pass
    
    @pytest.fixture
    def store(self, temp_db):
        return BenchmarkStore(temp_db)
    
    @pytest.fixture
    def sample_dataset(self):
        """Create a sample dataset for testing"""
        chunks = [
            GroundTruthChunk(
                chunk_id="chunk_1",
                relevance_score=1.0,
                is_evidence=True,
                evidence_order=1,
                annotation_notes="High relevance chunk"
            ),
            GroundTruthChunk(
                chunk_id="chunk_2",
                relevance_score=0.8,
                is_evidence=True,
                evidence_order=2,
                annotation_notes="Medium relevance chunk"
            )
        ]
        
        questions = [
            BenchmarkQuestion(
                question_id="tcfd_1",
                question_text="What are the climate risks?",
                ground_truth_chunks=chunks
            )
        ]
        
        return BenchmarkDatasetContent(
            dataset_id="test_dataset_v1",
            name="Test TCFD Dataset",
            description="Test dataset for TCFD questions",
            version="1.0",
            question_set="tcfd",
            created_at="2024-01-15",
            questions=questions
        )
    
    def test_save_and_get_dataset(self, store, sample_dataset):
        """Test saving and retrieving a dataset"""
        # Save dataset
        dataset_id = store.save_dataset(sample_dataset, "/path/to/dataset.yaml")
        assert dataset_id is not None
        
        # Retrieve dataset
        retrieved = store.get_dataset(sample_dataset.dataset_id)
        assert retrieved is not None
        assert retrieved.dataset_id == sample_dataset.dataset_id
        assert retrieved.name == sample_dataset.name
        assert retrieved.description == sample_dataset.description
        assert retrieved.version == sample_dataset.version
        assert retrieved.question_set == sample_dataset.question_set
        assert retrieved.file_path == "/path/to/dataset.yaml"
    
    def test_get_nonexistent_dataset(self, store):
        """Test retrieving a dataset that doesn't exist"""
        result = store.get_dataset("nonexistent_dataset")
        assert result is None
    
    def test_list_datasets(self, store, sample_dataset):
        """Test listing datasets"""
        # Initially empty
        datasets = store.list_datasets()
        assert len(datasets) == 0
        
        # Save a dataset
        store.save_dataset(sample_dataset, "/path/to/dataset.yaml")
        
        # Should now have one dataset
        datasets = store.list_datasets()
        assert len(datasets) == 1
        assert datasets[0].dataset_id == sample_dataset.dataset_id
    
    def test_get_ground_truth(self, store, sample_dataset):
        """Test retrieving ground truth data"""
        # Save dataset
        store.save_dataset(sample_dataset, "/path/to/dataset.yaml")
        
        # Get ground truth
        ground_truth = store.get_ground_truth(sample_dataset.dataset_id)
        
        assert "tcfd_1" in ground_truth
        question_gt = ground_truth["tcfd_1"]
        assert "chunk_1" in question_gt
        assert "chunk_2" in question_gt
        assert question_gt["chunk_1"] == 1.0
        assert question_gt["chunk_2"] == 0.8
    
    def test_save_and_get_evaluation(self, store, sample_dataset):
        """Test saving and retrieving evaluations"""
        # First save a dataset
        store.save_dataset(sample_dataset, "/path/to/dataset.yaml")
        
        # Create evaluation
        config = RetrievalConfig(
            chunk_size=1000,
            chunk_overlap=200,
            top_k=5,
            use_llm_scoring=True,
            llm_model="gpt-4o-mini"
        )
        
        metrics = EvaluationMetrics(
            precision_at_k={1: 0.8, 5: 0.6},
            recall_at_k={1: 0.2, 5: 0.5},
            f1_at_k={1: 0.32, 5: 0.55},
            mean_reciprocal_rank=0.75,
            mean_average_precision=0.65,
            ndcg_at_k={1: 0.8, 5: 0.68}
        )
        
        evaluation = BenchmarkEvaluation(
            dataset_id=sample_dataset.dataset_id,
            evaluation_name="test_evaluation",
            config_hash="test_hash",
            retrieval_config=config,
            evaluation_metrics=metrics
        )
        
        # Save evaluation
        eval_id = store.save_evaluation(evaluation)
        assert eval_id is not None
        
        # Retrieve evaluation
        retrieved = store.get_evaluation(eval_id)
        assert retrieved is not None
        assert retrieved.dataset_id == sample_dataset.dataset_id
        assert retrieved.evaluation_name == "test_evaluation"
        assert retrieved.retrieval_config.chunk_size == 1000
        assert retrieved.evaluation_metrics.mean_average_precision == 0.65
    
    def test_list_evaluations(self, store, sample_dataset):
        """Test listing evaluations"""
        # Save dataset
        store.save_dataset(sample_dataset, "/path/to/dataset.yaml")
        
        # Initially empty
        evaluations = store.list_evaluations()
        assert len(evaluations) == 0
        
        # Save evaluation
        evaluation = BenchmarkEvaluation(
            dataset_id=sample_dataset.dataset_id,
            evaluation_name="test_eval",
            config_hash="hash",
            retrieval_config=RetrievalConfig(),
            evaluation_metrics=EvaluationMetrics()
        )
        store.save_evaluation(evaluation)
        
        # Should now have one evaluation
        evaluations = store.list_evaluations()
        assert len(evaluations) == 1
        assert evaluations[0].evaluation_name == "test_eval"
        
        # Test filtering by dataset
        filtered = store.list_evaluations(dataset_id=sample_dataset.dataset_id)
        assert len(filtered) == 1
        
        filtered_empty = store.list_evaluations(dataset_id="nonexistent")
        assert len(filtered_empty) == 0
    
    def test_save_and_get_annotations(self, store, sample_dataset):
        """Test saving and retrieving human annotations"""
        # Save dataset and evaluation first
        store.save_dataset(sample_dataset, "/path/to/dataset.yaml")
        
        evaluation = BenchmarkEvaluation(
            dataset_id=sample_dataset.dataset_id,
            evaluation_name="test_eval",
            config_hash="hash",
            retrieval_config=RetrievalConfig(),
            evaluation_metrics=EvaluationMetrics()
        )
        eval_id = store.save_evaluation(evaluation)
        
        # Create annotation
        annotation = HumanAnnotation(
            evaluation_id=eval_id,
            question_id="tcfd_1",
            chunk_id="chunk_1",
            human_relevance_score=0.9,
            human_is_evidence=True,
            human_evidence_order=1,
            annotation_notes="Human annotation notes",
            annotator_id="annotator_1"
        )
        
        # Save annotation
        annotation_id = store.save_annotation(annotation)
        assert annotation_id is not None
        
        # Retrieve annotations
        annotations = store.get_annotations(eval_id)
        assert len(annotations) == 1
        
        retrieved = annotations[0]
        assert retrieved.evaluation_id == eval_id
        assert retrieved.question_id == "tcfd_1"
        assert retrieved.chunk_id == "chunk_1"
        assert retrieved.human_relevance_score == 0.9
        assert retrieved.human_is_evidence is True
        assert retrieved.annotator_id == "annotator_1"
    
    def test_delete_dataset(self, store, sample_dataset):
        """Test deleting a dataset and all related data"""
        # Save dataset
        store.save_dataset(sample_dataset, "/path/to/dataset.yaml")
        
        # Save evaluation
        evaluation = BenchmarkEvaluation(
            dataset_id=sample_dataset.dataset_id,
            evaluation_name="test_eval",
            config_hash="hash",
            retrieval_config=RetrievalConfig(),
            evaluation_metrics=EvaluationMetrics()
        )
        eval_id = store.save_evaluation(evaluation)
        
        # Save annotation
        annotation = HumanAnnotation(
            evaluation_id=eval_id,
            question_id="tcfd_1",
            chunk_id="chunk_1",
            human_relevance_score=0.9,
            human_is_evidence=True,
            annotator_id="annotator_1"
        )
        store.save_annotation(annotation)
        
        # Verify data exists
        assert store.get_dataset(sample_dataset.dataset_id) is not None
        assert len(store.list_evaluations(sample_dataset.dataset_id)) == 1
        assert len(store.get_annotations(eval_id)) == 1
        
        # Delete dataset
        deleted = store.delete_dataset(sample_dataset.dataset_id)
        assert deleted is True
        
        # Verify all related data is deleted
        assert store.get_dataset(sample_dataset.dataset_id) is None
        assert len(store.list_evaluations(sample_dataset.dataset_id)) == 0
        # Note: annotations are also deleted via foreign key cascade
    
    def test_delete_nonexistent_dataset(self, store):
        """Test deleting a dataset that doesn't exist"""
        deleted = store.delete_dataset("nonexistent_dataset")
        assert deleted is False
    
    def test_save_dataset_replace_existing(self, store, sample_dataset):
        """Test that saving a dataset with same ID replaces the existing one"""
        # Save dataset
        store.save_dataset(sample_dataset, "/path/to/dataset.yaml")
        
        # Modify and save again
        sample_dataset.name = "Updated Dataset Name"
        store.save_dataset(sample_dataset, "/path/to/updated_dataset.yaml")
        
        # Should have updated the existing record
        datasets = store.list_datasets()
        assert len(datasets) == 1
        assert datasets[0].name == "Updated Dataset Name"
        assert datasets[0].file_path == "/path/to/updated_dataset.yaml"
