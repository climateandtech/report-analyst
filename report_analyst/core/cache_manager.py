import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from llama_index.core import Document, QueryBundle
from llama_index.core.indices import VectorStoreIndex
from sqlalchemy import text

from .database_manager import DatabaseManager
from .database_schema import indexes, metadata

logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(self, db_path: str = None, database_url: str = None):
        """
        Initialize CacheManager.

        Args:
            db_path: Path to SQLite database file (for backward compatibility).
                    If None and database_url is None, uses default SQLite path.
            database_url: SQLAlchemy database URL (e.g., 'sqlite:///path' or 'postgresql://...').
                         Takes precedence over db_path.
        """
        # Determine database URL
        if database_url:
            db_url = database_url
        elif db_path:
            # Convert file path to SQLite URL
            db_path_obj = Path(db_path)
            db_path_obj.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{db_path}"
            self.db_path = db_path_obj  # Keep for backward compatibility
        else:
            # Default to SQLite
            storage_path = os.getenv("STORAGE_PATH", "./storage")
            db_path = str(Path(storage_path) / "cache" / "analysis.db")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{db_path}"
            self.db_path = Path(db_path)  # Keep for backward compatibility

        # Initialize database manager
        self.db_manager = DatabaseManager(db_url)
        logger.info(f"Initializing CacheManager with database: {self.db_manager._mask_url(db_url)}")
        self.init_db()

        # In-memory vector store for current document
        self.vector_store = None
        self.current_file_path = None

    def init_db(self):
        """Initialize the database schema using SQLAlchemy"""
        try:
            engine = self.db_manager.get_engine()
            # Create all tables
            metadata.create_all(engine)
            
            # Create indexes (using raw SQL for IF NOT EXISTS support)
            # Note: Some databases may not support IF NOT EXISTS in CREATE INDEX
            # We'll try to create them and ignore errors if they already exist
            with self.db_manager.get_connection() as conn:
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                    except Exception as e:
                        # Index might already exist, which is fine
                        logger.debug(f"Index creation (may already exist): {e}")
                conn.commit()
            
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database schema: {str(e)}", exc_info=True)
            raise

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

            # Extract question set and number from question_id (format: set_number)
            question_set = question_id.split("_")[0]

            with self.db_manager.get_connection() as conn:
                # Ensure question exists in questions table
                logger.info(
                    f"Ensuring question {question_id} exists in questions table"
                )
                result_obj = conn.execute(
                    text("""
                        SELECT id FROM questions 
                        WHERE question_id = :question_id AND question_set = :question_set
                    """),
                    {"question_id": question_id, "question_set": question_set},
                )
                row = result_obj.fetchone()

                if row:
                    question_db_id = row[0]
                    logger.info(f"Found existing question with DB ID: {question_db_id}")
                else:
                    # Insert new question - use dialect-specific upsert
                    if self.db_manager.is_postgres():
                        # PostgreSQL: ON CONFLICT
                        result_obj = conn.execute(
                            text("""
                                INSERT INTO questions (question_id, question_set, question_text, guidelines)
                                VALUES (:question_id, :question_set, :question_text, :guidelines)
                                ON CONFLICT (question_id, question_set) DO UPDATE
                                SET question_text = EXCLUDED.question_text,
                                    guidelines = EXCLUDED.guidelines
                                RETURNING id
                            """),
                            {
                                "question_id": question_id,
                                "question_set": question_set,
                                "question_text": result.get("question_text", ""),
                                "guidelines": result.get("guidelines", ""),
                            },
                        )
                    else:
                        # SQLite: INSERT OR REPLACE
                        result_obj = conn.execute(
                            text("""
                                INSERT OR REPLACE INTO questions (question_id, question_set, question_text, guidelines)
                                VALUES (:question_id, :question_set, :question_text, :guidelines)
                            """),
                            {
                                "question_id": question_id,
                                "question_set": question_set,
                                "question_text": result.get("question_text", ""),
                                "guidelines": result.get("guidelines", ""),
                            },
                        )
                        # Get the ID separately for SQLite
                        result_obj = conn.execute(
                            text("SELECT id FROM questions WHERE question_id = :question_id AND question_set = :question_set"),
                            {"question_id": question_id, "question_set": question_set},
                        )
                    question_db_id = result_obj.fetchone()[0]
                    logger.info(f"Created new question with DB ID: {question_db_id}")

                # Save main analysis result
                logger.info("Saving main analysis result")
                if self.db_manager.is_postgres():
                    result_obj = conn.execute(
                        text("""
                            INSERT INTO question_analysis
                            (file_path, question_id, model, top_k, analysis_result, version, created_at)
                            VALUES (:file_path, :question_id, :model, :top_k, :analysis_result, :version, :created_at)
                            ON CONFLICT (file_path, question_id, model, top_k, version) DO UPDATE
                            SET analysis_result = EXCLUDED.analysis_result,
                                created_at = EXCLUDED.created_at
                            RETURNING id
                        """),
                        {
                            "file_path": str(file_path),
                            "question_id": question_db_id,
                            "model": config["model"],
                            "top_k": config["top_k"],
                            "analysis_result": json.dumps(result),
                            "version": 1,
                            "created_at": datetime.now().isoformat(),
                        },
                    )
                else:
                    result_obj = conn.execute(
                        text("""
                            INSERT OR REPLACE INTO question_analysis
                            (file_path, question_id, model, top_k, analysis_result, version, created_at)
                            VALUES (:file_path, :question_id, :model, :top_k, :analysis_result, :version, :created_at)
                        """),
                        {
                            "file_path": str(file_path),
                            "question_id": question_db_id,
                            "model": config["model"],
                            "top_k": config["top_k"],
                            "analysis_result": json.dumps(result),
                            "version": 1,
                            "created_at": datetime.now().isoformat(),
                        },
                    )
                    # Get ID separately for SQLite
                    result_obj = conn.execute(
                        text("""
                            SELECT id FROM question_analysis
                            WHERE file_path = :file_path AND question_id = :question_id
                            AND model = :model AND top_k = :top_k AND version = :version
                        """),
                        {
                            "file_path": str(file_path),
                            "question_id": question_db_id,
                            "model": config["model"],
                            "top_k": config["top_k"],
                            "version": 1,
                        },
                    )
                analysis_id = result_obj.fetchone()[0]
                logger.info(f"Analysis ID: {analysis_id}")

                # Save chunk relevance information
                if "chunks" in result:
                    logger.info(
                        f"Processing {len(result['chunks'])} chunks for relevance"
                    )
                    for chunk in result["chunks"]:
                        logger.debug(f"Processing chunk: {json.dumps(chunk, indent=2)}")

                        # Get chunk ID from document_chunks table
                        # Must match on file_path, chunk_text, chunk_size, and chunk_overlap
                        result_obj = conn.execute(
                            text("""
                                SELECT id FROM document_chunks 
                                WHERE file_path = :file_path 
                                AND chunk_text = :chunk_text
                                AND chunk_size = :chunk_size
                                AND chunk_overlap = :chunk_overlap
                            """),
                            {
                                "file_path": str(file_path), 
                                "chunk_text": chunk["text"],
                                "chunk_size": config["chunk_size"],
                                "chunk_overlap": config["chunk_overlap"],
                            },
                        )
                        row = result_obj.fetchone()
                        if row:
                            chunk_id = row[0]
                            logger.debug(f"Found chunk ID: {chunk_id}")
                            
                            # Save chunk relevance with all available information
                            if self.db_manager.is_postgres():
                                conn.execute(
                                    text("""
                                        INSERT INTO chunk_relevance
                                        (question_analysis_id, document_chunk_id, chunk_order,
                                         similarity_score, llm_score, is_evidence, evidence_order, metadata)
                                        VALUES (:question_analysis_id, :document_chunk_id, :chunk_order,
                                                :similarity_score, :llm_score, :is_evidence, :evidence_order, :metadata)
                                        ON CONFLICT (question_analysis_id, document_chunk_id) DO UPDATE
                                        SET chunk_order = EXCLUDED.chunk_order,
                                            similarity_score = EXCLUDED.similarity_score,
                                            llm_score = EXCLUDED.llm_score,
                                            is_evidence = EXCLUDED.is_evidence,
                                            evidence_order = EXCLUDED.evidence_order,
                                            metadata = EXCLUDED.metadata
                                    """),
                                    {
                                        "question_analysis_id": analysis_id,
                                        "document_chunk_id": chunk_id,
                                        "chunk_order": chunk.get("chunk_order", 0),
                                        "similarity_score": chunk.get("similarity_score", 0.0),
                                        "llm_score": chunk.get("llm_score"),
                                        "is_evidence": chunk.get("is_evidence", False),
                                        "evidence_order": chunk.get("evidence_order"),
                                        "metadata": json.dumps(chunk.get("metadata", {})),
                                    },
                                )
                            else:
                                conn.execute(
                                    text("""
                                        INSERT OR REPLACE INTO chunk_relevance
                                        (question_analysis_id, document_chunk_id, chunk_order,
                                         similarity_score, llm_score, is_evidence, evidence_order, metadata)
                                        VALUES (:question_analysis_id, :document_chunk_id, :chunk_order,
                                                :similarity_score, :llm_score, :is_evidence, :evidence_order, :metadata)
                                    """),
                                    {
                                        "question_analysis_id": analysis_id,
                                        "document_chunk_id": chunk_id,
                                        "chunk_order": chunk.get("chunk_order", 0),
                                        "similarity_score": chunk.get("similarity_score", 0.0),
                                        "llm_score": chunk.get("llm_score"),
                                        "is_evidence": chunk.get("is_evidence", False),
                                        "evidence_order": chunk.get("evidence_order"),
                                        "metadata": json.dumps(chunk.get("metadata", {})),
                                    },
                                )
                            logger.info(
                                f"Saving raw values to DB - similarity_score: {chunk.get('similarity_score')}, llm_score: {chunk.get('llm_score')}, is_evidence: {chunk.get('is_evidence')}"
                            )
                        else:
                            # Chunk doesn't exist in document_chunks - create it first (even without embedding)
                            logger.info(
                                f"Chunk not found in document_chunks, creating it for file_path={file_path}, chunk_size={config['chunk_size']}, chunk_overlap={config['chunk_overlap']}"
                            )
                            
                            chunk_metadata = chunk.get("metadata", {})
                            timestamp = datetime.now().isoformat()
                            
                            # Insert chunk into document_chunks (embedding can be NULL)
                            if self.db_manager.is_postgres():
                                insert_result = conn.execute(
                                    text("""
                                        INSERT INTO document_chunks
                                        (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
                                        VALUES (:file_path, :chunk_text, :chunk_size, :chunk_overlap, :embedding, :metadata, :created_at)
                                        ON CONFLICT (file_path, chunk_text, chunk_size, chunk_overlap) DO UPDATE
                                        SET metadata = EXCLUDED.metadata
                                        RETURNING id
                                    """),
                                    {
                                        "file_path": str(file_path),
                                        "chunk_text": chunk["text"],
                                        "chunk_size": config["chunk_size"],
                                        "chunk_overlap": config["chunk_overlap"],
                                        "embedding": None,  # No embedding available, but we still need the chunk
                                        "metadata": json.dumps(chunk_metadata),
                                        "created_at": timestamp,
                                    },
                                )
                                chunk_id = insert_result.fetchone()[0]
                            else:
                                conn.execute(
                                    text("""
                                        INSERT OR IGNORE INTO document_chunks
                                        (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
                                        VALUES (:file_path, :chunk_text, :chunk_size, :chunk_overlap, :embedding, :metadata, :created_at)
                                    """),
                                    {
                                        "file_path": str(file_path),
                                        "chunk_text": chunk["text"],
                                        "chunk_size": config["chunk_size"],
                                        "chunk_overlap": config["chunk_overlap"],
                                        "embedding": None,  # No embedding available, but we still need the chunk
                                        "metadata": json.dumps(chunk_metadata),
                                        "created_at": timestamp,
                                    },
                                )
                                # Get the ID after insert
                                result_obj = conn.execute(
                                    text("""
                                        SELECT id FROM document_chunks 
                                        WHERE file_path = :file_path 
                                        AND chunk_text = :chunk_text
                                        AND chunk_size = :chunk_size
                                        AND chunk_overlap = :chunk_overlap
                                    """),
                                    {
                                        "file_path": str(file_path), 
                                        "chunk_text": chunk["text"],
                                        "chunk_size": config["chunk_size"],
                                        "chunk_overlap": config["chunk_overlap"],
                                    },
                                )
                                row = result_obj.fetchone()
                                if row:
                                    chunk_id = row[0]
                                else:
                                    logger.error(f"Failed to retrieve chunk ID after insert")
                                    continue
                            
                            logger.info(f"Created chunk in document_chunks with ID: {chunk_id}, now saving chunk_relevance")
                            
                            # Now save chunk_relevance with the newly created chunk_id
                            if self.db_manager.is_postgres():
                                conn.execute(
                                    text("""
                                        INSERT INTO chunk_relevance
                                        (question_analysis_id, document_chunk_id, chunk_order,
                                         similarity_score, llm_score, is_evidence, evidence_order, metadata)
                                        VALUES (:question_analysis_id, :document_chunk_id, :chunk_order,
                                                :similarity_score, :llm_score, :is_evidence, :evidence_order, :metadata)
                                        ON CONFLICT (question_analysis_id, document_chunk_id) DO UPDATE
                                        SET chunk_order = EXCLUDED.chunk_order,
                                            similarity_score = EXCLUDED.similarity_score,
                                            llm_score = EXCLUDED.llm_score,
                                            is_evidence = EXCLUDED.is_evidence,
                                            evidence_order = EXCLUDED.evidence_order,
                                            metadata = EXCLUDED.metadata
                                    """),
                                    {
                                        "question_analysis_id": analysis_id,
                                        "document_chunk_id": chunk_id,
                                        "chunk_order": chunk.get("chunk_order", 0),
                                        "similarity_score": chunk.get("similarity_score", 0.0),
                                        "llm_score": chunk.get("llm_score"),
                                        "is_evidence": chunk.get("is_evidence", False),
                                        "evidence_order": chunk.get("evidence_order"),
                                        "metadata": json.dumps(chunk.get("metadata", {})),
                                    },
                                )
                            else:
                                conn.execute(
                                    text("""
                                        INSERT OR REPLACE INTO chunk_relevance
                                        (question_analysis_id, document_chunk_id, chunk_order,
                                         similarity_score, llm_score, is_evidence, evidence_order, metadata)
                                        VALUES (:question_analysis_id, :document_chunk_id, :chunk_order,
                                                :similarity_score, :llm_score, :is_evidence, :evidence_order, :metadata)
                                    """),
                                    {
                                        "question_analysis_id": analysis_id,
                                        "document_chunk_id": chunk_id,
                                        "chunk_order": chunk.get("chunk_order", 0),
                                        "similarity_score": chunk.get("similarity_score", 0.0),
                                        "llm_score": chunk.get("llm_score"),
                                        "is_evidence": chunk.get("is_evidence", False),
                                        "evidence_order": chunk.get("evidence_order"),
                                        "metadata": json.dumps(chunk.get("metadata", {})),
                                    },
                                )
                            logger.info(
                                f"Saved chunk_relevance - similarity_score: {chunk.get('similarity_score')}, llm_score: {chunk.get('llm_score')}, is_evidence: {chunk.get('is_evidence')}"
                            )

                # Save to analysis cache
                logger.info("Saving to analysis cache")
                if self.db_manager.is_postgres():
                    conn.execute(
                        text("""
                            INSERT INTO analysis_cache
                            (file_path, question_id, chunk_size, chunk_overlap, top_k,
                             model, question_set, result, created_at)
                            VALUES (:file_path, :question_id, :chunk_size, :chunk_overlap, :top_k,
                                    :model, :question_set, :result, :created_at)
                            ON CONFLICT (file_path, question_id, chunk_size, chunk_overlap, top_k, model, question_set) DO UPDATE
                            SET result = EXCLUDED.result,
                                created_at = EXCLUDED.created_at
                        """),
                        {
                            "file_path": str(file_path),
                            "question_id": question_id,
                            "chunk_size": config["chunk_size"],
                            "chunk_overlap": config["chunk_overlap"],
                            "top_k": config["top_k"],
                            "model": config["model"],
                            "question_set": config["question_set"],
                            "result": json.dumps(result),
                            "created_at": datetime.now().isoformat(),
                        },
                    )
                else:
                    conn.execute(
                        text("""
                            INSERT OR REPLACE INTO analysis_cache
                            (file_path, question_id, chunk_size, chunk_overlap, top_k,
                             model, question_set, result, created_at)
                            VALUES (:file_path, :question_id, :chunk_size, :chunk_overlap, :top_k,
                                    :model, :question_set, :result, :created_at)
                        """),
                        {
                            "file_path": str(file_path),
                            "question_id": question_id,
                            "chunk_size": config["chunk_size"],
                            "chunk_overlap": config["chunk_overlap"],
                            "top_k": config["top_k"],
                            "model": config["model"],
                            "question_set": config["question_set"],
                            "result": json.dumps(result),
                            "created_at": datetime.now().isoformat(),
                        },
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
            with self.db_manager.get_connection() as conn:
                # Map question set to database identifier (same mapping as in save_analysis)
                question_set_mapping = {
                    "everest": "ev",
                    "tcfd": "tcfd",
                    "s4m": "s4m",
                    "lucia": "lucia",
                }
                db_question_set = question_set_mapping.get(
                    config["question_set"], config["question_set"]
                )

                # First get the analysis results from the cache table
                query = """
                    SELECT question_id, result
                    FROM analysis_cache
                    WHERE file_path = :file_path
                    AND chunk_size = :chunk_size
                    AND chunk_overlap = :chunk_overlap
                    AND top_k = :top_k
                    AND model = :model
                    AND question_set = :question_set
                """
                params = {
                    "file_path": str(file_path),
                    "chunk_size": config["chunk_size"],
                    "chunk_overlap": config["chunk_overlap"],
                    "top_k": config["top_k"],
                    "model": config["model"],
                    "question_set": db_question_set,
                }

                if question_ids:
                    # Use SQLAlchemy's IN clause with bind parameters
                    placeholders = ",".join(f":qid_{i}" for i in range(len(question_ids)))
                    query += f" AND question_id IN ({placeholders})"
                    for i, qid in enumerate(question_ids):
                        params[f"qid_{i}"] = qid

                result_obj = conn.execute(text(query), params)
                rows = result_obj.fetchall()

                # Process results
                results = {}
                for row in rows:
                    question_id, result_json = row
                    result = json.loads(result_json)
                    
                    # Ensure SCORE is a number, not a string (fix for JSON deserialization)
                    if "SCORE" in result:
                        try:
                            result["SCORE"] = float(result["SCORE"]) if result["SCORE"] is not None else 0
                        except (ValueError, TypeError):
                            result["SCORE"] = 0
                    
                    results[question_id] = {
                        "result": result,
                        "chunks": [],  # Will be populated from chunk_relevance
                    }

                # Now get the chunk information for each question
                if results:
                    # Build IN clause for question IDs
                    qid_placeholders = ",".join(f":qid_{i}" for i in range(len(results)))
                    chunk_query = f"""
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
                        JOIN question_analysis qa ON qa.question_id = q.id 
                            AND qa.file_path = ac.file_path
                            AND qa.model = ac.model
                            AND qa.top_k = ac.top_k
                        JOIN chunk_relevance cr ON cr.question_analysis_id = qa.id
                        JOIN document_chunks dc ON cr.document_chunk_id = dc.id
                        WHERE ac.file_path = :file_path
                        AND ac.chunk_size = :chunk_size
                        AND ac.chunk_overlap = :chunk_overlap
                        AND ac.top_k = :top_k
                        AND ac.model = :model
                        AND ac.question_set = :question_set
                        AND ac.question_id IN ({qid_placeholders})
                        ORDER BY ac.question_id, cr.chunk_order
                    """

                    chunk_params = {
                        "file_path": str(file_path),
                        "chunk_size": config["chunk_size"],
                        "chunk_overlap": config["chunk_overlap"],
                        "top_k": config["top_k"],
                        "model": config["model"],
                        "question_set": db_question_set,
                    }
                    for i, qid in enumerate(results.keys()):
                        chunk_params[f"qid_{i}"] = qid

                    logger.info(f"Executing chunk query with params: {list(chunk_params.keys())}")
                    logger.info(f"Chunk query params values: file_path={file_path}, chunk_size={config['chunk_size']}, chunk_overlap={config['chunk_overlap']}, top_k={config['top_k']}, model={config['model']}, question_set={db_question_set}, question_ids={list(results.keys())}")
                    
                    # Debug: Check if question_analysis records exist
                    qid_placeholders_test = ",".join(f":qid_{i}" for i in range(len(results)))
                    test_params = {"file_path": str(file_path), "model": config["model"], "top_k": config["top_k"]}
                    for i, qid in enumerate(results.keys()):
                        test_params[f"qid_{i}"] = qid
                    
                    test_query = text(f"""
                        SELECT COUNT(*) FROM question_analysis qa
                        JOIN questions q ON q.id = qa.question_id
                        WHERE q.question_id IN ({qid_placeholders_test})
                        AND qa.file_path = :file_path
                        AND qa.model = :model
                        AND qa.top_k = :top_k
                    """)
                    test_result = conn.execute(test_query, test_params)
                    test_count = test_result.scalar()
                    logger.info(f"Found {test_count} question_analysis records matching file_path, model, and top_k")
                    
                    # Debug: Check if chunk_relevance records exist
                    if test_count > 0:
                        chunk_relevance_query = text(f"""
                            SELECT COUNT(*) FROM question_analysis qa
                            JOIN questions q ON q.id = qa.question_id
                            JOIN chunk_relevance cr ON cr.question_analysis_id = qa.id
                            WHERE q.question_id IN ({qid_placeholders_test})
                            AND qa.file_path = :file_path
                            AND qa.model = :model
                            AND qa.top_k = :top_k
                        """)
                        cr_result = conn.execute(chunk_relevance_query, test_params)
                        cr_count = cr_result.scalar()
                        logger.info(f"Found {cr_count} chunk_relevance records for these question_analysis records")
                    
                    chunk_result = conn.execute(text(chunk_query), chunk_params)
                    chunk_rows = chunk_result.fetchall()
                    logger.info(f"Retrieved {len(chunk_rows)} chunk rows from database via chunk_relevance JOIN")

                    # If no chunks found via chunk_relevance, try to get chunks directly from document_chunks
                    # This is a fallback for cases where chunks exist but weren't linked via chunk_relevance
                    if len(chunk_rows) == 0:
                        logger.warning("No chunks found via chunk_relevance JOIN, trying fallback: get chunks directly from document_chunks")
                        
                        # Get all document_chunks for this file with matching parameters
                        fallback_query = text("""
                            SELECT 
                                dc.id,
                                dc.chunk_text,
                                dc.metadata as chunk_metadata
                            FROM document_chunks dc
                            WHERE dc.file_path = :file_path
                            AND dc.chunk_size = :chunk_size
                            AND dc.chunk_overlap = :chunk_overlap
                            ORDER BY dc.id
                        """)
                        fallback_params = {
                            "file_path": str(file_path),
                            "chunk_size": config["chunk_size"],
                            "chunk_overlap": config["chunk_overlap"],
                        }
                        fallback_result = conn.execute(fallback_query, fallback_params)
                        fallback_chunks = fallback_result.fetchall()
                        logger.info(f"Found {len(fallback_chunks)} chunks in document_chunks (fallback)")
                        
                        # If we have chunks but no chunk_relevance, we can't match them to questions
                        # So we'll assign them to all questions that have analysis results
                        if fallback_chunks and len(results) > 0:
                            logger.warning("Chunks exist in document_chunks but not linked via chunk_relevance. Cannot match to specific questions without chunk_relevance data.")
                            # For now, we'll skip the fallback since we can't match chunks to questions without chunk_relevance
                            # The chunks need to be properly linked during analysis save
                    
                    if len(chunk_rows) == 0:
                        logger.warning(f"No chunks found in database for file_path={file_path}, question_set={db_question_set}")
                        logger.warning(f"Query was: {chunk_query[:500]}...")
                        # Check each step of the JOIN
                        logger.warning("Debugging JOIN query step by step:")
                        
                        # Step 1: Check analysis_cache
                        ac_query = text(f"""
                            SELECT COUNT(*) FROM analysis_cache ac
                            WHERE ac.file_path = :file_path
                            AND ac.chunk_size = :chunk_size
                            AND ac.chunk_overlap = :chunk_overlap
                            AND ac.top_k = :top_k
                            AND ac.model = :model
                            AND ac.question_set = :question_set
                            AND ac.question_id IN ({qid_placeholders_test})
                        """)
                        ac_result = conn.execute(ac_query, chunk_params)
                        ac_count = ac_result.scalar()
                        logger.warning(f"  - analysis_cache records: {ac_count}")
                        
                        # Step 2: Check questions
                        q_query = text(f"""
                            SELECT COUNT(*) FROM questions q
                            WHERE q.question_id IN ({qid_placeholders_test})
                            AND q.question_set = :question_set
                        """)
                        q_params = {"question_set": db_question_set}
                        for i, qid in enumerate(results.keys()):
                            q_params[f"qid_{i}"] = qid
                        q_result = conn.execute(q_query, q_params)
                        q_count = q_result.scalar()
                        logger.warning(f"  - questions records: {q_count}")
                        
                        # Step 3: Check question_analysis (already done above)
                        logger.warning(f"  - question_analysis records: {test_count}")
                        
                        # Step 4: Check chunk_relevance
                        if test_count > 0:
                            cr_query = text(f"""
                                SELECT COUNT(*) FROM question_analysis qa
                                JOIN questions q ON q.id = qa.question_id
                                JOIN chunk_relevance cr ON cr.question_analysis_id = qa.id
                                WHERE q.question_id IN ({qid_placeholders_test})
                                AND qa.file_path = :file_path
                                AND qa.model = :model
                                AND qa.top_k = :top_k
                            """)
                            cr_result = conn.execute(cr_query, test_params)
                            cr_count = cr_result.scalar()
                            logger.warning(f"  - chunk_relevance records: {cr_count}")
                        
                        # Step 5: Check document_chunks
                        dc_query = text("""
                            SELECT COUNT(*) FROM document_chunks dc
                            WHERE dc.file_path = :file_path
                            AND dc.chunk_size = :chunk_size
                            AND dc.chunk_overlap = :chunk_overlap
                        """)
                        dc_params = {
                            "file_path": str(file_path),
                            "chunk_size": config["chunk_size"],
                            "chunk_overlap": config["chunk_overlap"],
                        }
                        dc_result = conn.execute(dc_query, dc_params)
                        dc_count = dc_result.scalar()
                        logger.warning(f"  - document_chunks records: {dc_count}")

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
                        logger.debug(
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

            with self.db_manager.get_connection() as conn:
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
                        chunk_data.append({
                            "file_path": file_path,
                            "chunk_text": chunk["text"],
                            "chunk_size": chunk_size,
                            "chunk_overlap": chunk_overlap,
                            "embedding": embedding_bytes,
                            "metadata": json.dumps(metadata_with_shape),
                            "created_at": datetime.now().isoformat(),
                        })
                    except Exception as e:
                        logger.warning(
                            f"Error preparing chunk {i} for storage: {str(e)}"
                        )
                        continue

                if chunk_data:
                    # Insert all chunks - use dialect-specific upsert
                    if self.db_manager.is_postgres():
                        # PostgreSQL: ON CONFLICT
                        for chunk_row in chunk_data:
                            conn.execute(
                                text("""
                                    INSERT INTO document_chunks
                                    (file_path, chunk_text, chunk_size, chunk_overlap,
                                     embedding, metadata, created_at)
                                    VALUES (:file_path, :chunk_text, :chunk_size, :chunk_overlap,
                                            :embedding, :metadata, :created_at)
                                    ON CONFLICT (file_path, chunk_text, chunk_size, chunk_overlap) DO UPDATE
                                    SET embedding = EXCLUDED.embedding,
                                        metadata = EXCLUDED.metadata,
                                        created_at = EXCLUDED.created_at
                                """),
                                chunk_row,
                            )
                    else:
                        # SQLite: INSERT OR REPLACE
                        for chunk_row in chunk_data:
                            conn.execute(
                                text("""
                                    INSERT OR REPLACE INTO document_chunks
                                    (file_path, chunk_text, chunk_size, chunk_overlap,
                                     embedding, metadata, created_at)
                                    VALUES (:file_path, :chunk_text, :chunk_size, :chunk_overlap,
                                            :embedding, :metadata, :created_at)
                                """),
                                chunk_row,
                            )

                    logger.info(
                        f"Successfully saved all {len(chunk_data)} chunks to database"
                    )

                    # Verify the insertion
                    result_obj = conn.execute(
                        text("SELECT COUNT(*) FROM document_chunks WHERE file_path = :file_path"),
                        {"file_path": file_path},
                    )
                    count = result_obj.fetchone()[0]
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
            with self.db_manager.get_connection() as conn:
                result_obj = conn.execute(
                    text("""
                        SELECT chunk_text, embedding, metadata
                        FROM document_chunks
                        WHERE file_path = :file_path
                    """),
                    {"file_path": str(file_path)},
                )
                chunks = []
                for row in result_obj:
                    metadata_dict = json.loads(row[2]) if row[2] else {}

                    # Reconstruct embedding with proper shape
                    embedding = None
                    if row[1]:
                        try:
                            # Get shape and dtype from metadata
                            shape = tuple(metadata_dict.get("embedding_shape", []))
                            dtype = metadata_dict.get("embedding_dtype", "float32")

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
                        for k, v in metadata_dict.items()
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
            with self.db_manager.get_connection() as conn:
                if file_path:
                    conn.execute(
                        text("DELETE FROM analysis_cache WHERE file_path = :file_path"),
                        {"file_path": str(file_path)},
                    )
                    conn.execute(
                        text("DELETE FROM document_chunks WHERE file_path = :file_path"),
                        {"file_path": str(file_path)},
                    )
                    logger.info(f"Cleared cache for {file_path}")
                else:
                    conn.execute(text("DELETE FROM analysis_cache"))
                    conn.execute(text("DELETE FROM document_chunks"))
                    logger.info("Cleared all cache")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}", exc_info=True)

    def check_cache_status(self, file_path: str = None):
        """Debug method to check cache contents"""
        try:
            with self.db_manager.get_connection() as conn:
                if file_path:
                    logger.info(f"Checking cache for file: {file_path}")
                    result_obj = conn.execute(
                        text("""
                            SELECT DISTINCT chunk_size, chunk_overlap, top_k, model, question_set
                            FROM analysis_cache
                            WHERE file_path = :file_path
                        """),
                        {"file_path": str(file_path)},
                    )
                else:
                    logger.info("Checking all cache entries")
                    result_obj = conn.execute(
                        text("""
                            SELECT DISTINCT file_path, chunk_size, chunk_overlap, top_k, model, question_set
                            FROM analysis_cache
                        """)
                    )

                rows = result_obj.fetchall()
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
            with self.db_manager.get_connection() as conn:
                # First get all analysis results
                result_obj = conn.execute(
                    text("""
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
                        WHERE ac.question_set = :question_set
                        ORDER BY ac.question_id, cr.chunk_order
                    """),
                    {"question_set": question_set},
                )

                results = {}
                for row in result_obj:
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

            timestamp = datetime.now().isoformat()

            with self.db_manager.get_connection() as conn:
                for i, chunk in enumerate(chunks):
                    logger.debug(f"Processing chunk {i+1}/{len(chunks)}")

                    if "embedding" not in chunk or chunk["embedding"] is None:
                        logger.warning(f"Skipping chunk {i} - no valid embedding")
                        continue

                    # Ensure embedding is float32
                    embedding = np.array(chunk["embedding"], dtype=np.float32)
                    embedding_bytes = embedding.tobytes()

                    metadata_json = json.dumps(chunk.get("metadata", {}))

                    if self.db_manager.is_postgres():
                        conn.execute(
                            text("""
                                INSERT INTO document_chunks
                                (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
                                VALUES (:file_path, :chunk_text, :chunk_size, :chunk_overlap, :embedding, :metadata, :created_at)
                                ON CONFLICT (file_path, chunk_text, chunk_size, chunk_overlap) DO UPDATE
                                SET embedding = EXCLUDED.embedding,
                                    metadata = EXCLUDED.metadata,
                                    created_at = EXCLUDED.created_at
                            """),
                            {
                                "file_path": str(file_path),
                                "chunk_text": chunk["text"],
                                "chunk_size": chunk_size,
                                "chunk_overlap": chunk_overlap,
                                "embedding": embedding_bytes,
                                "metadata": metadata_json,
                                "created_at": timestamp,
                            },
                        )
                    else:
                        conn.execute(
                            text("""
                                INSERT OR REPLACE INTO document_chunks
                                (file_path, chunk_text, chunk_size, chunk_overlap, embedding, metadata, created_at)
                                VALUES (:file_path, :chunk_text, :chunk_size, :chunk_overlap, :embedding, :metadata, :created_at)
                            """),
                            {
                                "file_path": str(file_path),
                                "chunk_text": chunk["text"],
                                "chunk_size": chunk_size,
                                "chunk_overlap": chunk_overlap,
                                "embedding": embedding_bytes,
                                "metadata": metadata_json,
                                "created_at": timestamp,
                            },
                        )

                logger.info(f"Successfully saved all {len(chunks)} chunks to database")

                # Verify chunks were saved
                result_obj = conn.execute(
                    text("""
                        SELECT COUNT(*) FROM document_chunks 
                        WHERE file_path = :file_path AND chunk_size = :chunk_size AND chunk_overlap = :chunk_overlap
                    """),
                    {
                        "file_path": str(file_path),
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap,
                    },
                )
                count = result_obj.fetchone()[0]
                logger.info(
                    f"Verification: Found {count} chunks in database for {file_path}"
                )

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

            with self.db_manager.get_connection() as conn:
                query = """
                    SELECT id, chunk_text, embedding, metadata, chunk_size, chunk_overlap
                    FROM document_chunks
                    WHERE file_path = :file_path
                """
                params = {"file_path": str(file_path)}

                if chunk_size is not None:
                    query += " AND chunk_size = :chunk_size"
                    params["chunk_size"] = chunk_size

                if chunk_overlap is not None:
                    query += " AND chunk_overlap = :chunk_overlap"
                    params["chunk_overlap"] = chunk_overlap

                logger.debug(f"Executing query: {query}")
                logger.debug(f"Query parameters: {params}")

                result_obj = conn.execute(text(query), params)
                rows = result_obj.fetchall()

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

    def get_chunks_without_embeddings(
        self, file_path: str, chunk_size: int = None, chunk_overlap: int = None
    ) -> List[Dict]:
        """Get chunks without embeddings (where embedding IS NULL)"""
        try:
            logger.info(f"Retrieving chunks without embeddings for {file_path}")
            logger.info(
                f"Filters: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}"
            )

            with self.db_manager.get_connection() as conn:
                query = """
                    SELECT id, chunk_text, metadata, chunk_size, chunk_overlap
                    FROM document_chunks
                    WHERE file_path = :file_path AND embedding IS NULL
                """
                params = {"file_path": str(file_path)}

                if chunk_size is not None:
                    query += " AND chunk_size = :chunk_size"
                    params["chunk_size"] = chunk_size

                if chunk_overlap is not None:
                    query += " AND chunk_overlap = :chunk_overlap"
                    params["chunk_overlap"] = chunk_overlap

                logger.debug(f"Executing query: {query}")
                logger.debug(f"Query parameters: {params}")

                result_obj = conn.execute(text(query), params)
                rows = result_obj.fetchall()

                chunks = []
                for row in rows:
                    chunk_id, chunk_text, metadata_json, chunk_size, chunk_overlap = row

                    # Parse metadata JSON
                    metadata = {}
                    if metadata_json:
                        metadata = json.loads(metadata_json)

                    chunks.append(
                        {
                            "id": chunk_id,
                            "text": chunk_text,
                            "embedding": None,
                            "metadata": metadata,
                            "chunk_size": chunk_size,
                            "chunk_overlap": chunk_overlap,
                        }
                    )

                logger.info(f"Retrieved {len(chunks)} chunks without embeddings")
                return chunks

        except Exception as e:
            logger.error(
                f"Error getting chunks without embeddings: {str(e)}", exc_info=True
            )
            return []

    def has_chunk_scoring(self, file_path: str, config: Dict) -> bool:
        """Check if any questions have been scored for this file/config"""
        try:
            with self.db_manager.get_connection() as conn:
                result_obj = conn.execute(
                    text("""
                        SELECT COUNT(DISTINCT q.question_id)
                        FROM questions q
                        JOIN question_analysis qa ON qa.question_id = q.id
                        JOIN chunk_relevance cr ON cr.question_analysis_id = qa.id
                        WHERE qa.file_path = :file_path AND qa.model = :model AND qa.top_k = :top_k
                    """),
                    {
                        "file_path": str(file_path),
                        "model": config["model"],
                        "top_k": config["top_k"],
                    },
                )

                count = result_obj.fetchone()[0]
                return count > 0

        except Exception as e:
            logger.error(f"Error checking chunk scoring: {str(e)}")
            return False
