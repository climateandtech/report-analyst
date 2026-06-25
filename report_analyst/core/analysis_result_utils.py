"""Detect and partition failed vs successful analysis results."""

from __future__ import annotations

from typing import Any

_ERROR_ANSWER_PREFIXES = (
    "Error analyzing document:",
    "Error parsing analysis:",
)


def result_payload(entry: dict[str, Any]) -> dict[str, Any]:
    """Unwrap cache/get_analysis entries that nest payload under ``result``."""
    if not isinstance(entry, dict):
        return {}
    nested = entry.get("result")
    return nested if isinstance(nested, dict) else entry


def is_stored_analysis_error(result: dict[str, Any] | None) -> bool:
    """True when a result dict represents a failed analysis, not a real answer."""
    if not result:
        return False
    if result.get("analysis_status") == "error":
        return True
    if result.get("error"):
        return True
    answer = str(result.get("ANSWER", ""))
    return any(answer.startswith(prefix) for prefix in _ERROR_ANSWER_PREFIXES)


def analysis_error_message(result: dict[str, Any]) -> str:
    if result.get("error"):
        return str(result["error"])
    return str(result.get("ANSWER", "Analysis failed"))


def split_analysis_results(results: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Return (successful_results, question_id -> error_message)."""
    successes: dict[str, Any] = {}
    failures: dict[str, str] = {}
    for question_id, entry in results.items():
        payload = result_payload(entry)
        if is_stored_analysis_error(payload):
            failures[question_id] = analysis_error_message(payload)
        else:
            successes[question_id] = entry
    return successes, failures


def filter_successful_analysis_results(results: dict[str, Any]) -> dict[str, Any]:
    successes, _ = split_analysis_results(results)
    return successes


def normalize_results_container(results: Any) -> dict[str, Any]:
    """Normalize UI session results to ``{\"answers\": {question_id: entry}}``."""
    if not isinstance(results, dict):
        return {"answers": {}}
    answers = results.get("answers")
    if isinstance(answers, dict):
        return results
    return {"answers": dict(results)}


def session_answers_map(results: dict[str, Any]) -> dict[str, Any]:
    """Return question_id -> entry from nested or legacy flat session results."""
    return normalize_results_container(results)["answers"]
