"""
Job management routes.

This module provides endpoints for creating, monitoring, and managing
background processing jobs.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from datetime import datetime

from dependencies.auth import get_current_user_id
from dependencies.database import get_database
from db import DatabaseAbc
from models.jobs import (
    Job, JobType, JobStatus, JobPriority,
    JobCreate, JobUpdate, JobResponse, JobListResponse, JobStats
)
from app.job_client import job_client

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Create a new job."""
    # Set the user ID from authentication
    job_data.user_id = current_user_id

    # Create job in database
    job = await db.create_job(job_data)

    # Enqueue job for processing
    try:
        success = await job_client.enqueue_job(job)
        if not success:
            # Mark job as failed if queueing fails
            await db.update_job(job.id, JobUpdate(status=JobStatus.FAILED,
                                               error_message="Failed to enqueue job"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to queue job for processing"
            )
    except Exception as e:
        # Mark job as failed and return error
        await db.update_job(job.id, JobUpdate(status=JobStatus.FAILED,
                                           error_message=f"Queue error: {str(e)}"))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job queue error: {str(e)}"
        )

    return JobResponse(**job.model_dump())


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Get job details by ID."""
    # Get job from database
    job = await db.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Check user access (only user who created the job can view it)
    if job.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return JobResponse(**job.model_dump())


@router.get("", response_model=JobListResponse)
async def get_user_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    job_type: Optional[JobType] = Query(None, description="Filter by job type"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Get current user's jobs with optional filters."""
    offset = (page - 1) * per_page

    # Get jobs from database
    jobs = await db.get_user_jobs(
        user_id=current_user_id,
        status=status,
        job_type=job_type,
        project_id=project_id,
        limit=per_page,
        offset=offset
    )

    # Get total count (approximate - we could add a count method to DB)
    total_jobs = len(jobs) if per_page == 1 and page == 1 else len(jobs) + (per_page - 1)

    job_responses = [JobResponse(**job.model_dump()) for job in jobs]

    return JobListResponse(
        jobs=job_responses,
        total=total_jobs,
        page=page,
        per_page=per_page,
        has_more=len(jobs) == per_page
    )


@router.get("/project/{project_id}", response_model=JobListResponse)
async def get_project_jobs(
    project_id: int,
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Get jobs for a specific project."""
    # Check user has access to project
    user_role = await db.get_user_project_role(project_id, current_user_id)
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    offset = (page - 1) * per_page

    # Get project jobs
    jobs = await db.get_project_jobs(
        project_id=project_id,
        status=status,
        limit=per_page
    )

    # Filter jobs to only include those created by current user (or admin/owner)
    if user_role not in ["owner", "admin"]:
        jobs = [job for job in jobs if job.user_id == current_user_id]

    total_jobs = len(jobs) if per_page == 1 and page == 1 else len(jobs) + (per_page - 1)

    job_responses = [JobResponse(**job.model_dump()) for job in jobs]

    return JobListResponse(
        jobs=job_responses,
        total=total_jobs,
        page=page,
        per_page=per_page,
        has_more=len(jobs) == per_page
    )


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Update job (primarily for cancellation by user)."""
    # Get job from database
    job = await db.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Check user access
    if job.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Only allow status updates to cancelled (users can't modify other aspects)
    if job_update.status and job_update.status != JobStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users can only cancel jobs"
        )

    # Update job in database
    success = await db.update_job(job_id, job_update)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job"
        )

    # Update in Redis queue if cancelling
    if job_update.status == JobStatus.CANCELLED:
        try:
            await job_client.cancel_job(job_id)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Warning: Failed to cancel job in queue: {e}")

    # Get updated job
    updated_job = await db.get_job_by_id(job_id)
    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated job"
        )

    return JobResponse(**updated_job.model_dump())


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Delete a job (only completed or failed jobs)."""
    # Get job from database
    job = await db.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Check user access
    if job.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Only allow deletion of completed, failed, or cancelled jobs
    if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete completed, failed, or cancelled jobs"
        )

    # Delete job from database
    success = await db.delete_job(job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
        )

    return {"message": "Job deleted successfully"}


@router.get("/stats/user", response_model=JobStats)
async def get_user_job_stats(
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Get job statistics for current user."""
    stats = await db.get_job_stats(user_id=current_user_id)
    return JobStats(**stats)


@router.get("/stats/global", response_model=JobStats)
async def get_global_job_stats(
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Get global job statistics (admin only)."""
    # TODO: Add admin check here
    # For now, allow all authenticated users

    stats = await db.get_job_stats()
    return JobStats(**stats)


@router.get("/queue/stats")
async def get_queue_stats(
    current_user_id: int = Depends(get_current_user_id)
):
    """Get Redis queue statistics."""
    try:
        stats = await job_client.get_queue_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue stats: {str(e)}"
        )