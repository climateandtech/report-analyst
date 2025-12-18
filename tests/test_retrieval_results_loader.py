import pytest
import tempfile
import pandas as pd
from pathlib import Path
import sqlite3

from app.core.benchmark.retrieval_results_loader import (
    load_flexible_dataset_from_csv,
    load_flexible_dataset_from_sqlite,
    detect_dataset_type,
    export_retrieval_results_to_csv
)
from app.models.benchmark import BenchmarkDataset, FlexibleDatasetRow, DatasetType


class TestFlexibleDatasetLoader:
    """Test suite for flexible dataset loading with different column names"""
    
    def test_detect_dataset_type_ir(self):
        """Test detecting Information Retrieval dataset type"""
        columns = ['query_id', 'chunk_id', 'position', 'score']
        dataset_type = detect_dataset_type(columns)
        assert dataset_type == DatasetType.INFORMATION_RETRIEVAL
    
    def test_detect_dataset_type_ie(self):
        """Test detecting Information Extraction dataset type"""
        columns = ['question_id', 'answer', 'category', 'confidence_score']
        dataset_type = detect_dataset_type(columns)
        assert dataset_type == DatasetType.INFORMATION_EXTRACTION
    
    def test_detect_dataset_type_defaults_to_ir(self):
        """Test that unclear datasets default to IR"""
        columns = ['id', 'value']
        dataset_type = detect_dataset_type(columns)
        assert dataset_type == DatasetType.INFORMATION_RETRIEVAL
    
    def test_load_csv_with_standard_columns(self):
        """Test loading CSV with standard column names"""
        csv_content = """query_id,chunk_id,position,score
tcfd_1,chunk_001,1,0.95
tcfd_1,chunk_015,2,0.89
tcfd_2,chunk_023,1,0.93"""
        
        dataset = load_flexible_dataset_from_csv(csv_content=csv_content)
        
        assert dataset.dataset_id is not None
        assert dataset.dataset_type == DatasetType.INFORMATION_RETRIEVAL
        assert len(dataset.results) == 3
    
    def test_load_csv_with_variant_column_names(self):
        """Test loading CSV with variant column names (question_id instead of query_id)"""
        csv_content = """question_id,chunk,rank,relevance_score
tcfd_1,chunk_001,1,0.95
tcfd_1,chunk_015,2,0.89"""
        
        dataset = load_flexible_dataset_from_csv(csv_content=csv_content)
        
        assert len(dataset.results) == 2
        assert dataset.results[0].get_query_id() == "tcfd_1"
        assert dataset.results[0].get_chunk_id() == "chunk_001"
        assert dataset.results[0].get_position() == 1
        assert dataset.results[0].get_score() == 0.95
    
    def test_load_csv_ie_dataset(self):
        """Test loading Information Extraction dataset"""
        csv_content = """question_id,answer,category,confidence_score
tcfd_1,"The company identifies climate risks...","risk_identification",0.92
tcfd_2,"Strategy includes...","strategy",0.88"""
        
        dataset = load_flexible_dataset_from_csv(csv_content=csv_content)
        
        assert dataset.dataset_type == DatasetType.INFORMATION_EXTRACTION
        assert len(dataset.results) == 2
        assert dataset.results[0].get_answer() == "The company identifies climate risks..."
        assert dataset.results[0].get_category() == "risk_identification"
    
    def test_load_csv_from_file_path(self):
        """Test loading CSV from file path"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("query_id,chunk_id,position,score\n")
            f.write("tcfd_1,chunk_001,1,0.95\n")
            f.flush()
            temp_path = f.name
        
        try:
            dataset = load_flexible_dataset_from_csv(csv_path=temp_path)
            assert len(dataset.results) == 1
            assert dataset.source_path == temp_path
        finally:
            Path(temp_path).unlink()
    
    def test_load_csv_with_optional_columns(self):
        """Test loading CSV with optional columns"""
        csv_content = """query_id,report_id,chunk_id,chunk_text,position,score,similarity_score,llm_score
tcfd_1,report_001,chunk_001,"Climate risks...",1,0.95,0.92,0.88
tcfd_1,report_001,chunk_015,"Risk assessment...",2,0.89,0.87,0.85"""
        
        dataset = load_flexible_dataset_from_csv(csv_content=csv_content)
        
        assert len(dataset.results) == 2
        assert dataset.results[0].get('report_id') == "report_001"
        assert dataset.results[0].get('chunk_text') == "Climate risks..."
        assert dataset.results[0].get('similarity_score') == 0.92
        assert dataset.results[0].get('llm_score') == 0.88
    
    def test_load_csv_handles_missing_values(self):
        """Test loading CSV with missing/NaN values"""
        csv_content = """query_id,chunk_id,position,score,similarity_score
tcfd_1,chunk_001,1,0.95,
tcfd_1,chunk_015,2,0.89,0.87"""
        
        dataset = load_flexible_dataset_from_csv(csv_content=csv_content)
        
        assert len(dataset.results) == 2
        assert dataset.results[0].get('similarity_score') is None
        assert dataset.results[1].get('similarity_score') == 0.87
    
    def test_load_csv_requires_query_id(self):
        """Test that CSV must have query_id or question_id"""
        csv_content = """chunk_id,position,score
