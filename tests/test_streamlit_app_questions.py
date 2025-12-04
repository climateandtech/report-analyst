"""
Tests for question set functionality in streamlit_app.py using AppTest.
Tests dynamic question loading and selection.
"""

from streamlit.testing.v1 import AppTest


def test_question_set_selectbox_exists():
    """Test question set selectbox is present"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Find question set selectbox
    question_selectbox = None
    for sb in at.selectbox:
        if "Question Set" in str(sb.label):
            question_selectbox = sb
            break

    assert question_selectbox is not None, "Question set selectbox not found"
    assert not at.exception


def test_question_sets_loaded_dynamically():
    """Test question sets loaded from question_loader"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Find question set selectbox
    for sb in at.selectbox:
        if "Question Set" in str(sb.label):
            options = [str(opt) for opt in sb.options]
            # Should have multiple question sets
            assert (
                len(options) >= 4
            ), f"Expected at least 4 question sets, got {len(options)}"
            # Verify key question sets present
            options_lower = [opt.lower() for opt in options]
            assert any("tcfd" in opt for opt in options_lower), "TCFD not in options"
            assert any(
                "everest" in opt for opt in options_lower
            ), "Everest not in options"
            break

    assert not at.exception


def test_question_set_selectbox_has_options():
    """Test question set selectbox has multiple options available"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Find question set selectbox
    question_selectbox = None
    for sb in at.selectbox:
        if "Question Set" in str(sb.label):
            question_selectbox = sb
            break

    assert question_selectbox is not None, "Question set selectbox not found"
    assert (
        len(question_selectbox.options) >= 4
    ), f"Expected at least 4 question set options, got {len(question_selectbox.options)}"

    # Verify we have the expected question sets
    options = [str(opt) for opt in question_selectbox.options]
    options_lower = [opt.lower() for opt in options]

    # Should have the key question sets
    assert any(
        "tcfd" in opt for opt in options_lower
    ), f"TCFD not found in options: {options}"
    assert any(
        "everest" in opt for opt in options_lower
    ), f"Everest not found in options: {options}"
    assert any(
        "denali" in opt for opt in options_lower
    ), f"Denali not found in options: {options}"
    assert any(
        "kilimanjaro" in opt for opt in options_lower
    ), f"Kilimanjaro not found in options: {options}"

    assert not at.exception
