"""Streamlit script entrypoints for AppTest — real ``st``, no manual mocks."""

from __future__ import annotations


def run_answer_workflow_harness() -> None:
    """Execute run_report_answer_workflow; params in session_state['_test_workflow_params']."""
    import asyncio

    import streamlit as st

    from report_analyst.streamlit_app import run_report_answer_workflow

    params = st.session_state["_test_workflow_params"]
    progress = st.empty()
    asyncio.run(
        run_report_answer_workflow(
            params["analyzer"],
            analysis_file_path=params["analysis_file_path"],
            file_path=params["file_path"],
            questions=params["questions"],
            selected_questions=params["selected_questions"],
            config=params["config"],
            max_step=params["max_step"],
            reanalyze=params["reanalyze"],
            progress_text=progress,
        )
    )
