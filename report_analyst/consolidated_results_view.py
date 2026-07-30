"""All Results chunk search and consolidated report rendering."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


def _chunk_text(chunk: dict) -> str:
    return chunk.get("text", chunk.get("chunk_text", ""))


def _chunks_to_rows(chunks: list[dict], *, ranked: bool = False) -> list[dict]:
    rows = []
    for i, chunk in enumerate(chunks):
        row = {
            "Text": _chunk_text(chunk),
            "Has Embedding": chunk.get("embedding") is not None,
            "Chunk Size": chunk.get("chunk_size", "N/A"),
            "Chunk Overlap": chunk.get("chunk_overlap", "N/A"),
        }
        if ranked and "similarity" in chunk:
            row["Rank"] = i + 1
            row["Similarity"] = chunk["similarity"]
        else:
            row["Chunk #"] = i + 1
        rows.append(row)
    return rows


def _display_chunk_table(chunks_rows: list[dict], *, similarity_view: bool) -> None:
    chunks_df = pd.DataFrame(chunks_rows)
    if similarity_view and "Rank" in chunks_df.columns:
        column_config = {
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Similarity": st.column_config.NumberColumn("Similarity", format="%.4f", width="small"),
            "Text": st.column_config.TextColumn("Text", width="large"),
            "Has Embedding": st.column_config.CheckboxColumn("Has Embedding"),
            "Chunk Size": st.column_config.NumberColumn("Chunk Size", width="small"),
            "Chunk Overlap": st.column_config.NumberColumn("Chunk Overlap", width="small"),
        }
    else:
        column_config = {
            "Chunk #": st.column_config.NumberColumn("Chunk #", width="small"),
            "Text": st.column_config.TextColumn("Text", width="large"),
            "Has Embedding": st.column_config.CheckboxColumn("Has Embedding"),
            "Chunk Size": st.column_config.NumberColumn("Chunk Size", width="small"),
            "Chunk Overlap": st.column_config.NumberColumn("Chunk Overlap", width="small"),
        }

    st.dataframe(
        data=chunks_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )


def _render_text_only_chunks(raw_chunks: list[dict]) -> None:
    """Chunk-only cache: list chunks without similarity controls."""
    st.subheader("Document Chunks")
    st.caption("Text-only chunks. Run the **Embed** step on Report Analyst to enable similarity search.")
    rows = _chunks_to_rows(raw_chunks)
    _display_chunk_table(rows, similarity_view=False)
    st.info(f"Found {len(rows)} document chunks (not embedded yet).")


def _render_similarity_chunk_search(analyzer, question_set: str, file_path: str, raw_chunks: list[dict]) -> None:
    """Embedded chunks: question/custom query similarity ranking."""
    st.subheader("Similarity Search")

    if analyzer.analyzer.question_set != question_set:
        analyzer.analyzer.update_question_set(question_set)
    questions = analyzer.analyzer.questions

    col1, col2 = st.columns([1, 1])
    with col1:
        question_options = ["None"] + [f"{q_id}" for q_id in questions.keys()]
        selected_question_id = st.selectbox(
            "Select a question to sort by similarity:",
            options=question_options,
            key=f"chunk_similarity_question_{Path(file_path).name}",
            help="Choose a question from the current question set",
        )
        if selected_question_id != "None" and selected_question_id in questions:
            st.caption(f"**{selected_question_id}:** {questions[selected_question_id]['text'][:100]}...")

    with col2:
        custom_question = st.text_input(
            "Or enter custom question:",
            placeholder="Enter your own question to compare chunks against...",
            key=f"chunk_similarity_custom_{Path(file_path).name}",
        )

    query_text = None
    if custom_question.strip():
        query_text = custom_question.strip()
        st.info(f"Using custom question: {query_text[:100]}...")
    elif selected_question_id != "None" and selected_question_id in questions:
        query_text = questions[selected_question_id]["text"]
        st.info(f"Using question {selected_question_id}: {query_text[:100]}...")

    embedded_chunks = [c for c in raw_chunks if c.get("embedding") is not None]
    display_chunks = raw_chunks
    similarity_view = False

    if query_text:
        try:
            if analyzer.analyzer.use_backend_llm:
                st.warning("Similarity search is unavailable in backend LLM mode.")
            else:
                analyzer.analyzer._ensure_embeddings_client()
                query_embedding = np.array(
                    analyzer.analyzer.embeddings.get_text_embedding(query_text),
                    dtype=np.float32,
                )
                ranked = []
                for chunk in embedded_chunks:
                    chunk_embedding = np.frombuffer(chunk["embedding"], dtype=np.float32)
                    similarity = float(
                        np.dot(query_embedding, chunk_embedding)
                        / (np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding))
                    )
                    ranked.append({**chunk, "similarity": similarity})
                ranked.sort(key=lambda c: c["similarity"], reverse=True)
                display_chunks = ranked
                similarity_view = True
                st.success(f"Sorted {len(ranked)} embedded chunks by similarity to query")
        except RuntimeError as exc:
            st.warning(str(exc))
        except Exception as e:
            st.error(f"Error computing similarity: {e!s}")
            logger.error(f"Error computing similarity: {e!s}", exc_info=True)

    rows = _chunks_to_rows(display_chunks, ranked=similarity_view)
    _display_chunk_table(rows, similarity_view=similarity_view)
    st.info(
        f"Found {len(raw_chunks)} document chunks ({len(embedded_chunks)} with embeddings)."
    )


def render_consolidated_chunk_search(analyzer, question_set: str, file_path: str, config: dict) -> bool:
    """Render cached document chunks. Similarity search only when embeddings exist."""
    raw_chunks = analyzer.analyzer.cache_manager.resolve_document_chunks(
        file_path=file_path,
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
    )

    if not raw_chunks:
        st.subheader("Document Chunks")
        st.warning(
            "No document chunks in cache for this report and configuration. "
            "On **Report Analyst**, set the processing step to **Chunk** (or **Embed**) "
            "and click **Analyze Selected Questions** for this file first."
        )
        return False

    embedded_count = sum(1 for c in raw_chunks if c.get("embedding") is not None)
    if embedded_count == 0:
        _render_text_only_chunks(raw_chunks)
    else:
        _render_similarity_chunk_search(analyzer, question_set, file_path, raw_chunks)

    return True


def render_consolidated_report_view(
    analyzer,
    question_set: str,
    file_path: str,
    config: dict,
    *,
    display_analysis_results,
) -> None:
    """Show chunk search and optional cached answer results for one report/config."""
    logger.info(f"Getting results for {Path(file_path).name} with config: {config}")

    try:
        had_chunks = render_consolidated_chunk_search(analyzer, question_set, file_path, config)
    except Exception as e:
        logger.warning(f"Error displaying document chunks: {e!s}")
        had_chunks = False

    cached_results = analyzer.analyzer.cache_manager.get_analysis(
        file_path=file_path,
        config=config,
    )

    if not cached_results:
        if config.get("chunks_only") or had_chunks:
            st.info("No answer results yet for this configuration.")
        else:
            st.warning("No stored results found for this configuration")
        return

    if analyzer.analyzer.question_set != question_set:
        analyzer.analyzer.update_question_set(question_set)
    questions = analyzer.analyzer.questions

    analysis_rows = []
    question_chunks_rows = []

    for question_id, data in cached_results.items():
        try:
            result = data.get("result", {})
            analysis_rows.append(
                {
                    "Question ID": question_id,
                    "Question Text": (questions[question_id]["text"] if question_id in questions else question_id),
                    "Analysis": result.get("ANSWER", ""),
                    "Score": float(result.get("SCORE", 0)),
                    "Key Evidence": "\n".join([e.get("text", "") for e in result.get("EVIDENCE", [])]),
                    "Gaps": "\n".join(result.get("GAPS", [])),
                    "Sources": ", ".join(map(str, result.get("SOURCES", []))),
                }
            )
            if "chunks" in data:
                for chunk in data["chunks"]:
                    question_chunks_rows.append(
                        {
                            "Question ID": question_id,
                            "Text": chunk.get("text", ""),
                            "Vector Similarity": chunk.get("similarity_score", 0.0),
                            "LLM Score": chunk.get("llm_score", 0.0),
                            "Is Evidence": chunk.get("is_evidence", False),
                            "Position": chunk.get("chunk_order", 0),
                        }
                    )
        except Exception as e:
            logger.error(f"Error processing result for question {question_id}: {e!s}", exc_info=True)

    if analysis_rows:
        analysis_df = pd.DataFrame(analysis_rows)
        chunks_df = pd.DataFrame(question_chunks_rows) if question_chunks_rows else pd.DataFrame()
        file_key = f"{Path(file_path).stem}_cs{config['chunk_size']}"
        display_analysis_results(analysis_df, chunks_df, file_key)
    else:
        st.warning("No results found in stored for this configuration")