chunk_001,1,0.95"""
        
        with pytest.raises(ValueError, match="Missing required columns"):
            load_flexible_dataset_from_csv(csv_content=csv_content)
    
    def test_load_csv_requires_chunk_id_for_ir(self):
        """Test that IR datasets require chunk_id"""
        csv_content = """query_id,position,score
tcfd_1,1,0.95"""
        
        with pytest.raises(ValueError, match="Missing required columns"):
            load_flexible_dataset_from_csv(csv_content=csv_content)
    
    def test_get_unique_queries(self):
        """Test getting unique query IDs from dataset"""
        csv_content = """query_id,chunk_id,position,score
tcfd_1,chunk_001,1,0.95
tcfd_1,chunk_015,2,0.89
tcfd_2,chunk_023,1,0.93"""
        
        dataset = load_flexible_dataset_from_csv(csv_content=csv_content)
        
        unique_queries = dataset.get_unique_queries()
        assert len(unique_queries) == 2
        assert "tcfd_1" in unique_queries
        assert "tcfd_2" in unique_queries
    
    def test_get_results_by_query(self):
        """Test getting results for a specific query"""
        csv_content = """query_id,chunk_id,position,score
tcfd_1,chunk_001,1,0.95
tcfd_1,chunk_015,2,0.89
tcfd_2,chunk_023,1,0.93"""
        
        dataset = load_flexible_dataset_from_csv(csv_content=csv_content)
        
        tcfd_1_results = dataset.get_results_by_query("tcfd_1")
        assert len(tcfd_1_results) == 2
        assert tcfd_1_results[0].get_chunk_id() == "chunk_001"
        assert tcfd_1_results[1].get_chunk_id() == "chunk_015"
    
    def test_is_metadata_only(self):
        """Test checking if dataset is metadata-only"""
        dataset = BenchmarkDataset(
            dataset_id="test",
            name="Test",
            source="database"
        )
        assert dataset.is_metadata_only() is True
    
    def test_has_results(self):
        """Test checking if dataset has results"""
        csv_content = """query_id,chunk_id,position,score
tcfd_1,chunk_001,1,0.95"""
        
        dataset = load_flexible_dataset_from_csv(csv_content=csv_content)
        assert dataset.has_results() is True
    
    def test_load_sqlite_dataset(self):
        """Test loading dataset from SQLite"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        try:
            # Create table and insert data
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE benchmark_results (
                    query_id TEXT,
                    chunk_id TEXT,
                    position INTEGER,
                    score REAL
                )
            """)
            conn.execute("""
                INSERT INTO benchmark_results VALUES
                ('tcfd_1', 'chunk_001', 1, 0.95),
                ('tcfd_1', 'chunk_015', 2, 0.89)
            """)
            conn.commit()
            conn.close()
            
            dataset = load_flexible_dataset_from_sqlite(db_path, table_name="benchmark_results")
            
            assert len(dataset.results) == 2
            assert dataset.source == "sqlite"
            assert dataset.source_path == db_path
        finally:
            Path(db_path).unlink()
    
    def test_load_sqlite_with_filter(self):
        """Test loading SQLite dataset with query filter"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE benchmark_results (
                    query_id TEXT,
                    chunk_id TEXT,
                    position INTEGER,
                    score REAL
                )
            """)
            conn.execute("""
                INSERT INTO benchmark_results VALUES
                ('tcfd_1', 'chunk_001', 1, 0.95),
                ('tcfd_2', 'chunk_023', 1, 0.93)
            """)
            conn.commit()
            conn.close()
            
            dataset = load_flexible_dataset_from_sqlite(
                db_path, 
                table_name="benchmark_results",
                query_filter="query_id = 'tcfd_1'"
            )
            
            assert len(dataset.results) == 1
            assert dataset.results[0].get_query_id() == "tcfd_1"
        finally:
            Path(db_path).unlink()
    
    def test_export_to_csv(self):
        """Test exporting dataset to CSV"""
        csv_content = """query_id,chunk_id,position,score
tcfd_1,chunk_001,1,0.95
tcfd_1,chunk_015,2,0.89"""
        
        dataset = load_flexible_dataset_from_csv(csv_content=csv_content)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name
        
        try:
            export_retrieval_results_to_csv(dataset, output_path)
            
            # Verify file was created
            assert Path(output_path).exists()
            
            # Verify content
            df = pd.read_csv(output_path)
            assert len(df) == 2
            assert 'query_id' in df.columns
            assert 'chunk_id' in df.columns
            assert 'position' in df.columns
            assert 'score' in df.columns
        finally:
            Path(output_path).unlink()
    
    def test_flexible_row_get_method(self):
        """Test FlexibleDatasetRow get method with case-insensitive matching"""
        row = FlexibleDatasetRow(data={
            'Query_ID': 'tcfd_1',
            'Chunk_ID': 'chunk_001',
            'Score': 0.95
        })
        
        assert row.get('query_id') == 'tcfd_1'
        assert row.get('QUERY_ID') == 'tcfd_1'
        assert row.get('chunk_id') == 'chunk_001'
        assert row.get('score') == 0.95
        assert row.get('nonexistent') is None
        assert row.get('nonexistent', 'default') == 'default'
