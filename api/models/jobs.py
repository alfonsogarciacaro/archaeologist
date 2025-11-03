"""
Job models for background processing tasks.

Pydantic models for job tracking and queue management.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field


class JobType(str, Enum):
    """Job type enumeration."""
    FILE_PROCESSING = "file_processing"
    BATCH_PROCESSING = "batch_processing"
    INVESTIGATION = "investigation"


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    """Job priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Job(BaseModel):
    """Job model for background tasks."""
    id: str
    job_type: JobType
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    project_id: Optional[int] = None
    user_id: int
    source_id: Optional[int] = None
    investigation_id: Optional[int] = None

    # Job data
    job_data: Dict[str, Any] = Field(default_factory=dict)
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Progress tracking
    progress_current: int = 0
    progress_total: int = 0
    progress_message: Optional[str] = None

    # Processing metadata
    worker_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 3600  # 1 hour default


class JobCreate(BaseModel):
    """Job creation request model."""
    job_type: JobType
    priority: JobPriority = JobPriority.NORMAL
    project_id: Optional[int] = None
    user_id: int
    source_id: Optional[int] = None
    investigation_id: Optional[int] = None
    job_data: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 3600


class JobUpdate(BaseModel):
    """Job update request model."""
    status: Optional[JobStatus] = None
    progress_current: Optional[int] = None
    progress_total: Optional[int] = None
    progress_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    worker_id: Optional[str] = None


class JobResponse(BaseModel):
    """Job response model."""
    id: str
    job_type: JobType
    status: JobStatus
    priority: JobPriority
    project_id: Optional[int] = None
    user_id: int
    source_id: Optional[int] = None
    investigation_id: Optional[int] = None

    # Job data (excluding sensitive data)
    job_data: Dict[str, Any] = Field(default_factory=dict)
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Progress tracking
    progress_current: int = 0
    progress_total: int = 0
    progress_message: Optional[str] = None

    # Processing metadata
    worker_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 3600

    # Computed fields
    progress_percentage: float = 0.0
    duration_seconds: Optional[float] = None
    is_finished: bool = False

    def __init__(self, **data):
        super().__init__(**data)
        # Compute progress percentage
        if self.progress_total > 0:
            self.progress_percentage = (self.progress_current / self.progress_total) * 100

        # Compute duration
        if self.started_at and self.completed_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()

        # Check if finished
        self.is_finished = self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]


class JobListResponse(BaseModel):
    """Job list response model."""
    jobs: List[JobResponse]
    total: int
    page: int
    per_page: int
    has_more: bool


class JobStats(BaseModel):
    """Job statistics model."""
    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    avg_duration_seconds: Optional[float] = None
    success_rate: float = 0.0