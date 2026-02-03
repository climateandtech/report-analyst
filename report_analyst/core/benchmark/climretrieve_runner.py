"""
ClimRetrieve Benchmark Runner

This module orchestrates the full ClimRetrieve evaluation workflow:
1. Load ground truth dataset
2. Use ground truth paragraphs as retrieval pool (ensures exact matching)
3. Generate query strategies (IR, IR3, question)
4. Embed and retrieve paragraphs from ground truth pool
5. Format results and evaluate against ground truth

Key features:
- Uses ground truth paragraphs as retrieval pool (ensures exact matching for evaluation)
- Embeds paragraphs from ground truth for each (report, question) pair
- Fixes sanitization mismatch (queries are sanitized before embedding)
- Implements same evaluation logic as benchmark_climretrieve_one_model.py directly:
  - Relevance threshold: >= 1 is relevant (default)
  - nDCG gain scheme: exponential (default)
  - Direct pandas merge matching on (report, question, paragraph) columns
  - Macro-averaged metrics across queries
"""

import hashlib
import re
import logging
import time
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import requests
except ImportError:
    requests = None

try:
    import openpyxl  # Required for reading Excel files
except ImportError:
    openpyxl = None

from ..analyzer import DocumentAnalyzer
from .climretrieve_io import load_climretrieve_labels
from .evaluation_engine import EvaluationEngine
from .retrieval_results_loader import load_flexible_dataset_from_csv
from llama_index.readers.file import PyMuPDFReader
from ...models.benchmark import (
    BenchmarkDataset,
    DatasetType,
    EvaluationMetrics,
    FlexibleDatasetRow,
)

logger = logging.getLogger(__name__)


class QueryStrategyGenerator(ABC):
    """Abstract base class for generating query strategies from questions."""

    @abstractmethod
    def generate_ir_query(self, question: str) -> str:
        """Generate IR (Information Retrieval) query from question."""
        pass

    @abstractmethod
    def generate_ir3_query(self, question: str) -> str:
        """Generate IR3 query (top 3 keywords) from question."""
        pass

    @abstractmethod
    def generate_question_query(self, question: str) -> str:
        """Generate query using full question text."""
        pass


class DefaultQueryStrategyGenerator(QueryStrategyGenerator):
    """Default implementation of query strategy generator.
    
    This is a simple implementation. Users can provide their own
    QueryStrategyGenerator with more sophisticated logic.
    """

    def generate_ir_query(self, question: str) -> str:
        """Extract keywords from question for IR query."""
        # Simple implementation: remove common stop words and use remaining words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "should", "could", "may", "might", "must", "can", "this",
            "that", "these", "those", "what", "which", "who", "whom", "whose",
            "where", "when", "why", "how", "does", "do", "set", "by", "the"
        }
        words = question.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return " ".join(keywords)

    def generate_ir3_query(self, question: str) -> str:
        """Extract top 3 keywords from question for IR3 query."""
        # Simple implementation: take first 3 significant words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "should", "could", "may", "might", "must", "can", "this",
            "that", "these", "those", "what", "which", "who", "whom", "whose",
            "where", "when", "why", "how", "does", "do", "set", "by", "the"
        }
        words = question.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return " ".join(keywords[:3])

    def generate_question_query(self, question: str) -> str:
        """Use full question text as query."""
        return question


