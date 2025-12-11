import hashlib
import json
import logging
import os
import pickle
import re
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from llama_index.core import Document, Settings
from llama_index.core.ingestion import IngestionCache
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.readers.file import PyMuPDFReader

from .cache_manager import CacheManager
from .llm_providers import get_llm
from .prompt_manager import PromptManager
from .storage import LlamaVectorStore

# Setup logging at the top of the file
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for backend configuration first
use_backend = os.getenv("USE_BACKEND", "false").lower() == "true"
use_centralized_llm = os.getenv("USE_CENTRALIZED_LLM", "false").lower() == "true"
use_full_backend_analysis = (
    os.getenv("USE_FULL_BACKEND_ANALYSIS", "false").lower() == "true"
)

# Check for required environment variables
openai_key = os.getenv("OPENAI_API_KEY")
gemini_key = os.getenv("GOOGLE_API_KEY")
default_model = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo-1106")

# Log available model keys
logger.info(
    f"API Keys available - OpenAI: {bool(openai_key)}, Gemini: {bool(gemini_key)}"
)
logger.info(
    f"Backend mode - USE_BACKEND: {use_backend}, USE_CENTRALIZED_LLM: {use_centralized_llm}, USE_FULL_BACKEND_ANALYSIS: {use_full_backend_analysis}"
)

# If using backend for LLM, don't require local API keys
if use_backend and (use_centralized_llm or use_full_backend_analysis):
    logger.info("Using backend for LLM functionality - local API keys not required")
    # Set placeholder values for compatibility
    if not openai_key:
        openai_key = "backend-handles-llm"
    if not gemini_key:
        gemini_key = "backend-handles-llm"
else:
    # Only check for API keys if not using backend LLM
    # Check if we need to force the default model based on available keys
    if default_model.startswith("gemini-") and not gemini_key:
        logger.warning(
            f"Default model is {default_model} but no GOOGLE_API_KEY is available"
        )
        if openai_key:
            default_model = "gpt-3.5-turbo-1106"
            logger.info(f"Switching default model to {default_model}")
        else:
            logger.error("No valid API keys available for any models")
            raise ValueError(
                "No valid API keys found. Set either OPENAI_API_KEY or GOOGLE_API_KEY"
            )
    elif default_model.startswith("gpt-") and not openai_key:
        logger.warning(
            f"Default model is {default_model} but no OPENAI_API_KEY is available"
        )
        if gemini_key:
            default_model = "gemini-pro"
            logger.info(f"Switching default model to {default_model}")
        else:
            logger.error("No valid API keys available for any models")
            raise ValueError(
                "No valid API keys found. Set either OPENAI_API_KEY or GOOGLE_API_KEY"
            )

    # Ensure we have at least one API key for the selected model type
    if not openai_key and not gemini_key:
        logger.error("No API keys found - set either OPENAI_API_KEY or GOOGLE_API_KEY")
        raise ValueError(
            "Set either OPENAI_API_KEY or GOOGLE_API_KEY environment variable"
        )

if not os.getenv("OPENAI_ORGANIZATION"):
    logger.warning("OPENAI_ORGANIZATION environment variable is not set")


def log_analysis_step(message: str, level: str = "info"):
    """Helper function to log analysis steps with consistent formatting"""
    log_func = getattr(logger, level)
    log_func(f"[ANALYSIS] {message}")


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_params_hash(params: Dict) -> str:
    """Compute hash of parameters dictionary"""
    param_str = json.dumps(params, sort_keys=True)
    return hashlib.sha256(param_str.encode()).hexdigest()


