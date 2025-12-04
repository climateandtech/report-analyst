"""Base class for vector store implementations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from llama_index.core import Document


class BaseVectorStore(ABC):
    """Abstract base class for vector store implementations."""

    def __init__(self, storage_path: Path):
        """Initialize the vector store.

        Args:
            storage_path (Path): Path to store vector store files
        """
        self.storage_path = storage_path
        self.store = None

    @abstractmethod
    def load(self) -> bool:
        """Load an existing vector store from disk.

        Returns:
            bool: True if successfully loaded, False if not found
        """
        pass

    @abstractmethod
    def save(self) -> None:
        """Save the current vector store to disk."""
        pass

    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store.

        Args:
            documents (List[Document]): Documents to add
        """
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Search for similar documents.

        Args:
            query (str): Query text
            k (int): Number of results to return

        Returns:
            List[Document]: List of similar documents
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all documents from the store."""
        pass
