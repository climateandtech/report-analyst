"""
Report Analyst API Module

FastAPI-based API for document analysis.
"""

__version__ = "0.1.0"

try:
    from .main import app

    __all__ = ["app"]
except ImportError:
    # FastAPI dependencies not installed
    __all__ = []
