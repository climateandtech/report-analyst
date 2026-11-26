"""
Test for Settings page enterprise mode checkbox behavior.

Tests that the "Enterprise mode enabled" message only appears when:
1. The checkbox is checked (or env var is set and not overridden)
2. Backend integration is available
"""

import os
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


def test_enterprise_mode_message_only_when_checked():
    """Test that enterprise mode message only shows when checkbox is checked"""
    # Run without USE_S3_UPLOAD env var to test checkbox behavior
    with patch.dict(os.environ, {"USE_S3_UPLOAD": "false"}, clear=False):
        at = AppTest.from_file("report_analyst/streamlit_app.py")
        at.run(timeout=10)

        # Navigate to Settings page
        at.session_state["nav_page"] = "Settings"
        at.run(timeout=10)

        # Check that Settings page loaded
        assert "Settings" in str(at), "Settings page should be visible"

        # Find the checkbox (should exist when env var is not set)
        checkboxes = [w for w in at.checkbox if "S3+NATS" in str(w)]
        assert len(checkboxes) > 0, "S3+NATS checkbox should exist when env var not set"

        checkbox = checkboxes[0]
        initial_value = checkbox.value

        # If checkbox is checked initially, uncheck it
        if initial_value:
            checkbox.set_value(False)
            at.run(timeout=10)

        # After unchecking, the message should NOT appear
        page_text = str(at)
        if "Enterprise mode enabled" in page_text:
            assert False, "Enterprise mode message should not appear when checkbox is unchecked"

        # Now check the checkbox
        checkbox.set_value(True)
        at.run(timeout=10)

        # After checking, checkbox state should be reflected
        assert checkbox.value is True, "Checkbox should be checked"


def test_enterprise_mode_checkbox_state_persistence():
    """Test that checkbox state persists correctly across reruns"""
    # Run without USE_S3_UPLOAD env var to test checkbox behavior
    with patch.dict(os.environ, {"USE_S3_UPLOAD": "false"}, clear=False):
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
        assert checkbox.value is True, "Checkbox should be True after setting"

        # Set to False
        checkbox.set_value(False)
        at.run(timeout=10)
        assert checkbox.value is False, "Checkbox should be False after unchecking"

        # Check that enterprise mode message is NOT shown when unchecked
        page_text = str(at)
        if "Enterprise mode enabled" in page_text:
            assert False, "Enterprise mode message should NOT appear when checkbox is unchecked"

        # Rerun - state should persist
        at.run(timeout=10)
        assert checkbox.value is False, "Checkbox should remain False after rerun"


def test_enterprise_mode_env_var_detection():
    """Test that the app correctly detects USE_S3_UPLOAD env var"""
    # This test verifies the env var detection logic works
    # When USE_S3_UPLOAD=true is in env, session state should be True
    env_value = os.getenv("USE_S3_UPLOAD", "false").lower() == "true"

    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.run(timeout=10)

    # Navigate to Settings
    at.session_state["nav_page"] = "Settings"
    at.run(timeout=10)

    # Session state should match env var (unless overridden)
    # AppTest session_state doesn't support .get(), access with try/except
    try:
        session_value = at.session_state["use_s3_upload"]
    except KeyError:
        session_value = False

    # If env var is true, session should be true (unless override)
    if env_value:
        # When env is true, session should be true unless overridden
        try:
            override = at.session_state["override_s3_upload"]
        except KeyError:
            override = False
        if not override:
            assert session_value is True, "use_s3_upload should be True when USE_S3_UPLOAD=true"