class ClimRetrieveRunner:
    """Runner for ClimRetrieve benchmark evaluation."""

    def __init__(
        self,
        reports_dir: Optional[str | Path] = None,
        ground_truth_path: Optional[str | Path] = None,
        queries_dir: Optional[str | Path] = None,
        query_strategy_generator: Optional[QueryStrategyGenerator] = None,
        top_k: int = 10,
        chunk_size: int = 350,
        chunk_overlap: int = 50,
        output_dir: Optional[str | Path] = None,
    ):
        """
        Initialize ClimRetrieve runner.

        Args:
            reports_dir: Directory containing PDF reports (default: core/reports/)
            ground_truth_path: Path to ClimRetrieve labels CSV file 
                              (default: core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv)
            queries_dir: Directory containing query Excel files 
                        (default: core/Embedding_Search_Queries/)
            query_strategy_generator: Optional custom query strategy generator.
                                     If None and queries_dir provided, loads from Excel files.
                                     If None and no queries_dir, uses DefaultQueryStrategyGenerator
            top_k: Number of top chunks to retrieve per query
            chunk_size: Size of chunks for document processing
            chunk_overlap: Overlap between chunks
            output_dir: Directory to save results (default: core/benchmark/climretrieve/results)
        """
        # Set default paths relative to this file
        core_dir = Path(__file__).parent
        
        if reports_dir:
            self.reports_dir = Path(reports_dir)
        else:
            # Default: core/reports/
            self.reports_dir = core_dir.parent / "reports"
        
        if ground_truth_path:
            self.ground_truth_path = Path(ground_truth_path)
        else:
            # Default: core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv
            self.ground_truth_path = core_dir / "climretrieve" / "labels" / "ClimRetrieve_ReportLevel_V1.csv"
        
        if queries_dir:
            self.queries_dir = Path(queries_dir)
        else:
            # Default: core/Embedding_Search_Queries/
            self.queries_dir = core_dir.parent / "Embedding_Search_Queries"
        
        self.query_strategy_generator = query_strategy_generator
        self.top_k = top_k
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Set output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            # Default to core/benchmark/climretrieve/results
            self.output_dir = core_dir / "climretrieve" / "results"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up embedding cache directory (disk-based caching)
        self.embedding_cache_dir = core_dir / "climretrieve" / "cache_embeddings"
        self.embedding_cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Embedding cache directory: {self.embedding_cache_dir}")
        
        # Load queries from Excel files if queries_dir exists
        self.query_cache: Dict[str, Dict[str, str]] = {}
        if self.queries_dir.exists():
            self._load_queries_from_excel()
        
        # Initialize DocumentAnalyzer
        self.analyzer = DocumentAnalyzer()
        self.analyzer.chunk_params = {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "top_k": self.top_k,
        }

        # Initialize EvaluationEngine
        self.evaluation_engine = EvaluationEngine()

        # Cache for processed reports
        self._report_chunks_cache: Dict[str, List[Dict]] = {}

        logger.info(f"Initialized ClimRetrieveRunner")
        logger.info(f"  Reports directory: {self.reports_dir}")
        logger.info(f"  Ground truth: {self.ground_truth_path}")
        logger.info(f"  Queries directory: {self.queries_dir}")
        logger.info(f"  Output directory: {self.output_dir}")
        logger.info(f"  Top-K: {self.top_k}, Chunk size: {self.chunk_size}, Overlap: {self.chunk_overlap}")
        if self.query_cache:
            logger.info(f"  Loaded queries for {len(self.query_cache)} questions")
    
    def clear_embedding_cache(self) -> None:
        """Clear all cached embeddings."""
        if self.embedding_cache_dir.exists():
            cache_files = list(self.embedding_cache_dir.glob("*.npy"))
            for cache_file in cache_files:
                cache_file.unlink()
            logger.info(f"Cleared {len(cache_files)} cached embedding files")
            print(f"Cleared {len(cache_files)} cached embedding files")
        else:
            logger.info("No embedding cache directory found")

    def _load_queries_from_excel(self) -> None:
        """Load queries from Excel files in queries_dir."""
        if not self.queries_dir.exists():
            logger.warning(f"Queries directory does not exist: {self.queries_dir}")
            return
        
        # Try to load from available files
        available_files = list(self.queries_dir.glob("*.xlsx"))
        logger.info(f"Found {len(available_files)} query Excel files in {self.queries_dir}")
        
        if not available_files:
            logger.warning("No Excel query files found, will use query generator")
            return
        
        # Try to load files with IR queries (prefer question_with_IR_150len as default)
        ir_file = None
        # First priority: question_with_IR_150len (default)
        for file in available_files:
            if "question_with_IR_150len" in file.name.lower():
                ir_file = file
                break
        # Second priority: any file with 150len (not noQ)
        if not ir_file:
            for file in available_files:
                if "150len" in file.name and "noQ" not in file.name:
                    ir_file = file
                    break
        # Third priority: any file without noQ
        if not ir_file:
            for file in available_files:
                if "noQ" not in file.name:
                    ir_file = file
                    break
        
        # Try to load files with question queries (noQ files)
        question_file = None
        for file in available_files:
            if "150len" in file.name and "noQ" in file.name:
                question_file = file
                break
        if not question_file:
            for file in available_files:
                if "noQ" in file.name:
                    question_file = file
                    break
        
        # Load IR queries
        if ir_file:
            logger.info(f"Loading IR queries from: {ir_file.name}")
            try:
                if openpyxl is None:
                    logger.warning("openpyxl not installed, cannot read Excel files. Install with: pip install openpyxl")
                    return
                df_ir = pd.read_excel(ir_file, engine='openpyxl')
                logger.info(f"Loaded query file '{ir_file.name}' with columns: {list(df_ir.columns)}")
                # Load all strategies from this file (IR, IR3, question) - column names match strategies
                self._parse_query_file(df_ir, ["IR", "IR3", "question"])
            except Exception as e:
                logger.error(f"Error loading IR queries: {e}", exc_info=True)
        
        # Load question queries (if separate file)
        if question_file and question_file != ir_file:
            logger.info(f"Loading question queries from: {question_file.name}")
            try:
                if openpyxl is None:
                    logger.warning("openpyxl not installed, cannot read Excel files. Install with: pip install openpyxl")
                    return
                df_q = pd.read_excel(question_file, engine='openpyxl')
                logger.info(f"Loaded question file with columns: {list(df_q.columns)}")
                self._parse_query_file(df_q, ["question"])
            except Exception as e:
                logger.error(f"Error loading question queries: {e}", exc_info=True)
        
        if not self.query_cache:
            logger.warning("No queries loaded from Excel files, will use query generator")
        else:
            logger.info(f"Loaded queries for {len(self.query_cache)} questions")

    def _parse_query_file(self, df: pd.DataFrame, strategies: List[str]) -> None:
        """Parse a query DataFrame and populate query_cache.
        
        The Excel file should have columns named exactly as the strategies:
        - "question" or column with "question" in name (for question text)
        - "IR" (for IR queries)
        - "IR3" (for IR3 queries)
        - "question" (for question queries, can be same as question column)
        """
        # Find question column (for matching questions)
        question_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if "question" in col_lower and question_col is None:
                question_col = col
        
        if question_col is None:
            # Try first column as fallback
            question_col = df.columns[0]
            logger.warning(f"No 'question' column found, using first column: {question_col}")
        
        # Find strategy columns (exact match or case-insensitive)
        # Map known column name variations to strategies
        column_to_strategy_map = {
            "IR": "IR",
            "ir": "IR",
            "IR_three": "IR3",
            "ir_three": "IR3",
            "IR3": "IR3",
            "ir3": "IR3",
            "question": "question",
            "Question": "question",
        }
        
        strategy_columns = {}
        for strategy in strategies:
            strategy_upper = strategy.upper()
            strategy_lower = strategy.lower()
            
            # First, try known column name mappings
            found = False
            for col in df.columns:
                if col in column_to_strategy_map and column_to_strategy_map[col] == strategy:
                    strategy_columns[strategy] = col
                    found = True
                    break
            
            if not found:
                # Try exact match
                if strategy in df.columns:
                    strategy_columns[strategy] = strategy
                elif strategy_upper in df.columns:
                    strategy_columns[strategy] = strategy_upper
                elif strategy_lower in df.columns:
                    strategy_columns[strategy] = strategy_lower
                else:
                    # Try case-insensitive partial match
                    for col in df.columns:
                        if col.upper() == strategy_upper or col.lower() == strategy_lower:
                            strategy_columns[strategy] = col
                            break
        
        logger.info(f"Found strategy columns: {strategy_columns}")
        logger.info(f"All available columns: {list(df.columns)}")
        
        # Build query cache: question -> {IR: ..., IR3: ..., question: ...}
        for _, row in df.iterrows():
            question = str(row[question_col]).strip()
            if not question or question.lower() in ["nan", "none", ""]:
                continue
            
            # Initialize cache for this question if needed
            if question not in self.query_cache:
                self.query_cache[question] = {}
            
            # Load queries for each strategy from their respective columns
            for strategy in strategies:
                if strategy in strategy_columns:
                    col_name = strategy_columns[strategy]
                    if col_name in row and pd.notna(row[col_name]):
                        query_text = str(row[col_name]).strip()
                        if query_text and query_text.lower() not in ["nan", "none", ""]:
                            self.query_cache[question][strategy] = query_text
                            logger.debug(f"Loaded {strategy} query for question: {query_text[:50]}...")
                elif strategy == "question":
                    # Question strategy can use the question column itself
                    self.query_cache[question]["question"] = question
                else:
                    logger.warning(f"Strategy '{strategy}' column not found in Excel file")

    def _get_query_for_strategy(self, question: str, strategy: str) -> str:
        """Get query for a given question and strategy."""
        # First try to get from cache
        if question in self.query_cache and strategy in self.query_cache[question]:
            query = self.query_cache[question][strategy]
            logger.debug(f"Using cached {strategy} query for question: {query}")
            return query
        
        # Fall back to query generator
        if not self.query_strategy_generator:
            self.query_strategy_generator = DefaultQueryStrategyGenerator()
        
        if strategy == "IR":
            query = self.query_strategy_generator.generate_ir_query(question)
        elif strategy == "IR3":
            query = self.query_strategy_generator.generate_ir3_query(question)
            logger.warning(f"IR3 query generated (only 3 words): '{query}' from question: '{question[:80]}...'")
        elif strategy == "question":
            query = self.query_strategy_generator.generate_question_query(question)
        else:
            query = question
        
        logger.debug(f"Generated {strategy} query: {query[:100]}...")
        return query

    def _sanitize_text_for_embedding(self, text: str, max_chars: int = 1500) -> str:
        """Sanitize text for embedding (matches reference implementation).
        
        Removes null bytes and control characters (except \n and \t), then collapses whitespace.
        This is used ONLY for embedding, original text is kept for matching.
        """
        # Handle non-string types (NaN, float, None, etc.)
        if text is None:
            return ""
        if not isinstance(text, str):
            # Convert to string, handling NaN and other types
            if isinstance(text, float) and (text != text):  # Check for NaN
                return ""
            text = str(text)
        if not text:
            return ""
        
        # Match reference implementation: keep \n and \t, remove other control chars
        sanitized = "".join(ch for ch in text if (ch == "\n" or ch == "\t" or ord(ch) >= 32))
        
        # Collapse all whitespace (including \n and \t) to single spaces
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        
        # Truncate if needed
        if max_chars and max_chars > 0 and len(sanitized) > max_chars:
            sanitized = sanitized[:max_chars]
        
        return sanitized
    
    def _normalize_text_for_chunk_id(self, text: str) -> str:
        """Normalize text for consistent chunk_id generation."""
        # Remove extra whitespace, normalize line breaks, and trim
        normalized = re.sub(r'\s+', ' ', str(text).strip())
        # Remove leading/trailing whitespace again after normalization
        return normalized.strip()
    
    def _find_report_file(self, report_name: str) -> Optional[Path]:
        """Find report PDF file matching the report name from dataset."""
        # Try exact match first
        report_path = self.reports_dir / report_name
        if report_path.exists():
            return report_path

        # Try case-insensitive match
        for pdf_file in self.reports_dir.glob("*.pdf"):
            if pdf_file.name.lower() == report_name.lower():
                return pdf_file

        # Try partial match (report name might be substring of filename)
        report_name_lower = report_name.lower()
        for pdf_file in self.reports_dir.glob("*.pdf"):
            if report_name_lower in pdf_file.name.lower() or pdf_file.name.lower() in report_name_lower:
                return pdf_file

        logger.warning(f"Could not find report file for: {report_name}")
        return None

    def _extract_paragraphs_from_pdf(self, report_path: Path) -> List[str]:
        """Extract all paragraphs from a PDF report.
        
        This extracts paragraphs as natural text units from the PDF,
        preserving the original paragraph structure. This expands the
        paragraph pool beyond just what's in the ground truth CSV.
        
        Args:
            report_path: Path to the PDF file
            
        Returns:
            List of paragraph texts extracted from the PDF
        """
        try:
            logger.info(f"Extracting paragraphs from PDF: {report_path.name}")
            reader = PyMuPDFReader()
            documents = reader.load_data(file_path=str(report_path))
            
            # Extract paragraphs from documents
            paragraphs = []
            for doc in documents:
                text = doc.text
                if not text or not text.strip():
                    continue
                
                # Split by double newlines (paragraph breaks)
                # This preserves natural paragraph boundaries
                para_splits = re.split(r'\n\s*\n+', text)
                
                for para in para_splits:
                    para = para.strip()
                    if not para:
                        continue
                    
                    # Remove excessive whitespace but preserve structure
                    para = re.sub(r'\s+', ' ', para)
                    para = para.strip()
                    
                    # Filter out very short paragraphs (likely headers/footers/noise)
                    # But be more lenient to capture all relevant content
                    if len(para) > 30:  # Minimum paragraph length
                        paragraphs.append(para)
                    elif len(para) > 15 and not para.isupper() and not para.isdigit():  # Allow shorter if meaningful
                        paragraphs.append(para)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_paragraphs = []
            for para in paragraphs:
                # Normalize for duplicate detection
                para_normalized = re.sub(r'\s+', ' ', para.strip().lower())
                if para_normalized not in seen and len(para_normalized) > 10:
                    seen.add(para_normalized)
                    unique_paragraphs.append(para)  # Keep original case/spacing
            
            logger.info(f"Extracted {len(unique_paragraphs)} unique paragraphs from {report_path.name}")
            return unique_paragraphs
            
        except Exception as e:
            logger.error(f"Error extracting paragraphs from PDF {report_path}: {e}", exc_info=True)
            return []

    async def _load_and_chunk_report(self, report_name: str) -> Optional[List[Dict]]:
        """Load and chunk a report, caching the result."""
        if report_name in self._report_chunks_cache:
            logger.info(f"Using cached chunks for {report_name}")
            return self._report_chunks_cache[report_name]

        report_path = self._find_report_file(report_name)
        if not report_path:
            return None

        logger.info(f"Loading and chunking report: {report_path.name}")
        try:
            chunks = self.analyzer._create_chunks(str(report_path))
            self._report_chunks_cache[report_name] = chunks
            logger.info(f"Created {len(chunks)} chunks for {report_name}")
            # Embeddings are automatically saved to cache by _create_chunks via cache_manager.save_vectors()
            logger.info(f"Embeddings saved to cache for {report_name}")
            return chunks
        except Exception as e:
            logger.error(f"Error processing report {report_name}: {e}", exc_info=True)
            return None

    def _get_embedding_provider_info(self) -> Tuple[str, str, bool]:
        """Get embedding provider information (Ollama or OpenAI)."""
        use_ollama = os.getenv("USE_OLLAMA_EMBEDDINGS", "false").lower() == "true"
        if use_ollama:
            model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            return model, base_url, True
        else:
            # OpenAI
            model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
            api_key = os.getenv("OPENAI_API_KEY", "")
            return model, api_key, False
    
    def _sha1_for_embeddings(self, model: str, provider_info: str, is_ollama: bool, paragraphs: List[str], max_chars: int = 1500) -> str:
        """
        Generate stable cache key for embeddings (matches reference implementation).
        
        Args:
            model: Embedding model name
            provider_info: Base URL (Ollama) or API key (OpenAI) - for cache key only
            is_ollama: Whether using Ollama
            paragraphs: List of paragraph texts
            max_chars: Max characters for truncation
            
        Returns:
            SHA1 hash string for cache key
        """
        h = hashlib.sha1()
        h.update(model.encode("utf-8"))
        h.update(str(is_ollama).encode("utf-8"))
        h.update(str(max_chars).encode("utf-8"))
        # Include provider info in hash (base_url for Ollama, or "openai" for OpenAI)
        if is_ollama:
            h.update(provider_info.encode("utf-8"))
        else:
            h.update(b"openai")  # Don't include API key in hash for security
        for p in paragraphs:
            p = "" if p is None else str(p)
            if max_chars is not None and max_chars > 0:
                p = p[:max_chars]
            h.update(p.encode("utf-8", errors="ignore"))
            h.update(b"\n")  # separator
        return h.hexdigest()
    
    def _embed_batch_ollama(self, base_url: str, model: str, texts: List[str], timeout: int = 180) -> List[List[float]]:
        """Embed batch using Ollama /api/embed endpoint (matches reference implementation)."""
        if requests is None:
            raise ImportError("requests library is required for Ollama embeddings")
        
        def _post(batch: List[str]) -> List[List[float]]:
            resp = requests.post(
                f"{base_url}/api/embed",
                json={"model": model, "input": batch},
                timeout=timeout,
            )
            if resp.status_code >= 400:
                raise requests.HTTPError(
                    f"HTTP {resp.status_code}: {resp.text[:500]}",
                    response=resp,
                )
            data = resp.json()
            if "embeddings" not in data:
                raise ValueError(f"Expected 'embeddings' in response, got keys={list(data.keys())}")
            embs = data["embeddings"]
            if not isinstance(embs, list) or len(embs) != len(batch):
                raise ValueError(f"Embeddings length mismatch: expected {len(batch)}, got {len(embs)}")
            return embs
        
        # First try (and one retry)
        last_exc = None
        for attempt in (1, 2):
            try:
                return _post(texts)
            except Exception as e:
                last_exc = e
                if attempt == 2:
                    break
                time.sleep(1.0)
        
        # Fallback: split batch recursively
        if len(texts) == 1:
            logger.warning(f"Ollama failed to embed a single paragraph. Using zero-vector fallback.")
            dim = 768  # Default for nomic-embed-text
            return [[0.0] * dim]
        
        mid = len(texts) // 2
        left = self._embed_batch_ollama(base_url, model, texts[:mid], timeout=timeout)
        right = self._embed_batch_ollama(base_url, model, texts[mid:], timeout=timeout)
        return left + right
    
    def _embed_batch_openai(self, api_key: str, model: str, texts: List[str]) -> List[List[float]]:
        """Embed batch using OpenAI API."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.embeddings.create(
                model=model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except ImportError:
            raise ImportError("openai library is required for OpenAI embeddings. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Error embedding with OpenAI: {e}")
            raise
    
    async def _embed_paragraphs(self, paragraphs: List[str], normalize: bool = True) -> List[Optional[np.ndarray]]:
        """Embed a list of paragraphs with disk-based caching (matches reference implementation).
        
        Args:
            paragraphs: List of paragraph texts to embed
            normalize: If True, normalize embeddings (L2 normalization) before returning
        """
        try:
            # Get embedding provider info
            model, provider_info, is_ollama = self._get_embedding_provider_info()
            
            # Generate cache key based on model, provider, paragraphs, and max_chars
            cache_key = self._sha1_for_embeddings(model, provider_info, is_ollama, paragraphs, max_chars=1500)
            cache_path = self.embedding_cache_dir / f"{cache_key}.npy"
            
            # Try to load from disk cache
            if cache_path.exists():
                logger.info(f"Loading embeddings from cache: {cache_path.name}")
                print(f"  Loading embeddings from cache...")
                emb = np.load(cache_path)
                logger.info(f"Loaded {len(emb)} embeddings from cache")
                print(f"  ✓ Loaded {len(emb)} embeddings from cache")
                return [emb[i] if i < len(emb) else None for i in range(len(paragraphs))]
            
            # Cache miss - compute embeddings
            logger.info(f"Embedding {len(paragraphs)} paragraphs (cache miss)...")
            print(f"  Computing embeddings (cache miss)...")
            
            # DEBUG: Log first paragraph before/after sanitization
            if len(paragraphs) > 0:
                logger.info(f"  [DEBUG] First paragraph (raw, first 200 chars): {repr(paragraphs[0][:200])}")
            
            # Sanitize paragraphs for embedding
            sanitized = [self._sanitize_text_for_embedding(p, max_chars=1500) for p in paragraphs]
            
            # DEBUG: Log sanitized paragraph
            if len(sanitized) > 0:
                logger.info(f"  [DEBUG] First paragraph (sanitized, first 200 chars): {repr(sanitized[0][:200])}")
                logger.info(f"  [DEBUG] Sanitization changed length: {len(paragraphs[0])} -> {len(sanitized[0])}")
            
            # Embed using appropriate provider
            if is_ollama:
                base_url = provider_info
                batch_size = 32  # Match reference implementation
                embeddings_list = []
                n = len(sanitized)
                
                t0 = time.time()
                for start in range(0, n, batch_size):
                    batch = sanitized[start:start + batch_size]
                    batch_t0 = time.time()
                    batch_embs = self._embed_batch_ollama(base_url, model, batch, timeout=180)
                    embeddings_list.extend(batch_embs)
                    
                    done = min(start + batch_size, n)
                    batch_dt = time.time() - batch_t0
                    if done == batch_size or done % (batch_size * 5) == 0 or done == n:
                        logger.info(f"Embedded {done}/{n} paragraphs (last batch {batch_dt:.2f}s)")
                        print(f"  Embedded {done}/{n} paragraphs...")
            else:
                # OpenAI - needs batching to avoid token limit (max 300k tokens per request)
                api_key = provider_info
                batch_size = 100  # Conservative batch size to stay under token limit
                embeddings_list = []
                n = len(sanitized)
                
                t0 = time.time()
                for start in range(0, n, batch_size):
                    batch = sanitized[start:start + batch_size]
                    batch_t0 = time.time()
                    try:
                        batch_embs = self._embed_batch_openai(api_key, model, batch)
                        embeddings_list.extend(batch_embs)
                    except Exception as e:
                        logger.error(f"Error embedding batch {start}-{start+len(batch)}: {e}")
                        # Add zero vectors as fallback for failed batch
                        # Try to infer dimension from model name, default to 3072 for large models
                        dim = 3072 if "large" in model.lower() else 1536
                        logger.warning(f"Using zero-vector fallback (dim={dim}) for failed batch")
                        embeddings_list.extend([[0.0] * dim] * len(batch))
                        continue
                    
                    done = min(start + batch_size, n)
                    batch_dt = time.time() - batch_t0
                    if done == batch_size or done % (batch_size * 5) == 0 or done == n:
                        logger.info(f"Embedded {done}/{n} paragraphs via OpenAI (last batch {batch_dt:.2f}s)")
                        print(f"  Embedded {done}/{n} paragraphs via OpenAI...")
                
                logger.info(f"Embedded {len(embeddings_list)} paragraphs via OpenAI (took {time.time()-t0:.1f}s)")
            
            # Convert to numpy array
            emb = np.array(embeddings_list, dtype=np.float32)
            
            # Normalize embeddings (matches reference implementation)
            if normalize:
                norms = np.linalg.norm(emb, axis=1, keepdims=True)
                norms = np.where(norms == 0, 1, norms)
                emb = emb / norms
            
            # Save to disk cache
            np.save(cache_path, emb)
            total_time = time.time() - t0 if 't0' in locals() else 0
            logger.info(f"Saved embedding cache: {cache_path} (total {total_time:.1f}s)")
            print(f"  ✓ Saved embedding cache ({total_time:.1f}s)")
            
            valid_embeddings = len([e for e in embeddings_list if e])
            logger.info(f"Successfully embedded {valid_embeddings}/{len(paragraphs)} paragraphs")
            
            return [emb[i] if i < len(emb) else None for i in range(len(paragraphs))]
        except Exception as e:
            logger.error(f"Error embedding paragraphs: {e}", exc_info=True)
            return [None] * len(paragraphs)
    
    async def _retrieve_chunks_for_query(
        self, query_text: str, report_name: str, chunks: List[Dict]
    ) -> List[Dict]:
        """Retrieve top-K chunks for a query using DocumentAnalyzer.
        
        NOTE: This method is kept for backward compatibility but may not be used
        if we're using paragraph-based retrieval instead of chunking.
        """
        # Set current file path for cache manager
        report_path = self._find_report_file(report_name)
        if report_path:
            self.analyzer.current_file_path = str(report_path)

        # Use DocumentAnalyzer's method to get similar chunks
        similar_chunks = await self.analyzer._get_similar_chunks(
            query_text=query_text,
            chunks=chunks,
            top_k=self.top_k,
        )

        return similar_chunks

    async def run_evaluation(
        self,
        strategies: Optional[List[str]] = None,
        k_values: Optional[List[int]] = None,
        skip_if_results_exist: bool = True,
        use_existing_results: bool = False,
        existing_results_dir: Optional[Path] = None,
    ) -> Dict[str, EvaluationMetrics]:
        """
        Run full ClimRetrieve evaluation workflow.

        Args:
            strategies: List of strategies to evaluate (default: ["IR", "IR3", "question"])
            k_values: K values for evaluation (default: [1, 3, 5, 10])
            skip_if_results_exist: If True, skip computation if results CSV files already exist (default: True)
            use_existing_results: If True, load existing results from existing_results_dir instead of generating (default: False)
            existing_results_dir: Directory containing existing results CSV files (default: None)

        Returns:
            Dictionary mapping strategy names to EvaluationMetrics
        """
        if strategies is None:
            strategies = ["IR", "IR3", "question"]
        if k_values is None:
            k_values = [1, 3, 5, 10]

        logger.info("=" * 60)
        logger.info("Starting ClimRetrieve Evaluation")
        logger.info("=" * 60)

        # Step 1: Load ground truth
        logger.info("Loading ground truth dataset...")
        ground_truth_df = load_climretrieve_labels(self.ground_truth_path)
        logger.info(f"Loaded {len(ground_truth_df)} ground truth entries")
        logger.info(f"Unique reports: {ground_truth_df['report'].nunique()}")
        logger.info(f"Unique questions: {ground_truth_df['question'].nunique()}")
        
        # Calculate ground truth statistics
        logger.info("Calculating ground truth statistics...")
        total_gt_paragraphs = len(ground_truth_df)
        total_gt_unique = ground_truth_df["paragraph"].dropna().nunique()
        logger.info(f"Ground truth statistics:")
        logger.info(f"  Total paragraph rows in CSV: {total_gt_paragraphs}")
        logger.info(f"  Unique paragraphs in CSV: {total_gt_unique}")
        logger.info(f"  Average paragraphs per report: {total_gt_paragraphs / ground_truth_df['report'].nunique():.1f}")
        
        # Track embedding statistics
        total_embedded = 0
        total_embedded_unique = set()
        per_report_stats = []

        # Step 2: Load existing results or generate new ones
        if use_existing_results and existing_results_dir:
            logger.info(f"Loading existing results from: {existing_results_dir}")
            results_by_strategy = {}
            
            # Map strategy names to file names
            strategy_to_file = {
                "IR": "embedding_results_IR.csv",
                "IR3": "embedding_results_IR_three.csv",
                "question": "embedding_results_question.csv",
            }
            
            for strategy in strategies:
                filename = strategy_to_file.get(strategy, f"embedding_results_{strategy}.csv")
                results_path = Path(existing_results_dir) / filename
                
                if results_path.exists():
                    logger.info(f"Loading results for {strategy} from {results_path}")
                    results_by_strategy[strategy] = results_path
                else:
                    logger.warning(f"Results file not found for {strategy}: {results_path}")
                    # Try alternative patterns
                    alt_patterns = [
                        f"results_{strategy}.csv",
                        f"{strategy}_results.csv",
                        f"results_{strategy.lower()}.csv",
                    ]
                    found = False
                    for pattern in alt_patterns:
                        alt_path = Path(existing_results_dir) / pattern
                        if alt_path.exists():
                            logger.info(f"Found alternative file: {alt_path}")
                            results_by_strategy[strategy] = alt_path
                            found = True
                            break
                    if not found:
                        logger.error(f"No results file found for strategy {strategy} in {existing_results_dir}")
        else:
            # Check if all results already exist (skip processing if so)
            all_results_exist = skip_if_results_exist and all(
                (self.output_dir / f"results_{strategy}.csv").exists() for strategy in strategies
            )
            
            if all_results_exist:
                logger.info("All result files already exist - skipping computation")
                results_by_strategy = {}
            else:
                # Step 2: Process reports and generate results for each strategy
                # MATCH REFERENCE: Per-report indexing (build embedding index per report, then retrieve for all questions)
                results_by_strategy: Dict[str, List[Dict]] = {
                    strategy: [] for strategy in strategies
                }

                # Group by report first (matches reference implementation)
                reports = ground_truth_df.groupby("report", sort=False)
                logger.info(f"Processing {len(reports)} reports with per-report indexing...")

                for report_idx, (report_name, report_df) in enumerate(reports, 1):
                    logger.info(
                        f"[{report_idx}/{len(reports)}] Processing report: {report_name[:50]}..."
                    )
                    print(f"\nProcessing report {report_idx}/{len(reports)}: {report_name[:50]}...")

                    # Get ALL paragraphs for this report (not filtered by question)
                    # This matches the reference: "Build corpus = paragraphs of this report"
                    # IMPORTANT: Use ALL paragraphs from CSV (including duplicates) - matches reference
                    # The reference implementation uses: paragraphs = dfr["paragraph"].tolist()
                    # No deduplication - this ensures the paragraph pool matches exactly
                    original_paragraphs = report_df["paragraph"].dropna().astype(str).tolist()
                    # Filter out empty strings but keep duplicates
                    original_paragraphs = [p.strip() for p in original_paragraphs if p.strip()]
                    
                    if not original_paragraphs:
                        logger.warning(f"No valid paragraphs found for report: {report_name}")
                        continue
                    
                    logger.info(f"  Building embedding index with {len(original_paragraphs)} paragraphs for {report_name}")
                    print(f"  Building embedding index with {len(original_paragraphs)} paragraphs")
                    
                    # DEBUG: Log paragraph details
                    if report_idx == 1:  # Only log for first report to avoid spam
                        logger.info(f"  [DEBUG] First 3 paragraphs for {report_name}:")
                        for i, para in enumerate(original_paragraphs[:3], 1):
                            logger.info(f"    [{i}] {para[:100]}...")
                        logger.info(f"  [DEBUG] Total paragraphs per report: {len(original_paragraphs)}")
                        logger.info(f"  [DEBUG] Unique paragraphs: {len(set(original_paragraphs))}")
                        logger.info(f"  [DEBUG] Total paragraph rows in CSV for this report: {len(report_df)}")
                    
                    # Embed ALL paragraphs for this report (per-report indexing)
                    # Disk-based caching handled inside _embed_paragraphs
                    logger.info(f"  Embedding {len(original_paragraphs)} paragraphs...")
                    print(f"  Embedding {len(original_paragraphs)} paragraphs...")
                    paragraph_embeddings = await self._embed_paragraphs(original_paragraphs, normalize=True)
                    
                    # Track embedding statistics
                    valid_embeddings_count = sum(1 for emb in paragraph_embeddings if emb is not None)
                    total_embedded += valid_embeddings_count
                    total_embedded_unique.update(original_paragraphs)
                    
                    # Per-report statistics
                    report_stats = {
                        "report": report_name,
                        "gt_paragraphs": len(report_df),  # Total rows for this report in CSV
                        "gt_unique_paragraphs": report_df["paragraph"].dropna().nunique(),
                        "paragraphs_to_embed": len(original_paragraphs),
                        "embedded_count": valid_embeddings_count,
                        "unique_embedded": len(set(original_paragraphs))
                    }
                    per_report_stats.append(report_stats)
                    
                    logger.info(f"  [STATS] Report: {report_name[:50]}")
                    logger.info(f"    GT paragraphs (CSV rows): {report_stats['gt_paragraphs']}")
                    logger.info(f"    GT unique paragraphs: {report_stats['gt_unique_paragraphs']}")
                    logger.info(f"    Paragraphs to embed: {report_stats['paragraphs_to_embed']}")
                    logger.info(f"    Successfully embedded: {report_stats['embedded_count']}")
                    logger.info(f"    Unique embedded: {report_stats['unique_embedded']}")
                    
                    # Create a mapping from paragraph text to index for quick lookup
                    paragraph_to_index = {para: idx for idx, para in enumerate(original_paragraphs)}
                    
                    # Get all unique questions for this report
                    report_questions = report_df["question"].unique()
                    logger.info(f"  Processing {len(report_questions)} questions for this report")
                    
                    # DEBUG: Log first question details
                    if report_idx == 1 and len(report_questions) > 0:
                        first_question = report_questions[0]
                        logger.info(f"  [DEBUG] First question for {report_name}: {first_question[:100]}...")
                        for strategy in strategies:
                            query = self._get_query_for_strategy(first_question, strategy)
                            logger.info(f"  [DEBUG]   {strategy} query: {query[:150]}...")
                    
                    # Process each question for this report (using the same embedding index)
                    for question in report_questions:
                        logger.info(f"    Question: {question[:50]}...")
                        
                        # Get queries for each strategy (from cache or generator)
                        queries = {}
                        for strategy in strategies:
                            queries[strategy] = self._get_query_for_strategy(question, strategy)

                        # Retrieve paragraphs for each query strategy
                        for strategy, query_text in queries.items():
                            logger.info(f"    Computing similarities for {strategy} strategy...")
                            logger.info(f"    Query text: {query_text[:100]}...")
                            print(f"    Computing similarities for {strategy} strategy (query: '{query_text[:50]}...')...")
                            
                            # DEBUG: Log query details for first report/question
                            if report_idx == 1 and question == report_questions[0]:
                                logger.info(f"  [DEBUG] Raw query text ({strategy}): {repr(query_text[:200])}")
                                logger.info(f"  [DEBUG] Query length: {len(query_text)}")
                            
                            # IMPORTANT: Reference implementation strips query text but doesn't sanitize before embedding
                            # However, we sanitize to match paragraph sanitization (which happens before embedding)
                            # The reference sanitizes both query and paragraphs the same way before embedding
                            sanitized_query = self._sanitize_text_for_embedding(query_text, max_chars=1500)
                            
                            # DEBUG: Log sanitized query
                            if report_idx == 1 and question == report_questions[0]:
                                logger.info(f"  [DEBUG] Sanitized query ({strategy}): {repr(sanitized_query[:200])}")
                                logger.info(f"  [DEBUG] Sanitized query length: {len(sanitized_query)}")
                            
                            # Get query embedding using same provider as paragraphs
                            model, provider_info, is_ollama = self._get_embedding_provider_info()
                            if is_ollama:
                                base_url = provider_info
                                query_emb_list = self._embed_batch_ollama(base_url, model, [sanitized_query], timeout=60)
                                query_embedding = np.array(query_emb_list[0], dtype=np.float32) if query_emb_list else None
                            else:
                                api_key = provider_info
                                query_emb_list = self._embed_batch_openai(api_key, model, [sanitized_query])
                                query_embedding = np.array(query_emb_list[0], dtype=np.float32) if query_emb_list else None
                            
                            if query_embedding is None:
                                logger.warning("Failed to embed query, skipping")
                                continue
                            
                            # Normalize query embedding (matches reference implementation)
                            norm_q = np.linalg.norm(query_embedding)
                            if norm_q > 0:
                                query_embedding = query_embedding / norm_q
                            
                            # Calculate similarity scores for ALL paragraphs in report (dot product of normalized vectors)
                            similarities = []
                            valid_embeddings = 0
                            for i, para_emb in enumerate(paragraph_embeddings):
                                if para_emb is not None:
                                    para_emb = np.array(para_emb, dtype=np.float32)
                                    # Since both are normalized, cosine similarity = dot product
                                    similarity = float(np.dot(query_embedding, para_emb))
                                    valid_embeddings += 1
                                else:
                                    similarity = 0.0
                                similarities.append(similarity)
                            
                            logger.info(f"    Calculated {len(similarities)} similarity scores ({valid_embeddings} valid embeddings)")
                            
                            # DEBUG: Log similarity score distribution
                            if report_idx == 1 and question == report_questions[0] and strategy == strategies[0]:
                                logger.info(f"  [DEBUG] Similarity score stats: min={min(similarities):.4f}, max={max(similarities):.4f}, mean={sum(similarities)/len(similarities):.4f}")
                                logger.info(f"  [DEBUG] Top 5 similarity scores: {sorted(similarities, reverse=True)[:5]}")
                            
                            # Get top-K paragraphs by similarity (from ALL report paragraphs)
                            top_indices = np.argsort(similarities)[::-1][:self.top_k]
                            top_scores = [similarities[i] for i in top_indices]
                            logger.info(f"    Top-{self.top_k} similarity scores: {[f'{s:.4f}' for s in top_scores[:3]]}...")
                            print(f"    ✓ Retrieved top-{self.top_k} paragraphs (scores: {', '.join([f'{s:.3f}' for s in top_scores[:3]])}...)")
                            
                            # DEBUG: Log retrieved paragraphs
                            if report_idx == 1 and question == report_questions[0] and strategy == strategies[0]:
                                logger.info(f"  [DEBUG] Top-{self.top_k} retrieved paragraphs:")
                                for pos, idx in enumerate(top_indices[:5], 1):
                                    para_preview = original_paragraphs[idx][:100].replace('\n', ' ')
                                    logger.info(f"    [{pos}] Score: {similarities[idx]:.4f} | Para: {para_preview}...")
                            
                            # Format results using ORIGINAL paragraph text
                            # Retrieve top-K from ALL report paragraphs (matches reference implementation)
                            # Evaluation will match on (report, question, paragraph) - paragraphs not in GT will get relevance=0
                            for position, idx in enumerate(top_indices, 1):
                                retrieved_paragraph = original_paragraphs[idx]
                                score = float(similarities[idx])
                                
                                # Create query_id matching ground truth format
                                query_id = f"{report_name}|||{question}"
                                
                                # Use original paragraph text for chunk_id
                                chunk_id = hashlib.md5(retrieved_paragraph.encode()).hexdigest()[:16]
                                
                                results_by_strategy[strategy].append({
                                    "query_id": query_id,
                                    "report": report_name,
                                    "question": question,
                                    "paragraph": retrieved_paragraph,  # Store ORIGINAL text (matches ground truth)
                                    "chunk_id": chunk_id,
                                    "score": score,
                                    "position": position,
                                })

        # Step 3: Save results to CSV files (or use existing paths)
        logger.info("Preparing results files...")
        results_paths = {}
        
        if use_existing_results and existing_results_dir:
            # Use existing results paths
            for strategy in strategies:
                if strategy in results_by_strategy:
                    results_paths[strategy] = results_by_strategy[strategy]
                    logger.info(f"Using existing results for {strategy}: {results_paths[strategy]}")
        else:
            # Save results to CSV files (or skip if they exist)
            for strategy in strategies:
                output_path = self.output_dir / f"results_{strategy}.csv"
                
                # Check if results already exist and skip computation if requested
                if skip_if_results_exist and output_path.exists():
                    logger.info(f"Results file {output_path} already exists - skipping computation for {strategy}")
                    results_paths[strategy] = output_path
                    continue
                
                results = results_by_strategy.get(strategy, [])
                if not results:
                    logger.warning(f"No results for strategy {strategy}")
                    continue

                df_results = pd.DataFrame(results)
                
                # Ensure required columns for benchmarking UI: report, question, paragraph, score
                # Keep all columns for backward compatibility, but ensure required ones exist
                required_cols = ["report", "question", "paragraph", "score"]
                for col in required_cols:
                    if col not in df_results.columns:
                        raise ValueError(f"Missing required column '{col}' in results DataFrame. Columns: {list(df_results.columns)}")
                
                # Save with UTF-8 encoding and proper quoting to preserve exact paragraph text
                # quoting=1 (QUOTE_ALL) ensures all fields are quoted, preserving exact text
                import csv
                df_results.to_csv(output_path, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)
                results_paths[strategy] = output_path
                logger.info(f"Saved {len(results)} results to {output_path}")
                logger.info(f"CSV columns: {list(df_results.columns)} (includes required: {required_cols})")

        # Step 4: Evaluate each strategy against ground truth
        logger.info("Evaluating strategies against ground truth...")
        logger.info("Using same evaluation logic as benchmark_climretrieve_one_model.py")

        metrics_by_strategy = {}
        for strategy in strategies:
            if strategy not in results_paths:
                logger.warning(f"Skipping evaluation for {strategy} - no results file")
                continue

            logger.info(f"Evaluating strategy: {strategy}")
            
            # Load results CSV using the same function as benchmark_climretrieve_one_model.py
            # This ensures consistent column handling and extraction
            from report_analyst.core.benchmark.climretrieve_io import load_climretrieve_results
            try:
                df_results = load_climretrieve_results(
                    results_csv=str(results_paths[strategy]),
                    score_col="score",
                    paragraph_col="paragraph"
                )
            except ValueError as e:
                logger.error(f"Error loading results CSV: {e}")
                continue
            
            # Evaluate using same logic as benchmark_climretrieve_one_model.py
            metrics = self._evaluate_climretrieve_style(
                labels=ground_truth_df,
                results=df_results,
                k_values=k_values,
                relevance_threshold=1,  # Default: >= 1 is relevant
                gain_scheme="exp",  # Default: exponential gain for nDCG
            )

            metrics_by_strategy[strategy] = metrics
            logger.info(f"Strategy {strategy} metrics:")
            logger.info(f"  Precision@K: {metrics.precision_at_k}")
            logger.info(f"  Recall@K: {metrics.recall_at_k}")
            logger.info(f"  F1@K: {metrics.f1_at_k}")
            logger.info(f"  nDCG@K: {metrics.ndcg_at_k}")

        logger.info("=" * 60)
        logger.info("ClimRetrieve Evaluation Complete")
        logger.info("=" * 60)

        # Save metrics to file
        self._save_metrics(metrics_by_strategy, k_values)
        
        # Save embeddings info
        self._save_embeddings_info()
        
        # Print summary statistics (use both logger and print to ensure visibility)
        print("\n" + "=" * 60)
        print("EMBEDDING STATISTICS SUMMARY")
        print("=" * 60)
        logger.info("=" * 60)
        logger.info("EMBEDDING STATISTICS SUMMARY")
        logger.info("=" * 60)
        
        print(f"Ground Truth Dataset:")
        print(f"  Total paragraph rows: {total_gt_paragraphs}")
        print(f"  Unique paragraphs: {total_gt_unique}")
        logger.info(f"Ground Truth Dataset:")
        logger.info(f"  Total paragraph rows: {total_gt_paragraphs}")
        logger.info(f"  Unique paragraphs: {total_gt_unique}")
        
        print(f"")
        print(f"Embedded Paragraphs:")
        print(f"  Total embedded: {total_embedded}")
        print(f"  Unique embedded: {len(total_embedded_unique)}")
        logger.info(f"")
        logger.info(f"Embedded Paragraphs:")
        logger.info(f"  Total embedded: {total_embedded}")
        logger.info(f"  Unique embedded: {len(total_embedded_unique)}")
        
        print(f"")
        print(f"Comparison:")
        logger.info(f"")
        logger.info(f"Comparison:")
        if total_gt_paragraphs > 0:
            coverage_pct = 100*total_embedded/total_gt_paragraphs
            print(f"  Coverage: {total_embedded}/{total_gt_paragraphs} ({coverage_pct:.1f}%)")
            logger.info(f"  Coverage: {total_embedded}/{total_gt_paragraphs} ({coverage_pct:.1f}%)")
        if total_gt_unique > 0:
            unique_coverage_pct = 100*len(total_embedded_unique)/total_gt_unique
            print(f"  Unique coverage: {len(total_embedded_unique)}/{total_gt_unique} ({unique_coverage_pct:.1f}%)")
            logger.info(f"  Unique coverage: {len(total_embedded_unique)}/{total_gt_unique} ({unique_coverage_pct:.1f}%)")
        
        print(f"")
        logger.info(f"")
        
        # Per-report summary (show first 5)
        if per_report_stats:
            print("Per-Report Statistics (first 5):")
            logger.info("Per-Report Statistics (first 5):")
            for rs in per_report_stats[:5]:
                print(f"  {rs['report'][:40]}: GT={rs['gt_paragraphs']}, Embedded={rs['embedded_count']}")
                logger.info(f"  {rs['report'][:40]}: GT={rs['gt_paragraphs']}, Embedded={rs['embedded_count']}")
            if len(per_report_stats) > 5:
                print(f"  ... and {len(per_report_stats) - 5} more reports")
                logger.info(f"  ... and {len(per_report_stats) - 5} more reports")
        else:
            print("  (Statistics only available when generating new results)")
            logger.info("  (Statistics only available when generating new results)")
        
        print("=" * 60 + "\n")
        logger.info("=" * 60)

        return metrics_by_strategy

    def _save_metrics(
        self,
        metrics_by_strategy: Dict[str, EvaluationMetrics],
        k_values: List[int],
    ) -> None:
        """Save evaluation metrics to CSV and JSON files."""
        import json

        # Save metrics as CSV
        metrics_rows = []
        for strategy, metrics in metrics_by_strategy.items():
            for k in k_values:
                metrics_rows.append({
                    "strategy": strategy,
                    "k": k,
                    "precision_at_k": metrics.precision_at_k.get(k, 0.0),
                    "recall_at_k": metrics.recall_at_k.get(k, 0.0),
                    "f1_at_k": metrics.f1_at_k.get(k, 0.0),
                    "ndcg_at_k": metrics.ndcg_at_k.get(k, 0.0),
                })
            # Add overall metrics
            metrics_rows.append({
                "strategy": strategy,
                "k": "overall",
                "precision_at_k": None,
                "recall_at_k": None,
                "f1_at_k": None,
                "ndcg_at_k": None,
                "mean_average_precision": metrics.mean_average_precision,
                "mean_reciprocal_rank": metrics.mean_reciprocal_rank,
            })

        metrics_df = pd.DataFrame(metrics_rows)
        metrics_csv_path = self.output_dir / "evaluation_metrics.csv"
        metrics_df.to_csv(metrics_csv_path, index=False)
        logger.info(f"Saved metrics to {metrics_csv_path}")

        # Save metrics as JSON (more detailed)
        metrics_json = {}
        for strategy, metrics in metrics_by_strategy.items():
            metrics_json[strategy] = {
                "precision_at_k": metrics.precision_at_k,
                "recall_at_k": metrics.recall_at_k,
                "f1_at_k": metrics.f1_at_k,
                "ndcg_at_k": metrics.ndcg_at_k,
                "mean_average_precision": metrics.mean_average_precision,
                "mean_reciprocal_rank": metrics.mean_reciprocal_rank,
            }

        metrics_json_path = self.output_dir / "evaluation_metrics.json"
        with open(metrics_json_path, "w") as f:
            json.dump(metrics_json, f, indent=2)
        logger.info(f"Saved detailed metrics to {metrics_json_path}")

    def _save_embeddings_info(self) -> None:
        """Save information about stored embeddings."""
        import json
        
        # Get cache database path from analyzer
        cache_path = getattr(self.analyzer.cache_manager, 'db_path', None)
        if cache_path:
            cache_path = Path(cache_path)
            embeddings_info = {
                "cache_database": str(cache_path),
                "cache_exists": cache_path.exists() if cache_path else False,
                "note": "Embeddings are stored in SQLite cache database. Use DocumentAnalyzer to retrieve them.",
            }
            
            embeddings_info_path = self.output_dir / "embeddings_info.json"
            with open(embeddings_info_path, "w") as f:
                json.dump(embeddings_info, f, indent=2)
            logger.info(f"Saved embeddings info to {embeddings_info_path}")
        else:
            logger.warning("Could not determine cache database path for embeddings info")

    def _create_ground_truth_dataset(self, ground_truth_df: pd.DataFrame) -> BenchmarkDataset:
        """Convert ground truth DataFrame to BenchmarkDataset format."""
        # Create results rows from ground truth
        results = []
        for _, row in ground_truth_df.iterrows():
            # Normalize text for consistent chunk_id generation
            paragraph_text = str(row["paragraph"]).strip()
            normalized_text = self._normalize_text_for_chunk_id(paragraph_text)
            chunk_id = hashlib.md5(normalized_text.encode()).hexdigest()[:16]

            # Create a unique query_id from report + question (must match results format)
            query_id = f"{row['report']}|||{row['question']}"

            # Use relevance as score (0-3, normalize to 0-1 for consistency)
            score = float(row["relevance"]) / 3.0 if row["relevance"] > 0 else 0.0

            result_row = FlexibleDatasetRow(
                data={
                    "query_id": query_id,
                    "report_id": row["report"],
                    "chunk_id": chunk_id,
                    "chunk_text": paragraph_text,
                    "position": 1,  # Ground truth doesn't have position, use 1
                    "score": score,
                    "relevance": row["relevance"],
                }
            )
            results.append(result_row)

        return BenchmarkDataset(
            dataset_id="climretrieve_ground_truth",
            name="ClimRetrieve Ground Truth",
            description="ClimRetrieve expert-annotated ground truth labels",
            version="1.0",
            question_set=None,
            dataset_type=DatasetType.INFORMATION_RETRIEVAL,
            source="csv",
            source_path=str(self.ground_truth_path),
            column_mapping={},
            results=results,
        )

    def _dcg(self, rels: List[int], gain_scheme: str = "exp") -> float:
        """
        DCG with either:
          - exp gain: (2^rel - 1) / log2(i+1)
          - linear gain: rel / log2(i+1)
        
        Same logic as benchmark_climretrieve_one_model.py
        """
        dcg = 0.0
        for i, rel in enumerate(rels, start=1):
            if gain_scheme == "exp":
                gain = (2 ** rel) - 1
            elif gain_scheme == "linear":
                gain = rel
            else:
                raise ValueError(f"Unknown gain_scheme={gain_scheme}")
            dcg += gain / np.log2(i + 1)
        return float(dcg)

    def _ndcg_at_k(self, rels_ranked: List[int], k: int, gain_scheme: str = "exp", all_gt_relevance: List[int] = None) -> float:
        """
        Compute nDCG@K.
        
        Same logic as benchmark_climretrieve_one_model.py
        """
        rels_k = rels_ranked[:k]
        dcg_k = self._dcg(rels_k, gain_scheme=gain_scheme)

        # For IDCG, use all ground truth relevance scores if provided
        if all_gt_relevance is not None:
            ideal = sorted(all_gt_relevance, reverse=True)[:k]
        else:
            ideal = sorted(rels_ranked, reverse=True)[:k]
        idcg_k = self._dcg(ideal, gain_scheme=gain_scheme)

        if idcg_k == 0.0:
            return 0.0
        return dcg_k / idcg_k

    def _evaluate_climretrieve_style(
        self,
        labels: pd.DataFrame,
        results: pd.DataFrame,
        k_values: List[int],
        relevance_threshold: int = 1,
        gain_scheme: str = "exp",
    ) -> EvaluationMetrics:
        """
        Evaluate retrieval results using the same logic as benchmark_climretrieve_one_model.py.
        
        This implements the exact same evaluation logic:
        - Direct pandas merge on (report, question, paragraph) columns (NO normalization)
        - Relevance threshold: >= threshold is relevant
        - nDCG with configurable gain scheme (exp or linear)
        - Macro-averaged metrics across queries
        
        Args:
            labels: Ground truth DataFrame with columns: report, question, paragraph, relevance (0-3)
            results: Results DataFrame with columns: report, question, paragraph, score
            k_values: List of K values for evaluation
            relevance_threshold: Relevance threshold (>= threshold is relevant, default: 1)
            gain_scheme: nDCG gain scheme ("exp" or "linear", default: "exp")
            
        Returns:
            EvaluationMetrics with computed scores
        """
        k_values = sorted(set(int(k) for k in k_values))

        # Direct merge on raw paragraph text (same as benchmark_climretrieve_one_model.py)
        # NO normalization - expects exact matches as stored in CSV files
        # Convert paragraph to string to ensure consistent type matching
        results = results.copy()
        labels = labels.copy()
        results["paragraph"] = results["paragraph"].astype(str)
        labels["paragraph"] = labels["paragraph"].astype(str)
        
        # Verify labels has required columns
        required_label_cols = ["report", "question", "paragraph", "relevance"]
        missing_cols = [col for col in required_label_cols if col not in labels.columns]
        if missing_cols:
            raise ValueError(f"Labels DataFrame missing required columns: {missing_cols}. Found: {list(labels.columns)}")
        
        # Verify results has required columns
        required_result_cols = ["report", "question", "paragraph"]
        missing_cols = [col for col in required_result_cols if col not in results.columns]
        if missing_cols:
            raise ValueError(f"Results DataFrame missing required columns: {missing_cols}. Found: {list(results.columns)}")
        
        # Perform merge
        # If results already has 'relevance', drop it first to avoid suffix conflicts
        results_for_merge = results.copy()
        if "relevance" in results_for_merge.columns:
            logger.info("Results DataFrame already has 'relevance' column - dropping it before merge to use labels' relevance")
            results_for_merge = results_for_merge.drop(columns=["relevance"])
        
        try:
            merged = results_for_merge.merge(
                labels[["report", "question", "paragraph", "relevance"]],
                on=["report", "question", "paragraph"],
                how="left",
            )
        except KeyError as e:
            logger.error(f"Error during merge - labels DataFrame missing column: {e}")
            logger.error(f"Labels columns: {list(labels.columns)}")
            logger.error(f"Results columns: {list(results.columns)}")
            raise
        
        # Ensure relevance column exists (should always exist after left join, but handle edge case)
        if "relevance" not in merged.columns:
            # Check for suffixed columns (relevance_x, relevance_y) - use relevance_y (from labels)
            if "relevance_y" in merged.columns:
                logger.info("Using 'relevance_y' column from merge (labels' relevance)")
                merged["relevance"] = merged["relevance_y"]
                merged = merged.drop(columns=["relevance_y"])
            elif "relevance_x" in merged.columns:
                logger.warning("Only 'relevance_x' found - this is from results, not labels. Using zeros instead.")
                merged["relevance"] = 0
            else:
                logger.warning("No 'relevance' column found after merge - adding with zeros")
                merged["relevance"] = 0
        
        merged["relevance"] = merged["relevance"].fillna(0).astype(int)
        
        # Debug: Log merge statistics
        matches_found = (merged["relevance"] > 0).sum()
        total_rows = len(merged)
        logger.info(f"Merge statistics: {matches_found}/{total_rows} rows matched ({(matches_found/total_rows*100):.1f}%)")

        # Stable sort: within each (report, question), highest score first
        merged = merged.sort_values(
            by=["report", "question", "score"],
            ascending=[True, True, False],
            kind="mergesort",
        )

        # Ground-truth totals per query (from labels, not from results)
        gt = labels.copy()
        gt["is_rel"] = gt["relevance"] >= relevance_threshold
        total_relevant = (
            gt.groupby(["report", "question"])["is_rel"].sum().astype(int)
        )
        
        # Build ground truth relevance scores per query for proper IDCG calculation
        gt_relevance_per_query = {}
        for (report, question), g in labels.groupby(["report", "question"], sort=False):
            gt_relevance_per_query[(report, question)] = g["relevance"].tolist()

        # Prepare accumulators for per-query values
        prec_per_k = {k: [] for k in k_values}
        rec_per_k = {k: [] for k in k_values}
        f1_per_k = {k: [] for k in k_values}
        ndcg_per_k = {k: [] for k in k_values}

        # Evaluate each query group
        for (report, question), g in merged.groupby(["report", "question"], sort=False):
            rels_ranked = g["relevance"].tolist()
            bin_ranked = [1 if r >= relevance_threshold else 0 for r in rels_ranked]

            # Get total relevant for this query (same as benchmark_climretrieve_one_model.py)
            gt_rel = int(total_relevant.get((report, question), 0))
            
            # Get all ground truth relevance scores for this query (for proper IDCG)
            all_gt_relevance = gt_relevance_per_query.get((report, question), [])

            for k in k_values:
                hits_k = int(sum(bin_ranked[:k]))
                precision_k = hits_k / float(k)

                if gt_rel > 0:
                    recall_k = hits_k / float(gt_rel)
                else:
                    recall_k = 0.0

                if precision_k + recall_k > 0:
                    f1_k = 2 * precision_k * recall_k / (precision_k + recall_k)
                else:
                    f1_k = 0.0

                ndcg_k = self._ndcg_at_k(rels_ranked, k=k, gain_scheme=gain_scheme, all_gt_relevance=all_gt_relevance)

                prec_per_k[k].append(precision_k)
                rec_per_k[k].append(recall_k)
                f1_per_k[k].append(f1_k)
                ndcg_per_k[k].append(ndcg_k)

        # Macro average across queries
        precision_at_k = {k: float(np.mean(prec_per_k[k])) if prec_per_k[k] else 0.0 for k in k_values}
        recall_at_k = {k: float(np.mean(rec_per_k[k])) if rec_per_k[k] else 0.0 for k in k_values}
        f1_at_k = {k: float(np.mean(f1_per_k[k])) if f1_per_k[k] else 0.0 for k in k_values}
        ndcg_at_k = {k: float(np.mean(ndcg_per_k[k])) if ndcg_per_k[k] else 0.0 for k in k_values}

        return EvaluationMetrics(
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            f1_at_k=f1_at_k,
            ndcg_at_k=ndcg_at_k,
            mean_average_precision=0.0,  # Not calculated in this evaluation style (default to 0.0)
            mean_reciprocal_rank=0.0,  # Not calculated in this evaluation style (default to 0.0)
        )

