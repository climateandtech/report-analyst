import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
import sqlite3

from app.core.benchmark.dataset_loader import DatasetLoader, DatasetValidationError
from app.models.benchmark import BenchmarkDatasetContent, BenchmarkQuestion, GroundTruthChunk

class TestDatasetLoader:
    """Test suite for dataset loading and validation"""
    
    @pytest.fixture
    def loader(self):
        return DatasetLoader()
    
    @pytest.fixture
    def valid_dataset_yaml(self):
        return """
dataset_id: "test_dataset_v1"
name: "Test TCFD Dataset"
description: "Test dataset for TCFD questions"
version: "1.0"
question_set: "tcfd"
created_at: "2024-01-15"
questions:
  - question_id: "tcfd_1"
    question_text: "What are the climate-related risks?"
    ground_truth_chunks:
      - chunk_id: "chunk_001"
        relevance_score: 1.0
        is_evidence: true
        evidence_order: 1
        annotation_notes: "Contains specific climate risk metrics"
      - chunk_id: "chunk_002"
        relevance_score: 0.8
        is_evidence: true
        evidence_order: 2
        annotation_notes: "Describes governance processes"
  - question_id: "tcfd_2"
    question_text: "What are the climate opportunities?"
    ground_truth_chunks:
      - chunk_id: "chunk_003"
        relevance_score: 0.9
        is_evidence: true
        evidence_order: 1
        annotation_notes: "Lists specific opportunities"
"""
    
    @pytest.fixture
    def invalid_dataset_missing_field(self):
        return """
dataset_id: "test_dataset_v1"
name: "Test TCFD Dataset"
# Missing description field
version: "1.0"
question_set: "tcfd"
questions: []
"""
    
    @pytest.fixture
    def invalid_dataset_bad_score(self):
        return """
dataset_id: "test_dataset_v1"
name: "Test TCFD Dataset"
description: "Test dataset"
version: "1.0"
question_set: "tcfd"
questions:
  - question_id: "tcfd_1"
    question_text: "What are the climate-related risks?"
    ground_truth_chunks:
      - chunk_id: "chunk_001"
        relevance_score: 1.5  # Invalid score > 1.0
        is_evidence: true
"""
    
    def test_load_valid_yaml_dataset(self, loader, valid_dataset_yaml):
        """Test loading a valid YAML dataset"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(valid_dataset_yaml)
            f.flush()
            
            dataset = loader.load_dataset(f.name)
            
            # Verify dataset structure
            assert dataset.dataset_id == "test_dataset_v1"
            assert dataset.name == "Test TCFD Dataset"
            assert dataset.question_set == "tcfd"
            assert len(dataset.questions) == 2
            
            # Verify first question
            q1 = dataset.questions[0]
            assert q1.question_id == "tcfd_1"
            assert len(q1.ground_truth_chunks) == 2
            
            # Verify chunks
            chunk1 = q1.ground_truth_chunks[0]
            assert chunk1.chunk_id == "chunk_001"
            assert chunk1.relevance_score == 1.0
            assert chunk1.is_evidence is True
            assert chunk1.evidence_order == 1
            
            Path(f.name).unlink()
    
    def test_load_nonexistent_file(self, loader):
        """Test loading a file that doesn't exist"""
        with pytest.raises(FileNotFoundError):
            loader.load_dataset("nonexistent_file.yaml")
    
    def test_load_unsupported_format(self, loader):
        """Test loading an unsupported file format"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"some content")
            f.flush()
            
            with pytest.raises(ValueError, match="Unsupported file format"):
                loader.load_dataset(f.name)
            
            Path(f.name).unlink()
    
    def test_load_invalid_yaml(self, loader):
        """Test loading invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            
            with pytest.raises(DatasetValidationError):
                loader.load_dataset(f.name)
            
            Path(f.name).unlink()
    
    def test_validation_missing_required_field(self, loader, invalid_dataset_missing_field):
        """Test validation with missing required field"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_dataset_missing_field)
            f.flush()
            
            with pytest.raises(DatasetValidationError, match="Missing required field"):
                loader.load_dataset(f.name)
            
            Path(f.name).unlink()
    
    def test_validation_invalid_relevance_score(self, loader, invalid_dataset_bad_score):
        """Test validation with invalid relevance score"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_dataset_bad_score)
            f.flush()
            
            with pytest.raises(DatasetValidationError, match="Invalid relevance_score"):
                loader.load_dataset(f.name)
            
            Path(f.name).unlink()
    
    def test_validate_dataset_consistency(self, loader, valid_dataset_yaml):
        """Test dataset consistency validation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(valid_dataset_yaml)
            f.flush()
            
            dataset = loader.load_dataset(f.name)
            warnings = loader.validate_dataset_consistency(dataset)
            
            # Should have no warnings for valid dataset
            assert len(warnings) == 0
            
            Path(f.name).unlink()
    
    def test_validate_duplicate_question_ids(self, loader):
        """Test validation catches duplicate question IDs"""
        duplicate_dataset = """
dataset_id: "test_dataset"
name: "Test Dataset"
description: "Test"
version: "1.0"
question_set: "tcfd"
questions:
  - question_id: "tcfd_1"
    question_text: "Question 1"
    ground_truth_chunks:
      - chunk_id: "chunk_001"
        relevance_score: 1.0
        is_evidence: true
  - question_id: "tcfd_1"  # Duplicate ID
    question_text: "Question 2"
    ground_truth_chunks:
      - chunk_id: "chunk_002"
        relevance_score: 0.8
        is_evidence: true
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(duplicate_dataset)
            f.flush()
            
            dataset = loader.load_dataset(f.name)
            warnings = loader.validate_dataset_consistency(dataset)
            
            assert any("Duplicate question IDs" in warning for warning in warnings)
            
            Path(f.name).unlink()
    
    def test_generate_dataset_hash(self, loader, valid_dataset_yaml):
        """Test dataset hash generation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(valid_dataset_yaml)
            f.flush()
            
            dataset = loader.load_dataset(f.name)
            hash1 = loader.generate_dataset_hash(dataset)
            hash2 = loader.generate_dataset_hash(dataset)
            
            # Hash should be consistent
            assert hash1 == hash2
            assert len(hash1) == 16  # SHA256 truncated to 16 chars
            
            Path(f.name).unlink()
    
    def test_load_json_dataset(self, loader):
        """Test loading a JSON dataset"""
        json_data = {
            "dataset_id": "test_json",
            "name": "Test JSON Dataset",
            "description": "Test dataset in JSON format",
            "version": "1.0",
            "question_set": "tcfd",
            "questions": [
                {
                    "question_id": "tcfd_1",
                    "question_text": "Test question",
                    "ground_truth_chunks": [
                        {
                            "chunk_id": "chunk_001",
                            "relevance_score": 0.9,
                            "is_evidence": True,
                            "evidence_order": 1
                        }
                    ]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            f.flush()
            
            dataset = loader.load_dataset(f.name)
            
            assert dataset.dataset_id == "test_json"
            assert len(dataset.questions) == 1
            assert dataset.questions[0].ground_truth_chunks[0].relevance_score == 0.9
            
            Path(f.name).unlink()
