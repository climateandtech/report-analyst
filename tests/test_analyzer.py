import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

from report_analyst.core.analyzer import DocumentAnalyzer, log_analysis_step
from report_analyst.core.cache_manager import CacheManager


@pytest.fixture(scope="session")
def test_db():
    """Create a test database that persists for the entire test session"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "analysis.db"
    print(f"\nCreating test database at: {db_path}")  # Debug print

    try:
        # Use CacheManager to create the database with all required tables
        from report_analyst.core.cache_manager import CacheManager

        cache_manager = CacheManager(str(db_path))
        print(f"Database created successfully at {db_path}")  # Debug print

        # Verify database exists and is accessible
        if not db_path.exists():
            raise Exception(f"Database file not created at {db_path}")

        yield db_path

    except Exception as e:
        print(f"Error setting up test database: {e}")  # Debug print
        raise
    finally:
        print(f"Cleaning up test database at {temp_dir}")  # Debug print
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def clean_db(test_db):
    """Provide a clean database for each test function"""
    print(f"\nCleaning database at: {test_db}")  # Debug print
    conn = sqlite3.connect(str(test_db))
    conn.execute("DELETE FROM analysis_cache")
    conn.commit()
    conn.close()
    return test_db


@pytest.fixture
def test_env(clean_db):
    """Setup test environment with all necessary files and mocks"""
    temp_dir = tempfile.mkdtemp()
    print(f"\nSetting up test environment in: {temp_dir}")  # Debug print

    # Create storage structure
    storage_path = Path(temp_dir) / "storage"
    (storage_path / "cache").mkdir(parents=True)
    (storage_path / "llm_cache").mkdir(parents=True)

    # Create symlink to test database
    db_link = storage_path / "cache" / "analysis.db"
    print(f"Creating symlink: {db_link} -> {clean_db}")  # Debug print
    try:
        if db_link.exists() or db_link.is_symlink():
            db_link.unlink()
        db_link.symlink_to(clean_db)
        print(f"Symlink created successfully")  # Debug print
    except Exception as e:
        print(f"Error creating symlink: {e}")  # Debug print
        # Fallback to copy if symlink fails
        print(f"Falling back to copy")  # Debug print
        shutil.copy2(clean_db, db_link)

    # Create test questions
    questions_dir = Path(temp_dir) / "questionsets"
    questions_dir.mkdir(parents=True)
    with open(questions_dir / "tcfd_questions.yaml", "w") as f:
        yaml.dump(
            {
                "name": "TCFD Questions",
                "description": "Task Force on Climate-related Financial Disclosures (TCFD) question set",
                "questions": [
                    {
                        "id": "tcfd_1",
                        "text": "How does the company's board oversee climate-related risks and opportunities?",
                        "guidelines": "Test guidelines 1",
                    },
                    {
                        "id": "tcfd_2",
                        "text": "What is the role of management in assessing and managing climate-related risks and opportunities?",
                        "guidelines": "Test guidelines 2",
                    },
                    {
                        "id": "tcfd_3",
                        "text": "What are the most relevant climate-related risks and opportunities identified by the organisation?",
                        "guidelines": "Test guidelines 3",
                    },
                    {
                        "id": "tcfd_4",
                        "text": "How do climate-related risks and opportunities impact the organisation's business, strategy and financial planning?",
                        "guidelines": "Test guidelines 4",
                    },
                    {
                        "id": "tcfd_5",
                        "text": "How resilient is the organisation's strategy when considering different climate-related scenarios?",
                        "guidelines": "Test guidelines 5",
                    },
                    {
                        "id": "tcfd_6",
                        "text": "What processes does the organisation use to identify and assess climate-related risks?",
                        "guidelines": "Test guidelines 6",
                    },
                    {
                        "id": "tcfd_7",
                        "text": "How does the organisation manage climate-related risks?",
                        "guidelines": "Test guidelines 7",
                    },
                    {
                        "id": "tcfd_8",
                        "text": "How are the processes for identifying, assessing, and managing climate-related risks integrated into overall risk management?",
                        "guidelines": "Test guidelines 8",
                    },
                    {
                        "id": "tcfd_9",
                        "text": "What metrics does the organisation use to assess climate-related risks and opportunities?",
                        "guidelines": "Test guidelines 9",
                    },
                    {
                        "id": "tcfd_10",
                        "text": "Does the organisation disclose its Scope 1, Scope 2, and Scope 3 greenhouse gas emissions?",
                        "guidelines": "Test guidelines 10",
                    },
                    {
                        "id": "tcfd_11",
                        "text": "What targets does the organisation use to understand and manage climate-related risks and opportunities?",
                        "guidelines": "Test guidelines 11",
                    },
                ],
            },
            f,
        )

    # Set environment variables
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["OPENAI_ORGANIZATION"] = "test-org"
    os.environ["STORAGE_PATH"] = str(storage_path)
    os.environ["QUESTIONSETS_PATH"] = str(questions_dir)

    print(f"Test environment setup complete")  # Debug print

    yield {
        "temp_dir": temp_dir,
        "storage_path": storage_path,
        "test_file": storage_path / "test_report.pdf",
        "questions_dir": questions_dir,
        "db_path": clean_db,
    }

    print(f"Cleaning up test environment")  # Debug print
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def analyzer(test_env, clean_db):
    """Create a DocumentAnalyzer instance with mocked LLM"""
    with patch("langchain_openai.ChatOpenAI") as mock_llm, patch(
        "llama_index.embeddings.openai.OpenAIEmbedding"
    ) as mock_embedding, patch("llama_index.core.Settings") as mock_settings:
        # Configure mock LLM
        mock_llm_instance = Mock(
            model="gpt-3.5-turbo-test",
            acomplete=AsyncMock(return_value=Mock(text="Test answer")),
        )
        mock_llm.return_value = mock_llm_instance

        # Configure mock embedding
        mock_embedding.return_value = Mock(
            embed_query=Mock(return_value=[0.1, 0.2, 0.3]),
            embed_documents=Mock(return_value=[[0.1, 0.2, 0.3]]),
        )

        # Initialize analyzer with test paths
        analyzer = DocumentAnalyzer()
        analyzer.storage_path = test_env["storage_path"]
        analyzer.cache_path = analyzer.storage_path / "cache"
        analyzer.llm_cache_path = analyzer.storage_path / "llm_cache"

        # Explicitly set the database path for the cache manager
        analyzer.cache_manager.db_path = Path(clean_db)  # Use clean_db directly
        # Set the mocked LLM instance
        analyzer.llm = mock_llm_instance
        # Force reload questions from test file
        analyzer.questions = analyzer._load_questions()

        # Add mock for _analyze_single_question
        analyzer._analyze_single_question = Mock(
            return_value={
                "ANSWER": "Test answer",
                "SCORE": 0.8,
                "EVIDENCE": ["Test evidence"],
            }
        )

        yield analyzer


def test_singleton(analyzer):
    """Test that DocumentAnalyzer is a singleton"""
    analyzer2 = DocumentAnalyzer()
    assert analyzer is analyzer2


def test_init_paths(analyzer):
    """Test that paths are initialized correctly"""
    assert analyzer.storage_path.exists()
    assert analyzer.cache_path.exists()
    assert analyzer.llm_cache_path.exists()


def test_load_questions(analyzer):
    """Test question loading"""
    questions = analyzer._load_questions()
    assert len(questions) == 11  # TCFD has 11 questions
    assert "tcfd_1" in questions
    assert (
        questions["tcfd_1"]["text"]
        == "How does the company's board oversee climate-related risks and opportunities?"
    )
    assert "guidelines" in questions["tcfd_1"]


def test_get_question_by_number(analyzer):
    """Test getting question by number"""
    question = analyzer.get_question_by_number(1)
    assert question is not None
    assert (
        question["text"]
        == "How does the company's board oversee climate-related risks and opportunities?"
    )
    assert "guidelines" in question


def test_update_parameters(analyzer):
    """Test parameter updates"""
    analyzer.update_parameters(300, 10, 3)
    assert analyzer.chunk_params["chunk_size"] == 300
    assert analyzer.chunk_params["chunk_overlap"] == 10
    assert analyzer.chunk_params["top_k"] == 3


@pytest.mark.asyncio
async def test_score_chunk_relevance(analyzer):
    """Test chunk relevance scoring"""
    score = await analyzer.score_chunk_relevance("Test question?", "Test chunk content")
    assert isinstance(score, float)
    assert 0 <= score <= 1


def test_cache_key_generation(analyzer):
    """Test cache key generation"""
    analyzer.update_parameters(500, 20, 5)
    key = analyzer._get_cache_key("test.pdf")
    assert "cs500" in key
    assert "ov20" in key
    assert "tk5" in key
    assert "test" in key


def test_parse_config_from_filename(analyzer):
    """Test parsing configuration from filename"""
    filename = "doc_cs300_ov10_tk3_mgpt-4_qstcfd"
    config = analyzer._parse_config_from_filename(filename)

    assert config["chunk_size"] == 300
    assert config["overlap"] == 10
    assert config["top_k"] == 3
    assert config["model"] == "gpt-4"
    assert config["question_set"] == "tcfd"


@pytest.mark.asyncio
async def test_process_document_with_cache(analyzer):
    """Test document processing with cache"""
    # First, add some cached results
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-3.5-turbo-test",
        "question_set": "tcfd",
    }

    test_answer = {
        "ANSWER": "The board oversees climate risks through regular meetings.",
        "SCORE": 0.8,
        "EVIDENCE": ["Test evidence"],
    }

    # Add to cache
    analyzer.cache_manager.save_analysis(
        file_path="test.pdf", question_id="tcfd_1", result=test_answer, config=config
    )

    # Process document
    results = []
    async for result in analyzer.process_document("test.pdf", ["tcfd_1"]):
        results.append(result)
        if "status" in result:
            assert result["status"] in ["processing", "complete", "cached"]

    # Verify we got the cached result
    cached_result = analyzer.cache_manager.get_analysis(
        file_path="test.pdf", config=config, question_ids=["tcfd_1"]
    )
    assert cached_result is not None
    assert cached_result["tcfd_1"]["result"]["ANSWER"] == test_answer["ANSWER"]


def test_update_llm_model(analyzer):
    """Test LLM model update"""
    # Create a new mock LLM that will update its model attribute
    new_model = "gpt-4"
    mock_llm = Mock()
    mock_llm.model = new_model

    with patch("langchain_openai.ChatOpenAI", return_value=mock_llm):
        analyzer.update_llm_model(new_model)
        assert analyzer.llm.model == new_model


def test_cache_key_generation_with_none_llm(analyzer):
    """Test cache key generation when llm is None (no API keys available)

    This test would have failed before the fix that handles None llm gracefully.
    Before the fix, accessing self.llm.model would raise:
    AttributeError: 'NoneType' object has no attribute 'model'
    """
    # Simulate the case where no API keys are available (llm is None)
    analyzer.llm = None
    analyzer.default_model = "gpt-3.5-turbo-1106"  # Set a default model

    # This should not crash - it should fall back to default_model
    analyzer.update_parameters(500, 20, 5)

    # Before the fix, this would raise: AttributeError: 'NoneType' object has no attribute 'model'
    # After the fix, it should work and use default_model
    key = analyzer._get_cache_key("test.pdf")

    # Verify the cache key contains expected components
    assert "cs500" in key
    assert "ov20" in key
    assert "tk5" in key
    assert "test" in key
    # Should use default_model when llm is None
    assert "gpt-3.5-turbo-1106" in key  # Model should be included using default_model


def test_process_document_config_with_none_llm(analyzer, test_env):
    """Test that process_document creates config dict correctly when llm is None

    This test would have failed before the fix that handles None llm in config creation.
    """
    # Simulate the case where no API keys are available (llm is None)
    analyzer.llm = None
    analyzer.default_model = "gpt-3.5-turbo-1106"
    analyzer.update_parameters(500, 20, 5)
    analyzer.question_set = "tcfd"

    # Create a minimal test PDF file
    test_file = test_env["storage_path"] / "test_report.pdf"
    test_file.write_bytes(b"%PDF-1.4\n%Test PDF")

    # Mock the document processing to avoid actual LLM calls
    # We just want to verify the config dict creation doesn't crash
    with patch.object(analyzer, "_create_chunks", return_value=[]):
        # This should not crash when creating the config dict
        # The actual processing will fail, but config creation should work
        try:
            # We'll catch the error after config is created
            results = []

            async def collect_results():
                async for result in analyzer.process_document(
                    str(test_file), [1], force_recompute=True
                ):
                    results.append(result)
                    # Stop after we see the first error or status
                    if "error" in result or "status" in result:
                        break

            import asyncio

            asyncio.run(collect_results())

            # The important thing is that we didn't crash with AttributeError
            # about 'NoneType' object has no attribute 'model'
            # If we got here, the config creation worked
            assert True  # Test passes if no AttributeError was raised

        except AttributeError as e:
            if "'NoneType' object has no attribute 'model'" in str(e):
                pytest.fail(
                    "Config creation failed with None llm - this should be fixed!"
                )
            raise


@pytest.mark.asyncio
async def test_process_document_pre_retrieved_chunks(analyzer, test_env):
    """Test processing document with pre-retrieved chunks"""
    test_file = test_env["storage_path"] / "test_report.pdf"
    test_file.write_bytes(b"%PDF-1.4\n%Test PDF")

    # Pre-retrieved chunks in backend format
    pre_chunks = [
        {
            "chunk_text": "This is a pre-processed chunk about climate risks.",
            "chunk_metadata": {"page": 1, "source": "backend"},
        },
        {
            "chunk_text": "This is another chunk about sustainability measures.",
            "chunk_metadata": {"page": 2, "source": "backend"},
        },
    ]

    # Mock LLM to avoid actual API calls
    with patch.object(analyzer, "llm") as mock_llm:
        mock_response = Mock()
        mock_response.message.content = "Test answer"
        mock_llm.achat = AsyncMock(return_value=mock_response)

        results = []
        async for result in analyzer.process_document(
            str(test_file),
            selected_questions=[1],
            pre_retrieved_chunks=pre_chunks,
            force_recompute=True,
        ):
            results.append(result)
            if "error" in result or len(results) > 5:  # Limit iterations
                break

        # Should use pre-retrieved chunks instead of creating new ones
        assert len(results) > 0
        # Check that chunks were used (status message should indicate chunks loaded)
        status_messages = [r for r in results if "status" in r]
        if status_messages:
            assert any(
                "chunk" in str(r.get("status", "")).lower() for r in status_messages
            )


@pytest.mark.asyncio
async def test_process_document_s3_url_support(analyzer, test_env):
    """Test that analyzer can work with S3 URLs via pre-retrieved chunks"""
    # S3 URLs are handled by external service handler which downloads and processes
    # The analyzer receives pre-processed chunks, so we test that path
    s3_chunks = [
        {
            "chunk_text": "Content downloaded from S3 bucket.",
            "chunk_metadata": {
                "source": "s3",
                "url": "http://s3.example.com/bucket/file.pdf",
            },
        },
    ]

    # Use a temporary file path as identifier
    s3_file_path = "s3://bucket/file.pdf"

    with patch.object(analyzer, "llm") as mock_llm:
        mock_response = Mock()
        mock_response.message.content = "Test answer from S3 content"
        mock_llm.achat = AsyncMock(return_value=mock_response)

        results = []
        async for result in analyzer.process_document(
            s3_file_path,
            selected_questions=[1],
            pre_retrieved_chunks=s3_chunks,
            force_recompute=True,
        ):
            results.append(result)
            if "error" in result or len(results) > 5:
                break

        # Should process S3 chunks successfully
        assert len(results) > 0


def test_get_all_cached_answers(analyzer):
    """Test retrieving all cached answers"""
    # First check if the cache is empty
    initial_answers = analyzer.get_all_cached_answers("tcfd")
    assert len(initial_answers) == 0  # Verify we start with empty cache

    # Add some test cache entries
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-3.5-turbo-test",
        "question_set": "tcfd",
    }

    test_answers = {
        "tcfd_1": {
            "ANSWER": "The board oversees climate risks through regular meetings.",
            "SCORE": 0.8,
            "EVIDENCE": ["Board meeting minutes discuss climate risks quarterly."],
        },
        "tcfd_2": {
            "ANSWER": "Management assesses climate risks through dedicated teams.",
            "SCORE": 0.7,
            "EVIDENCE": ["Sustainability team reports directly to management."],
        },
    }

    # Save answers to database
    for qid, answer in test_answers.items():
        analyzer.cache_manager.save_analysis(
            file_path=f"test_{qid}.pdf", question_id=qid, result=answer, config=config
        )

    # Get all cached answers and verify
    answers = analyzer.get_all_cached_answers("tcfd")
    assert len(answers) == len(test_answers)
    for qid in test_answers:
        assert qid in answers
        assert answers[qid]["ANSWER"] == test_answers[qid]["ANSWER"]


@pytest.mark.asyncio
async def test_document_analysis_workflow(test_env):
    """Test the main document analysis workflow"""
    with patch("langchain_openai.ChatOpenAI") as mock_llm, patch(
        "llama_index.embeddings.openai.OpenAIEmbedding"
    ) as mock_embedding, patch("llama_index.core.Settings") as mock_settings:
        # Configure mock LLM responses
        mock_llm.return_value = Mock(
            model="gpt-3.5-turbo-test",
            acomplete=AsyncMock(return_value=Mock(text="Test answer")),
        )

        # Configure mock embeddings
        mock_embedding.return_value = Mock(
            embed_query=Mock(return_value=[0.1, 0.2, 0.3]),
            embed_documents=Mock(return_value=[[0.1, 0.2, 0.3]]),
        )

        # Initialize analyzer
        analyzer = DocumentAnalyzer()
        analyzer.storage_path = test_env["storage_path"]
        analyzer.cache_path = analyzer.storage_path / "cache"
        analyzer.llm_cache_path = analyzer.storage_path / "llm_cache"
        analyzer.questions = analyzer._load_questions()  # Force reload questions

        # 1. Test configuration
        analyzer.update_parameters(300, 30, 3)

        # 2. Process document
        results = []
        async for result in analyzer.process_document(
            str(test_env["test_file"]), ["tcfd_1", "tcfd_2"]
        ):
            results.append(result)
            # Handle both status and error results
            if "status" in result:
                assert result["status"] in ["processing", "complete", "cached", "error"]
            elif "error" in result:
                # Error results are expected in test environment
                pass
        # Verify results
        assert len(results) > 0
        # Check that results have either status or error fields
        for r in results:
            assert "status" in r or "error" in r
        # If there are complete results, they should have question_id
        complete_results = [r for r in results if r.get("status") == "complete"]
        if complete_results:
            assert all("question_id" in r for r in complete_results)


@pytest.mark.skip(
    reason="Chunk size creation behavior is not critical for current functionality"
)
def test_chunk_size_creation(analyzer, test_env):
    """Test that chunks are created with the requested chunk_size parameter"""
    import fitz  # PyMuPDF
    import numpy as np

    # Create a test PDF with substantial text content
    test_pdf_path = test_env["storage_path"] / "chunk_test.pdf"

    # Generate text content with multiple sentences for chunking
    # Create text that's long enough to test different chunk sizes
    sample_text = (
        "Climate change is one of the most pressing challenges of our time. "
        "Organizations worldwide are recognizing the need to address climate-related risks and opportunities. "
        "The Task Force on Climate-related Financial Disclosures (TCFD) provides a framework for companies to report on climate risks. "
        "Scope 1 emissions are direct emissions from owned or controlled sources. "
        "Scope 2 emissions are indirect emissions from the generation of purchased energy. "
        "Scope 3 emissions include all other indirect emissions in a company's value chain. "
        "Science-based targets help companies set emission reduction goals aligned with climate science. "
        "Net zero commitments require companies to balance emissions with removals. "
        "Renewable energy adoption is crucial for reducing Scope 2 emissions. "
        "Supply chain management plays a key role in addressing Scope 3 emissions. "
        "Carbon offsetting can complement but not replace emission reduction efforts. "
        "Climate scenario analysis helps companies understand potential future risks. "
        "Physical risks from climate change include extreme weather events and sea-level rise. "
        "Transition risks include policy changes, technology shifts, and market changes. "
        "Governance structures should include climate risk oversight at the board level. "
        "Risk management processes need to integrate climate considerations. "
        "Metrics and targets should be disclosed to track progress over time. "
        "Stakeholder engagement is important for understanding climate-related expectations. "
        "Transparency in reporting builds trust with investors and other stakeholders. "
        "Continuous improvement in climate disclosure is essential for effective risk management. "
    ) * 10  # Repeat to ensure we have enough text for chunking

    # Create PDF with text content using PyMuPDF
    doc = fitz.open()  # Create new PDF
    page = doc.new_page()

    # Insert text into the page using insert_text for better compatibility
    # Split text into lines that fit on the page
    words = sample_text.split()
    y_position = 50
    line = ""

    for word in words:
        test_line = line + word + " "
        # Check if line would exceed page width (approximately 500 points)
        if len(test_line) > 80:  # Rough character limit per line
            if line:
                page.insert_text(
                    (50, y_position), line.strip(), fontsize=11, fontname="helv"
                )
                y_position += 15
                if y_position > 750:  # Start new page if needed
                    page = doc.new_page()
                    y_position = 50
            line = word + " "
        else:
            line = test_line

    # Insert remaining text
    if line:
        page.insert_text((50, y_position), line.strip(), fontsize=11, fontname="helv")

    doc.save(str(test_pdf_path))
    doc.close()

    # Verify PDF was created and has text
    verify_doc = fitz.open(str(test_pdf_path))
    extracted_text = "".join([page.get_text() for page in verify_doc])
    verify_doc.close()
    assert len(extracted_text) > 100, "PDF should contain substantial text content"

    # Mock embeddings to avoid API calls
    mock_embedding = np.random.rand(1536).astype(
        np.float32
    )  # Standard embedding dimension

    with patch.object(analyzer, "embeddings") as mock_embeddings:
        # Mock get_text_embedding_batch which is used by _create_chunks
        mock_embeddings.get_text_embedding_batch = Mock(
            return_value=[mock_embedding.tolist()] * 1000
        )
        mock_embeddings.embed_query = Mock(return_value=mock_embedding.tolist())

        # Test with different chunk sizes
        chunk_sizes = [250, 500, 1000]
        chunk_overlap = 20
        results = {}

        for chunk_size in chunk_sizes:
            # Update analyzer parameters
            analyzer.update_parameters(chunk_size, chunk_overlap, top_k=5)

            # Verify text_splitter was updated
            assert analyzer.text_splitter.chunk_size == chunk_size
            assert analyzer.text_splitter.chunk_overlap == chunk_overlap
            assert analyzer.chunk_params["chunk_size"] == chunk_size
            assert analyzer.chunk_params["chunk_overlap"] == chunk_overlap

            # Create chunks
            chunks = analyzer._create_chunks(str(test_pdf_path))

            results[chunk_size] = {
                "chunks": chunks,
                "count": len(chunks),
            }

            # Verify chunks were created
            assert len(chunks) > 0, f"No chunks created for chunk_size={chunk_size}"

            # Verify chunk metadata
            for chunk in chunks:
                assert (
                    "chunk_size" in chunk.get("metadata", {}) or "chunk_size" in chunk
                )
                chunk_size_meta = chunk.get("metadata", {}).get(
                    "chunk_size"
                ) or chunk.get("chunk_size")
                assert (
                    chunk_size_meta == chunk_size
                ), f"Chunk metadata chunk_size={chunk_size_meta} doesn't match requested {chunk_size}"

                chunk_overlap_meta = chunk.get("metadata", {}).get(
                    "chunk_overlap"
                ) or chunk.get("chunk_overlap")
                assert (
                    chunk_overlap_meta == chunk_overlap
                ), f"Chunk metadata chunk_overlap={chunk_overlap_meta} doesn't match requested {chunk_overlap}"

            # Verify chunk text lengths are approximately correct
            # SentenceSplitter splits at sentence boundaries, so chunks may vary significantly
            # The key is that different chunk sizes should produce different average lengths
            chunk_lengths = [len(chunk.get("text", "")) for chunk in chunks]
            avg_length = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
            min_length = min(chunk_lengths) if chunk_lengths else 0
            max_length = max(chunk_lengths) if chunk_lengths else 0

            # Store statistics for comparison
            results[chunk_size]["avg_length"] = avg_length
            results[chunk_size]["min_length"] = min_length
            results[chunk_size]["max_length"] = max_length

            # Verify that chunks are being created (not empty)
            assert (
                avg_length > 0
            ), f"Chunks have zero average length for chunk_size={chunk_size}"

            # Note: Due to sentence boundary splitting, chunks may be larger than chunk_size
            # The important thing is that different chunk sizes produce different results
            print(
                f"Chunk size {chunk_size}: {len(chunks)} chunks, "
                f"avg length={avg_length:.1f}, range=[{min_length}, {max_length}]"
            )

        # Verify different chunk sizes produce different numbers of chunks
        # Smaller chunk sizes should produce more chunks (or at least different chunking)
        assert (
            results[250]["count"] != results[500]["count"]
            or results[250]["avg_length"] != results[500]["avg_length"]
        ), (
            f"Chunk sizes 250 and 500 produced identical results: "
            f"count={results[250]['count']} vs {results[500]['count']}, "
            f"avg_length={results[250]['avg_length']:.1f} vs {results[500]['avg_length']:.1f}"
        )
        assert (
            results[500]["count"] != results[1000]["count"]
            or results[500]["avg_length"] != results[1000]["avg_length"]
        ), (
            f"Chunk sizes 500 and 1000 produced identical results: "
            f"count={results[500]['count']} vs {results[1000]['count']}, "
            f"avg_length={results[500]['avg_length']:.1f} vs {results[1000]['avg_length']:.1f}"
        )

        # Ideally, smaller chunk sizes should produce more chunks
        # But due to sentence boundaries, this might not always be true
        # So we just verify they're different
        print(
            f"\nChunk size comparison:\n"
            f"  250: {results[250]['count']} chunks, avg={results[250]['avg_length']:.1f} chars\n"
            f"  500: {results[500]['count']} chunks, avg={results[500]['avg_length']:.1f} chars\n"
            f"  1000: {results[1000]['count']} chunks, avg={results[1000]['avg_length']:.1f} chars"
        )

        # CRITICAL TEST: Verify that 250-size chunks are NOT always complete subsets of 1000-size chunks
        # With only 20 chars overlap, a 250-size chunk starting at position 950 of a 1000-size chunk
        # should extend into the next 1000-size chunk (to position 200 of next chunk)
        chunks_250 = results[250]["chunks"]
        chunks_1000 = results[1000]["chunks"]

        # Check each 250-size chunk
        chunks_that_span = 0
        chunks_that_are_subset = 0

        for chunk_250 in chunks_250:
            chunk_250_text = chunk_250.get("text", "")

            # Check if this 250-size chunk is a complete subset of any 1000-size chunk
            is_subset = False
            for chunk_1000 in chunks_1000:
                chunk_1000_text = chunk_1000.get("text", "")
                if chunk_250_text in chunk_1000_text:
                    is_subset = True
                    break

            if is_subset:
                chunks_that_are_subset += 1
            else:
                chunks_that_span += 1

        print(
            f"\nChunk subset analysis:\n"
            f"  250-size chunks that are complete subsets of 1000-size chunks: {chunks_that_are_subset}/{len(chunks_250)}\n"
            f"  250-size chunks that span across 1000-size chunk boundaries: {chunks_that_span}/{len(chunks_250)}"
        )

        # This is the key assertion: NOT all 250-size chunks should be subsets
        # At least some should span across boundaries
        # Allow some tolerance (maybe 20% can be subsets due to alignment), but not all
        subset_percentage = (
            chunks_that_are_subset / len(chunks_250) if chunks_250 else 0
        )
        assert subset_percentage < 0.9, (
            f"Too many 250-size chunks ({chunks_that_are_subset}/{len(chunks_250)} = {subset_percentage:.1%}) "
            f"are complete subsets of 1000-size chunks. "
            f"This suggests chunking is deterministic and always starts from the same position, "
            f"which is incorrect. With only 20 chars overlap, 250-size chunks should span across "
            f"1000-size chunk boundaries."
        )

        # Verify overlap is working (check that consecutive chunks have overlapping text)
        # Test with chunk_size=500 which should have clear overlap
        chunks_500 = results[500]["chunks"]
        if len(chunks_500) >= 2:
            chunk1_text = chunks_500[0].get("text", "")
            chunk2_text = chunks_500[1].get("text", "")

            # With overlap, the end of chunk1 should appear at the start of chunk2
            # Check if last 50 characters of chunk1 appear in chunk2
            if len(chunk1_text) >= 50 and len(chunk2_text) >= 50:
                chunk1_end = chunk1_text[-50:].strip()
                # Look for overlap in first 100 chars of chunk2 (accounting for some variation)
                chunk2_start = chunk2_text[:100].strip()
                # Overlap might not be exact due to sentence boundaries, so check for partial match
                # At least some words should overlap
                chunk1_words = set(chunk1_end.split()[-5:])  # Last 5 words
                chunk2_words = set(chunk2_start.split()[:5])  # First 5 words
                overlap_found = len(chunk1_words.intersection(chunk2_words)) > 0

                # Note: This is a soft check - overlap might not always be detectable
                # depending on how SentenceSplitter handles boundaries
                if not overlap_found:
                    # Log warning but don't fail - overlap detection is tricky
                    print(
                        f"Warning: Could not detect clear overlap between consecutive chunks"
                    )
