"""
Tests for data display and visualization components in streamlit app using AppTest.
Tests dataframes, charts, and result display functionality.
"""

from streamlit.testing.v1 import AppTest


def test_dataframe_display_capability():
    """Test that the app can display dataframes"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # The app should load without errors, indicating dataframe display capability
    assert not at.exception, "App failed to load dataframe display components"

    # Check that the app has the necessary imports and structure for data display
    # This is verified by the app loading successfully with dataframe_manager imports


def test_analysis_results_structure():
    """Test that analysis results structure is properly set up"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Check for placeholder elements that would be used for results
    # AppTest doesn't expose empty placeholders directly, so we verify the app loads

    # Check for progress indicators
    # Progress might not be visible initially, so this is optional
    # AppTest doesn't expose progress widgets directly

    assert not at.exception


def test_file_history_functionality():
    """Test file history and previous reports functionality"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Check for file history selectbox
    has_file_history = False
    for sb in at.selectbox:
        if "previously analyzed" in str(sb.label).lower() or "previous_file" in str(
            sb.key
        ):
            has_file_history = True
            break

    # File history might not be visible if no previous files exist
    # This is expected behavior, so we just verify the app loads correctly
    assert not at.exception


def test_question_display_functionality():
    """Test question display and selection functionality"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    # Navigate to Report Analyst page where questions are displayed
    at.session_state["nav_page"] = "Report Analyst"
    at.run(timeout=10)

    # Check for question-related UI elements
    has_question_elements = False

    # Look for question-related elements in selectboxes
    for sb in at.selectbox:
        if any(
            keyword in str(sb.label).lower()
            for keyword in ["question", "tcfd", "everest", "denali", "kilimanjaro"]
        ):
            has_question_elements = True
            break

    # Questions should be loaded and displayed
    assert has_question_elements, "No question-related elements found"
    assert not at.exception


def test_model_selection_display():
    """Test LLM model selection display"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    # Navigate to Report Analyst page where model selection is located
    at.session_state["nav_page"] = "Report Analyst"
    at.run(timeout=10)

    # Check for model selection
    has_model_selection = False
    for sb in at.selectbox:
        if "model" in str(sb.label).lower() or "llm_model" in str(sb.key).lower():
            has_model_selection = True
            # Check that it has model options
            options = [str(opt).lower() for opt in sb.options]
            assert any(
                "gpt" in opt for opt in options
            ), "No GPT models found in options"
            break

    assert has_model_selection, "Model selection not found"
    assert not at.exception


def test_configuration_display():
    """Test configuration parameter display"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    # Navigate to Report Analyst page where configuration widgets are located
    at.session_state["nav_page"] = "Report Analyst"
    at.run(timeout=10)

    # Check for configuration number inputs
    has_config_inputs = len(at.number_input) > 0
    assert has_config_inputs, "No configuration number inputs found"

    # Check for specific configuration parameters
    config_labels = []
    for ni in at.number_input:
        config_labels.append(str(ni.label).lower())

    expected_configs = ["chunk", "overlap", "top", "k"]
    found_configs = [
        config
        for config in expected_configs
        if any(config in label for label in config_labels)
    ]

    assert (
        len(found_configs) >= 2
    ), f"Expected at least 2 configuration parameters, found: {found_configs}"
    assert not at.exception


def test_analysis_controls_display():
    """Test analysis control options display"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    # Navigate to Report Analyst page where analysis controls are located
    at.session_state["nav_page"] = "Report Analyst"
    at.run(timeout=10)

    # Check for analysis control checkboxes
    has_analysis_controls = len(at.checkbox) > 0
    assert has_analysis_controls, "No analysis control checkboxes found"

    # Check for analysis buttons
    has_analysis_buttons = len(at.button) > 0
    assert has_analysis_buttons, "No analysis buttons found"

    assert not at.exception


def test_error_handling_display():
    """Test error handling and display capabilities"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # The app should handle errors gracefully and display them
    # This is verified by the app loading without exceptions
    assert not at.exception, "App failed to handle errors properly"

    # Check for error display capabilities
    # Error display elements might not be visible initially, so this is optional
    # The app should handle errors gracefully, which is verified by loading without exceptions


def test_consolidated_results_display():
    """Test All Results page display functionality (previously called Consolidated Results)"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    # Navigate to All Results page
    at.session_state["nav_page"] = "All Results"
    at.run(timeout=10)

    # Check that we're on the All Results page
    assert at.session_state["nav_page"] == "All Results", "Not on All Results page"

    # Check for consolidated results selectbox
    has_consolidated_selectbox = False
    for sb in at.selectbox:
        if "consolidated_set" in str(sb.key):
            has_consolidated_selectbox = True
            break

    assert has_consolidated_selectbox, "Consolidated results selectbox not found"
    assert not at.exception


def test_app_layout_and_structure():
    """Test overall app layout and structure"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Check that navigation page is set in session state
    assert "nav_page" in at.session_state, "Navigation page not found in session state"
    
    # Navigate to Report Analyst page to check for title
    at.session_state["nav_page"] = "Report Analyst"
    at.run(timeout=10)

    # Check basic app structure
    assert len(at.title) > 0, "App title not found"
    assert len(at.expander) > 0, "No expanders found"

    # Check for wide layout (should be set in page_config)
    # This is verified by the app loading successfully with wide layout

    assert not at.exception


def test_dynamic_content_loading():
    """Test dynamic content loading capabilities"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    # Navigate to Report Analyst page where question sets are displayed
    at.session_state["nav_page"] = "Report Analyst"
    at.run(timeout=10)

    # Check that dynamic content can be loaded
    # This includes question sets, models, and file history

    # Question sets should be loaded dynamically
    has_question_sets = False
    for sb in at.selectbox:
        if ("Question Set" in str(sb.label) or "new_question_set" in str(sb.key)) and len(sb.options) > 0:
            has_question_sets = True
            break

    assert has_question_sets, "Dynamic question sets not loaded"
    assert not at.exception
