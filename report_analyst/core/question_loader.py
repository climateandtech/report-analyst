"""
Centralized Question Set Loader

This module consolidates all question set loading functionality to eliminate
duplication and ensure consistency across the application.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

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


def bundled_questionsets_dir() -> Path:
    return Path(__file__).parent.parent / "questionsets"


class QuestionSetLoader:
    """Centralized loader for question sets from YAML files and installed DB rows."""

    def __init__(self):
        self._question_sets: Optional[Dict[str, QuestionSet]] = None
        self._questionsets_paths = self._get_questionsets_paths()

    def _get_questionsets_paths(self) -> List[Path]:
        """Volume/custom paths; bundled image dir is always merged separately."""
        env_path = os.getenv("QUESTIONSETS_PATH")
        if env_path:
            return [Path(env_path)]
        return [
            Path(__file__).parent.parent / "questionsets",
            Path(__file__).parent.parent.parent / "questionsets",
            Path.cwd() / "questionsets",
        ]

    def _question_set_from_config(self, question_set_id: str, config: dict) -> QuestionSet:
        questions = {}
        for q in config.get("questions", []):
            q_id = q.get("id", "")
            if q_id:
                questions[q_id] = {
                    "text": q.get("text", ""),
                    "guidelines": q.get("guidelines", ""),
                }
        return QuestionSet(
            id=question_set_id,
            name=config.get("name", f"{question_set_id.title()} Question Set"),
            description=config.get("description", "") or "",
            shortcut=config.get("shortcut", question_set_id),
            questions=questions,
        )

    def _load_yaml_from_paths(self, paths: List[Path]) -> Dict[str, QuestionSet]:
        question_sets: Dict[str, QuestionSet] = {}
        for path in paths:
            if not path.exists():
                continue
            for yaml_file in path.glob("*_questions.yaml"):
                try:
                    with open(yaml_file, "r", encoding="utf-8") as handle:
                        config = yaml.safe_load(handle) or {}
                    question_set_id = yaml_file.stem.replace("_questions", "")
                    question_sets[question_set_id] = self._question_set_from_config(question_set_id, config)
                except (OSError, yaml.YAMLError, AttributeError, TypeError, ValueError, KeyError) as e:
                    logger.error(f"[QUESTION_LOADER] Error loading {yaml_file}: {e!s}")
        return question_sets

    def _load_bundled_yaml(self) -> Dict[str, QuestionSet]:
        base = bundled_questionsets_dir()
        if not base.is_dir():
            return {}
        return self._load_yaml_from_paths([base])

    def _load_installed_db(self) -> Dict[str, QuestionSet]:
        try:
            from sqlalchemy.exc import SQLAlchemyError

            from report_analyst.core.installed_questionsets import load_installed_question_sets

            return load_installed_question_sets()
        except (ImportError, OSError, SQLAlchemyError) as e:
            logger.warning("[QUESTION_LOADER] Could not load installed question sets: %s", e)
            return {}

    def _load_question_sets(self) -> Dict[str, QuestionSet]:
        """Bundled YAML, optional volume YAML, then DB (DB wins on same id)."""
        question_sets = {}
        question_sets.update(self._load_bundled_yaml())

        env_only = os.getenv("QUESTIONSETS_PATH")
        if env_only:
            extra = self._load_yaml_from_paths([Path(env_only)])
            question_sets.update(extra)
        elif self._questionsets_paths != [bundled_questionsets_dir()]:
            extra = self._load_yaml_from_paths(self._questionsets_paths)
            for sid, qset in extra.items():
                if sid not in question_sets:
                    question_sets[sid] = qset

        question_sets.update(self._load_installed_db())
        logger.info("[QUESTION_LOADER] Loaded %d question set(s)", len(question_sets))
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
        """Force reload of question sets (also re-reads QUESTIONSETS_PATH)."""
        self._question_sets = None
        self._questionsets_paths = self._get_questionsets_paths()
        logger.info("[QUESTION_LOADER] Question sets cache cleared, will reload on next access")


# Global singleton instance
_question_loader = QuestionSetLoader()


def get_question_loader() -> QuestionSetLoader:
    """Get the global question loader instance"""
    return _question_loader
