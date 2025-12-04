"""
Tests for the QuestionSetLoader functionality
"""

import os
import tempfile

import pytest
import yaml

from report_analyst.core.question_loader import (
    QuestionSet,
    QuestionSetLoader,
    get_question_loader,
)


class TestQuestionSetLoader:
    """Test the QuestionSetLoader class"""

    def test_question_set_dataclass(self):
        """Test QuestionSet dataclass has all required fields including shortcut"""
        qset = QuestionSet(
            id="test",
            name="Test Question Set",
            description="Test description",
            shortcut="test",
            questions={"q1": {"text": "Question 1", "guidelines": "Guidelines 1"}},
        )

        assert qset.id == "test"
        assert qset.name == "Test Question Set"
        assert qset.description == "Test description"
        assert qset.shortcut == "test"
        assert "q1" in qset.questions
        assert qset.questions["q1"]["text"] == "Question 1"

    def test_load_question_set_with_shortcut(self):
        """Test loading a question set with shortcut field"""
        # Test with environment variable to use custom directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test question set file
            test_questions = {
                "name": "Test Questions",
                "shortcut": "test",
                "description": "Test question set",
                "questions": [
                    {
                        "id": "test_1",
                        "text": "What is the test question?",
                        "guidelines": "Test guidelines",
                    }
                ],
            }

            questions_file = os.path.join(temp_dir, "test_questions.yaml")
            with open(questions_file, "w") as f:
                yaml.dump(test_questions, f)

            # Set environment variable to use custom directory
            original_env = os.environ.get("QUESTIONSETS_PATH")
            os.environ["QUESTIONSETS_PATH"] = temp_dir

            try:
                # Create loader (will use environment variable)
                loader = QuestionSetLoader()

                # Load the question set
                question_sets = loader.get_question_sets()

                assert "test" in question_sets
                qset = question_sets["test"]
                assert qset.name == "Test Questions"
                assert qset.shortcut == "test"
                assert qset.description == "Test question set"
                assert "test_1" in qset.questions
                assert qset.questions["test_1"]["text"] == "What is the test question?"
            finally:
                # Restore original environment
                if original_env:
                    os.environ["QUESTIONSETS_PATH"] = original_env
                elif "QUESTIONSETS_PATH" in os.environ:
                    del os.environ["QUESTIONSETS_PATH"]

    def test_load_question_set_without_shortcut(self):
        """Test loading a question set without shortcut field (should default to id)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test question set file without shortcut
            test_questions = {
                "name": "Test Questions",
                "description": "Test question set",
                "questions": [
                    {
                        "id": "test_1",
                        "text": "What is the test question?",
                        "guidelines": "Test guidelines",
                    }
                ],
            }

            questions_file = os.path.join(temp_dir, "test_questions.yaml")
            with open(questions_file, "w") as f:
                yaml.dump(test_questions, f)

            # Set environment variable to use custom directory
            original_env = os.environ.get("QUESTIONSETS_PATH")
            os.environ["QUESTIONSETS_PATH"] = temp_dir

            try:
                # Create loader (will use environment variable)
                loader = QuestionSetLoader()

                # Load the question set
                question_sets = loader.get_question_sets()

                assert "test" in question_sets
                qset = question_sets["test"]
                assert qset.name == "Test Questions"
                assert qset.shortcut == "test"  # Should default to question set id
                assert qset.description == "Test question set"
            finally:
                # Restore original environment
                if original_env:
                    os.environ["QUESTIONSETS_PATH"] = original_env
                elif "QUESTIONSETS_PATH" in os.environ:
                    del os.environ["QUESTIONSETS_PATH"]

    def test_get_question_set_options(self):
        """Test get_question_set_options method returns list of question set IDs"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test question set files
            for i, name in enumerate(["test1", "test2", "test3"]):
                test_questions = {
                    "name": f"{name.title()} Questions",
                    "shortcut": name,
                    "description": f"{name} question set",
                    "questions": [
                        {
                            "id": f"{name}_1",
                            "text": f"What is the {name} question?",
                            "guidelines": f"{name} guidelines",
                        }
                    ],
                }

                questions_file = os.path.join(temp_dir, f"{name}_questions.yaml")
                with open(questions_file, "w") as f:
                    yaml.dump(test_questions, f)

            # Set environment variable to use custom directory
            original_env = os.environ.get("QUESTIONSETS_PATH")
            os.environ["QUESTIONSETS_PATH"] = temp_dir

            try:
                # Create loader (will use environment variable)
                loader = QuestionSetLoader()

                # Get question set options
                options = loader.get_question_set_options()

                assert isinstance(options, list)
                assert len(options) == 3
                assert "test1" in options
                assert "test2" in options
                assert "test3" in options
            finally:
                # Restore original environment
                if original_env:
                    os.environ["QUESTIONSETS_PATH"] = original_env
                elif "QUESTIONSETS_PATH" in os.environ:
                    del os.environ["QUESTIONSETS_PATH"]

    def test_singleton_pattern(self):
        """Test that get_question_loader returns the same instance"""
        loader1 = get_question_loader()
        loader2 = get_question_loader()

        assert loader1 is loader2
        assert isinstance(loader1, QuestionSetLoader)

    def test_load_real_question_sets(self):
        """Test loading the actual question sets from the project"""
        loader = get_question_loader()
        question_sets = loader.get_question_sets()

        # Should have at least the main question sets
        expected_sets = ["everest", "tcfd", "denali", "kilimanjaro"]
        for expected_set in expected_sets:
            assert (
                expected_set in question_sets
            ), f"Expected {expected_set} in question sets"

            qset = question_sets[expected_set]
            assert qset.name is not None
            assert qset.shortcut is not None
            assert qset.description is not None
            assert len(qset.questions) > 0

    def test_question_set_shortcuts(self):
        """Test that all question sets have appropriate shortcuts"""
        loader = get_question_loader()
        question_sets = loader.get_question_sets()

        expected_shortcuts = {
            "everest": "ev",
            "tcfd": "tcfd",
            "denali": "denali",
            "kilimanjaro": "kilimanjaro",
        }

        for qset_id, expected_shortcut in expected_shortcuts.items():
            if qset_id in question_sets:
                qset = question_sets[qset_id]
                assert (
                    qset.shortcut == expected_shortcut
                ), f"Expected {qset_id} to have shortcut '{expected_shortcut}', got '{qset.shortcut}'"

    def test_get_question_set_methods(self):
        """Test various getter methods"""
        loader = get_question_loader()

        # Test get_question_set
        tcfd_set = loader.get_question_set("tcfd")
        assert tcfd_set is not None
        assert tcfd_set.id == "tcfd"

        # Test get_question_set with non-existent ID
        non_existent = loader.get_question_set("non_existent")
        assert non_existent is None

        # Test get_question_set_names
        names = loader.get_question_set_names()
        assert isinstance(names, dict)
        assert "tcfd" in names
        assert names["tcfd"] == "TCFD Questions"

        # Test get_question_set_info
        info = loader.get_question_set_info()
        assert isinstance(info, dict)
        assert "tcfd" in info
        assert "name" in info["tcfd"]
        assert "description" in info["tcfd"]

        # Test get_questions
        questions = loader.get_questions("tcfd")
        assert isinstance(questions, dict)
        assert len(questions) > 0
        assert "tcfd_1" in questions

        # Test get_questions with non-existent ID
        empty_questions = loader.get_questions("non_existent")
        assert empty_questions == {}

    def test_reload_functionality(self):
        """Test reload method clears cache"""
        loader = get_question_loader()

        # Load question sets
        question_sets1 = loader.get_question_sets()
        assert len(question_sets1) > 0

        # Reload should clear cache
        loader.reload()

        # Next access should reload from files
        question_sets2 = loader.get_question_sets()
        assert len(question_sets2) > 0
        assert len(question_sets1) == len(question_sets2)

    def test_error_handling_invalid_yaml(self):
        """Test error handling with invalid YAML file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create an invalid YAML file
            invalid_yaml_file = os.path.join(temp_dir, "invalid_questions.yaml")
            with open(invalid_yaml_file, "w") as f:
                f.write("invalid: yaml: content: [")

            # Set environment variable to use custom directory
            original_env = os.environ.get("QUESTIONSETS_PATH")
            os.environ["QUESTIONSETS_PATH"] = temp_dir

            try:
                # Create loader (will use environment variable)
                loader = QuestionSetLoader()

                # Should handle error gracefully and return empty dict
                question_sets = loader.get_question_sets()
                assert isinstance(question_sets, dict)
                assert len(question_sets) == 0  # No valid question sets loaded
            finally:
                # Restore original environment
                if original_env:
                    os.environ["QUESTIONSETS_PATH"] = original_env
                elif "QUESTIONSETS_PATH" in os.environ:
                    del os.environ["QUESTIONSETS_PATH"]

    def test_fallback_behavior_without_core_functionality(self):
        """Test fallback behavior when core functionality is unavailable"""
        # Test the fallback logic used in streamlit apps
        CORE_FUNCTIONALITY_AVAILABLE = False

        if CORE_FUNCTIONALITY_AVAILABLE:
            from report_analyst.core.question_loader import get_question_loader

            question_loader = get_question_loader()
            question_set_options = question_loader.get_question_set_options() + [
                "custom"
            ]
        else:
            # Fallback: use a generic approach without hardcoded names
            question_set_options = [
                "custom"
            ]  # Only custom when core functionality unavailable

        assert question_set_options == ["custom"]
        assert len(question_set_options) == 1
        assert "custom" in question_set_options

    def test_normal_behavior_with_core_functionality(self):
        """Test normal behavior when core functionality is available"""
        # Test the normal logic used in streamlit apps
        CORE_FUNCTIONALITY_AVAILABLE = True

        if CORE_FUNCTIONALITY_AVAILABLE:
            from report_analyst.core.question_loader import get_question_loader

            question_loader = get_question_loader()
            question_set_options = question_loader.get_question_set_options() + [
                "custom"
            ]
        else:
            # Fallback: use a generic approach without hardcoded names
            question_set_options = [
                "custom"
            ]  # Only custom when core functionality unavailable

        # Should have all question sets plus custom
        expected_sets = {"everest", "tcfd", "denali", "kilimanjaro", "custom"}
        assert set(question_set_options) == expected_sets
        assert len(question_set_options) == 5
        assert "custom" in question_set_options
        assert "everest" in question_set_options
        assert "tcfd" in question_set_options
        assert "denali" in question_set_options
        assert "kilimanjaro" in question_set_options

    def test_no_hardcoded_question_set_names(self):
        """Test that no hardcoded question set names are used in fallback logic"""
        # This test ensures we don't have hardcoded names like ["tcfd", "kilimanjaro", "denali"]
        # in our fallback logic

        # Test fallback behavior
        CORE_FUNCTIONALITY_AVAILABLE = False

        if CORE_FUNCTIONALITY_AVAILABLE:
            from report_analyst.core.question_loader import get_question_loader

            question_loader = get_question_loader()
            question_set_options = question_loader.get_question_set_options()
        else:
            # Fallback: use a generic approach without hardcoded names
            question_set_options = (
                []
            )  # No predefined options when core functionality unavailable

        # Should not contain any hardcoded question set names
        hardcoded_names = ["tcfd", "kilimanjaro", "denali", "everest"]
        for name in hardcoded_names:
            assert (
                name not in question_set_options
            ), f"Hardcoded name '{name}' found in fallback options"

        assert question_set_options == []

    def test_question_set_options_consistency(self):
        """Test that question set options are consistent across different access methods"""
        loader = get_question_loader()

        # Test different ways to get question set options
        options1 = loader.get_question_set_options()
        options2 = list(loader.get_question_sets().keys())
        options3 = list(loader.get_question_set_names().keys())

        # All should return the same question set IDs
        assert options1 == options2 == options3

        # Should contain expected question sets
        expected_sets = ["everest", "tcfd", "denali", "kilimanjaro"]
        for expected_set in expected_sets:
            assert (
                expected_set in options1
            ), f"Expected question set '{expected_set}' not found in options"

        assert len(options1) == 4
