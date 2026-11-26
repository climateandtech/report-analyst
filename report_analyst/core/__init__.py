"""Core analysis modules."""

from typing import Any

__all__ = ["CacheManager"]


def __getattr__(name: str) -> Any:
    if name == "CacheManager":
        from .cache_manager import CacheManager

        return CacheManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
