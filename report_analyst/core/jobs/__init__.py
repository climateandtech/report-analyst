"""
Job Coordination System (Core)

This package provides basic job coordination using NATS for the core report_analyst package.
For universal analysis functions that can be integrated into Lambda/Celery/etc.,
use the separate `report_analyst_jobs` module instead.

This core jobs system is primarily for:
- NATS-based job coordination
- Local job execution
- Integration with the Streamlit app
"""

from .coordinator import JobCoordinator, create_job_coordinator
from .interfaces import (
    AnalysisJobDefinition,
    ExecutionBackend,
    JobDefinition,
    JobResult,
    JobStatus,
)

__all__ = [
    # Core interfaces
    "JobDefinition",
    "JobResult",
    "JobStatus",
    "ExecutionBackend",
    "AnalysisJobDefinition",
    # Job coordination
    "JobCoordinator",
    "create_job_coordinator",
]
