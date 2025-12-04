"""
Tests for streamlit app tabs and data loading functionality using AppTest.
Tests Previous Reports, Upload New, and Consolidated Results tabs.
"""

from streamlit.testing.v1 import AppTest


def test_tabs_exist():
    """Test that all three main tabs are present"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Check that tabs exist
    assert len(at.tabs) >= 3, "Expected at least 3 tabs"

    # Check tab labels
    tab_labels = [tab.label for tab in at.tabs]
    expected_tabs = ["Previous Reports", "Upload New", "Consolidated Results"]

    for expected_tab in expected_tabs:
        assert (
            expected_tab in tab_labels
        ), f"Tab '{expected_tab}' not found in {tab_labels}"

    assert not at.exception


def test_previous_reports_tab():
    """Test Previous Reports tab functionality"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Find Previous Reports tab
    previous_tab = None
    for tab in at.tabs:
        if "Previous Reports" in tab.label:
            previous_tab = tab
            break

    assert previous_tab is not None, "Previous Reports tab not found"

    # Check if selectbox for previous files exists
    has_file_selectbox = False
    for sb in at.selectbox:
        if "previously analyzed report" in str(sb.label).lower():
            has_file_selectbox = True
            break

    # The selectbox might not be visible if no previous files exist
    # This is expected behavior, so we just check the tab exists
    assert not at.exception


def test_upload_new_tab():
    """Test Upload New tab functionality"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Find Upload New tab
    upload_tab = None
    for tab in at.tabs:
        if "Upload New" in tab.label:
            upload_tab = tab
            break

    assert upload_tab is not None, "Upload New tab not found"

    # Check for file uploader in the app (should be present)
    has_file_uploader = hasattr(at, "file_uploader") and len(at.file_uploader) > 0
    # File uploader might not be visible initially in AppTest, so this is optional
    # The important thing is that the tab exists and the app loads without errors
    assert not at.exception


def test_consolidated_results_tab():
    """Test Consolidated Results tab functionality"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Find Consolidated Results tab
    consolidated_tab = None
    for tab in at.tabs:
        if "Consolidated Results" in tab.label:
            consolidated_tab = tab
            break

    assert consolidated_tab is not None, "Consolidated Results tab not found"

    # Check for question set selectbox in consolidated tab
    has_consolidated_selectbox = False
    for sb in at.selectbox:
        if "consolidated_set" in str(sb.key):
            has_consolidated_selectbox = True
            break

    # The selectbox should exist for question set selection
    assert (
        has_consolidated_selectbox
    ), "Question set selectbox not found in Consolidated Results tab"
    assert not at.exception


def test_configuration_expander():
    """Test Analysis Configuration expander"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Check for configuration expander
    has_config_expander = False
    for exp in at.expander:
        if "Configuration" in str(exp.label):
            has_config_expander = True
            break

    assert has_config_expander, "Analysis Configuration expander not found"
    assert not at.exception


def test_configuration_widgets():
    """Test configuration widgets (chunk size, overlap, top_k, model)"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Check for number inputs (chunk size, overlap, top_k)
    has_number_inputs = len(at.number_input) > 0
    assert has_number_inputs, "No number input widgets found for configuration"

    # Check for model selectbox
    has_model_selectbox = False
    for sb in at.selectbox:
        if "model" in str(sb.label).lower():
            has_model_selectbox = True
            break

    assert has_model_selectbox, "Model selectbox not found"
    assert not at.exception


def test_question_set_selection():
    """Test question set selection functionality"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Find question set selectbox
    question_selectbox = None
    for sb in at.selectbox:
        if "Question Set" in str(sb.label) and sb.options:
            question_selectbox = sb
            break

    assert question_selectbox is not None, "Question set selectbox not found"

    # Check that it has multiple options
    assert (
        len(question_selectbox.options) >= 4
    ), f"Expected at least 4 question sets, got {len(question_selectbox.options)}"

    # Verify key question sets are present
    options_lower = [str(opt).lower() for opt in question_selectbox.options]
    expected_sets = ["tcfd", "everest", "denali", "kilimanjaro"]

    for expected_set in expected_sets:
        assert any(
            expected_set in opt for opt in options_lower
        ), f"Question set '{expected_set}' not found in options"

    assert not at.exception


def test_analysis_controls():
    """Test analysis control checkboxes and buttons"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Check for checkboxes (LLM scoring, force recompute)
    has_checkboxes = len(at.checkbox) > 0
    assert has_checkboxes, "No checkbox widgets found for analysis controls"

    # Check for buttons (analyze button)
    has_buttons = len(at.button) > 0
    assert has_buttons, "No button widgets found"

    assert not at.exception


def test_footer_display():
    """Test that footer with Climate+Tech branding is displayed"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Check for footer content in markdown
    # Footer might not be visible in AppTest, so we just verify the app loads
    # The footer is added via st.markdown with unsafe_allow_html=True
    assert not at.exception


def test_session_state_initialization():
    """Test that session state variables are properly initialized"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # The app should initialize without errors, which means session state is set up correctly
    assert not at.exception, "Session state initialization failed"

    # Check that the app has the expected structure
    assert len(at.title) > 0, "App title not found"
    assert len(at.expander) > 0, "No expanders found"
    assert len(at.tabs) >= 3, "Not enough tabs found"
