# Test Failures Analysis

## Summary
- **Total Failures**: 25 tests
- **Dataframe Manager**: 3 failures
- **UI Tests**: 22 failures

---

## 1. Dataframe Manager Tests (3 failures)

### Issue Analysis
The `create_analysis_dataframes()` function in `report_analyst/core/dataframe_manager.py` does NOT use `format_list_field()` for formatting EVIDENCE, GAPS, and SOURCES. Instead, it just converts them to strings with newlines:

```python
"Key Evidence": "\n".join(str(e) for e in result.get("EVIDENCE", [])),
"Gaps": "\n".join(str(gap) for gap in result.get("GAPS", [])),
"Sources": "\n".join(str(source) for source in result.get("SOURCES", [])),
```

But the tests expect formatted output with bullet points:
- Evidence: `"• CO2 emissions data for FY 2024 [Chunk 3]"`
- Gaps: `"• Missing data point 1\n• Missing data point 2"`
- Sources: `"• 1\n• 2\n• 3"`

### Failed Tests
1. `test_create_analysis_dataframes_with_evidence` - Expects formatted evidence with `[Chunk X]` but gets raw dict string
2. `test_create_analysis_dataframes_with_gaps_and_sources` - Expects bullet points but gets plain newlines
3. `test_create_analysis_dataframes_with_chunks` - Expects `is_evidence` to be boolean True/False but assertion fails (might be pandas boolean)

### Discussion
**Option A**: Update `create_analysis_dataframes()` to use `format_list_field()` for EVIDENCE, GAPS, and SOURCES
- **Pros**: Matches expected behavior from feature branch
- **Cons**: Changes current working implementation

**Option B**: Update tests to match current implementation
- **Pros**: No code changes needed
- **Cons**: Loses formatting feature that was in feature branch

**Option C**: Check if formatting is actually needed/used in UI
- **Pros**: Makes informed decision
- **Cons**: Requires investigation

**Recommendation**: Option A - The `format_list_field()` function exists and is tested, so we should use it. The feature branch had this formatting, so it was intentional.

---

## 2. UI Test Failures (22 failures)

### Category: Clearly Path to Fix (We Changed It)

#### A. Tab-Based Navigation → Sidebar Navigation Menu (8 failures)
**Root Cause**: We replaced `st.tabs()` with `streamlit-option-menu` sidebar navigation

**Failed Tests**:
1. `test_streamlit_app_tabs.py::test_tabs_exist` - Looks for `at.tabs` with labels ["Previous Reports", "Upload New", "Consolidated Results"]
2. `test_streamlit_app_tabs.py::test_previous_reports_tab` - Looks for tab with "Previous Reports" label
3. `test_streamlit_app_tabs.py::test_upload_new_tab` - Looks for tab with "Upload New" label
4. `test_streamlit_app_tabs.py::test_consolidated_results_tab` - Looks for tab with "Consolidated Results" label
5. `test_streamlit_app_tabs.py::test_session_state_initialization` - Checks `len(at.tabs) >= 3`
6. `test_streamlit_app_basic.py::test_app_title_and_layout` - Checks `len(at.title) > 0` and looks for "Report Analyst" in title
7. `test_streamlit_app_upload.py::test_app_loads_with_upload_capability` - Checks `len(at.title) > 0`
8. `test_streamlit_app_data_display.py::test_app_layout_and_structure` - Likely checks for tabs

