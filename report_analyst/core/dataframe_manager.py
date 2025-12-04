import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Setup logging
logger = logging.getLogger(__name__)


def format_list_field(field: Any) -> str:
    """Format list fields for better display"""
    if isinstance(field, str):
        try:
            # Try to parse if it's a string representation of a list
            field = eval(field)
        except:
            return field

    if isinstance(field, list):
        formatted_items = []
        for item in field:
            if isinstance(item, dict):
                # Handle evidence items with text and chunk info
                text = item.get("text", "")
                chunk = item.get("chunk", "Unknown")
                formatted_items.append(f"• {text} [Chunk {chunk}]")
            else:
                formatted_items.append(f"• {str(item)}")
        return "\n".join(formatted_items)
    return str(field)


def extract_evidence_text(evidence: Any) -> str:
    """Extract text from evidence items"""
    if isinstance(evidence, dict):
        text = evidence.get("text", "")
        chunk = evidence.get("chunk", "Unknown")
        return f"{text} [Chunk {chunk}]"
    return str(evidence)


def create_analysis_dataframes(
    cached_results: Dict, file_key: str = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Create analysis and chunks dataframes from database results."""
    try:
        analysis_rows = []
        chunks_rows = []

        logger.info(
            f"Processing {len(cached_results)} results for file_key: {file_key}"
        )
        logger.info(f"Input cached_results keys: {list(cached_results.keys())}")

        # Handle each question's results
        for question_id, data in cached_results.items():
            try:
                # Get the result data - it might be nested under 'result' key
                result = data.get("result", data)
                logger.info(
                    f"Processing question {question_id} with keys: {list(result.keys())}"
                )

                # Create analysis row
                analysis_row = {
                    "Question ID": question_id,
                    "Analysis": result.get("ANSWER", ""),
                    "Score": float(result.get("SCORE", 0)),
                    "Key Evidence": "\n".join(
                        str(e) for e in result.get("EVIDENCE", [])
                    ),
                    "Gaps": "\n".join(str(gap) for gap in result.get("GAPS", [])),
                    "Sources": "\n".join(
                        str(source) for source in result.get("SOURCES", [])
                    ),
                }
                analysis_rows.append(analysis_row)
                logger.info(f"Added analysis row for question {question_id}")

                # Process chunks - use exactly what's in the database
                chunks = data.get("chunks", [])
                logger.info(
                    f"Processing {len(chunks)} chunks for question {question_id}"
                )

                for chunk in chunks:
                    # Create chunk row with exactly what's in the database
                    chunk_row = {
                        "Question ID": question_id,
                        "Chunk Text": chunk["text"],
                        "Vector Similarity": chunk[
                            "similarity_score"
                        ],  # Raw value from DB
                        "LLM Score": chunk.get("llm_score"),  # Raw value from DB
                        "Is Evidence": chunk.get("is_evidence"),  # Raw value from DB
                        "Position": chunk.get("chunk_order"),  # Raw value from DB
                    }
                    chunks_rows.append(chunk_row)

                    # Log the exact values we're using
                    logger.info(
                        f"Raw chunk values - similarity_score: {chunk['similarity_score']}, llm_score: {chunk.get('llm_score')}, is_evidence: {chunk.get('is_evidence')}"
                    )

            except Exception as e:
                logger.error(
                    f"Error processing result for question {question_id}: {str(e)}"
                )
                logger.error(f"Result data: {data}")
                continue

        # Create DataFrames
        analysis_df = pd.DataFrame(analysis_rows) if analysis_rows else pd.DataFrame()
        chunks_df = pd.DataFrame(chunks_rows) if chunks_rows else pd.DataFrame()

        # Log DataFrame information
        logger.info(
            f"Created dataframes - Analysis: {len(analysis_df)} rows, Chunks: {len(chunks_df)} rows"
        )
        if not chunks_df.empty:
            logger.info(f"Chunks columns: {chunks_df.columns.tolist()}")
            logger.info(
                f"Vector similarity range: {chunks_df['Vector Similarity'].min():.4f} - {chunks_df['Vector Similarity'].max():.4f}"
            )
            if "LLM Score" in chunks_df.columns:
                logger.info(
                    f"LLM score range: {chunks_df['LLM Score'].min():.4f} - {chunks_df['LLM Score'].max():.4f}"
                )

        return analysis_df, chunks_df

    except Exception as e:
        logger.error(f"Error creating dataframes: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()


def is_chunk_referenced(position: int, evidence_list: List[Dict]) -> bool:
    """Check if a chunk is referenced in the evidence list"""
    for evidence in evidence_list:
        if evidence.get("chunk") == position:
            return True
    return False


def create_combined_dataframe(
    analysis_df: pd.DataFrame, chunks_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Create a combined dataframe with analysis results and their chunks.

    Args:
        analysis_df: DataFrame with analysis results
        chunks_df: DataFrame with chunk information

    Returns:
        Combined DataFrame with multi-index
    """
    if analysis_df.empty or chunks_df.empty:
        return pd.DataFrame()

    # Create multi-index dataframes
    analysis_indexed = analysis_df.set_index(["Question ID"])
    chunks_indexed = chunks_df.set_index(["Question ID"])

    # Combine the dataframes
    combined_df = pd.concat([analysis_indexed, chunks_indexed], axis=1)

    # Remove duplicate columns
    combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]

    return combined_df


def format_evidence_for_display(evidence_list: List[Dict[str, Any]]) -> str:
    """Format evidence items for display in the UI"""
    if not evidence_list:
        return ""

    formatted = []
    for i, evidence in enumerate(evidence_list, 1):
        text = evidence.get("text", "")
        page = evidence.get("metadata", {}).get("page_number", "")
        page_info = f" (Page {page})" if page else ""
        formatted.append(f"{i}. {text}{page_info}")

    return "\n".join(formatted)


def get_analysis_summary(results: Dict[str, Any], report_name: str) -> pd.DataFrame:
    """
    Create a summary dataframe for all analyses in a report.

    Args:
        results: Dict mapping question_ids to their analysis results
        report_name: Name of the report

    Returns:
        Summary DataFrame
    """
    summary_rows = []

    for question_id, data in results.items():
        if not data or "result" not in data:
            continue

        result = data["result"]

        # Count evidence chunks
        evidence_count = len(result.get("EVIDENCE", []))

        # Count total chunks
        total_chunks = len(data.get("chunks", []))

        summary_rows.append(
            {
                "Report": report_name,
                "Question ID": question_id,
                "Question": result.get("QUESTION", ""),
                "Score": float(result.get("SCORE", 0)),
                "Evidence Count": evidence_count,
                "Total Chunks": total_chunks,
                "Gaps Count": len(result.get("GAPS", [])),
                "Analysis Length": len(result.get("ANSWER", "")),
            }
        )

    return pd.DataFrame(summary_rows) if summary_rows else pd.DataFrame()
