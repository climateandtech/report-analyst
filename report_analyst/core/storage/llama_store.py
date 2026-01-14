"""LlamaIndex vector store implementation."""

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from llama_index.core import (
    Document,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.schema import NodeWithScore, TextNode

from .base import BaseVectorStore

logger = logging.getLogger(__name__)


class LlamaVectorStore(BaseVectorStore):
    """Vector store implementation using LlamaIndex."""

    def __init__(self, storage_path: Path):
        """Initialize the LlamaIndex vector store.

        Args:
            storage_path (Path): Path to store vector store files
        """
        self.storage_path = Path(storage_path).resolve()
        self.store = None
        self.storage_context = None

    def load(self) -> bool:
        """
        Check if vector store exists and load it.
        Returns True if successfully loaded, False if needs to be created.
        """
        try:
            # Check if required files exist
            if not self.storage_path.exists():
                logger.warning(f"Storage path does not exist: {self.storage_path}")
                return False

            docstore_path = self.storage_path / "docstore.json"
            if not docstore_path.exists():
                logger.warning(f"docstore.json not found in {self.storage_path}")
                return False

            # Load the existing index
            logger.info(f"Loading vector store from {self.storage_path}")
            self.storage_context = StorageContext.from_defaults(
                persist_dir=str(self.storage_path)
            )
            self.store = load_index_from_storage(storage_context=self.storage_context)
            logger.info("Successfully loaded existing vector store")
            return True

        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return False

    def save(self) -> None:
        """Save the current vector store to disk."""
        try:
            if self.store is None:
                raise ValueError("No vector store to save")

            # Ensure directory exists
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # Save the index directly
            self.store.storage_context.persist(persist_dir=str(self.storage_path))
            logger.info(f"Successfully saved vector store to {self.storage_path}")

        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise

    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to vector store, creating new if needed or updating existing."""
        try:
            # Ensure directory exists
            self.storage_path.mkdir(parents=True, exist_ok=True)

            if not self.load():
                # Create new vector store if loading failed
                logger.info("Creating new vector store")
                self.storage_context = StorageContext.from_defaults()
                self.store = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=self.storage_context,
                    show_progress=True,
                    embed_batch_size=100,
                )
            else:
                # Add to existing vector store
                logger.info("Adding documents to existing vector store")
                for doc in documents:
                    # Convert to TextNode if needed
                    if not isinstance(doc, TextNode):
                        node = TextNode(text=doc.text, metadata=doc.metadata)
                    else:
                        node = doc
                    self.store.insert(node, batch_size=100)

            # Persist changes
            logger.info(f"Persisting vector store to {self.storage_path}")
            self.storage_context.persist(persist_dir=str(self.storage_path))
            logger.info("Successfully persisted vector store")

        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise

    def similarity_search(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        """Search for similar documents and return documents with their similarity scores."""
        if self.store is None:
            raise ValueError("Vector store not initialized")

        try:
            # Get retriever from index
            retriever = self.store.as_retriever(similarity_top_k=k)

            # Get nodes and convert to Document format with scores
            nodes = retriever.retrieve(query)
            return [
                (Document(text=node.node.text, metadata=node.node.metadata), node.score)
                for node in nodes
            ]

        except Exception as e:
            logger.error(f"Error during similarity search: {e}")
            raise

    def clear(self) -> None:
        """Clear all documents from the store."""
        try:
            if self.storage_path.exists():
                shutil.rmtree(self.storage_path)
            self.store = None
            logger.info("Vector store cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            raise
