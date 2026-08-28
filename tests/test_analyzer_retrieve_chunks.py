"""Unit tests for DocumentAnalyzer.retrieve_chunks library API."""

from unittest.mock import AsyncMock, Mock

import pytest

from report_analyst.core.analyzer import DocumentAnalyzer


@pytest.mark.asyncio
async def test_retrieve_chunks_reuses_cached_chunks():
    DocumentAnalyzer.reset_instance()
    analyzer = DocumentAnalyzer()
    analyzer.chunk_params = {"chunk_size": 500, "chunk_overlap": 20, "top_k": 5}
    analyzer.cache_manager = Mock()
    cached = [{"text": "cached chunk"}]
    analyzer.cache_manager.get_document_chunks.return_value = cached
    analyzer._create_chunks = Mock(side_effect=AssertionError("should not chunk"))
    analyzer._get_similar_chunks = AsyncMock(return_value=[{"text": "cached chunk", "score": 0.8}])

    result = await analyzer.retrieve_chunks("report.pdf", "What are the targets?", top_k=3)

    assert result[0]["text"] == "cached chunk"
    analyzer._get_similar_chunks.assert_awaited_once()
    analyzer.cache_manager.save_document_chunks.assert_not_called()
    DocumentAnalyzer.reset_instance()


@pytest.mark.asyncio
async def test_retrieve_chunks_creates_chunks_on_cache_miss():
    DocumentAnalyzer.reset_instance()
    analyzer = DocumentAnalyzer()
    analyzer.chunk_params = {"chunk_size": 400, "chunk_overlap": 40, "top_k": 5}
    analyzer.cache_manager = Mock()
    analyzer.cache_manager.get_document_chunks.return_value = []
    created = [{"text": "new chunk", "embedding": [0.1, 0.2]}]
    analyzer._create_chunks = Mock(return_value=created)
    analyzer._get_similar_chunks = AsyncMock(return_value=created)

    result = await analyzer.retrieve_chunks("report.pdf", "Board climate oversight?")

    assert result == created
    analyzer._create_chunks.assert_called_once_with("report.pdf")
    analyzer.cache_manager.save_document_chunks.assert_called_once()
    DocumentAnalyzer.reset_instance()
