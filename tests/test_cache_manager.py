import pytest
import sqlite3
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime
import os

from app.core.cache_manager import CacheManager

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ['STORAGE_PATH'] = str(Path(__file__).parent / 'test_storage')
    yield
    # Cleanup after tests
    if Path(os.environ['STORAGE_PATH']).exists():
        import shutil
        shutil.rmtree(os.environ['STORAGE_PATH'])

@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_cache.db"
    cache_manager = CacheManager(str(db_path))
    yield cache_manager
    shutil.rmtree(temp_dir)

def test_init_db(temp_db):
    """Test database initialization"""
    # Check if tables exist
    with sqlite3.connect(temp_db.db_path) as conn:
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('analysis_cache', 'document_chunks', 'questions', 'question_analysis', 'chunk_relevance')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
    assert 'analysis_cache' in tables
    assert 'document_chunks' in tables
    assert 'questions' in tables
    assert 'question_analysis' in tables
    assert 'chunk_relevance' in tables

def test_save_and_get_analysis(temp_db):
    """Test saving and retrieving analysis results"""
    # Test data
    file_path = "test_doc.pdf"
    question_id = "tcfd_1"
    result = {
        "ANSWER": "Test answer",
        "SCORE": 8,
        "EVIDENCE": [{"text": "Test evidence", "chunk": 1}],
        "GAPS": ["Test gap"],
        "SOURCES": [1]
    }
    config = {
        'chunk_size': 500,
        'chunk_overlap': 20,
        'top_k': 5,
        'model': 'gpt-4',
        'question_set': 'tcfd'
    }
    
    # Save analysis
    temp_db.save_analysis(file_path, question_id, result, config)
    
    # Retrieve analysis
    cached = temp_db.get_analysis(file_path, config)
    
    # Check results - note the structure change
    assert question_id in cached
    assert cached[question_id]["result"]["ANSWER"] == "Test answer"  # Now nested under 'result'
    assert cached[question_id]["result"]["SCORE"] == 8

def test_save_and_get_vectors(temp_db):
    """Test saving and retrieving document chunks"""
    # Test data - note: we now use document_chunks instead of vector_cache
    file_path = "test_doc.pdf"
    chunks = [
        {
            'text': 'First chunk',
            'embedding': [0.1, 0.2, 0.3],
            'metadata': {'page': 1}
        },
        {
            'text': 'Second chunk', 
            'embedding': [0.4, 0.5, 0.6],
            'metadata': {'page': 2}
        }
    ]
    
    # Save chunks
    temp_db.save_document_chunks(file_path, chunks, chunk_size=500, chunk_overlap=20)
    
    # Retrieve chunks
    cached_chunks = temp_db.get_document_chunks(file_path, chunk_size=500, chunk_overlap=20)
    
    assert len(cached_chunks) == 2
    assert cached_chunks[0]['text'] == 'First chunk'
    assert cached_chunks[1]['text'] == 'Second chunk'

def test_config_matching(temp_db):
    """Test that results are only returned with matching config"""
    file_path = "test_doc.pdf"
    question_id = "tcfd_1"
    result = {"ANSWER": "Test"}
    
    config1 = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4",
        "question_set": "tcfd"
    }
    
    config2 = {
        "chunk_size": 300,  # Different chunk size
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4",
        "question_set": "tcfd"
    }
    
    # Save with config1
    temp_db.save_analysis(file_path, question_id, result, config1)
    
    # Try to retrieve with config2
    cached = temp_db.get_analysis(file_path, config2, [question_id])
    assert len(cached) == 0  # Should not find results with different config

def test_multiple_questions(temp_db):
    """Test handling multiple questions"""
    file_path = "test_doc.pdf"
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4",
        "question_set": "tcfd"
    }
    
    # Save multiple questions
    questions = {
        "tcfd_1": {"ANSWER": "Answer 1"},
        "tcfd_2": {"ANSWER": "Answer 2"},
        "tcfd_3": {"ANSWER": "Answer 3"}
    }
    
    for qid, result in questions.items():
        temp_db.save_analysis(file_path, qid, result, config)
    
    # Retrieve subset of questions
    cached = temp_db.get_analysis(file_path, config, ["tcfd_1", "tcfd_3"])
    assert len(cached) == 2
    assert "tcfd_1" in cached
    assert "tcfd_3" in cached
    assert "tcfd_2" not in cached

