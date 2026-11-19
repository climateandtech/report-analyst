import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from report_analyst.core.cache_manager import CacheManager
from report_analyst.models.source_tag import SourceTag


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
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
              AND name IN ('analysis_cache', 'document_chunks', 'source_annotations')
        """)
        tables = [row[0] for row in cursor.fetchall()]

    assert "analysis_cache" in tables
    assert "document_chunks" in tables
    assert "source_annotations" in tables


SOURCE_ANNOTATION = {
    "id": "source-1",
    "document_id": "document-hash",
    "page": 1,
    "span_start": 0,
    "span_end": 8,
    "selected_text": "Evidence",
    "rects": [{"x": 10, "y": 20, "width": 50, "height": 12}],
}


def test_save_and_get_source_annotations(temp_db):
    rects = [
        {"x": 10.5, "y": 20.25, "width": 100.0, "height": 12.0},
        {"x": 10.5, "y": 35.25, "width": 65.0, "height": 12.0},
    ]

    temp_db.save_source_annotation({**SOURCE_ANNOTATION, "rects": rects})

    saved = temp_db.get_source_annotations("document-hash")
    assert [annotation["selected_text"] for annotation in saved] == ["Evidence"]
    assert saved[0]["rects"] == rects
    assert temp_db.get_source_annotations("different-document") == []


def test_source_annotations_allow_overlapping_spans(temp_db):
    temp_db.save_source_annotation({**SOURCE_ANNOTATION, "id": "disclosure", "span_end": 50})
    temp_db.save_source_annotation({**SOURCE_ANNOTATION, "id": "value", "span_start": 33, "span_end": 40})

    saved = temp_db.get_source_annotations("document-hash")
    assert [annotation["id"] for annotation in saved] == ["disclosure", "value"]


def test_delete_source_annotation_is_scoped_to_its_document(temp_db):
    temp_db.save_source_annotation(SOURCE_ANNOTATION)

    temp_db.delete_source_annotation("source-1", "other-document")
    assert len(temp_db.get_source_annotations("document-hash")) == 1

    temp_db.delete_source_annotation("source-1", "document-hash")
    assert temp_db.get_source_annotations("document-hash") == []


def test_source_annotation_records_when_it_was_created(temp_db):
    before = datetime.now()
    temp_db.save_source_annotation(SOURCE_ANNOTATION)
    after = datetime.now()

    saved = temp_db.get_source_annotations("document-hash")[0]
    assert before <= datetime.fromisoformat(saved["created_at"]) <= after


def test_source_annotation_ignores_created_at_sent_by_the_browser(temp_db):
    before = datetime.now()

    temp_db.save_source_annotation({**SOURCE_ANNOTATION, "created_at": "2000-01-01T00:00:00"})

    saved = temp_db.get_source_annotations("document-hash")[0]
    assert datetime.fromisoformat(saved["created_at"]) >= before


def test_source_annotation_id_used_by_another_document_is_rejected(temp_db):
    temp_db.save_source_annotation(SOURCE_ANNOTATION)

    with pytest.raises(IntegrityError):
        temp_db.save_source_annotation({**SOURCE_ANNOTATION, "document_id": "other-document"})

    assert len(temp_db.get_source_annotations("document-hash")) == 1
    assert temp_db.get_source_annotations("other-document") == []


def test_source_annotation_with_an_empty_span_is_rejected(temp_db):
    with pytest.raises(ValidationError):
        temp_db.save_source_annotation({**SOURCE_ANNOTATION, "span_start": 8})


def test_clear_cache_keeps_source_annotations(temp_db):
    temp_db.save_source_annotation(SOURCE_ANNOTATION)

    temp_db.clear_cache("report.pdf")
    temp_db.clear_cache()

    assert len(temp_db.get_source_annotations("document-hash")) == 1


def source_tag(**fields):
    return SourceTag(
        **{
            "id": "tag-1",
            "source_id": "source-1",
            "document_id": "document-hash",
            "concept": "esrs:GrossScope1GreenhouseGasEmissions",
            "value": "1240",
            "unit": "tCO2e",
            "decimals": 0,
            **fields,
        }
    )


def test_save_and_get_source_tags(temp_db):
    temp_db.save_source_annotation(SOURCE_ANNOTATION)
    temp_db.save_source_tag(source_tag())
    temp_db.save_source_tag(source_tag(id="tag-2", concept="esrs:PolicyTextBlock", value="Text", unit=None, decimals=None))

    saved = temp_db.get_source_tags("document-hash")

    assert [(tag.id, tag.value, tag.unit, tag.decimals) for tag in saved] == [
        ("tag-1", "1240", "tCO2e", 0),
        ("tag-2", "Text", None, None),
    ]
    assert all(tag.created_at for tag in saved)
    assert temp_db.get_source_tags("other-document") == []


def test_deleting_a_source_deletes_only_its_tags(temp_db):
    temp_db.save_source_annotation(SOURCE_ANNOTATION)
    temp_db.save_source_annotation({**SOURCE_ANNOTATION, "id": "source-2"})
    temp_db.save_source_tag(source_tag())
    temp_db.save_source_tag(source_tag(id="tag-2", source_id="source-2"))

    temp_db.delete_source_annotation("source-1", "document-hash")

    assert [tag.id for tag in temp_db.get_source_tags("document-hash")] == ["tag-2"]


def test_deleting_a_source_of_another_document_keeps_its_tags(temp_db):
    temp_db.save_source_annotation(SOURCE_ANNOTATION)
    temp_db.save_source_tag(source_tag())

    temp_db.delete_source_annotation("source-1", "other-document")

    assert len(temp_db.get_source_tags("document-hash")) == 1


def test_delete_source_tag_is_scoped_to_its_document(temp_db):
    temp_db.save_source_tag(source_tag())
    temp_db.save_source_tag(source_tag(id="tag-2"))

    temp_db.delete_source_tag("tag-1", "other-document")
    assert len(temp_db.get_source_tags("document-hash")) == 2

    temp_db.delete_source_tag("tag-1", "document-hash")
    assert [tag.id for tag in temp_db.get_source_tags("document-hash")] == ["tag-2"]


def test_source_tag_needs_decimals_with_its_unit():
    with pytest.raises(ValidationError):
        source_tag(decimals=None)
    with pytest.raises(ValidationError):
        source_tag(unit=None)


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


def test_get_analysis_keeps_chunks_with_matching_model(temp_db):
    file_path = "test_doc.pdf"
    question_id = "tcfd_1"
    base_config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "question_set": "tcfd",
    }
    gpt4_config = {**base_config, "model": "gpt-4o"}
    mini_config = {**base_config, "model": "gpt-4o-mini"}
    chunks = [
        {
            "text": "Shared report chunk",
            "embedding": [0.1, 0.2],
            "chunk_order": 0,
            "similarity_score": 0.8,
            "llm_score": None,
            "metadata": {"page_number": 1},
        }
    ]
    temp_db.save_document_chunks(file_path, chunks, 500, 20)

    temp_db.save_analysis(
        file_path,
        question_id,
        {
            "ANSWER": "Answer with evidence",
            "EVIDENCE": [{"chunk": 1}],
            "chunks": [{**chunks[0], "is_evidence": True, "evidence_order": 1}],
        },
        gpt4_config,
    )
    temp_db.save_analysis(
        file_path,
        question_id,
        {
            "ANSWER": "Answer without evidence",
            "EVIDENCE": [],
            "chunks": [{**chunks[0], "is_evidence": False, "evidence_order": None}],
        },
        mini_config,
    )

    gpt4_result = temp_db.get_analysis(file_path, gpt4_config, [question_id])[question_id]
    mini_result = temp_db.get_analysis(file_path, mini_config, [question_id])[question_id]

    assert gpt4_result["result"]["ANSWER"] == "Answer with evidence"
    assert [chunk["is_evidence"] for chunk in gpt4_result["chunks"]] == [True]
    assert mini_result["result"]["ANSWER"] == "Answer without evidence"
    assert [chunk["is_evidence"] for chunk in mini_result["chunks"]] == [False]


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
    # Test invalid JSON / non-dict result (AttributeError on .get / json.dumps TypeError)
    with pytest.raises(Exception):  # noqa: B017
        temp_db.save_analysis(
            "test.pdf",
            "tcfd_1",
            object(),  # Un-serializable object
            {"chunk_size": 500},
        )

    # Test missing required config params
    with pytest.raises(Exception):  # noqa: B017
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


@pytest.mark.asyncio
async def test_vector_store_reloads_on_chunk_size_change(temp_db):
    """Test that vector store reloads when chunk_size or chunk_overlap changes"""
    import numpy as np

    file_path = "test_doc.pdf"

    # Use consistent embedding dimension for all chunks and query
    embedding_dim = 384  # Common embedding dimension (e.g., sentence-transformers)

    # Create test chunks with chunk_size=500
    chunks_500 = [
        {
            "text": "This is a test chunk for chunk size 500. " * 20,  # Make it long enough
            "embedding": np.random.rand(embedding_dim).astype(np.float32),
            "metadata": {"page": 1, "chunk_size": 500, "chunk_overlap": 20},
        },
        {
            "text": "Another test chunk for chunk size 500. " * 20,
            "embedding": np.random.rand(embedding_dim).astype(np.float32),
            "metadata": {"page": 2, "chunk_size": 500, "chunk_overlap": 20},
        },
    ]

    # Create test chunks with chunk_size=1000 (different chunking)
    chunks_1000 = [
        {
            "text": "This is a test chunk for chunk size 1000. " * 40,  # Different content
            "embedding": np.random.rand(embedding_dim).astype(np.float32),
            "metadata": {"page": 1, "chunk_size": 1000, "chunk_overlap": 20},
        },
        {
            "text": "Another test chunk for chunk size 1000. " * 40,
            "embedding": np.random.rand(embedding_dim).astype(np.float32),
            "metadata": {"page": 2, "chunk_size": 1000, "chunk_overlap": 20},
        },
    ]

    # Save chunks with chunk_size=500
    temp_db.save_vectors(file_path, chunks_500)

    # Get similar chunks with chunk_size=500
    query_embedding = np.random.rand(embedding_dim).astype(np.float32)
    similar_chunks_500 = await temp_db.get_similar_chunks(
        query_embedding=query_embedding,
        file_path=file_path,
        top_k=2,
        chunk_size=500,
        chunk_overlap=20,
    )

    # Verify we got chunks with chunk_size=500
    assert len(similar_chunks_500) > 0
    assert temp_db.current_chunk_size == 500
    assert temp_db.current_chunk_overlap == 20

    # Save chunks with chunk_size=1000
    temp_db.save_vectors(file_path, chunks_1000)

    # Get similar chunks with chunk_size=1000
    # This should trigger a reload of the vector store
    similar_chunks_1000 = await temp_db.get_similar_chunks(
        query_embedding=query_embedding,
        file_path=file_path,
        top_k=2,
        chunk_size=1000,
        chunk_overlap=20,
    )

    # Verify the vector store was reloaded with new chunk_size
    assert temp_db.current_chunk_size == 1000
    assert temp_db.current_chunk_overlap == 20

    # Verify we got different chunks (or at least that the vector store was reloaded)
    # The chunks should be different because we saved different chunks for chunk_size=1000
    assert len(similar_chunks_1000) > 0

    # Test chunk_overlap change
    chunks_diff_overlap = [
        {
            "text": "This is a test chunk with different overlap. " * 20,
            "embedding": np.random.rand(embedding_dim).astype(np.float32),
            "metadata": {
                "page": 1,
                "chunk_size": 1000,
                "chunk_overlap": 50,
            },  # Different overlap
        },
    ]

    temp_db.save_vectors(file_path, chunks_diff_overlap)

    # Get similar chunks with different chunk_overlap
    await temp_db.get_similar_chunks(
        query_embedding=query_embedding,
        file_path=file_path,
        top_k=2,
        chunk_size=1000,
        chunk_overlap=50,  # Different overlap
    )

    # Verify the vector store was reloaded with new chunk_overlap
    assert temp_db.current_chunk_overlap == 50
    assert temp_db.current_chunk_size == 1000
