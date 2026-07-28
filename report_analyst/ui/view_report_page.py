"""View Report page: PDF viewer with chunk overlays."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


def render_view_report_page(analyzer, question_sets: dict, get_uploaded_files_history) -> None:
    """Render the View Report navigation page."""
    st.header("View Report")
    st.write("View PDF with chunks and analysis results by question")

    # Get file list for dropdown (including backend resources if enabled)
    backend_config = st.session_state.get("backend_config")
    previous_files = get_uploaded_files_history(backend_config=backend_config)

    if not previous_files:
        st.info("No reports available. Please upload a report first.")
    else:
        # File selector
        selected_file_dropdown = st.selectbox(
            "Select Report",
            options=previous_files,
            format_func=lambda x: x["name"],
            key="view_report_file",
        )

        if selected_file_dropdown:
            selected_uri = selected_file_dropdown.get("uri", selected_file_dropdown.get("path", ""))
            is_backend = selected_uri.startswith("urn:report-analyst:backend:")

            # Determine file path: use URI for backend, absolute path for local files
            if is_backend:
                file_path = selected_uri  # Use URN for backend resources
            else:
                file_path = selected_file_dropdown.get("path", "")
                # Handle file:// URI format
                if file_path.startswith("file://"):
                    file_path = file_path.replace("file://", "")
                # Resolve to absolute path (same as Report Analyst)
                file_path = str(Path(file_path).resolve()) if file_path else file_path

            # Question set selection
            selected_set = st.selectbox(
                "Select Question Set",
                options=list(question_sets.keys()),
                format_func=lambda x: question_sets[x]["name"],
                key="view_report_set",
            )

            if selected_set and file_path:
                # Load questions (always needed for PDF viewer)
                # Use global question_loader (imported at module level)
                from report_analyst.core.question_loader import get_question_loader
                q_loader = get_question_loader()
                question_set_obj = q_loader.get_question_set(selected_set)
                questions_data = {}
                if question_set_obj:
                    for q_id, q_data in question_set_obj.questions.items():
                        questions_data[q_id] = q_data.get("text", q_id)

                # Try to get cached results (optional - PDF will show even without them)
                cached_results = None
                selected_config = None
                chunks_by_question = {}
                analysis_by_question = {}

                try:
                    # Map question set to database identifier
                    question_set_mapping = {
                        "tcfd": "tcfd",
                        "s4m": "s4m",
                        "lucia": "lucia",
                        "everest": "ev",
                    }
                    db_question_set = question_set_mapping.get(selected_set, selected_set)

                    # Get all cache configs
                    cache_configs = analyzer.analyzer.cache_manager.check_cache_status()
                    logger.info(f"Found {len(cache_configs)} total cache configs")
                    logger.info(f"Looking for file_path: {file_path}, question_set: {db_question_set}")

                    # Filter configs for this file and question set
                    matching_configs = []
                    for config in cache_configs:
                        if len(config) == 6:
                            cfg_file_path, chunk_size, chunk_overlap, top_k, model, qs = config
                            # Match file path and question set
                            # Compare both as strings to handle path variations
                            if str(cfg_file_path) == str(file_path) and qs == db_question_set:
                                matching_configs.append({
                                    "chunk_size": chunk_size,
                                    "chunk_overlap": chunk_overlap,
                                    "top_k": top_k,
                                    "model": model,
                                    "question_set": selected_set,  # Use original question set ID - get_analysis will map it internally
                                })

                    logger.info(f"Found {len(matching_configs)} matching configs for file and question set")

                    if matching_configs:
                        # Let user select config if multiple, otherwise use first
                        if len(matching_configs) > 1:
                            config_options = [
                                f"Chunk: {cfg['chunk_size']}, Overlap: {cfg['chunk_overlap']}, Top-K: {cfg['top_k']}, Model: {cfg['model']}"
                                for cfg in matching_configs
                            ]
                            selected_config_idx = st.selectbox(
                                "Select Configuration",
                                options=range(len(matching_configs)),
                                format_func=lambda i: config_options[i],
                                key="view_report_config",
                            )
                            selected_config = matching_configs[selected_config_idx]
                        else:
                            selected_config = matching_configs[0]

                        # Get cached results with the selected config
                        # Note: get_analysis will map question_set internally, so we pass the ID
                        logger.info(f"Retrieving cached results with config: {selected_config}")
                        # Get all question IDs for this question set
                        all_question_ids = list(questions_data.keys())
                        logger.info(f"Retrieving chunks for {len(all_question_ids)} questions: {all_question_ids}")
                        cached_results = analyzer.analyzer.cache_manager.get_analysis(
                            file_path=file_path,
                            config=selected_config,
                            question_ids=all_question_ids
                        )
                        logger.info(f"Retrieved cached results for {len(cached_results) if cached_results else 0} questions")

                        if cached_results:
                            # Prepare chunks by question and normalize page numbers
                            for q_id, data in cached_results.items():
                                chunks = data.get("chunks", [])
                                # Normalize page_number in metadata (convert from 'source' if needed)
                                for chunk in chunks:
                                    if chunk.get("metadata"):
                                        metadata = chunk["metadata"]
                                        # PyMuPDFReader uses 'source' as page number string, normalize to 'page_number' as integer
                                        if "page_number" not in metadata and "source" in metadata:
                                            try:
                                                metadata["page_number"] = int(metadata["source"])
                                            except (ValueError, TypeError):
                                                metadata["page_number"] = 1
                                        elif "page_number" in metadata:
                                            # Ensure it's an integer
                                            try:
                                                metadata["page_number"] = int(metadata["page_number"])
                                            except (ValueError, TypeError):
                                                metadata["page_number"] = 1
                                        else:
                                            # Default to page 1 if no page info
                                            metadata["page_number"] = 1
                                chunks_by_question[q_id] = chunks
                                logger.info(f"Question {q_id}: Found {len(chunks)} chunks")
                                if chunks:
                                    logger.debug(f"First chunk sample for {q_id}: {chunks[0] if chunks else 'None'}")
                                result = data.get("result", {})
                                # Ensure score is a number, not a string
                                score = result.get("SCORE", 0)
                                try:
                                    score = float(score) if score is not None else 0
                                except (ValueError, TypeError):
                                    score = 0

                                analysis_by_question[q_id] = {
                                    "answer": result.get("ANSWER", ""),
                                    "score": score,
                                    "evidence": result.get("EVIDENCE", []),
                                    "gaps": result.get("GAPS", []),
                                }

                            # Log total chunks for debugging
                            total_chunks = sum(len(chunks) for chunks in chunks_by_question.values())
                            logger.info(f"Total chunks prepared for PDF viewer: {total_chunks}")
                        else:
                            st.info("No cached analysis results found. PDF will display without chunks.")
                    else:
                        st.info(f"No cached results found for this file and question set '{selected_set}'. PDF will display without chunks. Run analysis in 'Report Analyst' tab to see chunks.")

                except Exception as e:
                    logger.error(f"Error getting cached results: {e}", exc_info=True)
                    st.warning(f"Could not load cached results: {e!s}. PDF will display without chunks.")

                # Try to import PDF viewer
                pdf_viewer_available = False
                try:
                    from report_analyst_enterprise.components.streamlit_component.backend import pdf_viewer
                    pdf_viewer_available = True
                except ImportError:
                    pass

                # Create two-column layout: questions on left, PDF viewer on right
                if pdf_viewer_available:
                    left_col, right_col = st.columns([1, 1])
                else:
                    left_col = st.container()
                    right_col = None

                with left_col:
                    st.subheader("Questions & Chunks")

                    if cached_results and chunks_by_question:
                        # Sort questions by question_id for consistent display
                        sorted_question_ids = sorted(questions_data.keys())

                        for q_id in sorted_question_ids:
                            question_text = questions_data[q_id]
                            chunks = chunks_by_question.get(q_id, [])
                            analysis = analysis_by_question.get(q_id, {})

                            with st.expander(f"**{q_id}**: {question_text[:80]}{'...' if len(question_text) > 80 else ''}", expanded=False):
                                if chunks:
                                    # Sort chunks: evidence first, then by score (higher is better)
                                    sorted_chunks = sorted(
                                        chunks,
                                        key=lambda c: (
                                            not c.get("is_evidence", False),  # Evidence first (False < True)
                                            -(c.get("llm_score") if c.get("llm_score") is not None else c.get("similarity_score", 0))  # Higher scores first
                                        )
                                    )

                                    # Create dataframe for chunks with chunk IDs for navigation
                                    chunk_rows = []
                                    chunk_id_map = {}  # Map row index to chunk_id
                                    for idx, chunk in enumerate(sorted_chunks):
                                        chunk_order = chunk.get('chunk_order', 0)
                                        # Generate chunk ID: "question_id_chunk_order"
                                        chunk_id = f"{q_id}_{chunk_order}"
                                        chunk_id_map[idx] = chunk_id
                                        chunk_rows.append({
                                            "Chunk": f"Chunk {chunk_order + 1}",
                                            "Text": chunk.get("text", "")[:200] + ("..." if len(chunk.get("text", "")) > 200 else ""),
                                            "Page": chunk.get("metadata", {}).get("page_number", "N/A"),
                                            "Evidence": "✓" if chunk.get("is_evidence", False) else "",
                                            "Similarity": f"{chunk.get('similarity_score', 0):.3f}",
                                            "LLM Score": f"{chunk.get('llm_score', 0):.3f}" if chunk.get("llm_score") else "N/A",
                                        })

                                    chunks_df = pd.DataFrame(chunk_rows)

                                    # Use session state to track selected chunk for this question
                                    chunk_selection_key = f"selected_chunk_{q_id}_{selected_set}"

                                    # Add a "Select" column with buttons for each chunk
                                    select_buttons = []
                                    for idx in range(len(chunks_df)):
                                        chunk_id = chunk_id_map[idx]
                                        select_buttons.append(chunk_id)

                                    # Display chunks with clickable select buttons
                                    for idx, row in chunks_df.iterrows():
                                        chunk_id = chunk_id_map[idx]
                                        col1, col2 = st.columns([0.12, 0.88])
                                        with col1:
                                            if st.button("📍", key=f"select_chunk_{chunk_id}", help="Click to highlight this chunk in PDF", use_container_width=True):
                                                st.session_state[chunk_selection_key] = chunk_id
                                                st.rerun()
                                        with col2:
                                            st.markdown(f"**{row['Chunk']}** | Page {row['Page']} | {row['Evidence']} | Similarity: {row['Similarity']}")
                                            st.caption(row['Text'])

                                    # Also show as compact dataframe for overview
                                    st.dataframe(
                                        chunks_df,
                                        use_container_width=True,
                                        hide_index=True,
                                        column_config={
                                            "Chunk": st.column_config.TextColumn("Chunk", width="small"),
                                            "Text": st.column_config.TextColumn("Text", width="large"),
                                            "Page": st.column_config.TextColumn("Page", width="small"),
                                            "Evidence": st.column_config.TextColumn("Evidence", width="small"),
                                            "Similarity": st.column_config.TextColumn("Similarity", width="small"),
                                            "LLM Score": st.column_config.TextColumn("LLM Score", width="small"),
                                        }
                                    )

                                    # Show analysis result below chunks
                                    st.markdown("---")
                                    st.markdown("**Analysis Result:**")
                                    if analysis.get("answer"):
                                        st.write(analysis["answer"])
                                    if analysis.get("score") is not None:
                                        # Handle score as either number or string
                                        try:
                                            score_value = float(analysis["score"])
                                            st.metric("Score", f"{score_value:.1f}")
                                        except (ValueError, TypeError):
                                            # If score is not a number, display as-is
                                            st.metric("Score", str(analysis["score"]))
                                else:
                                    st.info("No chunks available for this question.")
                    else:
                        st.info("No cached analysis results available. Run analysis in 'Report Analyst' tab to see chunks and analysis.")

                # PDF viewer on the right - always show if file is selected
                if pdf_viewer_available and right_col:
                    with right_col:
                        st.subheader("PDF Viewer")

                        # Get selected chunk ID from session state (check all questions)
                        selected_chunk_id = None
                        for q_id_check in questions_data.keys():
                            chunk_key = f"selected_chunk_{q_id_check}_{selected_set}"
                            if chunk_key in st.session_state:
                                selected_chunk_id = st.session_state[chunk_key]
                                break  # Use first found, or could use most recent

                        pdf_viewer(
                            pdf_path=file_path,
                            chunks_data=chunks_by_question,
                            questions_data=questions_data,
                            highlight_chunk_id=selected_chunk_id,
                            height=800,
                            key=f"view_report_pdf_viewer_{selected_set}"
                        )
                elif not pdf_viewer_available:
                    st.info("PDF viewer component not available. Install enterprise components to enable PDF viewing.")

