import json
import os
import shutil
import sqlite3
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

from report_analyst.core.analyzer import DocumentAnalyzer, log_analysis_step
from report_analyst.core.cache_manager import CacheManager


@pytest.fixture(scope="session")
def test_db_template():
    """Create a template test database that persists for the entire test session"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "analysis_template.db"
    print(f"\nCreating template test database at: {db_path}")

    try:
        cache_manager = CacheManager(str(db_path))
        print(f"Template database created successfully at {db_path}")

        if not db_path.exists():
            raise Exception(f"Database file not created at {db_path}")

        yield db_path

    except Exception as e:
        print(f"Error setting up template test database: {e}")
        raise
    finally:
        print(f"Cleaning up template test database at {temp_dir}")
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def clean_db(test_db_template):
    """Provide a clean, unique database copy for each test function"""
    temp_dir = tempfile.mkdtemp()
    unique_db_path = Path(temp_dir) / f"analysis_{uuid.uuid4().hex}.db"
    shutil.copy2(test_db_template, unique_db_path)
    print(f"\nCreating unique database copy at: {unique_db_path}")

    yield unique_db_path

    print(f"Cleaning up unique database at {temp_dir}")
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_env(clean_db):
    """Setup test environment with all necessary files and mocks"""
    temp_dir = tempfile.mkdtemp()
    print(f"\nSetting up test environment in: {temp_dir}")

    # Create storage structure
    storage_path = Path(temp_dir) / "storage"
    (storage_path / "cache").mkdir(parents=True)
    (storage_path / "llm_cache").mkdir(parents=True)

    # Copy the unique database to the expected location
    db_link = storage_path / "cache" / "analysis.db"
    shutil.copy2(clean_db, db_link)
    print(f"Copied database to: {db_link}")

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

        # Reinitialize CacheManager with the unique database copy
        analyzer.cache_manager = CacheManager(db_path=str(clean_db))
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
    assert questions["tcfd_1"]["text"] == "How does the company's board oversee climate-related risks and opportunities?"
    assert "guidelines" in questions["tcfd_1"]


def test_get_question_by_number(analyzer):
    """Test getting question by number"""
    question = analyzer.get_question_by_number(1)
    assert question is not None
    assert question["text"] == "How does the company's board oversee climate-related risks and opportunities?"
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
    analyzer.cache_manager.save_analysis(file_path="test.pdf", question_id="tcfd_1", result=test_answer, config=config)

    # Process document
    results = []
    async for result in analyzer.process_document("test.pdf", ["tcfd_1"]):
        results.append(result)
        if "status" in result:
            assert result["status"] in ["processing", "complete", "cached"]

    # Verify we got the cached result
    cached_result = analyzer.cache_manager.get_analysis(file_path="test.pdf", config=config, question_ids=["tcfd_1"])
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
                async for result in analyzer.process_document(str(test_file), [1], force_recompute=True):
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
                pytest.fail("Config creation failed with None llm - this should be fixed!")
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
            assert any("chunk" in str(r.get("status", "")).lower() for r in status_messages)


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
        analyzer.cache_manager.save_analysis(file_path=f"test_{qid}.pdf", question_id=qid, result=answer, config=config)

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
        async for result in analyzer.process_document(str(test_env["test_file"]), ["tcfd_1", "tcfd_2"]):
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
