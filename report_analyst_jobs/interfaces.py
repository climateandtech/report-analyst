"""
Abstract Interfaces for Job System

These interfaces allow jobs to be executed on different backends:
NATS, AWS Lambda, Step Functions, local workers, etc.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class JobStatus(str, Enum):
    """Job execution status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionBackend(str, Enum):
    """Available execution backends"""

    NATS = "nats"
    LAMBDA = "lambda"
    STEP_FUNCTIONS = "step_functions"
    LOCAL = "local"
    SEARCH_BACKEND = "search_backend"


@dataclass
class JobDefinition:
    """Definition of a job to be executed"""

    job_id: str
    job_type: str
    parameters: Dict[str, Any]
    priority: int = 1
    timeout_seconds: int = 300
    retry_count: int = 3
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "parameters": self.parameters,
            "priority": self.priority,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobDefinition":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class JobResult:
    """Result of job execution"""

    job_id: str
    status: JobStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (self.completed_at.isoformat() if self.completed_at else None),
            "metadata": self.metadata or {},
        }


class JobHandler(ABC):
    """Abstract base class for job handlers"""

    @abstractmethod
    async def execute(self, job: JobDefinition) -> JobResult:
        """Execute a job and return result"""
        pass

    @abstractmethod
    def get_supported_job_types(self) -> List[str]:
        """Return list of job types this handler supports"""
        pass


class JobExecutor(ABC):
    """Abstract base class for job executors (backends)"""

    @abstractmethod
    async def submit_job(self, job: JobDefinition) -> str:
        """Submit a job for execution, return job_id"""
        pass

    @abstractmethod
    async def get_job_status(self, job_id: str) -> JobResult:
        """Get status and result of a job"""
        pass

    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        pass

    @abstractmethod
    async def list_jobs(self, status: Optional[JobStatus] = None) -> List[JobResult]:
        """List jobs with optional status filter"""
        pass

    @property
    @abstractmethod
    def backend_type(self) -> ExecutionBackend:
        """Return the backend type"""
        pass


class ConfigurationProvider(ABC):
    """Abstract base class for configuration providers"""

    @abstractmethod
    async def get_config(self, key: str) -> Optional[Dict[str, Any]]:
        """Get configuration by key"""
        pass

    @abstractmethod
    async def set_config(self, key: str, value: Dict[str, Any]) -> bool:
        """Set configuration value"""
        pass

    @abstractmethod
    async def watch_config(self, key_pattern: str, callback) -> None:
        """Watch for configuration changes"""
        pass


# Specific job types for report analyst
class AnalysisJobDefinition(JobDefinition):
    """Specialized job definition for document analysis"""

    def __init__(
        self,
        document_id: str,
        question_set_id: str,
        selected_questions: List[str],
        model_name: str = "gpt-4o-mini",
        use_search_backend: bool = False,
        configuration: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):

        super().__init__(
            job_id=kwargs.get("job_id", str(uuid.uuid4())),
            job_type="document_analysis",
            parameters={
                "document_id": document_id,
                "question_set_id": question_set_id,
                "selected_questions": selected_questions,
                "model_name": model_name,
                "use_search_backend": use_search_backend,
                "configuration": configuration or {},
            },
            **kwargs,
        )

    @property
    def document_id(self) -> str:
        return self.parameters["document_id"]

    @property
    def question_set_id(self) -> str:
        return self.parameters["question_set_id"]

    @property
    def selected_questions(self) -> List[str]:
        return self.parameters["selected_questions"]

    @property
    def model_name(self) -> str:
        return self.parameters.get("model_name", "gpt-4o-mini")

    @property
    def use_search_backend(self) -> bool:
        return self.parameters.get("use_search_backend", False)
