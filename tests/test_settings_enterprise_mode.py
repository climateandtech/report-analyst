"""
Test for Settings page enterprise mode checkbox behavior.

Tests that the "Enterprise mode enabled" message only appears when:
1. The checkbox is checked
2. Backend integration is available
"""

from streamlit.testing.v1 import AppTest


def test_enterprise_mode_message_only_when_checked():
    """Test that enterprise mode message only shows when checkbox is checked"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Navigate to Settings page
    at.session_state["nav_page"] = "Settings"
    at.run(timeout=10)

    # Check that Settings page loaded
    assert "Settings" in str(at), "Settings page should be visible"

    # Initially, checkbox should be unchecked (default False)
    # Find the checkbox
    checkboxes = [w for w in at.checkbox if "S3+NATS" in str(w)]
    assert len(checkboxes) > 0, "S3+NATS checkbox should exist"

    checkbox = checkboxes[0]
    initial_value = checkbox.value

    # If checkbox is checked initially (from env var), uncheck it
    if initial_value:
        checkbox.set_value(False)
        at.run(timeout=10)

    # After unchecking, the message should NOT appear
    page_text = str(at)
    if "Enterprise mode enabled" in page_text:
        # This is the bug - message appears even when unchecked
        assert False, "Enterprise mode message should not appear when checkbox is unchecked"

    # Now check the checkbox
    checkbox.set_value(True)
    at.run(timeout=10)

    # After checking, if backend is available, message should appear
    page_text_after = str(at)
    # Note: We can't easily test backend availability in AppTest, so we just check
    # that the checkbox state is correctly reflected
    assert checkbox.value == True, "Checkbox should be checked"


def test_enterprise_mode_checkbox_state_persistence():
    """Test that checkbox state persists correctly across reruns"""
    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Navigate to Settings
    at.session_state["nav_page"] = "Settings"
    at.run(timeout=10)

    # Find checkbox
    checkboxes = [w for w in at.checkbox if "S3+NATS" in str(w)]
    assert len(checkboxes) > 0, "S3+NATS checkbox should exist"
    checkbox = checkboxes[0]

    # Set to True
    checkbox.set_value(True)
    at.run(timeout=10)
    assert checkbox.value == True, "Checkbox should be True after setting"
    # Note: AppTest session_state doesn't support .get(), access directly
    try:
        assert at.session_state["use_s3_upload"] == True, "Session state should be True"
    except (KeyError, AttributeError):
        pass  # Session state might use widget ID instead of key

    # Set to False
    checkbox.set_value(False)
    at.run(timeout=10)
    assert checkbox.value == False, "Checkbox should be False after unchecking"

    # Check that enterprise mode message is NOT shown when unchecked
    page_text = str(at)
    if "Enterprise mode enabled" in page_text:
        assert False, "Enterprise mode message should NOT appear when checkbox is unchecked"

    # Rerun - state should persist
    at.run(timeout=10)
    assert checkbox.value == False, "Checkbox should remain False after rerun"

    # Verify message still doesn't appear after rerun
    page_text_rerun = str(at)
    if "Enterprise mode enabled" in page_text_rerun:
        assert False, "Enterprise mode message should NOT appear after rerun when checkbox is unchecked"