def test_error_handling(temp_db):
    """Test error handling"""
    # Test invalid JSON
    with pytest.raises(Exception):
        temp_db.save_analysis(
            "test.pdf",
            "tcfd_1",
            object(),  # Un-serializable object
            {"chunk_size": 500}
        )
    
    # Test missing required config params
    with pytest.raises(Exception):
        temp_db.get_analysis(
            "test.pdf",
            {"chunk_size": 500}  # Missing required params
        )

def test_cache_status(temp_db):
    """Test cache status checking"""
    file_path = "test_doc.pdf"
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4",
        "question_set": "tcfd"
    }
    
    # Save some data
    temp_db.save_analysis(file_path, "tcfd_1", {"ANSWER": "Test"}, config)
    
    # Check status
    status = temp_db.check_cache_status(file_path)
    assert len(status) > 0
    assert status[0][0] == 500  # chunk_size
    assert status[0][1] == 20   # chunk_overlap
    assert status[0][2] == 5    # top_k
    assert status[0][3] == "gpt-4"  # model 

def test_question_set_mapping_in_get_analysis(temp_db):
    """Test that question set mapping works correctly in get_analysis"""
    # Test data with everest question set
    file_path = "test_doc.pdf"
    question_id = "ev_24"
    config = {
        'chunk_size': 500,
        'chunk_overlap': 20,
        'top_k': 5,
        'model': 'gpt-4o-mini',
        'question_set': 'everest'  # UI uses 'everest'
    }
    result = {
        "ANSWER": "Test answer for everest question",
        "SCORE": 8,
        "EVIDENCE": [{"text": "Test evidence", "chunk": 1}],
        "GAPS": ["Test gap"],
        "SOURCES": [1],
        "chunks": [
            {
                "text": "Test chunk",
                "chunk_order": 0,
                "similarity_score": 0.9,
                "llm_score": None,
                "is_evidence": True,
                "evidence_order": 1,
                "metadata": {}
            }
        ]
    }
    
    # Save analysis (should map everest -> ev in database)
    temp_db.save_analysis(file_path, question_id, result, config)
    
    # Retrieve analysis using everest question_set
    retrieved = temp_db.get_analysis(file_path, config)
    
    # Should find the analysis despite mapping
    assert question_id in retrieved
    assert retrieved[question_id]['result']['ANSWER'] == "Test answer for everest question"

def test_database_path_configuration():
    """Test that database path is configured correctly"""
    # Test default path without explicit path
    cache_manager = CacheManager()
    
    # Should use ./data/cache/analysis.db by default
    expected_path = Path("./data/cache/analysis.db").resolve()
    actual_path = Path(cache_manager.db_path).resolve()
    
    assert actual_path.name == "analysis.db"
    assert "cache" in str(actual_path)

def test_evidence_formatting_in_save_analysis(temp_db):
    """Test that evidence is properly formatted when saved"""
    file_path = "test_doc.pdf"
    question_id = "tcfd_1"
    config = {
        'chunk_size': 500,
        'chunk_overlap': 20,
        'top_k': 5,
        'model': 'gpt-4o-mini',
        'question_set': 'tcfd'
    }
    
    # Test with properly formatted evidence
    result = {
        "ANSWER": "Test answer",
        "SCORE": 7,
        "EVIDENCE": [
            {
                "chunk": 1,
                "text": "Key evidence from chunk 1",
                "chunk_text": "Full chunk text here...",
                "score": 1.0,
                "order": 1,
                "metadata": {"source": "test"}
            }
        ],
        "GAPS": ["Missing data"],
        "SOURCES": [1],
        "chunks": [
            {
                "text": "Full chunk text here...",
                "chunk_order": 0,
                "similarity_score": 0.85,
                "llm_score": None,
                "is_evidence": True,
                "evidence_order": 1,
                "metadata": {"source": "test"}
            }
        ]
    }
    
    # Save and retrieve
    temp_db.save_analysis(file_path, question_id, result, config)
    retrieved = temp_db.get_analysis(file_path, config)
    
    # Check evidence is preserved correctly
    assert question_id in retrieved
    evidence = retrieved[question_id]['result']['EVIDENCE']
    assert len(evidence) == 1
    assert evidence[0]['text'] == "Key evidence from chunk 1"
    assert evidence[0]['chunk'] == 1 