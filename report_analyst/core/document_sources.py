"""
Document Source Interfaces

This module defines abstract interfaces for document processing and chunk retrieval.
Different implementations can be provided by separate modules.
"""

import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class DocumentChunk:
    """Represents a chunk of a document"""

    def __init__(
        self,
        chunk_id: str,
        chunk_text: str,
        chunk_metadata: Dict[str, Any],
        relevance_scores: Optional[Dict[str, float]] = None,
    ):
        self.chunk_id = chunk_id
        self.chunk_text = chunk_text
        self.chunk_metadata = chunk_metadata
        self.relevance_scores = relevance_scores or {}


class DocumentSource(ABC):
    """Abstract interface for document processing and chunk retrieval"""

    @abstractmethod
    async def upload_document(self, file_path: Union[str, Path]) -> str:
        """
        Upload a document and return a document ID.

        Args:
            file_path: Path to the document file

        Returns:
            Document ID for subsequent operations
        """
        pass

    @abstractmethod
    async def get_chunks(
        self, document_id: str, configuration: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Get chunks for a document.

        Args:
            document_id: ID of the document
            configuration: Optional configuration for chunking (chunk_size, overlap, etc.)

        Returns:
            List of document chunks
        """
        pass

    @abstractmethod
    async def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """
        Get processing status of a document.

        Args:
            document_id: ID of the document

        Returns:
            Status information including processing state, error messages, etc.
        """
        pass

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its associated chunks.

        Args:
            document_id: ID of the document

        Returns:
            True if successful, False otherwise
        """
        # Default implementation - can be overridden
        return False


class LocalDocumentSource(DocumentSource):
    """Local document processing implementation using existing analyzer logic"""

    def __init__(self):
        # Import here to avoid circular imports
        from .analyzer import DocumentAnalyzer
        from .document_processor import DocumentProcessor

        self.processor = DocumentProcessor()
        self.analyzer = DocumentAnalyzer()
        self._document_cache = {}  # Simple in-memory cache

    async def upload_document(self, file_path: Union[str, Path]) -> str:
        """Upload document using local processor"""
        result = await self.processor.process_upload(file_path)
        document_id = result["document_id"]

        # Cache the document path for later use
        doc_path = await self.processor.get_document_path(document_id)
        self._document_cache[document_id] = {
            "path": str(doc_path),
            "metadata": result["metadata"],
            "status": "uploaded",
        }

        return document_id

    async def get_chunks(
        self, document_id: str, configuration: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """Get chunks using existing analyzer logic"""
        if document_id not in self._document_cache:
            raise ValueError(f"Document {document_id} not found")

        doc_info = self._document_cache[document_id]
        file_path = doc_info["path"]

        # Use existing analyzer to create chunks
        chunks_data = self.analyzer._create_chunks(file_path)

        # Convert to DocumentChunk objects
        chunks = []
        for i, chunk_data in enumerate(chunks_data):
            chunk = DocumentChunk(
                chunk_id=f"{document_id}_chunk_{i}",
                chunk_text=chunk_data["text"],
                chunk_metadata=chunk_data.get("metadata", {}),
                relevance_scores={},
            )
            chunks.append(chunk)

        return chunks

    async def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Get document status from cache"""
        if document_id not in self._document_cache:
            return {"status": "not_found"}

        return {
            "status": self._document_cache[document_id]["status"],
            "document_id": document_id,
            "metadata": self._document_cache[document_id]["metadata"],
        }

    async def delete_document(self, document_id: str) -> bool:
        """Delete document and cleanup files"""
        if document_id in self._document_cache:
            # Clean up file
            success = await self.processor.cleanup_document(document_id)
            # Remove from cache
            del self._document_cache[document_id]
            return success
        return False
