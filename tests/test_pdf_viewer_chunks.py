"""
Tests for PDF viewer component with chunk loading verification.

This test suite verifies that:
1. Chunks are correctly saved to the database during analysis
2. Chunks are correctly retrieved from the database
3. Chunks are properly formatted and passed to the PDF viewer component
4. The PDF viewer receives the expected chunk data structure
"""

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from sqlalchemy import text

from report_analyst.core.cache_manager import CacheManager


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    original_storage = os.environ.get("STORAGE_PATH")
    test_storage = Path(__file__).parent / "test_storage_pdf_viewer"
    os.environ["STORAGE_PATH"] = str(test_storage)
    yield
    # Cleanup after tests
    if test_storage.exists():
        shutil.rmtree(test_storage)
    # Restore original
    if original_storage:
        os.environ["STORAGE_PATH"] = original_storage
    elif "STORAGE_PATH" in os.environ:
        del os.environ["STORAGE_PATH"]


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_cache.db"
    cache_manager = CacheManager(db_path=str(db_path))
    yield cache_manager
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing"""
    temp_dir = tempfile.mkdtemp()
    pdf_path = Path(temp_dir) / "test_report.pdf"
    # Create a minimal valid PDF
    pdf_content = b"%PDF-1.4\n%Test PDF\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n100\n%%EOF"
    pdf_path.write_bytes(pdf_content)
    yield str(pdf_path)
    import shutil
    shutil.rmtree(temp_dir)


def test_pdf_viewer_chunk_loading(temp_db, sample_pdf_file):
    """
    Test that chunks are correctly loaded from database and passed to PDF viewer.
    
    This test:
    1. Creates chunks in document_chunks table
    2. Saves analysis results with chunk_relevance links
    3. Retrieves chunks via get_analysis
    4. Verifies chunks are in the correct format for PDF viewer
    """
    file_path = sample_pdf_file
    question_id = "tcfd_1"
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4o-mini",
        "question_set": "tcfd",
    }
    
    # Step 1: Create chunks in document_chunks table
    chunk_texts = [
        "This is the first chunk about climate risks.",
        "This is the second chunk about governance.",
        "This is the third chunk about metrics.",
    ]
    
    with temp_db.db_manager.get_connection() as conn:
        timestamp = datetime.now().isoformat()
        chunk_ids = []
        
        for i, chunk_text in enumerate(chunk_texts):
            # Insert chunk (with or without embedding - doesn't matter for PDF viewer)
            embedding_bytes = None  # PDF viewer doesn't need embeddings
            conn.execute(
                text("""
                    INSERT INTO document_chunks
                    (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
                    VALUES (:file_path, :chunk_text, :chunk_size, :chunk_overlap, :embedding, :metadata, :created_at)
                """),
                {
                    "file_path": file_path,
                    "chunk_text": chunk_text,
                    "chunk_size": config["chunk_size"],
                    "chunk_overlap": config["chunk_overlap"],
                    "embedding": embedding_bytes,
                    "metadata": json.dumps({"page_number": i + 1}),
                    "created_at": timestamp,
                },
            )
            # Get the chunk ID
            result = conn.execute(
                text("""
                    SELECT id FROM document_chunks
                    WHERE file_path = :file_path
                    AND chunk_text = :chunk_text
                    AND chunk_size = :chunk_size
                    AND chunk_overlap = :chunk_overlap
                """),
                {
                    "file_path": file_path,
                    "chunk_text": chunk_text,
                    "chunk_size": config["chunk_size"],
                    "chunk_overlap": config["chunk_overlap"],
                },
            )
            row = result.fetchone()
            assert row is not None, f"Chunk {i} was not inserted"
            chunk_ids.append(row[0])
    
    # Step 2: Save analysis result with chunks
    result = {
        "ANSWER": "Test answer about climate risks",
        "SCORE": 7,
        "EVIDENCE": ["evidence1", "evidence2"],
        "GAPS": ["gap1"],
        "chunks": [
            {
                "text": chunk_texts[0],
                "chunk_order": 0,
                "similarity_score": 0.85,
                "llm_score": 0.75,
                "is_evidence": True,
                "evidence_order": 1,
                "metadata": {"page_number": 1},
            },
            {
                "text": chunk_texts[1],
                "chunk_order": 1,
                "similarity_score": 0.80,
                "llm_score": None,
                "is_evidence": False,
                "evidence_order": None,
                "metadata": {"page_number": 2},
            },
            {
                "text": chunk_texts[2],
                "chunk_order": 2,
                "similarity_score": 0.75,
                "llm_score": 0.70,
                "is_evidence": True,
                "evidence_order": 2,
                "metadata": {"page_number": 3},
            },
        ],
    }
    
    temp_db.save_analysis(file_path, question_id, result, config)
    
    # Step 3: Retrieve chunks via get_analysis
    retrieved = temp_db.get_analysis(file_path, config, [question_id])
    
    # Step 4: Verify chunks are retrieved correctly
    assert question_id in retrieved, f"Question {question_id} not in retrieved results"
    assert "chunks" in retrieved[question_id], "Chunks not in retrieved data"
    
    chunks = retrieved[question_id]["chunks"]
    assert len(chunks) == 3, f"Expected 3 chunks, got {len(chunks)}"
    
    # Step 5: Verify chunk structure matches what PDF viewer expects
    expected_fields = ["text", "metadata", "chunk_order", "similarity_score", "is_evidence"]
    for i, chunk in enumerate(chunks):
        for field in expected_fields:
            assert field in chunk, f"Chunk {i} missing field: {field}"
        
        # Verify specific values
        assert chunk["text"] == chunk_texts[i], f"Chunk {i} text mismatch"
        assert chunk["chunk_order"] == i, f"Chunk {i} order mismatch"
        assert chunk["metadata"]["page_number"] == i + 1, f"Chunk {i} page number mismatch"
        assert isinstance(chunk["similarity_score"], (int, float)), f"Chunk {i} similarity_score should be numeric"
        # SQLite stores booleans as integers (0/1), so check for bool or int 0/1
        assert isinstance(chunk["is_evidence"], (bool, int)), f"Chunk {i} is_evidence should be boolean or int"
        if isinstance(chunk["is_evidence"], int):
            assert chunk["is_evidence"] in [0, 1], f"Chunk {i} is_evidence should be 0 or 1 if int"
        # Convert to bool for consistency (SQLite returns 0/1)
        is_evidence_bool = bool(chunk["is_evidence"])
    
    # Step 6: Verify chunks can be formatted for PDF viewer
    chunks_data = {question_id: chunks}
    questions_data = {question_id: "Test question"}
    
    # This is the format expected by pdf_viewer function
    assert len(chunks_data[question_id]) == 3
    assert all("text" in chunk for chunk in chunks_data[question_id])
    assert all("metadata" in chunk for chunk in chunks_data[question_id])
    assert all("is_evidence" in chunk for chunk in chunks_data[question_id])


def test_pdf_viewer_chunk_loading_with_evidence_filter(temp_db, sample_pdf_file):
    """
    Test that chunks are correctly filtered by evidence flag for PDF viewer.
    """
    file_path = sample_pdf_file
    question_id = "tcfd_2"
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4o-mini",
        "question_set": "tcfd",
    }
    
    # Create chunks with mixed evidence flags
    chunk_data = [
        {"text": "Evidence chunk 1", "is_evidence": True, "similarity": 0.9},
        {"text": "Non-evidence chunk", "is_evidence": False, "similarity": 0.6},
        {"text": "Evidence chunk 2", "is_evidence": True, "similarity": 0.85},
    ]
    
    # Save chunks to document_chunks
    with temp_db.db_manager.get_connection() as conn:
        timestamp = datetime.now().isoformat()
        for i, chunk_info in enumerate(chunk_data):
            conn.execute(
                text("""
                    INSERT INTO document_chunks
                    (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
                    VALUES (:file_path, :chunk_text, :chunk_size, :chunk_overlap, :embedding, :metadata, :created_at)
                """),
                {
                    "file_path": file_path,
                    "chunk_text": chunk_info["text"],
                    "chunk_size": config["chunk_size"],
                    "chunk_overlap": config["chunk_overlap"],
                    "embedding": None,
                    "metadata": json.dumps({"page_number": i + 1}),
                    "created_at": timestamp,
                },
            )
    
    # Save analysis with chunks
    result = {
        "ANSWER": "Test answer",
        "SCORE": 8,
        "EVIDENCE": [],
        "GAPS": [],
        "chunks": [
            {
                "text": chunk["text"],
                "chunk_order": i,
                "similarity_score": chunk["similarity"],
                "llm_score": None,
                "is_evidence": chunk["is_evidence"],
                "evidence_order": i + 1 if chunk["is_evidence"] else None,
                "metadata": {"page_number": i + 1},
            }
            for i, chunk in enumerate(chunk_data)
        ],
    }
    
    temp_db.save_analysis(file_path, question_id, result, config)
    
    # Retrieve chunks
    retrieved = temp_db.get_analysis(file_path, config, [question_id])
    chunks = retrieved[question_id]["chunks"]
    
    # Verify all chunks are retrieved
    assert len(chunks) == 3
    
    # Verify evidence flags are correct
    evidence_chunks = [c for c in chunks if c["is_evidence"]]
    non_evidence_chunks = [c for c in chunks if not c["is_evidence"]]
    
    assert len(evidence_chunks) == 2, "Should have 2 evidence chunks"
    assert len(non_evidence_chunks) == 1, "Should have 1 non-evidence chunk"
    
    # Verify chunks can be filtered for PDF viewer (show_evidence_only=True)
    all_chunks = chunks
    evidence_only = [c for c in all_chunks if c.get("is_evidence", False)]
    
    assert len(evidence_only) == 2, "Evidence filter should return 2 chunks"


def test_pdf_viewer_chunk_loading_empty_chunks(temp_db, sample_pdf_file):
    """
    Test that PDF viewer handles empty chunks gracefully.
    """
    file_path = sample_pdf_file
    question_id = "tcfd_3"
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4o-mini",
        "question_set": "tcfd",
    }
    
    # Save analysis with no chunks
    result = {
        "ANSWER": "Test answer without chunks",
        "SCORE": 5,
        "EVIDENCE": [],
        "GAPS": ["No chunks available"],
        "chunks": [],  # Empty chunks
    }
    
    temp_db.save_analysis(file_path, question_id, result, config)
    
    # Retrieve chunks
    retrieved = temp_db.get_analysis(file_path, config, [question_id])
    
    # Verify empty chunks are handled
    assert question_id in retrieved
    chunks = retrieved[question_id].get("chunks", [])
    assert len(chunks) == 0, "Should have 0 chunks"
    
    # Verify PDF viewer format works with empty chunks
    chunks_data = {question_id: chunks}
    questions_data = {question_id: "Test question"}
    
    assert len(chunks_data[question_id]) == 0
    assert chunks_data[question_id] == []


def test_pdf_viewer_chunk_loading_multiple_questions(temp_db, sample_pdf_file):
    """
    Test that chunks are correctly loaded for multiple questions.
    """
    file_path = sample_pdf_file
    question_ids = ["tcfd_1", "tcfd_2"]
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 3,
        "model": "gpt-4o-mini",
        "question_set": "tcfd",
    }
    
    # Create shared chunks
    shared_chunk_texts = [
        "Shared chunk 1",
        "Shared chunk 2",
    ]
    
    # Save chunks to document_chunks
    with temp_db.db_manager.get_connection() as conn:
        timestamp = datetime.now().isoformat()
        for i, chunk_text in enumerate(shared_chunk_texts):
            conn.execute(
                text("""
                    INSERT INTO document_chunks
                    (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
                    VALUES (:file_path, :chunk_text, :chunk_size, :chunk_overlap, :embedding, :metadata, :created_at)
                """),
                {
                    "file_path": file_path,
                    "chunk_text": chunk_text,
                    "chunk_size": config["chunk_size"],
                    "chunk_overlap": config["chunk_overlap"],
                    "embedding": None,
                    "metadata": json.dumps({"page_number": i + 1}),
                    "created_at": timestamp,
                },
            )
    
    # Save analysis for each question with different chunks
    for q_idx, question_id in enumerate(question_ids):
        result = {
            "ANSWER": f"Answer for {question_id}",
            "SCORE": 7,
            "EVIDENCE": [],
            "GAPS": [],
            "chunks": [
                {
                    "text": shared_chunk_texts[i],
                    "chunk_order": i,
                    "similarity_score": 0.8 + (q_idx * 0.05),  # Different scores per question
                    "llm_score": None,
                    "is_evidence": i == 0,  # First chunk is evidence
                    "evidence_order": 1 if i == 0 else None,
                    "metadata": {"page_number": i + 1},
                }
                for i in range(len(shared_chunk_texts))
            ],
        }
        temp_db.save_analysis(file_path, question_id, result, config)
    
    # Retrieve chunks for all questions
    retrieved = temp_db.get_analysis(file_path, config, question_ids)
    
    # Verify both questions have chunks
    assert len(retrieved) == 2, f"Expected 2 questions, got {len(retrieved)}"
    
    for question_id in question_ids:
        assert question_id in retrieved, f"Question {question_id} not in results"
        chunks = retrieved[question_id].get("chunks", [])
        assert len(chunks) == 2, f"Question {question_id} should have 2 chunks"
        
        # Verify chunks are correctly associated with question
        for chunk in chunks:
            assert "text" in chunk
            assert chunk["text"] in shared_chunk_texts
    
    # Verify chunks can be formatted for PDF viewer with multiple questions
    chunks_data = {
        q_id: retrieved[q_id]["chunks"]
        for q_id in question_ids
    }
    questions_data = {q_id: f"Question {q_id}" for q_id in question_ids}
    
    assert len(chunks_data) == 2
    assert all(len(chunks_data[q_id]) == 2 for q_id in question_ids)


def test_pdf_viewer_chunk_metadata_structure(temp_db, sample_pdf_file):
    """
    Test that chunk metadata is correctly structured for PDF viewer.
    """
    file_path = sample_pdf_file
    question_id = "tcfd_4"
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4o-mini",
        "question_set": "tcfd",
    }
    
    # Create chunk with rich metadata
    chunk_text = "Chunk with metadata"
    chunk_metadata = {
        "page_number": 5,
        "section": "Risk Management",
        "subsection": "Climate Risks",
    }
    
    # Save chunk
    with temp_db.db_manager.get_connection() as conn:
        timestamp = datetime.now().isoformat()
        conn.execute(
            text("""
                INSERT INTO document_chunks
                (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
                VALUES (:file_path, :chunk_text, :chunk_size, :chunk_overlap, :embedding, :metadata, :created_at)
            """),
            {
                "file_path": file_path,
                "chunk_text": chunk_text,
                "chunk_size": config["chunk_size"],
                "chunk_overlap": config["chunk_overlap"],
                "embedding": None,
                "metadata": json.dumps(chunk_metadata),
                "created_at": timestamp,
            },
        )
    
    # Save analysis
    result = {
        "ANSWER": "Test answer",
        "SCORE": 7,
        "EVIDENCE": [],
        "GAPS": [],
        "chunks": [
            {
                "text": chunk_text,
                "chunk_order": 0,
                "similarity_score": 0.85,
                "llm_score": 0.75,
                "is_evidence": True,
                "evidence_order": 1,
                "metadata": chunk_metadata,
            }
        ],
    }
    
    temp_db.save_analysis(file_path, question_id, result, config)
    
    # Retrieve chunks
    retrieved = temp_db.get_analysis(file_path, config, [question_id])
    chunks = retrieved[question_id]["chunks"]
    
    # Verify metadata structure
    assert len(chunks) == 1
    chunk = chunks[0]
    
    assert "metadata" in chunk
    assert isinstance(chunk["metadata"], dict)
    assert chunk["metadata"]["page_number"] == 5
    assert chunk["metadata"]["section"] == "Risk Management"
    assert chunk["metadata"]["subsection"] == "Climate Risks"
    
    # Verify metadata is suitable for PDF viewer (page_number is key for highlighting)
    assert "page_number" in chunk["metadata"], "PDF viewer needs page_number for highlighting"


def test_pdf_viewer_function_chunk_formatting(temp_db, sample_pdf_file):
    """
    Test that chunks retrieved from database are correctly formatted for PDF viewer function.
    
    This test verifies the integration between cache_manager.get_analysis and pdf_viewer function.
    """
    file_path = sample_pdf_file
    question_id = "tcfd_5"
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4o-mini",
        "question_set": "tcfd",
    }
    
    # Create and save chunks with analysis
    chunk_texts = [
        "First chunk with page 1",
        "Second chunk with page 2",
    ]
    
    # Save chunks to document_chunks
    with temp_db.db_manager.get_connection() as conn:
        timestamp = datetime.now().isoformat()
        for i, chunk_text in enumerate(chunk_texts):
            conn.execute(
                text("""
                    INSERT INTO document_chunks
                    (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
                    VALUES (:file_path, :chunk_text, :chunk_size, :chunk_overlap, :embedding, :metadata, :created_at)
                """),
                {
                    "file_path": file_path,
                    "chunk_text": chunk_text,
                    "chunk_size": config["chunk_size"],
                    "chunk_overlap": config["chunk_overlap"],
                    "embedding": None,
                    "metadata": json.dumps({"page_number": i + 1}),
                    "created_at": timestamp,
                },
            )
    
    # Save analysis with chunks
    result = {
        "ANSWER": "Test answer",
        "SCORE": 7,
        "EVIDENCE": [],
        "GAPS": [],
        "chunks": [
            {
                "text": chunk_texts[i],
                "chunk_order": i,
                "similarity_score": 0.8 + (i * 0.05),
                "llm_score": 0.7 if i == 0 else None,
                "is_evidence": i == 0,
                "evidence_order": 1 if i == 0 else None,
                "metadata": {"page_number": i + 1},
            }
            for i in range(len(chunk_texts))
        ],
    }
    
    temp_db.save_analysis(file_path, question_id, result, config)
    
    # Retrieve chunks (simulating what streamlit_app.py does)
    cached_results = temp_db.get_analysis(file_path, config, [question_id])
    
    # Format chunks for PDF viewer (simulating streamlit_app.py logic)
    chunks_by_question = {}
    questions_data = {}
    
    for q_id, data in cached_results.items():
        chunks = data.get("chunks", [])
        chunks_by_question[q_id] = chunks
        questions_data[q_id] = "Test question text"
    
    # Verify chunks are in the correct format for pdf_viewer function
    assert question_id in chunks_by_question
    chunks = chunks_by_question[question_id]
    
    # Verify chunk structure matches pdf_viewer expectations
    assert len(chunks) == 2
    
    for chunk in chunks:
        # Required fields for PDF viewer
        assert "text" in chunk, "PDF viewer needs chunk text"
        assert "metadata" in chunk, "PDF viewer needs chunk metadata"
        assert "is_evidence" in chunk, "PDF viewer needs is_evidence flag"
        assert "similarity_score" in chunk, "PDF viewer needs similarity_score"
        
        # Metadata should have page_number for highlighting
        assert "page_number" in chunk["metadata"], "PDF viewer needs page_number in metadata"
        assert isinstance(chunk["metadata"]["page_number"], int), "page_number should be int"
        
        # Verify chunk can be JSON serialized (pdf_viewer uses json.dumps)
        try:
            json_str = json.dumps(chunk)
            assert len(json_str) > 0
        except (TypeError, ValueError) as e:
            pytest.fail(f"Chunk not JSON serializable: {e}")
    
    # Verify chunks_by_question structure is correct for pdf_viewer
    assert isinstance(chunks_by_question, dict)
    assert all(isinstance(chunks, list) for chunks in chunks_by_question.values())
    assert all(isinstance(chunk, dict) for chunks in chunks_by_question.values() for chunk in chunks)
    
    # Verify questions_data structure
    assert isinstance(questions_data, dict)
    assert all(isinstance(q_text, str) for q_text in questions_data.values())
    
    # This is the exact format that pdf_viewer expects:
    # pdf_viewer(
    #     pdf_path=file_path,
    #     chunks_data=chunks_by_question,  # Dict[str, List[Dict]]
    #     questions_data=questions_data,    # Dict[str, str]
    #     ...
    # )
    # The test verifies this structure is correct


def test_pdf_viewer_receives_chunks_correctly(temp_db, sample_pdf_file):
    """
    Test that PDF viewer function receives chunks in the correct format.
    
    This test mocks the PDF viewer component and verifies it receives
    the correct chunk data structure.
    """
    file_path = sample_pdf_file
    question_id = "tcfd_6"
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 3,
        "model": "gpt-4o-mini",
        "question_set": "tcfd",
    }
    
    # Create and save chunks
    chunk_data = [
        {"text": "Chunk 1", "page": 1, "is_evidence": True, "similarity": 0.9},
        {"text": "Chunk 2", "page": 2, "is_evidence": False, "similarity": 0.7},
    ]
    
    with temp_db.db_manager.get_connection() as conn:
        timestamp = datetime.now().isoformat()
        for i, chunk_info in enumerate(chunk_data):
            conn.execute(
                text("""
                    INSERT INTO document_chunks
                    (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
                    VALUES (:file_path, :chunk_text, :chunk_size, :chunk_overlap, :embedding, :metadata, :created_at)
                """),
                {
                    "file_path": file_path,
                    "chunk_text": chunk_info["text"],
                    "chunk_size": config["chunk_size"],
                    "chunk_overlap": config["chunk_overlap"],
                    "embedding": None,
                    "metadata": json.dumps({"page_number": chunk_info["page"]}),
                    "created_at": timestamp,
                },
            )
    
    # Save analysis
    result = {
        "ANSWER": "Test answer",
        "SCORE": 8,
        "EVIDENCE": [],
        "GAPS": [],
        "chunks": [
            {
                "text": chunk["text"],
                "chunk_order": i,
                "similarity_score": chunk["similarity"],
                "llm_score": None,
                "is_evidence": chunk["is_evidence"],
                "evidence_order": 1 if chunk["is_evidence"] else None,
                "metadata": {"page_number": chunk["page"]},
            }
            for i, chunk in enumerate(chunk_data)
        ],
    }
    
    temp_db.save_analysis(file_path, question_id, result, config)
    
    # Retrieve chunks (as streamlit_app.py does)
    cached_results = temp_db.get_analysis(file_path, config, [question_id])
    
    # Format for PDF viewer (as streamlit_app.py does)
    chunks_by_question = {}
    questions_data = {}
    
    for q_id, data in cached_results.items():
        chunks_by_question[q_id] = data.get("chunks", [])
        questions_data[q_id] = "Test question"
    
    # Mock the PDF viewer component
    with patch('report_analyst_enterprise.components.streamlit_component.backend.pdf_viewer.components') as mock_components:
        mock_component = MagicMock()
        mock_components.declare_component.return_value = mock_component
        mock_component.return_value = None  # No return value from component
        
        # Import and call pdf_viewer
        from report_analyst_enterprise.components.streamlit_component.backend.pdf_viewer import pdf_viewer
        
        result = pdf_viewer(
            pdf_path=file_path,
            chunks_data=chunks_by_question,
            questions_data=questions_data,
            height=800,
            key="test_pdf_viewer"
        )
        
        # Verify component was called
        assert mock_components.declare_component.called, "PDF viewer component should be declared"
        assert mock_component.called, "PDF viewer component should be called"
        
        # Get the call arguments
        call_args = mock_component.call_args
        assert call_args is not None, "Component should be called with arguments"
        
        # Verify chunks were passed
        call_kwargs = call_args.kwargs
        assert "chunks" in call_kwargs, "Component should receive chunks parameter"
        
        # Parse chunks JSON
        chunks_json = call_kwargs["chunks"]
        assert isinstance(chunks_json, str), "Chunks should be JSON string"
        chunks_list = json.loads(chunks_json)
        
        # Verify chunks structure
        assert len(chunks_list) == 2, f"Should have 2 chunks, got {len(chunks_list)}"
        
        for chunk in chunks_list:
            assert "text" in chunk
            assert "question_id" in chunk, "Chunk should have question_id for filtering"
            assert chunk["question_id"] == question_id
            assert "metadata" in chunk
            assert "page_number" in chunk["metadata"]
            assert "is_evidence" in chunk
            assert "similarity_score" in chunk
        
        # Verify questions were passed
        assert "questions" in call_kwargs, "Component should receive questions parameter"
        questions_json = call_kwargs["questions"]
        questions_list = json.loads(questions_json)
        
        assert len(questions_list) == 1
        assert questions_list[0]["question_id"] == question_id
        assert "chunks" in questions_list[0]
        assert len(questions_list[0]["chunks"]) == 2

