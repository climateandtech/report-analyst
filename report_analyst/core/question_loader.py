"""
Centralized Question Set Loader

This module consolidates all question set loading functionality to eliminate
duplication and ensure consistency across the application.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class QuestionSet:
    """Data class for a question set"""

    id: str
    name: str
    description: str
    shortcut: str  # short display name for UI
    questions: Dict[str, Dict[str, str]]  # question_id -> {text, guidelines}


class QuestionSetLoader:
    """Centralized loader for question sets from YAML files"""

    def __init__(self):
        self._question_sets: Optional[Dict[str, QuestionSet]] = None
        self._questionsets_paths = self._get_questionsets_paths()

    def _get_questionsets_paths(self) -> List[Path]:
        """Get possible paths for questionsets directory"""
        # Check environment variable first
        env_path = os.getenv("QUESTIONSETS_PATH")
        if env_path:
            return [Path(env_path)]

        # Default search paths
        return [
            Path(__file__).parent.parent / "questionsets",  # app/questionsets
            Path(__file__).parent.parent.parent / "questionsets",  # project root
            Path.cwd() / "questionsets",  # current working directory
        ]

    def _load_question_sets(self) -> Dict[str, QuestionSet]:
        """Load all question sets from YAML files"""
        question_sets = {}

        logger.info(f"[QUESTION_LOADER] Looking for question set files in:")
        for path in self._questionsets_paths:
            logger.info(f"[QUESTION_LOADER] - {path.resolve()}")

        # Find all YAML files in the questionsets directories
        yaml_files = []
        for path in self._questionsets_paths:
            if path.exists():
                yaml_files.extend(path.glob("*_questions.yaml"))

        logger.info(f"[QUESTION_LOADER] Found {len(yaml_files)} question set files")

        for yaml_file in yaml_files:
            try:
                logger.info(f"[QUESTION_LOADER] Loading question set from: {yaml_file}")

                with open(yaml_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                # Extract question set ID from filename (e.g., "lucia_questions.yaml" -> "lucia")
                question_set_id = yaml_file.stem.replace("_questions", "")

                # Convert questions list to dictionary format
                questions = {}
                for q in config.get("questions", []):
                    q_id = q.get("id", "")
                    if q_id:
                        questions[q_id] = {
                            "text": q.get("text", ""),
                            "guidelines": q.get("guidelines", ""),
                        }
                        logger.debug(f"[QUESTION_LOADER] Added question {q_id}")

                question_set = QuestionSet(
                    id=question_set_id,
                    name=config.get("name", f"{question_set_id.title()} Question Set"),
                    description=config.get("description", ""),
                    shortcut=config.get("shortcut", question_set_id),
                    questions=questions,
                )

                question_sets[question_set_id] = question_set

                logger.info(f"[QUESTION_LOADER] ✓ Loaded {len(questions)} questions for {question_set_id}")

            except Exception as e:
                logger.error(f"[QUESTION_LOADER] Error loading question set from {yaml_file}: {str(e)}")
                continue

        if not question_sets:
            logger.warning("[QUESTION_LOADER] No question sets loaded!")

        return question_sets

    def get_question_sets(self) -> Dict[str, QuestionSet]:
        """Get all available question sets (lazy loaded)"""
        if self._question_sets is None:
            self._question_sets = self._load_question_sets()
        return self._question_sets

    def get_question_set(self, question_set_id: str) -> Optional[QuestionSet]:
        """Get a specific question set by ID"""
        question_sets = self.get_question_sets()
        return question_sets.get(question_set_id)

    def get_question_set_names(self) -> Dict[str, str]:
        """Get question set IDs and names for UI display"""
        question_sets = self.get_question_sets()
        return {qset.id: qset.name for qset in question_sets.values()}

    def get_question_set_info(self) -> Dict[str, Dict[str, str]]:
        """Get question set info (name and description) for UI display"""
        question_sets = self.get_question_sets()
        return {qset.id: {"name": qset.name, "description": qset.description} for qset in question_sets.values()}

    def get_questions(self, question_set_id: str) -> Dict[str, Dict[str, str]]:
        """Get questions for a specific question set"""
        question_set = self.get_question_set(question_set_id)
        return question_set.questions if question_set else {}

    def get_question_set_options(self) -> List[str]:
        """Get list of question set IDs for UI dropdown options"""
        return list(self.get_question_sets().keys())

    def reload(self):
        """Force reload of question sets"""
        self._question_sets = None
        logger.info("[QUESTION_LOADER] Question sets cache cleared, will reload on next access")


# Global singleton instance
_question_loader = QuestionSetLoader()


def get_question_loader() -> QuestionSetLoader:
    """Get the global question loader instance"""
    return _question_loader