**Fix Path**: 
- Update tests to look for `streamlit-option-menu` navigation instead of tabs
- Check for navigation options: ["Upload Report", "Report Analyst", "All Results"]
- Title might be in different location now (check if it's still `st.title()` or moved)

---

### Category: Unknown (Need Investigation)

#### B. Widget/Selectbox Location Changes (8 failures)
**Root Cause**: Widgets might be in different locations (inside expanders, different pages, etc.)

**Failed Tests**:
1. `test_streamlit_app_tabs.py::test_configuration_expander` - Looks for expander with "Configuration" in label
2. `test_streamlit_app_tabs.py::test_configuration_widgets` - Looks for number inputs and model selectbox
3. `test_streamlit_app_tabs.py::test_question_set_selection` - Looks for selectbox with "Question Set" in label
4. `test_streamlit_app_tabs.py::test_analysis_controls` - Looks for checkboxes and buttons
5. `test_streamlit_app_questions.py::test_question_set_selectbox_exists` - Looks for "Question Set" selectbox
6. `test_streamlit_app_questions.py::test_question_set_selectbox_has_options` - Checks question set selectbox has options
7. `test_streamlit_app_data_display.py::test_question_display_functionality` - Looks for question-related elements
8. `test_streamlit_app_data_display.py::test_model_selection_display` - Looks for model selectbox

**Investigation Needed**:
- Are these widgets still present but in different locations?
- Are they inside the "Analysis Configuration" expander?
- Are they on specific pages (Report Analyst page) that need navigation to access?
- Check if `at.selectbox` can find them when they're inside expanders or conditional blocks

**Possible Issues**:
- Widgets might be inside `st.expander("Analysis Configuration")` which might not be expanded by default in AppTest
- Widgets might be on "Report Analyst" page which requires navigation to access
- Widgets might have different keys/labels now

---

#### C. Title/Content Display (3 failures)
**Root Cause**: Title might be in different location or not rendered initially

**Failed Tests**:
1. `test_streamlit_app_basic.py::test_app_title_and_layout` - `len(at.title) > 0` fails
2. `test_streamlit_app_upload.py::test_app_loads_with_upload_capability` - `len(at.title) > 0` fails
3. `test_streamlit_app_tabs.py::test_session_state_initialization` - `len(at.title) > 0` fails

**Investigation Needed**:
- Check if `st.title("Report Analyst")` is still called in the main function
- Check if title is conditional (only shown on certain pages)
- Check if AppTest can see titles that are inside conditional blocks
- Title might be on specific page that requires navigation

---

#### D. File/Content Display (3 failures)
**Root Cause**: File-related UI might be conditional or on different pages

**Failed Tests**:
1. `test_streamlit_app_upload.py::test_app_has_file_related_ui` - `len(at.selectbox) > 0` fails
2. `test_streamlit_app_data_display.py::test_configuration_display` - Likely checks for configuration widgets
3. `test_streamlit_app_data_display.py::test_consolidated_results_display` - Likely checks for consolidated results UI
4. `test_streamlit_app_data_display.py::test_analysis_controls_display` - Likely checks for analysis controls
5. `test_streamlit_app_data_display.py::test_dynamic_content_loading` - Likely checks for dynamic content

**Investigation Needed**:
- Are file selectboxes only shown when files exist?
- Are they on specific pages that need navigation?
- Check if AppTest can see widgets inside conditional blocks

---

#### E. Backend Integration (1 failure)
**Root Cause**: Unknown - might be related to backend configuration changes

**Failed Tests**:
1. `test_streamlit_app_backend_integration.py::test_backend_integration_compatibility` - Unknown specific issue

**Investigation Needed**:
- Check what this test is checking
- Might be related to Settings expander changes
- Might be related to backend config changes

---

## Recommendations

### Immediate Actions
1. **Dataframe Manager**: Update `create_analysis_dataframes()` to use `format_list_field()` for EVIDENCE, GAPS, and SOURCES
2. **Tab Tests**: Update all tab-related tests to check for sidebar navigation instead
3. **Title Tests**: Investigate why `at.title` is empty - check if title is conditional or on specific page

### Investigation Needed
1. Run AppTest manually to see what widgets are actually visible
2. Check if widgets inside expanders are accessible in AppTest
3. Check if navigation to specific pages is needed before widgets are visible
4. Verify if conditional rendering affects AppTest visibility

### Test Update Strategy
1. **Clear Path**: Update tab tests → navigation tests (straightforward)
2. **Unknown**: Investigate widget visibility → update tests based on findings
3. **Consider**: Some tests might need to navigate to specific pages first before checking for widgets



