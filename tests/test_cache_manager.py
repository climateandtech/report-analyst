import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from report_analyst.core.cache_manager import CacheManager


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["STORAGE_PATH"] = str(Path(__file__).parent / "test_storage")
    yield
    # Cleanup after tests
    if Path(os.environ["STORAGE_PATH"]).exists():
        import shutil

        shutil.rmtree(os.environ["STORAGE_PATH"])


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
        cursor = conn.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND (name='analysis_cache' OR name='document_chunks')
        """
        )
        tables = [row[0] for row in cursor.fetchall()]

    assert "analysis_cache" in tables
    assert "document_chunks" in tables


def test_save_and_get_analysis(temp_db):
    """Test saving and retrieving analysis results"""
    # Test data
    file_path = "test_doc.pdf"
    question_id = "tcfd_1"
    result = {
        "ANSWER": "Test answer",
        "SCORE": 7,
        "EVIDENCE": ["evidence1", "evidence2"],
    }
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4",
        "question_set": "tcfd",
    }

    # Save analysis
    temp_db.save_analysis(file_path, question_id, result, config)

    # Retrieve analysis
    cached = temp_db.get_analysis(file_path, config, [question_id])

    assert question_id in cached
    assert cached[question_id]["result"]["ANSWER"] == "Test answer"
    assert cached[question_id]["result"]["SCORE"] == 7
    assert len(cached[question_id]["result"]["EVIDENCE"]) == 2


def test_save_and_get_vectors(temp_db):
    """Test saving and retrieving vector embeddings"""
    import numpy as np

    # Test data
    file_path = "test_doc.pdf"
    chunks = [
        {
            "text": "Test chunk 1",
            "embedding": np.array([0.1, 0.2, 0.3]),
            "metadata": {"page": 1},
        },
        {
            "text": "Test chunk 2",
            "embedding": np.array([0.4, 0.5, 0.6]),
            "metadata": {"page": 2},
        },
    ]

    # Save vectors
    temp_db.save_vectors(file_path, chunks)

    # Retrieve vectors
    cached_chunks = temp_db.get_vectors(file_path)

    assert len(cached_chunks) == 2
    assert cached_chunks[0]["text"] == "Test chunk 1"
    assert np.allclose(cached_chunks[0]["embedding"], np.array([0.1, 0.2, 0.3]))
    assert cached_chunks[0]["metadata"]["page"] == 1


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
        "question_set": "tcfd",
    }

    config2 = {
        "chunk_size": 300,  # Different chunk size
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4",
        "question_set": "tcfd",
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
        "question_set": "tcfd",
    }

    # Save multiple questions
    questions = {
        "tcfd_1": {"ANSWER": "Answer 1"},
        "tcfd_2": {"ANSWER": "Answer 2"},
        "tcfd_3": {"ANSWER": "Answer 3"},
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
            {"chunk_size": 500},
        )

    # Test missing required config params
    with pytest.raises(Exception):
        temp_db.get_analysis("test.pdf", {"chunk_size": 500})  # Missing required params


def test_cache_status(temp_db):
    """Test cache status checking"""
    file_path = "test_doc.pdf"
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4",
        "question_set": "tcfd",
    }

    # Save some data
    temp_db.save_analysis(file_path, "tcfd_1", {"ANSWER": "Test"}, config)

    # Check status
    status = temp_db.check_cache_status(file_path)
    assert len(status) > 0
    assert status[0][0] == 500  # chunk_size
    assert status[0][1] == 20  # chunk_overlap
    assert status[0][2] == 5  # top_k
    assert status[0][3] == "gpt-4"  # model


def test_get_chunks_without_embeddings(temp_db):
    """Test get_chunks_without_embeddings method"""
    import sqlite3
    from datetime import datetime

    import numpy as np

    file_path = "test_file.pdf"
    chunk_size = 500
    chunk_overlap = 20

    # Insert chunks directly into database (some without embeddings, some with)
    with sqlite3.connect(temp_db.db_path) as conn:
        timestamp = datetime.now().isoformat()

        # Insert chunks without embeddings
        conn.execute(
            """
            INSERT INTO document_chunks
            (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                file_path,
                "Chunk 1 without embedding",
                chunk_size,
                chunk_overlap,
                None,  # No embedding
                json.dumps({}),
                timestamp,
            ),
        )
        conn.execute(
            """
            INSERT INTO document_chunks
            (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                file_path,
                "Chunk 2 without embedding",
                chunk_size,
                chunk_overlap,
                None,  # No embedding
                json.dumps({}),
                timestamp,
            ),
        )

        # Insert chunk with embedding
        embedding_bytes = np.array([0.1, 0.2, 0.3], dtype=np.float32).tobytes()
        conn.execute(
            """
            INSERT INTO document_chunks
            (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                file_path,
                "Chunk 3 with embedding",
                chunk_size,
                chunk_overlap,
                embedding_bytes,
                json.dumps({}),
                timestamp,
            ),
        )

    # Get chunks without embeddings
    result = temp_db.get_chunks_without_embeddings(file_path, chunk_size, chunk_overlap)

    # Should return only chunks without embeddings
    assert len(result) == 2
    assert all(chunk.get("embedding") is None for chunk in result)
    assert all("Chunk" in chunk["text"] for chunk in result)


def test_has_chunk_scoring(temp_db):
    """Test has_chunk_scoring method"""
    import sqlite3
    from datetime import datetime

    import numpy as np

    file_path = "test_file.pdf"
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4",
        "question_set": "tcfd",
    }

    # Initially should be False
    assert temp_db.has_chunk_scoring(file_path, config) is False

    # First, save the chunk to document_chunks table so it can be referenced
    chunk_text = "Chunk 1"
    embedding_bytes = np.array([0.1, 0.2, 0.3], dtype=np.float32).tobytes()
    with sqlite3.connect(temp_db.db_path) as conn:
        timestamp = datetime.now().isoformat()
        conn.execute(
            """
            INSERT INTO document_chunks
            (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                file_path,
                chunk_text,
                config["chunk_size"],
                config["chunk_overlap"],
                embedding_bytes,
                json.dumps({}),
                timestamp,
            ),
        )

    # Save analysis with chunk relevance (scoring)
    temp_db.save_analysis(
        file_path,
        "tcfd_1",
        {
            "ANSWER": "Test answer",
            "chunks": [
                {
                    "text": chunk_text,
                    "similarity_score": 0.8,
                    "llm_score": 0.7,
                    "is_evidence": True,
                    "chunk_order": 1,
                }
            ],
        },
        config,
    )

    # Now should be True
    assert temp_db.has_chunk_scoring(file_path, config) is True
