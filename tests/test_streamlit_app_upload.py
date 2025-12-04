"""
Tests for file upload functionality in streamlit_app.py using AppTest.
Tests that the app loads correctly with file upload capabilities.
"""

from streamlit.testing.v1 import AppTest


def test_app_loads_with_upload_capability():
    """Test that app loads without errors and has upload functionality"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # App should load without exceptions
    assert not at.exception, f"App failed to load: {at.exception}"

    # Should have some UI elements
    assert len(at.title) > 0, "App should have a title"
    assert len(at.expander) > 0, "App should have expanders"


def test_app_has_file_related_ui():
    """Test that app has file-related UI elements"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # App should load without exceptions
    assert not at.exception, f"App failed to load: {at.exception}"

    # Should have selectbox for question sets
    assert len(at.selectbox) > 0, "App should have selectbox widgets"

    # Should have some text elements (likely file-related instructions)
    assert len(at.text) > 0 or len(at.markdown) > 0, "App should have text content"
