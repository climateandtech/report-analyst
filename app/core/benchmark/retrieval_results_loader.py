"""
Loader for retrieval results datasets from CSV or SQLite.

This module provides functions to load retrieval results in CSV format,
which can be used for benchmarking. The functions are designed to be
webhook-ready and can be used in API endpoints.
"""

import csv
import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from io import StringIO, BytesIO
import logging

from ...models.benchmark import (
    RetrievalResultsDataset, 
    RetrievalResultRow,
    BenchmarkDataset,
    FlexibleDatasetRow,
    DatasetType
)

logger = logging.getLogger(__name__)


def load_retrieval_results_from_csv(
    csv_path: Optional[str] = None,
    csv_content: Optional[Union[str, bytes]] = None,
    dataset_id: Optional[str] = None,
    dataset_name: Optional[str] = None
) -> RetrievalResultsDataset:
    """
    Load retrieval results from CSV file or content.
    
    This function is webhook-ready and can accept either a file path or CSV content.
    
    Expected CSV format:
    - query_id: Question/query identifier (required)
    - report_id: Report/document identifier (optional)
    - chunk_id: Chunk identifier (required)
    - chunk_text: Chunk text content (optional)
    - position: Position/rank in retrieval (required, 1-indexed)
    - score: Retrieval score (required)
    - similarity_score: Vector similarity score (optional)
    - llm_score: LLM-based relevance score (optional)
    
    Args:
        csv_path: Path to CSV file (if loading from file)
        csv_content: CSV content as string or bytes (if loading from upload/webhook)
        dataset_id: Optional dataset identifier (auto-generated if not provided)
        dataset_name: Optional dataset name (defaults to filename or 'uploaded_dataset')
        
    Returns:
        RetrievalResultsDataset with loaded results
        
    Raises:
        ValueError: If neither csv_path nor csv_content is provided
        FileNotFoundError: If csv_path is provided but file doesn't exist
    """
    if csv_path is None and csv_content is None:
        raise ValueError("Either csv_path or csv_content must be provided")
    
    # Determine source info
    if csv_path:
        source_path = csv_path
        source_name = Path(csv_path).stem if not dataset_name else dataset_name
        if not Path(csv_path).exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
    else:
        source_path = None
        source_name = dataset_name or "uploaded_dataset"
    
    dataset_id = dataset_id or f"{source_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Load CSV
    if csv_path:
        df = pd.read_csv(csv_path)
    else:
        # Handle both string and bytes
        if isinstance(csv_content, bytes):
            csv_content = csv_content.decode('utf-8')
        df = pd.read_csv(StringIO(csv_content))
    
    # Validate required columns
    required_columns = ['query_id', 'chunk_id', 'position', 'score']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Convert to RetrievalResultRow objects
    results = []
    for _, row in df.iterrows():
        result_row = RetrievalResultRow(
            query_id=str(row['query_id']),
            report_id=str(row['report_id']) if 'report_id' in df.columns and pd.notna(row.get('report_id')) else None,
            chunk_id=str(row['chunk_id']),
            chunk_text=str(row['chunk_text']) if 'chunk_text' in df.columns and pd.notna(row.get('chunk_text')) else None,
            position=int(row['position']),
            score=float(row['score']),
            similarity_score=float(row['similarity_score']) if 'similarity_score' in df.columns and pd.notna(row.get('similarity_score')) else None,
            llm_score=float(row['llm_score']) if 'llm_score' in df.columns and pd.notna(row.get('llm_score')) else None,
            metadata={k: v for k, v in row.items() if k not in ['query_id', 'report_id', 'chunk_id', 'chunk_text', 'position', 'score', 'similarity_score', 'llm_score'] and pd.notna(v)}
        )
        results.append(result_row)
    
    logger.info(f"Loaded {len(results)} retrieval results from CSV for dataset '{dataset_id}'")
    
    return RetrievalResultsDataset(
        dataset_id=dataset_id,
        name=source_name,
        description=f"Retrieval results loaded from CSV",
        source="csv",
        source_path=source_path,
        results=results
    )