class DocumentAnalyzer:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DocumentAnalyzer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.prompt_manager = PromptManager()
        # Use absolute paths for storage
        self.storage_path = Path(__file__).parent.parent.parent / "storage"
        self.cache_path = self.storage_path / "cache"
        self.llm_cache_path = self.storage_path / "llm_cache"

        # Create cache directories
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.llm_cache_path.mkdir(parents=True, exist_ok=True)

        log_analysis_step(f"Storage path: {self.storage_path.resolve()}", "debug")
        log_analysis_step(f"Cache path: {self.cache_path.resolve()}", "debug")
        log_analysis_step(f"LLM cache path: {self.llm_cache_path.resolve()}", "debug")

        # Set default question set
        self.question_set = "tcfd"
        self.questions = self._load_questions()

        # Use model from environment variables as default
        self.default_model = default_model
        log_analysis_step(f"Using default model from env: {self.default_model}")

        # Check if we should use backend for all LLM functionality
        self.use_backend_llm = use_backend and (
            use_centralized_llm or use_full_backend_analysis
        )

        if self.use_backend_llm:
            log_analysis_step(
                "Skipping local LLM initialization - using backend for all LLM functionality",
                "info",
            )
            # Set minimal placeholders for compatibility
            self.llm = None
            self.embeddings = None
        else:
            try:
                # Initialize LLM with caching using the provider factory
                self.llm = get_llm(
                    model_name=self.default_model,
                    cache_dir=str(self.llm_cache_path),
                )

                # Initialize embeddings if OpenAI API key is available
                if openai_key and openai_key != "backend-handles-llm":
                    self.embeddings = OpenAIEmbedding(
                        api_key=openai_key,
                        api_base=os.getenv("OPENAI_API_BASE"),
                        model_name=os.getenv(
                            "OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"
                        ),
                        embed_batch_size=100,
                    )

                    # Configure embeddings globally for LlamaIndex
                    Settings.embed_model = self.embeddings
                else:
                    logger.warning(
                        "No OpenAI API key - embedding functionality will be limited"
                    )
                    self.embeddings = None

            except Exception as e:
                log_analysis_step(
                    f"Error initializing local LLM clients: {str(e)}", "error"
                )
                if not self.use_backend_llm:
                    raise
                else:
                    # In backend mode, local LLM failures are not critical
                    logger.warning(
                        "Local LLM initialization failed, but using backend mode"
                    )
                    self.llm = None
                    self.embeddings = None

        # Initialize caching and text processing (these are always needed)
        self.use_cache = True  # Default to True, can be overridden
        Settings.ingestion_cache = IngestionCache(
            cache_dir=str(self.llm_cache_path), cache_type="local"
        )

        self.text_splitter = SentenceSplitter(chunk_size=500, chunk_overlap=20)

        # Cache parameters
        self.chunk_params = {"chunk_size": 500, "chunk_overlap": 20, "top_k": 5}

        self.embedding_params = {
            "model": "text-embedding-ada-002",
            "batch_size": 100,
        }

        # Add a cache for loaded answers
        self._answers_cache = {}

        self.cache_manager = CacheManager()
        logger.info("Initialized DocumentAnalyzer with cache manager")

        self._initialized = True

    def _get_cache_key(self, file_path: str) -> str:
        """Generate a unique cache key based on file and all analysis parameters."""
        try:
            params_str = (
                f"cs{self.chunk_params['chunk_size']}_"
                f"ov{self.chunk_params['chunk_overlap']}_"
                f"tk{self.chunk_params['top_k']}_"
                f"m{self.llm.model}_"  # Include LLM model
                f"qs{self.question_set}"
            )  # Include question set
            return f"{Path(file_path).stem}_{params_str}"
        except Exception as e:
            logger.warning(f"[ANALYSIS] Cache ERROR: Failed to generate cache key: {e}")
            return f"{Path(file_path).stem}_fallback"

    def _get_vector_store_collection_name(self, cache_key: str) -> str:
        """Generate a valid collection name from cache key."""
        # Remove any invalid characters and ensure it's not too long
        valid_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in cache_key)
        return valid_name[:63]  # ChromaDB has a limit on collection name length

    def _load_chunks_cache(self, cache_key: str) -> Optional[List]:
        """Load text chunks from cache if available."""
        try:
            cache_file = self.cache_path / f"{cache_key}_chunks.json"
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    chunk_data = json.load(f)
                # Convert to LlamaIndex Document objects
                chunks = [
                    Document(
                        text=chunk[
                            "page_content"
                        ],  # LlamaIndex uses text instead of page_content
                        metadata=chunk["metadata"],
                    )
                    for chunk in chunk_data
                ]
                logger.info(
                    f"[ANALYSIS] ✓ Cache HIT: Loaded {len(chunks)} chunks from cache"
                )
                return chunks
            logger.info("[ANALYSIS] Cache MISS: No cached chunks found")
            return None
        except Exception as e:
            logger.warning(f"[ANALYSIS] Cache ERROR: Failed to load chunks cache: {e}")
            return None

    def _save_chunks_cache(self, cache_key: str, chunks: List) -> None:
        """Save text chunks to cache."""
        try:
            cache_file = self.cache_path / f"{cache_key}_chunks.json"
            # Convert Document objects to serializable format
            serializable_chunks = [
                {
                    "page_content": doc.text,  # Store as page_content for backward compatibility
                    "metadata": doc.metadata,
                }
                for doc in chunks
            ]
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(serializable_chunks, f)
            logger.info(f"[ANALYSIS] ✓ Cache SAVE: Saved {len(chunks)} chunks to cache")
        except Exception as e:
            logger.warning(f"[ANALYSIS] Cache ERROR: Failed to save chunks cache: {e}")

    def _load_vector_store(
        self, cache_key: str, chunks: List
    ) -> Optional[LlamaVectorStore]:
        """Load vector store from cache if available."""
        try:
            store_dir = self.cache_path / f"{cache_key}_vectors"

            if store_dir.exists():
                logger.info(f"[ANALYSIS] Found vector store directory at {store_dir}")
                try:
                    # Load LlamaVectorStore from local files
                    vector_store = LlamaVectorStore(store_dir)
                    # Try to load the store - this will verify if it's valid
                    if vector_store.load():
                        logger.info(
                            f"[ANALYSIS] ✓ Cache HIT: Loaded vector store from cache"
                        )
                        return vector_store
                except Exception as inner_e:
                    logger.error(
                        f"[ANALYSIS] Failed to load existing vector store: {inner_e}",
                        exc_info=True,
                    )

            logger.info("[ANALYSIS] Cache MISS: No cached vector store found")
            return None
        except Exception as e:
            logger.warning(
                f"[ANALYSIS] Cache ERROR: Failed to load vector store cache: {e}"
            )
            logger.debug(f"Full vector store cache error: {str(e)}", exc_info=True)
            return None

    async def score_chunk_relevance(self, question: str, chunk_text: str) -> float:
        """Score the relevance of a chunk to a question using LLM."""
        if not self.use_cache:
            Settings.ingestion_cache = None

        log_analysis_step(f"Computing relevance score for chunk: {chunk_text[:100]}...")

        try:
            response = await self.llm.achat(
                prompt=f"""As a senior equity analyst with expertise in climate science evaluating a company's sustainability report, you are tasked with evaluating text fragments for their usefulness in answering specific TCFD questions.

Your task is to score the relevance and quality of evidence in each text fragment. Consider:

1. Specificity and Concreteness:
   - Quantitative data and specific metrics (highest value)
   - Concrete policies and procedures
   - Specific commitments with timelines
   - General statements or vague claims (lowest value)

2. Evidence Quality:
   - Verifiable data and third-party verification
   - Clear methodologies and frameworks
   - Specific examples and case studies
   - Unsubstantiated claims (lowest value)

3. Direct Relevance:
   - Direct answers to the question components
   - Related but indirect information
   - Contextual background
   - Unrelated information (lowest value)

4. Disclosure Quality:
   - Comprehensive and transparent disclosure
   - Balanced reporting (both positive and negative)
   - Clear acknowledgment of limitations
   - Potential greenwashing or selective disclosure (lowest value)

Score from 0.0 to 1.0 where:
0.0 = Not useful (generic statements, unrelated content)
0.3 = Contains relevant context but no specific evidence
0.6 = Contains useful specific information but requires additional context
1.0 = Contains critical evidence or specific details that directly answer the question

Question: {question}

Text to evaluate:
{chunk_text}

Output only the numeric score (0.0-1.0):"""
            )

            score = float(response.message.content.strip())
            score = max(0.0, min(1.0, score))
            log_analysis_step(f"Computed relevance score: {score:.4f}")
            return score

        except Exception as e:
            log_analysis_step(f"Error scoring chunk relevance: {str(e)}", "error")
            return 0.0

    async def score_chunk_relevance_batch(
        self, question: str, chunks: List[Dict], single_call: bool = True
    ) -> List[float]:
        """Score a batch of chunks using LLM.

        Args:
            question: The question being analyzed
            chunks: List of chunks to score
            single_call: If True, score all chunks in one API call. If False, score each chunk individually.
        """
        try:
            if single_call:
                # Batch scoring - all chunks in one call
                chunks_text = "\n\n".join(
                    [
                        f"[CHUNK {i+1}]\n{chunk['text']}"
                        for i, chunk in enumerate(chunks)
                    ]
                )

                response = await self.llm.achat(
                    prompt=f"""As a senior equity analyst with expertise in climate science evaluating a company's sustainability report, you are tasked with evaluating text fragments for their usefulness in answering specific TCFD questions.

Your task is to score the relevance and quality of evidence in each text fragment marked as [CHUNK X]. Consider:

1. Specificity and Concreteness:
   - Quantitative data and specific metrics (highest value)
   - Concrete policies and procedures
   - Specific commitments with timelines
   - General statements or vague claims (lowest value)

2. Evidence Quality:
   - Verifiable data and third-party verification
   - Clear methodologies and frameworks
   - Specific examples and case studies
   - Unsubstantiated claims (lowest value)

3. Direct Relevance:
   - Direct answers to the question components
   - Related but indirect information
   - Contextual background
   - Unrelated information (lowest value)

4. Disclosure Quality:
   - Comprehensive and transparent disclosure
   - Balanced reporting (both positive and negative)
   - Clear acknowledgment of limitations
   - Potential greenwashing or selective disclosure (lowest value)

For each chunk marked [CHUNK X], provide a score from 0.0 to 1.0 where:
0.0 = Not useful (generic statements, unrelated content)
0.3 = Contains relevant context but no specific evidence
0.6 = Contains useful specific information but requires additional context
1.0 = Contains critical evidence or specific details that directly answer the question

Question: {question}

Text fragments to evaluate:
{chunks_text}

Output only the scores, one per line, in order:"""
                )

                # Parse scores from response
                try:
                    scores = [
                        float(score.strip())
                        for score in response.message.content.strip().split("\n")
                    ]
                    if len(scores) != len(chunks):
                        raise ValueError(
                            f"Got {len(scores)} scores for {len(chunks)} chunks"
                        )
                    return scores
                except Exception as e:
                    log_analysis_step(f"Error parsing batch scores: {str(e)}", "error")
                    return [0.0] * len(chunks)

            else:
                # Individual scoring - one API call per chunk
                scores = []
                for i, chunk in enumerate(chunks):
                    score = await self.score_chunk_relevance(question, chunk["text"])
                    scores.append(score)
                    log_analysis_step(f"Scored chunk {i+1}/{len(chunks)}: {score:.2f}")
                return scores

        except Exception as e:
            log_analysis_step(f"Error in batch scoring: {str(e)}", "error")
            return [0.0] * len(chunks)

    def _load_cached_answers(self, file_path: str) -> Dict:
        """Load cached answers for a file with exact configuration match"""
        try:
            # Log current configuration
            logger.info(f"Current configuration:")
            logger.info(f"- Chunk size: {self.chunk_params['chunk_size']}")
            logger.info(f"- Overlap: {self.chunk_params['chunk_overlap']}")
            logger.info(f"- Top K: {self.chunk_params['top_k']}")
            logger.info(f"- Model: {self.llm.model}")
            logger.info(f"- Question set: {self.question_set}")

            # Log cache directory and available files
            logger.info(f"Cache directory: {self.cache_path}")
            cache_files = list(self.cache_path.glob("*.json"))
            logger.info(f"Available cache files ({len(cache_files)}):")
            for cf in cache_files:
                logger.info(f"- {cf.name}")

            # Generate cache key for current configuration
            cache_key = f"cs{self.chunk_params['chunk_size']}_ov{self.chunk_params['chunk_overlap']}_tk{self.chunk_params['top_k']}_m{self.llm.model}_qs{self.question_set}"
            file_stem = Path(file_path).stem
            cache_file = Path(self.cache_path) / f"{file_stem}_{cache_key}.json"

            logger.info(f"Looking for cache file: {cache_file}")

            if not cache_file.exists():
                logger.info(f"No cache file found for current configuration")
                return {}

            with open(cache_file, "r") as f:
                cached_data = json.load(f)
                logger.info(f"Loaded cache data with keys: {list(cached_data.keys())}")
                logger.info(
                    f"Cache data structure: {json.dumps(cached_data, indent=2)[:500]}..."
                )  # Show first 500 chars
                return cached_data

        except Exception as e:
            logger.error(f"Error loading cache: {str(e)}")
            return {}

    def _validate_cache_filename(self, filename: str) -> bool:
        """Check if cache filename follows the required pattern."""
        # Pattern: filename_cs{num}_ov{num}_tk{num}_m{model}_qs{set}.json
        pattern = r"^.+_cs\d+_ov\d+_tk\d+_m[^_]+_qs[^_]+\.json$"
        return bool(re.match(pattern, filename))

    def _save_cached_answers(self, file_path: str, answers: Dict) -> None:
        """Save answers using the parameter-based format and update memory cache"""
        try:
            cache_key = self._get_cache_key(file_path)
            cache_path = self.cache_path / f"{cache_key}.json"

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(answers, f, indent=2)

            # Update memory cache
            self._answers_cache[cache_key] = answers
            logger.info(f"[ANALYSIS] ✓ Cache SAVE: Saved answers to {cache_path}")

        except Exception as e:
            logger.warning(f"[ANALYSIS] Cache ERROR: Failed to save answers: {e}")

    async def process_document(
        self,
        file_path: str,
        selected_questions: List[int],
        use_llm_scoring: bool = False,
        single_call: bool = True,
        force_recompute: bool = False,
    ) -> AsyncGenerator[Dict, None]:
        """Process a document for selected questions"""
        try:
            # Add more detailed logging
            logger.info(f"[ANALYSIS] Starting document processing for {file_path}")
            logger.info(f"[ANALYSIS] Selected questions: {selected_questions}")
            logger.info(
                f"[ANALYSIS] LLM scoring: {use_llm_scoring}, Single call: {single_call}, Force recompute: {force_recompute}"
            )
            logger.info(
                f"[ANALYSIS] Current chunk parameters: size={self.chunk_params['chunk_size']}, overlap={self.chunk_params['chunk_overlap']}, top_k={self.chunk_params['top_k']}"
            )

            # Store the current file path for use in _get_similar_chunks
            self.current_file_path = file_path

            # 1. Load and chunk the document - use CacheManager with current chunk parameters
            logger.info(
                f"[ANALYSIS] Getting document chunks from cache for {file_path} with size={self.chunk_params['chunk_size']}, overlap={self.chunk_params['chunk_overlap']}"
            )
            chunks = self.cache_manager.get_document_chunks(
                file_path=file_path,
                chunk_size=self.chunk_params["chunk_size"],
                chunk_overlap=self.chunk_params["chunk_overlap"],
            )
            logger.info(f"[ANALYSIS] Retrieved {len(chunks)} chunks from cache")

            if not chunks:
                logger.info(
                    f"[ANALYSIS] No chunks found in cache with current parameters, creating new chunks"
                )
                # If no chunks in cache with current parameters, create them
                chunks = self._create_chunks(file_path)
                logger.info(f"[ANALYSIS] Created {len(chunks)} new chunks")

                # Save chunks to cache with current parameters
                self.cache_manager.save_document_chunks(
                    file_path=file_path,
                    chunks=chunks,
                    chunk_size=self.chunk_params["chunk_size"],
                    chunk_overlap=self.chunk_params["chunk_overlap"],
                )
                logger.info(f"[ANALYSIS] Saved {len(chunks)} chunks to cache")

            yield {"status": f"Document loaded with {len(chunks)} chunks"}

            # 2. Process each question
            for question_number in selected_questions:
                try:
                    logger.info(
                        f"[ANALYSIS] Processing question number {question_number}"
                    )
                    question_data = self.get_question_by_number(question_number)
                    if not question_data:
                        logger.warning(
                            f"[ANALYSIS] Question {question_number} not found"
                        )
                        yield {"error": f"Question {question_number} not found"}
                        continue

                    question_id = f"{self.question_set}_{question_number}"
                    logger.info(f"[ANALYSIS] Question ID: {question_id}")

                    yield {
                        "status": f"Processing question {question_number}: {question_data['text'][:50]}..."
                    }

                    # 3. Get similar chunks using embeddings with current parameters
                    logger.info(
                        f"[ANALYSIS] Getting similar chunks for question {question_id}"
                    )
                    similar_chunks = await self._get_similar_chunks(
                        question_data["text"], chunks, self.chunk_params["top_k"]
                    )
                    logger.info(
                        f"[ANALYSIS] Found {len(similar_chunks)} similar chunks"
                    )

                    # 3.5. Apply LLM scoring to chunks if enabled (INDEPENDENT of evidence determination)
                    if use_llm_scoring:
                        logger.info(
                            f"[ANALYSIS] Applying LLM scoring to {len(similar_chunks)} chunks for question {question_id}"
                        )
                        yield {
                            "status": f"Scoring chunks with LLM for question {question_number}..."
                        }

                        try:
                            llm_scores = await self.score_chunk_relevance_batch(
                                question_data["text"],
                                similar_chunks,
                                single_call=single_call,
                            )

                            # Apply LLM scores to chunks
                            for i, chunk in enumerate(similar_chunks):
                                if i < len(llm_scores):
                                    chunk["llm_score"] = llm_scores[i]
                                    logger.debug(
                                        f"Applied LLM score {llm_scores[i]:.3f} to chunk {i+1}"
                                    )
                                else:
                                    chunk["llm_score"] = 0.0
                                    logger.warning(
                                        f"No LLM score available for chunk {i+1}"
                                    )

                            logger.info(
                                f"[ANALYSIS] Applied LLM scores to {len(similar_chunks)} chunks"
                            )

                        except Exception as e:
                            logger.error(
                                f"[ANALYSIS] Error applying LLM scores: {str(e)}",
                                exc_info=True,
                            )
                            # Set default scores if LLM scoring fails
                            for chunk in similar_chunks:
                                chunk["llm_score"] = 0.0
                    else:
                        logger.info(
                            f"[ANALYSIS] LLM scoring disabled for question {question_id}"
                        )
                        # Ensure llm_score is set to None when not using LLM scoring
                        for chunk in similar_chunks:
                            chunk["llm_score"] = None

                    # 4. Run LLM analysis (evidence determination happens here)
                    logger.info(
                        f"[ANALYSIS] Running LLM analysis for question {question_id}"
                    )
                    result = await self._analyze_chunks(
                        question_data, similar_chunks, use_llm_scoring
                    )
                    logger.info(
                        f"[ANALYSIS] LLM analysis complete for question {question_id}"
                    )

                    # Process evidence and update chunks
                    if "EVIDENCE" in result:
                        logger.info(
                            f"Processing {len(result['EVIDENCE'])} evidence items"
                        )
                        evidence_items = []
                        for evidence_idx, evidence in enumerate(result["EVIDENCE"]):
                            # Extract chunk number from evidence
                            if isinstance(evidence, dict):
                                chunk_num = evidence.get("chunk")
                                if chunk_num is not None:
                                    chunk_idx = (
                                        chunk_num - 1
                                    )  # Convert to 0-based index
                                    if 0 <= chunk_idx < len(similar_chunks):
                                        # Update chunk information - ONLY set evidence flags, NOT llm_score
                                        similar_chunks[chunk_idx].update(
                                            {
                                                "is_evidence": True,
                                                "evidence_order": evidence_idx + 1,
                                            }
                                        )
                                        # Add evidence item with chunk reference and preserve LLM's evidence text
                                        evidence_items.append(
                                            {
                                                "chunk": chunk_num,
                                                "text": evidence.get(
                                                    "text", ""
                                                ),  # Keep LLM's evidence text
                                                "chunk_text": similar_chunks[chunk_idx][
                                                    "text"
                                                ],  # Store full chunk text separately
                                                "score": evidence.get("score", 1.0),
                                                "order": evidence_idx + 1,
                                                "metadata": similar_chunks[chunk_idx][
                                                    "metadata"
                                                ],
                                            }
                                        )
                                        logger.info(
                                            f"Added evidence {evidence_idx + 1} from chunk {chunk_num}: {evidence.get('text', '')[:100]}..."
                                        )

                        # Replace evidence array with processed items
                        result["EVIDENCE"] = evidence_items
                        logger.info(f"Final evidence count: {len(evidence_items)}")
                    else:
                        logger.warning("No EVIDENCE field found in result")

                    # 5. Save complete analysis
                    logger.info(
                        f"[ANALYSIS] Saving analysis result for question {question_id}"
                    )

                    # Create config dict for cache manager
                    config = {
                        "chunk_size": self.chunk_params["chunk_size"],
                        "chunk_overlap": self.chunk_params["chunk_overlap"],
                        "top_k": self.chunk_params["top_k"],
                        "model": self.llm.model,
                        "question_set": self.question_set,
                    }

                    # Save analysis result
                    self.cache_manager.save_analysis(
                        file_path=file_path,
                        question_id=question_id,
                        result=result,
                        config=config,
                    )
                    logger.info(f"[ANALYSIS] Analysis saved for question {question_id}")

                    # 8. Yield the result
                    logger.info(
                        f"[ANALYSIS] Yielding result for question {question_id}"
                    )
                    yield {
                        "question_number": question_number,
                        "question_id": question_id,
                        "result": result,
                    }

                except Exception as e:
                    logger.error(
                        f"[ANALYSIS] Error processing question {question_number}: {str(e)}",
                        exc_info=True,
                    )
                    yield {
                        "error": f"Error processing question {question_number}: {str(e)}"
                    }

        except Exception as e:
            logger.error(
                f"[ANALYSIS] Error processing document: {str(e)}", exc_info=True
            )
            yield {"error": f"Error processing document: {str(e)}"}

    def _create_chunks(self, file_path: str) -> List[Dict[str, Any]]:
        """Create document chunks with embeddings"""
        try:
            logger.info(f"Creating chunks for {file_path}")
            reader = PyMuPDFReader()
            docs = reader.load(file_path=file_path)
            logger.info(f"Loaded {len(docs)} pages from document")

            # Convert the documents to text and create new Document objects
            text_chunks = []
            for doc in docs:
                nodes = self.text_splitter.split_text(doc.text)
                text_chunks.extend(
                    [
                        Document(
                            text=chunk,
                            metadata={
                                **doc.metadata,
                                "chunk_size": self.chunk_params["chunk_size"],
                                "chunk_overlap": self.chunk_params["chunk_overlap"],
                            },
                        )
                        for chunk in nodes
                    ]
                )

            logger.info(f"Created {len(text_chunks)} chunks")

            # Compute embeddings in batches
            BATCH_SIZE = 100  # Process 100 chunks at a time
            chunks_data = []

            for i in range(0, len(text_chunks), BATCH_SIZE):
                batch = text_chunks[i : i + BATCH_SIZE]
                logger.info(
                    f"Computing embeddings for batch {i//BATCH_SIZE + 1}/{(len(text_chunks)-1)//BATCH_SIZE + 1}"
                )

                # Get text from batch and clean it
                batch_texts = []
                for chunk in batch:
                    # Clean and validate text
                    text = chunk.text.strip()
                    if text and len(text) > 0:
                        # Remove any null characters and normalize whitespace
                        text = " ".join(text.replace("\x00", "").split())
                        batch_texts.append(text)
                    else:
                        logger.warning(f"Skipping empty or invalid chunk")
                        continue

                try:
                    # Only compute embeddings if we have valid texts
                    if batch_texts:
                        logger.info(
                            f"Computing embeddings for {len(batch_texts)} texts in batch"
                        )
                        batch_embeddings = self.embeddings.get_text_embedding_batch(
                            batch_texts
                        )
                        logger.info(
                            f"Successfully computed {len(batch_embeddings)} embeddings"
                        )

                        # Create chunk dictionaries with embeddings
                        for chunk, embedding in zip(batch, batch_embeddings):
                            if (
                                embedding is not None
                            ):  # Only add chunks with valid embeddings
                                chunk_dict = {
                                    "text": chunk.text,
                                    "metadata": chunk.metadata,
                                    "embedding": np.array(embedding, dtype=np.float32),
                                    "similarity": 0.0,  # Will be populated during analysis
                                    "computed_score": 0.0,  # Will be populated during analysis
                                }
                                chunks_data.append(chunk_dict)
                                logger.debug(
                                    f"Added chunk with text length {len(chunk.text)}"
                                )
                            else:
                                logger.warning(f"Skipping chunk - embedding is None")

                except Exception as e:
                    logger.error(
                        f"Error computing embeddings for batch: {str(e)}", exc_info=True
                    )
                    # Continue with next batch, storing chunks without embeddings
                    for chunk in batch:
                        chunk_dict = {
                            "text": chunk.text,
                            "metadata": chunk.metadata,
                            "embedding": None,
                            "similarity": 0.0,
                            "computed_score": 0.0,
                        }
                        chunks_data.append(chunk_dict)
                        logger.warning(f"Added chunk without embedding due to error")

            # Log embedding statistics
            chunks_with_embeddings = sum(
                1 for c in chunks_data if c["embedding"] is not None
            )
            logger.info(
                f"Created {len(chunks_data)} chunks, {chunks_with_embeddings} with embeddings"
            )

            # Only save chunks that have valid embeddings
            valid_chunks = [c for c in chunks_data if c["embedding"] is not None]
            if valid_chunks:
                logger.info(f"Saving {len(valid_chunks)} valid chunks to cache")
                try:
                    self.cache_manager.save_vectors(file_path, valid_chunks)
                    logger.info(f"Successfully saved chunks and vectors to cache")
                except Exception as e:
                    logger.error(
                        f"Failed to save vectors to cache: {str(e)}", exc_info=True
                    )
            else:
                logger.warning("No valid chunks to save to cache")

            return chunks_data

        except Exception as e:
            logger.error(f"Error creating chunks: {str(e)}", exc_info=True)
            raise

    async def _analyze_chunks(
        self,
        question_data: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        use_llm_scoring: bool = False,
    ) -> Dict[str, Any]:
        """Analyze chunks using LLM to extract evidence and generate answer."""
        try:
            logger.info(
                f"Analyzing {len(chunks)} chunks for question: {question_data['text'][:100]}..."
            )

            # Process chunks first
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
                # Get similarity score from either 'score' (from vector store) or 'similarity_score' (from cache)
                similarity_score = chunk.get(
                    "score", chunk.get("similarity_score", 0.0)
                )

                # Get LLM score if it exists (independent of evidence)
                llm_score = chunk.get("llm_score", None)

                chunk_data = {
                    "id": chunk.get("id"),
                    "text": chunk["text"],
                    "chunk_order": i,
                    "similarity_score": similarity_score,
                    "llm_score": llm_score,  # Use existing LLM score if available
                    "is_evidence": False,
                    "evidence_order": None,
                    "metadata": chunk.get("metadata", {}),
                    "relevance_metadata": {},
                }
                processed_chunks.append(chunk_data)
                logger.debug(
                    f"Processed chunk with similarity score: {similarity_score:.4f}, llm_score: {llm_score}"
                )

            # Create analysis prompt with indexed chunks
            messages = self.prompt_manager.get_analysis_messages(
                question=question_data["text"],
                context="",
                guidelines=question_data.get("guidelines", ""),
                chunks_data=[
                    {
                        "index": i + 1,  # Use 1-based indexing for LLM
                        "text": c["text"],
                        "metadata": c["metadata"],
                    }
                    for i, c in enumerate(processed_chunks)
                ],
            )

            # Log the exact messages being sent to the LLM
            logger.info("=== LLM Input Messages ===")
            for msg in messages:
                if isinstance(msg, ChatMessage):
                    logger.info(f"Role: {msg.role}")
                    logger.info(f"Content: {msg.content}")
                else:
                    logger.warning(f"Unexpected message type: {type(msg)}")
            logger.info("=== End LLM Input Messages ===")

            # Get LLM response
            try:
                response = await self.llm.achat(messages)
                response_text = (
                    response.message.content
                )  # Changed from response.content to response.message.content
                logger.info("=== LLM Response ===")
                logger.info(response_text)
                logger.info("=== End LLM Response ===")
            except Exception as e:
                logger.error(f"Error getting LLM response: {str(e)}")
                raise

            # Parse the response
            try:
                result = json.loads(response_text)
                logger.info("=== Parsed Result ===")
                logger.info(json.dumps(result, indent=2))
                logger.info("=== End Parsed Result ===")
            except json.JSONDecodeError:
                logger.warning("Response is not valid JSON, attempting to extract")
                import re

                json_match = re.search(r"({.*})", response_text, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                        logger.info("=== Extracted and Parsed Result ===")
                        logger.info(json.dumps(result, indent=2))
                        logger.info("=== End Extracted and Parsed Result ===")
                    except json.JSONDecodeError:
                        logger.error("Failed to extract valid JSON from response")
                        result = {
                            "ANSWER": response_text,
                            "SCORE": 0,
                            "EVIDENCE": [],
                            "GAPS": ["Error parsing response"],
                            "SOURCES": [],
                        }
                else:
                    result = {
                        "ANSWER": response_text,
                        "SCORE": 0,
                        "EVIDENCE": [],
                        "GAPS": ["Error parsing response"],
                        "SOURCES": [],
                    }

            # Add question information to result
            result["question_text"] = question_data["text"]
            result["guidelines"] = question_data.get("guidelines", "")

            # Process evidence and update chunks
            if "EVIDENCE" in result:
                logger.info(f"Processing {len(result['EVIDENCE'])} evidence items")
                evidence_items = []
                for evidence_idx, evidence in enumerate(result["EVIDENCE"]):
                    # Extract chunk number from evidence
                    if isinstance(evidence, dict):
                        chunk_num = evidence.get("chunk")
                        if chunk_num is not None:
                            chunk_idx = chunk_num - 1  # Convert to 0-based index
                            if 0 <= chunk_idx < len(processed_chunks):
                                # Update chunk information - ONLY set evidence flags, NOT llm_score
                                processed_chunks[chunk_idx].update(
                                    {
                                        "is_evidence": True,
                                        "evidence_order": evidence_idx + 1,
                                    }
                                )
                                # Add evidence item with chunk reference and preserve LLM's evidence text
                                evidence_items.append(
                                    {
                                        "chunk": chunk_num,
                                        "text": evidence.get(
                                            "text", ""
                                        ),  # Keep LLM's evidence text
                                        "chunk_text": processed_chunks[chunk_idx][
                                            "text"
                                        ],  # Store full chunk text separately
                                        "score": evidence.get("score", 1.0),
                                        "order": evidence_idx + 1,
                                        "metadata": processed_chunks[chunk_idx][
                                            "metadata"
                                        ],
                                    }
                                )
                                logger.info(
                                    f"Added evidence {evidence_idx + 1} from chunk {chunk_num}: {evidence.get('text', '')[:100]}..."
                                )

                # Replace evidence array with processed items
                result["EVIDENCE"] = evidence_items
                logger.info(f"Final evidence count: {len(evidence_items)}")
            else:
                logger.warning("No EVIDENCE field found in result")

            # Add processed chunks to result
            result["chunks"] = processed_chunks
            logger.info(
                f"Analysis complete. Found {sum(1 for c in processed_chunks if c['is_evidence'])} evidence chunks"
            )
            return result

        except Exception as e:
            logger.error(f"Error analyzing chunks: {str(e)}", exc_info=True)
            return {
                "ANSWER": f"Error analyzing document: {str(e)}",
                "SCORE": 0,
                "EVIDENCE": [],
                "GAPS": ["Error during analysis"],
                "SOURCES": [],
                "chunks": processed_chunks if "processed_chunks" in locals() else [],
                "question_text": question_data["text"],
                "guidelines": question_data.get("guidelines", ""),
            }

    def _load_questions(self) -> dict:
        """Load questions from YAML files"""
        # Look for question set file in multiple possible locations
        possible_paths = [
            Path(__file__).parent.parent
            / "questionsets"
            / f"{self.question_set}_questions.yaml",  # app/questionsets
            Path(__file__).parent.parent.parent
            / "questionsets"
            / f"{self.question_set}_questions.yaml",  # project root
            Path.cwd()
            / "questionsets"
            / f"{self.question_set}_questions.yaml",  # current working directory
        ]

        log_analysis_step(f"Looking for {self.question_set}_questions.yaml in:")
        for path in possible_paths:
            log_analysis_step(f"- {path.resolve()}")

        yaml_file = None
        for path in possible_paths:
            if path.exists():
                yaml_file = path
                log_analysis_step(f"✓ Found questions file at: {path.resolve()}")
                break

        if not yaml_file:
            log_analysis_step(
                f"Could not find questions file for {self.question_set} in any of: {[str(p) for p in possible_paths]}",
                "error",
            )
            return {}

        try:
            with open(yaml_file, "r") as f:
                config = yaml.safe_load(f)
                log_analysis_step(
                    f"Loaded YAML content: {str(config)[:200]}..."
                )  # Show first 200 chars

                questions = {}
                # Convert the questions list into a structured format
                for q in config.get("questions", []):
                    q_id = q.get("id", "")
                    if q_id:
                        questions[q_id] = {
                            "text": q.get("text", ""),
                            "guidelines": q.get("guidelines", ""),
                        }
                        log_analysis_step(
                            f"Added question {q_id}: {questions[q_id]['text'][:50]}..."
                        )

                log_analysis_step(
                    f"✓ Loaded {len(questions)} questions for {self.question_set}"
                )
                log_analysis_step(f"Available question IDs: {list(questions.keys())}")
                return questions
        except Exception as e:
            log_analysis_step(f"Error loading questions: {str(e)}", "error")
            logger.exception("Full error:")  # This will log the full traceback
            return {}

    def get_question_by_number(self, number: int) -> Optional[Dict]:
        """Get question data by its number."""
        try:
            # Handle question set to prefix mapping
            question_set_mapping = {
                "everest": "ev",
                "tcfd": "tcfd",
                "s4m": "s4m",
                "lucia": "lucia",
            }

            # Get the correct prefix for the question set
            question_prefix = question_set_mapping.get(
                self.question_set, self.question_set
            )
            question_key = f"{question_prefix}_{number}"

            logger.debug(f"Looking for question {number} with key: {question_key}")
            logger.debug(f"Available question keys: {list(self.questions.keys())}")

            return self.questions.get(question_key)
        except Exception as e:
            log_analysis_step(f"Error getting question {number}: {str(e)}", "error")
            logger.exception("Full error:")
            return None

    def update_parameters(self, chunk_size: int, chunk_overlap: int, top_k: int):
        """Update analysis parameters and recreate text splitter."""
        logger.info(
            f"Updating parameters: size={chunk_size}, overlap={chunk_overlap}, top_k={top_k}"
        )

        self.chunk_params = {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "top_k": top_k,
        }

        # Recreate text splitter with new parameters
        self.text_splitter = SentenceSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

        logger.info(f"Updated parameters and recreated text splitter")

    def update_llm_model(self, model_name: str):
        """Update the LLM model."""
        log_analysis_step(f"Updating LLM model to: {model_name}")

        # Initialize LLM with caching using the provider factory
        self.llm = get_llm(
            model_name=model_name,
            cache_dir=str(self.llm_cache_path),
        )

    def get_all_cached_answers(self, question_set: str) -> Dict[str, Any]:
        """Get all cached answers for a question set"""
        return self.cache_manager.get_all_answers_by_question_set(question_set)

    def update_question_set(self, question_set: str):
        """Update the question set and reload questions."""
        self.question_set = question_set
        self.questions = self._load_questions()

    def check_step_completion(self, file_path: str) -> Dict[str, bool]:
        """Check which steps are completed for a file with current configuration"""
        try:
            config = {
                "chunk_size": self.chunk_params["chunk_size"],
                "chunk_overlap": self.chunk_params["chunk_overlap"],
                "top_k": self.chunk_params["top_k"],
                "model": self.llm.model if self.llm and hasattr(self.llm, "model") else self.default_model,
                "question_set": self.question_set,
            }

            # Check step 1: Chunks without embeddings
            chunks_without_embeddings = self.cache_manager.get_chunks_without_embeddings(
                file_path=file_path,
                chunk_size=config["chunk_size"],
                chunk_overlap=config["chunk_overlap"],
            )
            step1_complete = len(chunks_without_embeddings) > 0

            # Check step 2: Chunks with embeddings
            chunks_with_embeddings = self.cache_manager.get_document_chunks(
                file_path=file_path,
                chunk_size=config["chunk_size"],
                chunk_overlap=config["chunk_overlap"],
            )
            step2_complete = (
                len(chunks_with_embeddings) > 0
                and any(c.get("embedding") is not None for c in chunks_with_embeddings)
            )

            # Check step 3: Chunk scoring (check if any questions have been scored)
            step3_complete = self.cache_manager.has_chunk_scoring(file_path, config)

            # Check step 4: Full analysis (check if any questions have been analyzed)
            step4_complete = len(self.cache_manager.get_analysis(file_path, config)) > 0

            return {
                "chunks": step1_complete,
                "embeddings": step2_complete,
                "scoring": step3_complete,
                "analysis": step4_complete,
            }

        except Exception as e:
            logger.error(f"Error checking step completion: {str(e)}")
            return {
                "chunks": False,
                "embeddings": False,
                "scoring": False,
                "analysis": False,
            }

    def _parse_config_from_filename(self, filename: str) -> Dict[str, Any]:
        """Parse configuration parameters from a cache filename.

        Args:
            filename: The filename (without extension) to parse

        Returns:
            Dict containing the parsed configuration parameters
        """
        config = {
            "chunk_size": 500,  # Default values
            "overlap": 20,
            "top_k": 5,
            "model": "gpt-3.5-turbo-1106",
            "question_set": "tcfd",
        }

        try:
            # Split filename into parts
            parts = filename.split("_")

            for part in parts:
                if part.startswith("cs"):
                    config["chunk_size"] = int(part[2:])
                elif part.startswith("ov"):
                    config["overlap"] = int(part[2:])
                elif part.startswith("tk"):
                    config["top_k"] = int(part[2:])
                elif part.startswith("m"):
                    config["model"] = part[1:]
                elif part.startswith("qs"):
                    config["question_set"] = part[2:]

            return config

        except Exception as e:
            logger.warning(f"Error parsing config from filename {filename}: {e}")
            return config

    async def _get_similar_chunks(
        self, query_text: str, chunks: List[Dict], top_k: int
    ) -> List[Dict]:
        """
        Get chunks most similar to the query text using vector similarity.

        Args:
            query_text: The text to compare chunks against
            chunks: List of document chunks
            top_k: Number of most similar chunks to return

        Returns:
            List of most similar chunks with similarity scores
        """
        try:
            logger.info(f"Getting similar chunks for query: {query_text[:50]}...")

            # Get embedding for the query
            query_embedding = self.embeddings.get_text_embedding(query_text)

            # Ensure the embedding is a numpy array with the correct dtype
            query_embedding = np.array(query_embedding, dtype=np.float32)

            # Use cache_manager to get similar chunks
            similar_chunks = await self.cache_manager.get_similar_chunks(
                query_embedding=query_embedding,
                file_path=self.current_file_path,
                top_k=top_k,
                chunk_size=self.chunk_params["chunk_size"],
                chunk_overlap=self.chunk_params["chunk_overlap"],
            )

            logger.info(f"Found {len(similar_chunks)} similar chunks")
            return similar_chunks

        except Exception as e:
            logger.error(f"Error getting similar chunks: {str(e)}", exc_info=True)
            return []

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the LLM response to extract structured analysis data.

        Args:
            response_text: The raw text response from the LLM

        Returns:
            Dict containing structured analysis data
        """
        try:
            logger.info(f"Parsing analysis response: {response_text[:100]}...")

            # Initialize result structure
            result = {
                "ANSWER": "",
                "SCORE": 0,
                "EVIDENCE": [],
                "GAPS": [],
                "SOURCES": [],
            }

            # Try to parse as JSON
            try:
                parsed_json = json.loads(response_text)

                # Update result with parsed JSON
                if "ANSWER" in parsed_json:
                    result["ANSWER"] = parsed_json["ANSWER"]

                if "SCORE" in parsed_json:
                    try:
                        result["SCORE"] = float(parsed_json["SCORE"])
                    except (ValueError, TypeError):
                        # Try to extract a number if it's not a valid float
                        if isinstance(parsed_json["SCORE"], str):
                            import re

                            score_match = re.search(
                                r"\d+(\.\d+)?", parsed_json["SCORE"]
                            )
                            if score_match:
                                result["SCORE"] = float(score_match.group(0))

                if "EVIDENCE" in parsed_json:
                    evidence_list = []
                    for evidence in parsed_json["EVIDENCE"]:
                        if isinstance(evidence, dict):
                            # Extract chunk number
                            chunk = evidence.get("chunk")
                            if chunk is not None:
                                evidence_item = {
                                    "chunk_index": int(chunk)
                                    - 1,  # Convert to 0-based index
                                    "order": len(evidence_list) + 1,
                                    "score": 1.0,  # Default score
                                    "text": evidence.get("text", ""),
                                }
                                evidence_list.append(evidence_item)
                    result["EVIDENCE"] = evidence_list

                if "GAPS" in parsed_json:
                    result["GAPS"] = parsed_json["GAPS"]

                if "SOURCES" in parsed_json:
                    result["SOURCES"] = parsed_json["SOURCES"]

                return result

            except json.JSONDecodeError:
                logger.warning(f"Response is not valid JSON: {response_text[:100]}...")

                # Try to extract JSON from the response
                import re

                json_match = re.search(r"({.*})", response_text, re.DOTALL)
                if json_match:
                    try:
                        parsed_json = json.loads(json_match.group(1))
                        # Recursively call this method with the extracted JSON
                        return self._parse_analysis_response(json_match.group(1))
                    except json.JSONDecodeError:
                        logger.error("Failed to extract valid JSON from response")

                # If JSON parsing fails, try to extract sections using markdown headers
                sections = response_text.split("###")

                for section in sections:
                    section = section.strip()
                    if not section:
                        continue

                    # Extract section name and content
                    parts = section.split("\n", 1)
                    if len(parts) < 2:
                        continue

                    section_name = parts[0].strip().upper()
                    section_content = parts[1].strip()

                    if section_name == "ANSWER":
                        result["ANSWER"] = section_content
                    elif section_name == "SCORE":
                        try:
                            result["SCORE"] = float(section_content)
                        except ValueError:
                            # If score is not a valid float, extract first number found
                            import re

                            score_match = re.search(r"\d+(\.\d+)?", section_content)
                            if score_match:
                                result["SCORE"] = float(score_match.group(0))
                    elif section_name == "EVIDENCE":
                        # Parse evidence items
                        evidence_items = []
                        for line in section_content.split("\n"):
                            line = line.strip()
                            if not line:
                                continue

                            # Try to extract chunk index
                            import re

                            chunk_match = re.search(r"\[CHUNK (\d+)\]", line)
                            if chunk_match:
                                evidence_item = {
                                    "chunk_index": int(chunk_match.group(1))
                                    - 1,  # Convert to 0-based index
                                    "order": len(evidence_items) + 1,
                                    "score": 1.0,  # Default score
                                    "text": line,
                                }
                                evidence_items.append(evidence_item)

                        result["EVIDENCE"] = evidence_items
                    elif section_name == "GAPS":
                        result["GAPS"] = [
                            line.strip()
                            for line in section_content.split("\n")
                            if line.strip()
                        ]
                    elif section_name == "SOURCES":
                        result["SOURCES"] = [
                            int(s.strip())
                            for s in section_content.split(",")
                            if s.strip().isdigit()
                        ]

                return result

        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}", exc_info=True)
            return {
                "ANSWER": f"Error parsing analysis: {str(e)}",
                "SCORE": 0,
                "EVIDENCE": [],
                "GAPS": ["Error during analysis"],
                "SOURCES": [],
            }


def create_analysis_dataframes(results: Dict) -> pd.DataFrame:
    """Create analysis dataframes with proper type handling"""
    analysis_rows = []

    # Get analyzer instance to access questions
    analyzer = DocumentAnalyzer()
    questions = analyzer.questions

    for question_id, data in results.items():
        # Skip empty results
        if not data:
            continue

        # Get question text from analyzer's questions data
        question_text = questions.get(question_id, {}).get(
            "text", f"Question {question_id}"
        )

        # Convert lists to strings and ensure proper types
        row = {
            "Question ID": str(question_id),
            "Question": str(question_text),
            "Analysis": str(data.get("ANSWER", "")),
            "Score": float(data.get("SCORE", 0)),
            "Key Evidence": ", ".join([str(x) for x in data.get("EVIDENCE", [])]),
            "Gaps": ", ".join([str(x) for x in data.get("GAPS", [])]),
            "Sources": ", ".join([str(x) for x in data.get("SOURCES", [])]),
        }
        analysis_rows.append(row)

    # Create DataFrame with explicit dtypes
    df = pd.DataFrame(analysis_rows)
    if not df.empty:
        df = df.astype(
            {
                "Question ID": "string",
                "Question": "string",
                "Analysis": "string",
                "Score": "float64",
                "Key Evidence": "string",
                "Gaps": "string",
                "Sources": "string",
            }
        )

    return df
