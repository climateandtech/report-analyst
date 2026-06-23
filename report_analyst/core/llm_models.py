"""LLM model lists for Streamlit UI and Report Analyst API.

Environment overrides (comma-separated model IDs):

- ``OPENAI_MODELS`` — OpenAI dropdown/API entries (replaces default OpenAI list)
- ``GEMINI_MODELS`` — Gemini entries when ``GOOGLE_API_KEY`` is set
- ``LLM_MODELS`` — full combined list (overrides OpenAI + Gemini merge)

Default selection: ``OPENAI_API_MODEL`` or ``DEFAULT_MODEL``, else first entry in
the active list.
"""

from __future__ import annotations

import os
import re

DEFAULT_OPENAI_MODELS: tuple[str, ...] = (
    "gpt-5.4-mini",
    "gpt-5.4",
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
)

DEFAULT_GEMINI_MODELS: tuple[str, ...] = (
    "gemini-3.5-flash",
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
)


def _parse_csv_models(env_value: str | None) -> list[str]:
    if not env_value or not env_value.strip():
        return []
    return [part.strip() for part in env_value.split(",") if part.strip()]


def _dedupe_preserve_order(models: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for model in models:
        if model not in seen:
            seen.add(model)
            out.append(model)
    return out


def get_openai_models() -> list[str]:
    override = _parse_csv_models(os.getenv("OPENAI_MODELS"))
    if override:
        return override
    return list(DEFAULT_OPENAI_MODELS)


def get_gemini_models() -> list[str]:
    override = _parse_csv_models(os.getenv("GEMINI_MODELS"))
    if override:
        return override
    return list(DEFAULT_GEMINI_MODELS)


def get_llm_models(*, include_gemini: bool | None = None) -> list[str]:
    combined = _parse_csv_models(os.getenv("LLM_MODELS"))
    if combined:
        return _dedupe_preserve_order(combined)

    models = list(get_openai_models())
    if include_gemini is None:
        include_gemini = bool(os.getenv("GOOGLE_API_KEY"))
    if include_gemini:
        models.extend(get_gemini_models())
    return _dedupe_preserve_order(models)


def get_default_llm_model() -> str:
    preferred = (os.getenv("OPENAI_API_MODEL") or os.getenv("DEFAULT_MODEL") or "").strip()
    models = get_llm_models()
    if preferred:
        if preferred in models:
            return preferred
        if preferred.startswith("gpt-") or preferred.startswith("gemini-"):
            return preferred
    return models[0] if models else "gpt-4o-mini"


def llm_model_index(models: list[str], preferred: str) -> int:
    try:
        return models.index(preferred)
    except ValueError:
        return 0


def model_display_name(model_id: str) -> str:
    """Human-readable label for API / UI."""
    if model_id.startswith("gpt-"):
        body = model_id.removeprefix("gpt-")
        parts = body.split("-")
        titled = " ".join(p.upper() if p.isdigit() or p in {"mini", "nano", "pro"} else p.title() for p in parts)
        return f"GPT-{titled}"
    if model_id.startswith("gemini-"):
        body = model_id.removeprefix("gemini-")
        parts = re.split(r"[-.]", body)
        titled = " ".join(p.upper() if p.isdigit() else p.title() for p in parts if p)
        return f"Gemini {titled}"
    return model_id


def get_models_for_api(*, include_gemini: bool | None = None) -> list[dict[str, str]]:
    return [{"id": mid, "name": model_display_name(mid)} for mid in get_llm_models(include_gemini=include_gemini)]