def load_retrieval_results_from_sqlite(
    db_path: str,
    table_name: str = "retrieval_results",
    dataset_id: Optional[str] = None,
    dataset_name: Optional[str] = None,
    query_filter: Optional[str] = None
) -> RetrievalResultsDataset:
    """
    Load retrieval results from SQLite database.
    
    Expected table schema:
    - query_id: TEXT (required)
    - report_id: TEXT (optional)
    - chunk_id: TEXT (required)
    - chunk_text: TEXT (optional)
    - position: INTEGER (required, 1-indexed)
    - score: REAL (required)
    - similarity_score: REAL (optional)
    - llm_score: REAL (optional)
    
    Args:
        db_path: Path to SQLite database
        table_name: Name of the table containing retrieval results
        dataset_id: Optional dataset identifier
        dataset_name: Optional dataset name
        query_filter: Optional SQL WHERE clause to filter results
        
    Returns:
        RetrievalResultsDataset with loaded results
        
    Raises:
        FileNotFoundError: If database file doesn't exist
        sqlite3.Error: If database query fails
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    dataset_id = dataset_id or f"{Path(db_path).stem}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    dataset_name = dataset_name or Path(db_path).stem
    
    # Build query
    base_query = f"SELECT * FROM {table_name}"
    if query_filter:
        base_query += f" WHERE {query_filter}"
    base_query += " ORDER BY query_id, position"
    
    # Load data
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(base_query, conn)
    finally:
        conn.close()
    
    # Validate required columns
    required_columns = ['query_id', 'chunk_id', 'position', 'score']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns in database table: {missing_columns}")
    
    # Convert to RetrievalResultRow objects
    results = []
    for _, row in df.iterrows():
        result_row = RetrievalResultRow(
            query_id=str(row['query_id']),
            report_id=str(row['report_id']) if 'report_id' in df.columns and pd.notna(row.get('report_id')) else None,
            chunk_id=str(row['chunk_id']),
            chunk_text=str(row['chunk_text']) if 'chunk_text' in df.columns and pd.notna(row.get('chunk_text')) else None,
            position=int(row['position']),
            score=float(row['score']),
            similarity_score=float(row['similarity_score']) if 'similarity_score' in df.columns and pd.notna(row.get('similarity_score')) else None,
            llm_score=float(row['llm_score']) if 'llm_score' in df.columns and pd.notna(row.get('llm_score')) else None,
            metadata={k: v for k, v in row.items() if k not in ['query_id', 'report_id', 'chunk_id', 'chunk_text', 'position', 'score', 'similarity_score', 'llm_score'] and pd.notna(v)}
        )
        results.append(result_row)
    
    logger.info(f"Loaded {len(results)} retrieval results from SQLite for dataset '{dataset_id}'")
    
    return RetrievalResultsDataset(
        dataset_id=dataset_id,
        name=dataset_name,
        description=f"Retrieval results loaded from SQLite database",
        source="sqlite",
        source_path=db_path,
        results=results
    )


def export_retrieval_results_to_csv(
    dataset: BenchmarkDataset,
    output_path: str
) -> str:
    """
    Export benchmark dataset to CSV file.
    
    Args:
        dataset: BenchmarkDataset to export
        output_path: Path where CSV file should be saved
        
    Returns:
        Path to the saved CSV file
    """
    rows = []
    for result in dataset.results:
        row = {
            'query_id': result.get_query_id() or '',
            'report_id': result.get('report_id') or result.get('document_id') or '',
            'chunk_id': result.get_chunk_id() or '',
            'chunk_text': result.get('chunk_text') or '',
            'position': result.get_position() or '',
            'score': result.get_score() or '',
            'similarity_score': result.get('similarity_score') or '',
            'llm_score': result.get('llm_score') or '',
        }
        # Add all other fields from data dict
        for key, value in result.data.items():
            if key not in row:
                row[key] = value if value is not None else ''
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Exported {len(rows)} retrieval results to CSV: {output_path}")
    return output_path


def detect_dataset_type(columns: List[str]) -> DatasetType:
    """
    Detect dataset type based on column names.
    
    Information Retrieval (IR) datasets typically have:
    - chunk_id, position, score, similarity_score
    
    Information Extraction (IE) datasets typically have:
    - answer, analysis, category, confidence_score
    
    Args:
        columns: List of column names in the dataset
        
    Returns:
        DatasetType enum value
    """
    columns_lower = [c.lower() for c in columns]
    
    # Check for IE indicators
    ie_indicators = ['answer', 'analysis', 'response', 'category', 'class', 'label', 'extracted_value']
    has_ie_indicators = any(indicator in columns_lower for indicator in ie_indicators)
    
    # Check for IR indicators
    ir_indicators = ['chunk_id', 'chunk', 'position', 'rank', 'similarity_score', 'relevance_score']
    has_ir_indicators = any(indicator in columns_lower for indicator in ir_indicators)
    
    # If both present, prioritize IE (more specific)
    if has_ie_indicators:
        return DatasetType.INFORMATION_EXTRACTION
    elif has_ir_indicators:
        return DatasetType.INFORMATION_RETRIEVAL
    else:
        # Default to IR if unclear
        return DatasetType.INFORMATION_RETRIEVAL


def load_flexible_dataset_from_csv(
    csv_path: Optional[str] = None,
    csv_content: Optional[Union[str, bytes]] = None,
    dataset_id: Optional[str] = None,
    dataset_name: Optional[str] = None,
    dataset_type: Optional[DatasetType] = None,
    column_mapping: Optional[Dict[str, str]] = None
) -> BenchmarkDataset:
    """
    Load a flexible benchmark dataset from CSV with automatic column name detection.
    
    This function is webhook-ready and handles different column name variations.
    It automatically detects dataset type (IR vs IE) and maps columns flexibly.
    
    Args:
        csv_path: Path to CSV file (if loading from file)
        csv_content: CSV content as string or bytes (if loading from upload/webhook)
        dataset_id: Optional dataset identifier (auto-generated if not provided)
        dataset_name: Optional dataset name
        dataset_type: Optional dataset type (auto-detected if not provided)
        column_mapping: Optional explicit column mapping (standard_name -> actual_name)
        
    Returns:
        BenchmarkDataset with loaded results
        
    Raises:
        ValueError: If neither csv_path nor csv_content is provided
        FileNotFoundError: If csv_path is provided but file doesn't exist
    """
    if csv_path is None and csv_content is None:
        raise ValueError("Either csv_path or csv_content must be provided")
    
    # Determine source info
    if csv_path:
        source_path = csv_path
        source_name = Path(csv_path).stem if not dataset_name else dataset_name
        if not Path(csv_path).exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
    else:
        source_path = None
        source_name = dataset_name or "uploaded_dataset"
    
    dataset_id = dataset_id or f"{source_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Load CSV
    if csv_path:
        df = pd.read_csv(csv_path)
    else:
        # Handle both string and bytes
        if isinstance(csv_content, bytes):
            csv_content = csv_content.decode('utf-8')
        df = pd.read_csv(StringIO(csv_content))
    
    # Detect dataset type if not provided
    if dataset_type is None:
        dataset_type = detect_dataset_type(df.columns.tolist())
        logger.info(f"Auto-detected dataset type: {dataset_type.value}")
    
    # Validate required columns
    columns_lower = [c.lower() for c in df.columns]
    
    # Check for query/question ID (required for all datasets)
    has_query_id = any(col in ['query_id', 'question_id', 'qid', 'query'] for col in columns_lower)
    if not has_query_id:
        raise ValueError("Missing required columns: query_id or question_id")
    
    # For IR datasets, check for chunk_id, position, and score
    if dataset_type == DatasetType.INFORMATION_RETRIEVAL:
        has_chunk_id = any(col in ['chunk_id', 'chunk', 'cid'] for col in columns_lower)
        if not has_chunk_id:
            raise ValueError("Missing required columns: chunk_id (required for IR datasets)")
        has_position = any(col in ['position', 'rank', 'order', 'pos'] for col in columns_lower)
        if not has_position:
            raise ValueError("Missing required columns: position or rank (required for IR datasets)")
        has_score = any(col in ['score', 'relevance_score', 'confidence_score', 'similarity_score'] for col in columns_lower)
        if not has_score:
            raise ValueError("Missing required columns: score (required for IR datasets)")
    
    # Build column mapping if not provided
    if column_mapping is None:
        column_mapping = {}
        # Map common variations to standard names
        standard_mappings = {
            'query_id': ['query_id', 'question_id', 'qid', 'query'],
            'chunk_id': ['chunk_id', 'chunk', 'cid'],
            'report_id': ['report_id', 'document_id', 'doc_id', 'report'],
            'position': ['position', 'rank', 'order', 'pos'],
            'score': ['score', 'relevance_score', 'confidence_score', 'similarity_score'],
            'answer': ['answer', 'analysis', 'response', 'text'],
            'category': ['category', 'class', 'label', 'type']
        }
        
        columns_lower_dict = {c.lower(): c for c in df.columns}
        for standard_name, variations in standard_mappings.items():
            for variation in variations:
                if variation.lower() in columns_lower_dict:
                    column_mapping[standard_name] = columns_lower_dict[variation.lower()]
                    break
    
    # Convert to FlexibleDatasetRow objects
    results = []
    for _, row in df.iterrows():
        # Convert row to dictionary, handling NaN values
        row_dict = {}
        for col in df.columns:
            value = row[col]
            # Convert NaN to None, keep other values as-is
            if pd.isna(value):
                row_dict[col] = None
            else:
                row_dict[col] = value
        
        result_row = FlexibleDatasetRow(data=row_dict)
        results.append(result_row)
    
    logger.info(f"Loaded {len(results)} rows from CSV for dataset '{dataset_id}' (type: {dataset_type.value})")
    
    return BenchmarkDataset(
        dataset_id=dataset_id,
        name=source_name,
        description=f"Flexible dataset loaded from CSV (type: {dataset_type.value})",
        version="1.0",  # Default version
        question_set=None,  # Can be inferred or set explicitly
        dataset_type=dataset_type,
        source="csv",
        source_path=source_path,
        column_mapping=column_mapping,
        results=results
    )


def load_flexible_dataset_from_sqlite(
    db_path: str,
    table_name: str = "benchmark_results",
    dataset_id: Optional[str] = None,
    dataset_name: Optional[str] = None,
    dataset_type: Optional[DatasetType] = None,
    column_mapping: Optional[Dict[str, str]] = None,
    query_filter: Optional[str] = None
) -> BenchmarkDataset:
    """
    Load a flexible benchmark dataset from SQLite database.
    
    Args:
        db_path: Path to SQLite database
        table_name: Name of the table containing results
        dataset_id: Optional dataset identifier
        dataset_name: Optional dataset name
        dataset_type: Optional dataset type (auto-detected if not provided)
        column_mapping: Optional explicit column mapping
        query_filter: Optional SQL WHERE clause to filter results
        
    Returns:
        BenchmarkDataset with loaded results
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    dataset_id = dataset_id or f"{Path(db_path).stem}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    dataset_name = dataset_name or Path(db_path).stem
    
    # Build query
    base_query = f"SELECT * FROM {table_name}"
    if query_filter:
        base_query += f" WHERE {query_filter}"
    
    # Load data
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(base_query, conn)
    finally:
        conn.close()
    
    # Detect dataset type if not provided
    if dataset_type is None:
        dataset_type = detect_dataset_type(df.columns.tolist())
        logger.info(f"Auto-detected dataset type: {dataset_type.value}")
    
    # Build column mapping if not provided (same logic as CSV loader)
    if column_mapping is None:
        column_mapping = {}
        standard_mappings = {
            'query_id': ['query_id', 'question_id', 'qid', 'query'],
            'chunk_id': ['chunk_id', 'chunk', 'cid'],
            'report_id': ['report_id', 'document_id', 'doc_id', 'report'],
            'position': ['position', 'rank', 'order', 'pos'],
            'score': ['score', 'relevance_score', 'confidence_score', 'similarity_score'],
            'answer': ['answer', 'analysis', 'response', 'text'],
            'category': ['category', 'class', 'label', 'type']
        }
        
        columns_lower = {c.lower(): c for c in df.columns}
        for standard_name, variations in standard_mappings.items():
            for variation in variations:
                if variation.lower() in columns_lower:
                    column_mapping[standard_name] = columns_lower[variation.lower()]
                    break
    
    # Convert to FlexibleDatasetRow objects
    results = []
    for _, row in df.iterrows():
        row_dict = {}
        for col in df.columns:
            value = row[col]
            if pd.isna(value):
                row_dict[col] = None
            else:
                row_dict[col] = value
        
        result_row = FlexibleDatasetRow(data=row_dict)
        results.append(result_row)
    
    logger.info(f"Loaded {len(results)} rows from SQLite for dataset '{dataset_id}' (type: {dataset_type.value})")
    
    return BenchmarkDataset(
        dataset_id=dataset_id,
        name=dataset_name,
        description=f"Flexible dataset loaded from SQLite (type: {dataset_type.value})",
        version="1.0",  # Default version
        question_set=None,  # Can be inferred or set explicitly
        dataset_type=dataset_type,
        source="sqlite",
        source_path=db_path,
        column_mapping=column_mapping,
        results=results
    )
