"""
Job Coordination System

This package provides job coordination and execution for the report_analyst system.
Includes NATS-based job coordination, local job execution, and integration examples.
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
