"""Tests for question-table selection helpers in streamlit_app."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from report_analyst.streamlit_app import selected_question_ids_from_editor


def test_is_true_on_select_column_is_not_element_wise_filter():
    """Regression: ``series is True`` compares object identity, not row values."""
    edited_df = pd.DataFrame(
        {
            "Select": [True, False, True],
            "QID": ["tcfd_1", "tcfd_2", "tcfd_3"],
        }
    )
    with pytest.raises(KeyError, match="False"):
        edited_df[edited_df["Select"] is True]["QID"].tolist()


def test_selected_question_ids_from_editor_returns_checked_qids():
    edited_df = pd.DataFrame(
        {
            "Select": [True, False, True],
            "QID": ["tcfd_1", "tcfd_2", "tcfd_3"],
            "QUESTION": ["Q1", "Q2", "Q3"],
        }
    )
    assert selected_question_ids_from_editor(edited_df) == ["tcfd_1", "tcfd_3"]


def test_selected_question_ids_from_editor_none_checked():
    edited_df = pd.DataFrame(
        {
            "Select": [False, False],
            "QID": ["tcfd_1", "tcfd_2"],
        }
    )
    assert selected_question_ids_from_editor(edited_df) == []


def test_selected_question_ids_from_editor_numpy_bool_column():
    edited_df = pd.DataFrame(
        {
            "Select": np.array([True, False], dtype=bool),
            "QID": ["tcfd_1", "tcfd_2"],
        }
    )
    assert selected_question_ids_from_editor(edited_df) == ["tcfd_1"]


def test_selected_question_ids_from_editor_empty_dataframe():
    assert selected_question_ids_from_editor(pd.DataFrame()) == []
