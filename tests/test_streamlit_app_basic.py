"""
Basic tests for streamlit_app.py using Streamlit's AppTest framework.
Tests app loading, title, and layout elements.
"""

from streamlit.testing.v1 import AppTest


def test_app_loads(streamlit_app_path):
    """Test that streamlit_app.py loads without errors"""
    at = AppTest.from_file(streamlit_app_path)
    at.run(timeout=10)  # Increase timeout
    assert not at.exception


def test_app_title_and_layout(streamlit_app_path):
    """Test app displays correct title and basic layout"""
    at = AppTest.from_file(streamlit_app_path)
    # Navigate to Report Analyst page where title is displayed
    at.session_state["nav_page"] = "Report Analyst"
    at.run(timeout=10)  # Increase timeout

    # Check title
    assert len(at.title) > 0, "Title not found"
    assert "Report Analyst" in str(at.title[0].value), f"Title should contain 'Report Analyst', got: {at.title[0].value}"

    # Check expanders exist
    assert len(at.expander) > 0, "No expanders found"

    # No exceptions
    assert not at.exception
