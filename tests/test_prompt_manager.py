"""Tests for PromptManager typed-answer prompt overrides."""

from report_analyst.core.prompt_manager import (
    DEFAULT_JSON_ANSWER,
    DEFAULT_RULE_4,
    TYPED_JSON_ANSWER,
    TYPED_RULE_4,
    PromptManager,
    build_analysis_user_content,
    has_typed_answer,
    parse_answer_type_line,
)

TCFD_GUIDELINES = """\
- Focus on board-specific oversight activities
- Look for details about processes and frequency of oversight
"""

ESRS_CLASSIFICATION_GUIDELINES = """\
- ANSWER type: classification — exactly one of Yes / No / Unclear / Not disclosed
- Name the specific plan or program
"""

ESRS_QUANTITY_GUIDELINES = """\
- ANSWER type: quantity — numeric value with unit (tCO2e, %, EUR/t, etc.) or Unclear / Not disclosed if not reported
- Do not count RECs as carbon credit purchases
"""


class TestParseAnswerType:
    def test_returns_none_for_tcfd_style_guidelines(self):
        assert parse_answer_type_line(TCFD_GUIDELINES) is None
        assert has_typed_answer(TCFD_GUIDELINES) is False

    def test_parses_classification_line(self):
        parsed = parse_answer_type_line(ESRS_CLASSIFICATION_GUIDELINES)
        assert parsed == "classification — exactly one of Yes / No / Unclear / Not disclosed"

    def test_parses_quantity_line(self):
        parsed = parse_answer_type_line(ESRS_QUANTITY_GUIDELINES)
        assert parsed.startswith("quantity —")


class TestBuildAnalysisUserContent:
    def test_tcfd_keeps_sixty_word_rule_and_prose_json_example(self):
        content = build_analysis_user_content("Q?", "[CHUNK 1]\ntext", TCFD_GUIDELINES)
        assert DEFAULT_RULE_4 in content
        assert TYPED_RULE_4 not in content
        assert f'"ANSWER": "{DEFAULT_JSON_ANSWER}"' in content
        assert "ANSWER must match the ANSWER type" not in content

    def test_esrs_classification_overrides_answer_rules(self):
        content = build_analysis_user_content("Q?", "[CHUNK 1]\ntext", ESRS_CLASSIFICATION_GUIDELINES)
        assert TYPED_RULE_4 in content
        assert DEFAULT_RULE_4 not in content
        assert f'"ANSWER": "{TYPED_JSON_ANSWER}"' in content
        assert "ANSWER must match the ANSWER type" in content
        assert ESRS_CLASSIFICATION_GUIDELINES in content

    def test_esrs_quantity_overrides_answer_rules(self):
        content = build_analysis_user_content("Q?", "[CHUNK 1]\ntext", ESRS_QUANTITY_GUIDELINES)
        assert TYPED_RULE_4 in content
        assert f'"ANSWER": "{TYPED_JSON_ANSWER}"' in content

    def test_evidence_gaps_score_unchanged_for_typed(self):
        content = build_analysis_user_content("Q?", "[CHUNK 1]\ntext", ESRS_CLASSIFICATION_GUIDELINES)
        assert '"EVIDENCE"' in content
        assert '"GAPS"' in content
        assert '"SCORE"' in content
        assert '"SOURCES"' in content
        assert "For each piece of evidence" in content


class TestPromptManagerMessages:
    def test_get_analysis_messages_uses_typed_content(self):
        pm = PromptManager()
        messages = pm.get_analysis_messages(
            question="Test?",
            context="",
            guidelines=ESRS_CLASSIFICATION_GUIDELINES,
            chunks_data=[{"text": "chunk", "relevance_score": 0.5}],
        )
        assert len(messages) == 2
        user_content = messages[1].content
        assert TYPED_RULE_4 in user_content
        assert "[CHUNK 1]" in user_content
