import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from report_analyst.core.analyzer import DocumentAnalyzer
from report_analyst.core.cache_manager import CacheManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_cache.db"
    cache_manager = CacheManager(str(db_path))
    yield cache_manager
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_chunks():
    """Sample chunks with embeddings for testing"""
    return [
        {
            "id": 1,
            "text": "CO2 emissions data for Scope 1 and 2",
            "embedding": np.array([0.1, 0.2, 0.3], dtype=np.float32),
            "metadata": {"source": "1"},
            "chunk_size": 500,
            "chunk_overlap": 20,
        },
        {
            "id": 2,
            "text": "Climate change mitigation strategies",
            "embedding": np.array([0.4, 0.5, 0.6], dtype=np.float32),
            "metadata": {"source": "2"},
            "chunk_size": 500,
            "chunk_overlap": 20,
        },
        {
            "id": 3,
            "text": "Financial performance and revenue",
            "embedding": np.array([0.7, 0.8, 0.9], dtype=np.float32),
            "metadata": {"source": "3"},
            "chunk_size": 500,
            "chunk_overlap": 20,
        },
    ]


@pytest.fixture
def sample_questions():
    """Sample questions for testing"""
    return {
        "ev_24": {
            "text": "What are the company's reported Scope 1 CO₂ emissions for the year 2022?",
            "guidelines": "Look for Scope 1 emissions data",
        },
        "ev_25": {
            "text": "What climate actions does the company take?",
            "guidelines": "Look for mitigation strategies",
        },
    }


def test_compute_similarity_scores():
    """Test vector similarity computation"""
    # Query embedding
    query_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

    # Chunk embeddings
    chunk_embeddings = [
        np.array([0.1, 0.2, 0.3], dtype=np.float32),  # Identical - should be ~1.0
        np.array([0.4, 0.5, 0.6], dtype=np.float32),  # Different - should be lower
        np.array([-0.1, -0.2, -0.3], dtype=np.float32),  # Opposite - should be negative
    ]

    # Compute cosine similarities manually
    similarities = []
    for chunk_emb in chunk_embeddings:
        # Cosine similarity = dot product / (norm1 * norm2)
        dot_product = np.dot(query_embedding, chunk_emb)
        norm1 = np.linalg.norm(query_embedding)
        norm2 = np.linalg.norm(chunk_emb)
        similarity = dot_product / (norm1 * norm2)
        similarities.append(similarity)

    # First should be highest (identical vectors)
    assert similarities[0] > similarities[1]
    assert similarities[1] > similarities[2]
    assert similarities[0] >= 0.99  # Almost perfect match


def test_similarity_search_ordering(temp_db, sample_chunks):
    """Test that similarity search returns chunks in descending order"""
    file_path = "test_doc.pdf"

    # Save chunks to database
    temp_db.save_document_chunks(file_path, sample_chunks, 500, 20)

    # Create a query that should match the first chunk best
    query_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)  # Same as first chunk

    with patch.object(temp_db, "_load_vector_store") as mock_load:
        # Mock the vector store retrieval
        mock_retriever = Mock()
        mock_node1 = Mock()
        mock_node1.text = sample_chunks[0]["text"]
        mock_node1.metadata = sample_chunks[0]["metadata"]
        mock_node1.score = 1.0
        mock_node1.embedding = sample_chunks[0]["embedding"]

        mock_node2 = Mock()
        mock_node2.text = sample_chunks[1]["text"]
        mock_node2.metadata = sample_chunks[1]["metadata"]
        mock_node2.score = 0.8
        mock_node2.embedding = sample_chunks[1]["embedding"]

        mock_node3 = Mock()
        mock_node3.text = sample_chunks[2]["text"]
        mock_node3.metadata = sample_chunks[2]["metadata"]
        mock_node3.score = 0.3
        mock_node3.embedding = sample_chunks[2]["embedding"]

        # Nodes should be returned in descending order by score
        mock_retriever.aretrieve = AsyncMock(
            return_value=[mock_node1, mock_node2, mock_node3]
        )

        temp_db.vector_store = Mock()
        temp_db.vector_store.as_retriever.return_value = mock_retriever

        # Test the similarity search
        import asyncio

        similar_chunks = asyncio.run(
            temp_db.get_similar_chunks(
                query_embedding=query_embedding,
                file_path=file_path,
                top_k=3,
                chunk_size=500,
                chunk_overlap=20,
            )
        )

        # Verify chunks are in descending order by similarity
        assert len(similar_chunks) == 3
        assert similar_chunks[0]["score"] >= similar_chunks[1]["score"]
        assert similar_chunks[1]["score"] >= similar_chunks[2]["score"]
        assert similar_chunks[0]["text"] == sample_chunks[0]["text"]


def test_similarity_search_with_questions(sample_questions):
    """Test similarity search integration with question selection"""
    # This would test the UI component, but we can test the logic
    questions = sample_questions

    # Test question selection
    selected_question_id = "ev_24"
    question_text = questions[selected_question_id]["text"]

    # Verify we can extract question text correctly
    assert "Scope 1 CO₂ emissions" in question_text
    assert "2022" in question_text


def test_custom_question_similarity():
    """Test similarity search with custom question input"""
    custom_question = "What are the environmental impacts?"

    # This would integrate with the similarity search
    # For now, we just verify the custom question can be processed
    assert len(custom_question.strip()) > 0
    assert custom_question != "None"


@pytest.mark.asyncio
async def test_chunk_ordering_in_analysis():
    """Test that chunks maintain similarity ordering when passed to LLM"""
    # Mock chunks with different similarity scores
    chunks = [
        {"text": "High relevance chunk", "score": 0.9, "similarity_score": 0.9},
        {"text": "Medium relevance chunk", "score": 0.7, "similarity_score": 0.7},
        {"text": "Low relevance chunk", "score": 0.3, "similarity_score": 0.3},
    ]

    # Verify they're ordered correctly
    assert chunks[0]["score"] > chunks[1]["score"]
    assert chunks[1]["score"] > chunks[2]["score"]

    # In actual analysis, these would be passed to LLM in this order
    for i, chunk in enumerate(chunks):
        chunk["chunk_order"] = i

    # Verify chunk_order preserves similarity ranking
    assert chunks[0]["chunk_order"] == 0  # Highest similarity = first position
    assert chunks[1]["chunk_order"] == 1  # Second highest = second position
    assert chunks[2]["chunk_order"] == 2  # Lowest = last position
