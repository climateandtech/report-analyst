import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from llama_index.core import Document, QueryBundle
from llama_index.core.indices import VectorStoreIndex

logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use the project's storage path
            storage_path = os.getenv("STORAGE_PATH", "./storage")
            db_path = str(Path(storage_path) / "cache" / "analysis.db")

        self.db_path = Path(db_path)
        # Create parent directories if they don't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing CacheManager with db: {self.db_path}")
        self.init_db()

        # In-memory vector store for current document
        self.vector_store = None
        self.current_file_path = None

    def init_db(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        try:
            # Create optimized table for document chunks
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                chunk_text TEXT,
                chunk_size INTEGER,
                chunk_overlap INTEGER,
                embedding BLOB,  -- Store embedding for caching
                metadata TEXT,
                created_at TIMESTAMP,
                UNIQUE(file_path, chunk_text, chunk_size, chunk_overlap)
            )
            """
            )

            # Create indices for better performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_file_path ON document_chunks(file_path)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunk_params ON document_chunks(chunk_size, chunk_overlap)"
            )

            # Store questions separately
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT,
                question_set TEXT,
                question_text TEXT,
                guidelines TEXT,
                UNIQUE(question_id, question_set)
            )
            """
            )

            # Create analysis cache table
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS analysis_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                question_id TEXT,
                chunk_size INTEGER,
                chunk_overlap INTEGER,
                top_k INTEGER,
                model TEXT,
                question_set TEXT,
                result TEXT,
                created_at TIMESTAMP,
                UNIQUE(file_path, question_id, chunk_size, chunk_overlap, top_k, model, question_set)
            )
            """
            )

            # Store analysis configurations and results
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS question_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                question_id INTEGER,
                model TEXT,
                top_k INTEGER,
                analysis_result TEXT,
                version INTEGER DEFAULT 1,
                created_at TIMESTAMP,
                FOREIGN KEY(question_id) REFERENCES questions(id),
                UNIQUE(file_path, question_id, model, top_k, version)
            )
            """
            )

            # Store chunk-question relationships with all scores and ordering
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS chunk_relevance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_analysis_id INTEGER,
                document_chunk_id INTEGER,
                chunk_order INTEGER,
                similarity_score REAL,
                llm_score REAL,
                is_evidence BOOLEAN,
                evidence_order INTEGER,
                metadata TEXT,
                FOREIGN KEY(question_analysis_id) REFERENCES question_analysis(id),
                FOREIGN KEY(document_chunk_id) REFERENCES document_chunks(id),
                UNIQUE(question_analysis_id, document_chunk_id)
            )
            """
            )

        finally:
            conn.close()

    def _load_vector_store(self, file_path: str, chunks: List[Dict]) -> None:
        """Load chunks into an in-memory vector store."""
        try:
            # Convert chunks to Documents
            documents = []
            for chunk in chunks:
                if chunk.get("embedding") is not None:
                    doc = Document(
                        text=chunk["text"],
                        metadata={
                            **chunk.get("metadata", {}),
                            "id": chunk.get("id"),
                            "chunk_size": chunk.get("chunk_size"),
                            "chunk_overlap": chunk.get("chunk_overlap"),
                        },
                        embedding=chunk["embedding"],
                    )
                    documents.append(doc)

            # Create vector store index with pre-computed embeddings
            from llama_index.core.indices.vector_store.base import VectorStoreIndex

            self.vector_store = VectorStoreIndex.from_documents(
                documents,
                store_nodes_override=True,  # Keep nodes in memory
                use_async=False,  # Synchronous operation since we have embeddings
                show_progress=True,  # Show progress during index creation
            )
            self.current_file_path = file_path

            logger.info(
                f"Loaded {len(documents)} chunks into vector store for {file_path}"
            )

        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}", exc_info=True)
            raise

    async def get_similar_chunks(
        self,
        query_embedding: np.ndarray,
        file_path: str,
        top_k: int = 5,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ) -> List[Dict]:
        """Get chunks most similar to the query embedding using LlamaIndex vector store."""
        try:
            # Load chunks into vector store if needed
            if self.current_file_path != file_path:
                chunks = self.get_document_chunks(file_path, chunk_size, chunk_overlap)
                self._load_vector_store(file_path, chunks)

            # Get similar nodes using vector store
            retriever = self.vector_store.as_retriever(similarity_top_k=top_k)

            # Create a query bundle with the embedding
            from llama_index.core import QueryBundle

            query_bundle = QueryBundle(
                query_str="",  # Empty query string since we're using embedding
                embedding=query_embedding.tolist(),  # Convert numpy array to list
            )

            # Retrieve similar nodes
            nodes = await retriever.aretrieve(query_bundle)

            # Convert nodes to chunks format
            chunks = []
            for node in nodes:
                # Ensure we have a valid similarity score
                similarity_score = (
                    node.score
                    if hasattr(node, "score")
                    else node.get_score() if hasattr(node, "get_score") else 0.0
                )

                chunk = {
                    "id": node.metadata.get("id"),
                    "text": node.text,
                    "embedding": node.embedding,
                    "metadata": node.metadata,
                    "score": similarity_score,  # Store as 'score' for consistency with vector store
                    "similarity_score": similarity_score,  # Also store as 'similarity_score' for backward compatibility
                }
                chunks.append(chunk)
                logger.debug(
                    f"Found chunk with similarity score: {similarity_score:.4f}"
                )

            logger.info(f"Retrieved {len(chunks)} similar chunks for {file_path}")
            if chunks:
                logger.info(
                    f"Similarity score range: {min(c['score'] for c in chunks):.4f} - {max(c['score'] for c in chunks):.4f}"
                )

            return chunks

        except Exception as e:
            logger.error(f"Error getting similar chunks: {str(e)}", exc_info=True)
            return []

    def save_analysis(
        self, file_path: str, question_id: str, result: Dict, config: Dict
    ):
        """Save analysis result to cache with improved logging"""
        try:
            logger.info(f"Saving analysis for {file_path} - {question_id}")
            logger.info(f"Configuration: {json.dumps(config, indent=2)}")

            # First, ensure question exists in questions table
            with sqlite3.connect(self.db_path) as conn:
                # Extract question set and number from question_id (format: set_number)
                question_set = question_id.split("_")[0]
                question_number = int(question_id.split("_")[1])

                logger.info(
                    f"Ensuring question {question_id} exists in questions table"
                )
                cursor = conn.execute(
                    """
                    SELECT id FROM questions 
                    WHERE question_id = ? AND question_set = ?
                """,
                    (question_id, question_set),
                )
                row = cursor.fetchone()

                if row:
                    question_db_id = row[0]
                    logger.info(f"Found existing question with DB ID: {question_db_id}")
                else:
                    # Insert new question
                    cursor = conn.execute(
                        """
                        INSERT INTO questions (question_id, question_set, question_text, guidelines)
                        VALUES (?, ?, ?, ?)
                        RETURNING id
                    """,
                        (
                            question_id,
                            question_set,
                            result.get("question_text", ""),
                            result.get("guidelines", ""),
                        ),
                    )
                    question_db_id = cursor.fetchone()[0]
                    logger.info(f"Created new question with DB ID: {question_db_id}")

                # Save main analysis result
                logger.info("Saving main analysis result")
                cursor = conn.execute(
                    """
                    INSERT OR REPLACE INTO question_analysis
                    (file_path, question_id, model, top_k, analysis_result, version, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    RETURNING id
                """,
                    (
                        str(file_path),
                        question_db_id,
                        config["model"],
                        config["top_k"],
                        json.dumps(result),
                        1,  # version
                        datetime.now().isoformat(),
                    ),
                )
                analysis_id = cursor.fetchone()[0]
                logger.info(f"Analysis ID: {analysis_id}")

                # Save chunk relevance information
                if "chunks" in result:
                    logger.info(
                        f"Processing {len(result['chunks'])} chunks for relevance"
                    )
                    for chunk in result["chunks"]:
                        logger.debug(f"Processing chunk: {json.dumps(chunk, indent=2)}")

                        # Get chunk ID from document_chunks table
                        cursor = conn.execute(
                            """
                            SELECT id FROM document_chunks 
                            WHERE file_path = ? AND chunk_text = ?
                        """,
                            (str(file_path), chunk["text"]),
                        )
                        row = cursor.fetchone()
                        if row:
                            chunk_id = row[0]
                            logger.debug(f"Found chunk ID: {chunk_id}")

                            # Save chunk relevance with all available information
                            conn.execute(
                                """
                                INSERT OR REPLACE INTO chunk_relevance
                                (question_analysis_id, document_chunk_id, chunk_order,
                                 similarity_score, llm_score, is_evidence, evidence_order, metadata)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    analysis_id,
                                    chunk_id,
                                    chunk.get("chunk_order", 0),
                                    chunk.get("similarity_score", 0.0),
                                    chunk.get("llm_score", None),
                                    chunk.get("is_evidence", False),
                                    chunk.get("evidence_order"),
                                    json.dumps(chunk.get("metadata", {})),
                                ),
                            )
                            logger.info(
                                f"Saving raw values to DB - similarity_score: {chunk.get('similarity_score')}, llm_score: {chunk.get('llm_score')}, is_evidence: {chunk.get('is_evidence')}"
                            )
                        else:
                            logger.warning(
                                f"Could not find chunk in document_chunks table"
                            )

                # Save to analysis cache
                logger.info("Saving to analysis cache")
                conn.execute(
                    """
                    INSERT OR REPLACE INTO analysis_cache
                    (file_path, question_id, chunk_size, chunk_overlap, top_k,
                     model, question_set, result, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(file_path),
                        question_id,  # Use original question_id here
                        config["chunk_size"],
                        config["chunk_overlap"],
                        config["top_k"],
                        config["model"],
                        config["question_set"],
                        json.dumps(result),
                        datetime.now().isoformat(),
                    ),
                )

                logger.info("Successfully saved complete analysis")

        except Exception as e:
            logger.error(f"Error saving analysis: {str(e)}", exc_info=True)
            raise

    def get_analysis(
        self, file_path: str, config: Dict, question_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get analysis results matching the exact configuration.

        Args:
            file_path: Path to the document
            config: Dict containing:
                - chunk_size: int
                - chunk_overlap: int
                - top_k: int
                - model: str
                - question_set: str
            question_ids: Optional list of specific question IDs to retrieve

        Returns:
            Dict mapping question_ids to their analysis results with chunks
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # First get the analysis results from the cache table
                query = """
                    SELECT question_id, result
                    FROM analysis_cache
                    WHERE file_path = ?
                    AND chunk_size = ?
                    AND chunk_overlap = ?
                    AND top_k = ?
                    AND model = ?
                    AND question_set = ?
                """
                params = [
                    str(file_path),
                    config["chunk_size"],
                    config["chunk_overlap"],
                    config["top_k"],
                    config["model"],
                    config["question_set"],
                ]

                if question_ids:
                    placeholders = ",".join("?" * len(question_ids))
                    query += f" AND question_id IN ({placeholders})"
                    params.extend(question_ids)

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                # Process results
                results = {}
                for row in rows:
                    question_id, result_json = row
                    result = json.loads(result_json)
                    results[question_id] = {
                        "result": result,
                        "chunks": [],  # Will be populated from chunk_relevance
                    }

                # Now get the chunk information for each question
                if results:
                    chunk_query = """
                        SELECT 
                            ac.question_id,
                            dc.chunk_text,
                            dc.metadata as chunk_metadata,
                            cr.chunk_order,
                            cr.similarity_score,
                            cr.llm_score,
                            cr.is_evidence,
                            cr.evidence_order,
                            cr.metadata as relevance_metadata
                        FROM analysis_cache ac
                        JOIN questions q ON q.question_id = ac.question_id
                        JOIN question_analysis qa ON qa.question_id = q.id AND qa.file_path = ac.file_path
                        JOIN chunk_relevance cr ON cr.question_analysis_id = qa.id
                        JOIN document_chunks dc ON cr.document_chunk_id = dc.id
                        WHERE ac.file_path = ?
                        AND ac.chunk_size = ?
                        AND ac.chunk_overlap = ?
                        AND ac.top_k = ?
                        AND ac.model = ?
                        AND ac.question_set = ?
                        AND ac.question_id IN ({})
                        ORDER BY ac.question_id, cr.chunk_order
                    """.format(
                        ",".join("?" * len(results))
                    )

                    chunk_params = [
                        str(file_path),
                        config["chunk_size"],
                        config["chunk_overlap"],
                        config["top_k"],
                        config["model"],
                        config["question_set"],
                    ] + list(results.keys())

                    logger.info(f"Executing chunk query with params: {chunk_params}")
                    chunk_cursor = conn.execute(chunk_query, chunk_params)
                    chunk_rows = chunk_cursor.fetchall()
                    logger.info(f"Retrieved {len(chunk_rows)} chunk rows")

                    # Add chunks to their respective questions
                    for row in chunk_rows:
                        question_id = row[0]
                        chunk_info = {
                            "text": row[1],
                            "metadata": json.loads(row[2]) if row[2] else {},
                            "chunk_order": row[3],
                            "similarity_score": row[4],  # Raw similarity score from DB
                            "llm_score": row[5],  # Raw LLM score from DB
                            "is_evidence": row[6],  # Raw is_evidence from DB
                            "evidence_order": row[7],
                            "relevance_metadata": json.loads(row[8]) if row[8] else {},
                        }
                        logger.info(
                            f"Raw DB values for chunk - similarity_score: {row[4]}, llm_score: {row[5]}, is_evidence: {row[6]}"
                        )
                        results[question_id]["chunks"].append(chunk_info)

                    # Sort chunks by their order
                    for question_id in results:
                        results[question_id]["chunks"].sort(
                            key=lambda x: x["chunk_order"]
                        )
                        logger.info(
                            f"Question {question_id}: {len(results[question_id]['chunks'])} chunks"
                        )
                        if results[question_id]["chunks"]:
                            logger.info(
                                f"  Similarity range: {min(c['similarity_score'] for c in results[question_id]['chunks']):.4f} - {max(c['similarity_score'] for c in results[question_id]['chunks']):.4f}"
                            )

                return results

        except Exception as e:
            logger.error(f"Error retrieving analysis: {str(e)}", exc_info=True)
            raise

    def save_vectors(self, file_path: str, chunks: List[Dict[str, Any]]) -> None:
        """Save vectors to the database"""
        try:
            logger.info(f"Starting to save {len(chunks)} chunks for {file_path}")

            # Get chunk parameters from first chunk's metadata
            chunk_size = chunks[0]["metadata"].get("chunk_size", 0) if chunks else 0
            chunk_overlap = (
                chunks[0]["metadata"].get("chunk_overlap", 0) if chunks else 0
            )
            logger.info(f"Chunk parameters: size={chunk_size}, overlap={chunk_overlap}")

            # Begin transaction
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Prepare chunks for insertion
                chunk_data = []
                for i, chunk in enumerate(chunks):
                    if "embedding" not in chunk or chunk["embedding"] is None:
                        logger.warning(f"Skipping chunk {i} - no valid embedding")
                        continue

                    try:
                        # Convert embedding to bytes with shape information
                        embedding = chunk["embedding"]
                        embedding_bytes = embedding.tobytes()
                        # Store shape information in metadata for proper reconstruction
                        metadata_with_shape = chunk["metadata"].copy()
                        metadata_with_shape["embedding_shape"] = list(embedding.shape)
                        metadata_with_shape["embedding_dtype"] = str(embedding.dtype)

                        # Prepare chunk data
                        chunk_data.append(
                            (
                                file_path,
                                chunk["text"],
                                chunk_size,
                                chunk_overlap,
                                embedding_bytes,
                                json.dumps(metadata_with_shape),
                                datetime.now().isoformat(),
                            )
                        )
                    except Exception as e:
                        logger.warning(
                            f"Error preparing chunk {i} for storage: {str(e)}"
                        )
                        continue

                if chunk_data:
                    # Insert all chunks in a single transaction
                    cursor.executemany(
                        """
                        INSERT INTO document_chunks (
                            file_path, chunk_text, chunk_size, chunk_overlap,
                            embedding, metadata, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        chunk_data,
                    )

                    logger.info(
                        f"Successfully saved all {len(chunk_data)} chunks to database"
                    )

                    # Verify the insertion
                    cursor.execute(
                        "SELECT COUNT(*) FROM document_chunks WHERE file_path = ?",
                        (file_path,),
                    )
                    count = cursor.fetchone()[0]
                    logger.info(
                        f"Verification: Found {count} chunks in database for {file_path}"
                    )
                else:
                    logger.warning("No valid chunks to save")

        except Exception as e:
            logger.error(f"Error saving vectors: {str(e)}", exc_info=True)
            raise

    def get_vectors(self, file_path: str) -> List[Dict[str, Any]]:
        """Get vector embeddings for a document"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                chunks = []
                for row in conn.execute(
                    """
                    SELECT chunk_text, embedding, metadata
                    FROM document_chunks
                    WHERE file_path = ?
                """,
                    (str(file_path),),
                ):
                    metadata = json.loads(row[2])

                    # Reconstruct embedding with proper shape
                    embedding = None
                    if row[1]:
                        try:
                            # Get shape and dtype from metadata
                            shape = tuple(metadata.get("embedding_shape", []))
                            dtype = metadata.get("embedding_dtype", "float32")

                            if shape:
                                embedding = np.frombuffer(row[1], dtype=dtype).reshape(
                                    shape
                                )
                            else:
                                # Fallback to default shape if not stored
                                embedding = np.frombuffer(row[1], dtype=np.float32)
                        except Exception as e:
                            logger.warning(f"Error reconstructing embedding: {e}")
                            embedding = None

                    # Remove embedding metadata from the returned metadata
                    clean_metadata = {
                        k: v
                        for k, v in metadata.items()
                        if k not in ["embedding_shape", "embedding_dtype"]
                    }

                    chunks.append(
                        {
                            "text": row[0],
                            "embedding": embedding,
                            "metadata": clean_metadata,
                        }
                    )
                logger.info(f"Retrieved {len(chunks)} vectors for {file_path}")
                return chunks
        except Exception as e:
            logger.error(f"Error retrieving vectors: {str(e)}", exc_info=True)
            return []

    def clear_cache(self, file_path: Optional[str] = None):
        """Clear cache entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if file_path:
                    conn.execute(
                        "DELETE FROM analysis_cache WHERE file_path = ?",
                        (str(file_path),),
                    )
                    conn.execute(
                        "DELETE FROM document_chunks WHERE file_path = ?",
                        (str(file_path),),
                    )
                    logger.info(f"Cleared cache for {file_path}")
                else:
                    conn.execute("DELETE FROM analysis_cache")
                    conn.execute("DELETE FROM document_chunks")
                    logger.info("Cleared all cache")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}", exc_info=True)

    def check_cache_status(self, file_path: str = None):
        """Debug method to check cache contents"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if file_path:
                    logger.info(f"Checking cache for file: {file_path}")
                    cursor = conn.execute(
                        """
                        SELECT DISTINCT chunk_size, chunk_overlap, top_k, model, question_set
                        FROM analysis_cache
                        WHERE file_path = ?
                    """,
                        (str(file_path),),
                    )
                else:
                    logger.info("Checking all cache entries")
                    cursor = conn.execute(
                        """
                        SELECT DISTINCT file_path, chunk_size, chunk_overlap, top_k, model, question_set
                        FROM analysis_cache
                    """
                    )

                rows = cursor.fetchall()
                logger.info(f"Found {len(rows)} distinct configurations:")
                for row in rows:
                    logger.info(f"Config: {row}")

                return rows

        except Exception as e:
            logger.error(f"Error checking cache status: {str(e)}", exc_info=True)
            return []

    def get_all_answers_by_question_set(self, question_set: str) -> Dict[str, Any]:
        """Get all cached answers for a specific question set"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # First get all analysis results
                cursor = conn.execute(
                    """
                    SELECT ac.question_id, ac.result,
                           dc.chunk_text, dc.metadata as chunk_metadata,
                           cr.chunk_order, cr.similarity_score,
                           cr.llm_score, cr.is_evidence, cr.evidence_order,
                           cr.metadata as relevance_metadata
                    FROM analysis_cache ac
                    LEFT JOIN questions q ON q.question_id = ac.question_id
                    LEFT JOIN question_analysis qa ON qa.question_id = q.id
                    LEFT JOIN chunk_relevance cr ON cr.question_analysis_id = qa.id
                    LEFT JOIN document_chunks dc ON cr.document_chunk_id = dc.id
                    WHERE ac.question_set = ?
                    ORDER BY ac.question_id, cr.chunk_order
                """,
                    (question_set,),
                )

                results = {}
                for row in cursor.fetchall():
                    question_id = row[0]
                    result_json = row[1]
                    chunk_text = row[2]
                    chunk_metadata = json.loads(row[3]) if row[3] else {}
                    chunk_order = row[4]
                    similarity_score = row[5]
                    llm_score = row[6]
                    is_evidence = row[7]
                    evidence_order = row[8]
                    relevance_metadata = json.loads(row[9]) if row[9] else {}

                    if question_id not in results:
                        results[question_id] = json.loads(result_json)
                        results[question_id]["chunks"] = []

                    if chunk_text:  # Only add chunk if it exists
                        chunk_info = {
                            "text": chunk_text,
                            "metadata": chunk_metadata,
                            "chunk_order": chunk_order,
                            "similarity_score": similarity_score,
                            "llm_score": llm_score,
                            "is_evidence": is_evidence,
                            "evidence_order": evidence_order,
                            "relevance_metadata": relevance_metadata,
                        }
                        results[question_id]["chunks"].append(chunk_info)

                # Sort chunks by their order for each result
                for question_id in results:
                    results[question_id]["chunks"].sort(
                        key=lambda x: x.get("chunk_order", 0)
                    )

                return results

        except Exception as e:
            logger.error(
                f"Error retrieving answers for question set {question_set}: {e}"
            )
            raise

    def save_document_chunks(
        self, file_path: str, chunks: List[Dict], chunk_size: int, chunk_overlap: int
    ) -> None:
        """Save document chunks to cache with their embeddings."""
        try:
            logger.info(f"Starting to save {len(chunks)} chunks for {file_path}")
            logger.info(f"Chunk parameters: size={chunk_size}, overlap={chunk_overlap}")

            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("BEGIN TRANSACTION")
                timestamp = datetime.now().isoformat()

                for i, chunk in enumerate(chunks):
                    logger.debug(f"Processing chunk {i+1}/{len(chunks)}")

                    if "embedding" not in chunk or chunk["embedding"] is None:
                        logger.warning(f"Skipping chunk {i} - no valid embedding")
                        continue

                    # Ensure embedding is float32
                    embedding = np.array(chunk["embedding"], dtype=np.float32)
                    embedding_bytes = embedding.tobytes()

                    metadata_json = json.dumps(chunk.get("metadata", {}))

                    cursor = conn.execute(
                        """
                        INSERT OR REPLACE INTO document_chunks
                        (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            str(file_path),
                            chunk["text"],
                            chunk_size,
                            chunk_overlap,
                            embedding_bytes,
                            metadata_json,
                            timestamp,
                        ),
                    )

                    logger.debug(f"Inserted chunk with ID: {cursor.lastrowid}")

                conn.execute("COMMIT")
                logger.info(f"Successfully saved all {len(chunks)} chunks to database")

                # Verify chunks were saved
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM document_chunks WHERE file_path = ? AND chunk_size = ? AND chunk_overlap = ?",
                    (str(file_path), chunk_size, chunk_overlap),
                )
                count = cursor.fetchone()[0]
                logger.info(
                    f"Verification: Found {count} chunks in database for {file_path}"
                )

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Error saving document chunks: {str(e)}", exc_info=True)
            raise

    def get_document_chunks(
        self, file_path: str, chunk_size: int = None, chunk_overlap: int = None
    ) -> List[Dict]:
        """
        Get document chunks from cache with improved logging.
        """
        try:
            logger.info(f"Retrieving chunks for {file_path}")
            logger.info(
                f"Filters: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}"
            )

            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT id, chunk_text, embedding, metadata, chunk_size, chunk_overlap
                    FROM document_chunks
                    WHERE file_path = ?
                """
                params = [str(file_path)]

                if chunk_size is not None:
                    query += " AND chunk_size = ?"
                    params.append(chunk_size)

                if chunk_overlap is not None:
                    query += " AND chunk_overlap = ?"
                    params.append(chunk_overlap)

                logger.debug(f"Executing query: {query}")
                logger.debug(f"Query parameters: {params}")

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                chunks = []
                for row in rows:
                    (
                        chunk_id,
                        chunk_text,
                        embedding_bytes,
                        metadata_json,
                        chunk_size,
                        chunk_overlap,
                    ) = row

                    logger.debug(f"Processing chunk ID: {chunk_id}")
                    logger.debug(f"Chunk text preview: {chunk_text[:100]}...")

                    # Convert embedding bytes to numpy array if present
                    embedding = None
                    if embedding_bytes:
                        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                        logger.debug(
                            f"Converted embedding bytes to numpy array, shape: {embedding.shape}"
                        )
                    else:
                        logger.debug("No embedding found for chunk")

                    # Parse metadata JSON
                    metadata = {}
                    if metadata_json:
                        metadata = json.loads(metadata_json)
                        logger.debug(
                            f"Parsed metadata: {json.dumps(metadata, indent=2)}"
                        )

                    chunks.append(
                        {
                            "id": chunk_id,
                            "text": chunk_text,
                            "embedding": embedding,
                            "metadata": metadata,
                            "chunk_size": chunk_size,
                            "chunk_overlap": chunk_overlap,
                        }
                    )

                logger.info(f"Retrieved {len(chunks)} chunks")
                logger.debug(
                    f"Chunks have embeddings: {sum(1 for c in chunks if c['embedding'] is not None)}/{len(chunks)}"
                )
                return chunks

        except Exception as e:
            logger.error(f"Error getting document chunks: {str(e)}", exc_info=True)
            return []
