"""
Redis-based job client for queueing and managing background jobs.

This module provides a client interface for interacting with Redis queues
to manage asynchronous job processing between API and scanner services.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from app.config import get_settings
from models.jobs import Job, JobType, JobStatus, JobPriority, JobCreate, JobUpdate

logger = logging.getLogger(__name__)


class JobQueueClient:
    """Redis-based job queue client for asynchronous job processing."""

    def __init__(self):
        self.settings = get_settings()
        self.redis_pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self) -> None:
        """Establish Redis connection."""
        if self._connected:
            return

        try:
            # Create connection pool
            self.redis_pool = ConnectionPool.from_url(
                self.settings.REDIS_URL,
                encoding='utf-8',
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # Create Redis client
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)

            # Test connection
            await self.redis_client.ping()
            self._connected = True
            logger.info("Successfully connected to Redis for job queue")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise RuntimeError(f"Redis connection failed: {e}")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis_pool:
            await self.redis_pool.disconnect()
            self._connected = False
            logger.info("Disconnected from Redis")

    async def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self._connected or not self.redis_client:
            return False

        try:
            await self.redis_client.ping()
            return True
        except Exception:
            self._connected = False
            return False

    async def enqueue_job(self, job: Job) -> bool:
        """Add a job to the queue."""
        if not await self.is_connected():
            await self.connect()

        try:
            # Prepare job data for queue
            job_data = {
                "id": job.id,
                "job_type": job.job_type.value,
                "status": job.status.value,
                "priority": job.priority.value,
                "project_id": job.project_id,
                "user_id": job.user_id,
                "source_id": job.source_id,
                "investigation_id": job.investigation_id,
                "job_data": job.job_data,
                "timeout_seconds": job.timeout_seconds,
                "max_retries": job.max_retries,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "queued_at": datetime.now(timezone.utc).isoformat()
            }

            # Add to Redis queue
            queue_name = self.settings.JOB_QUEUE_NAME
            job_json = json.dumps(job_data)

            # Use priority queue with score based on priority and timestamp
            priority_score = self._get_priority_score(job.priority)
            await self.redis_client.zadd(queue_name, {job_json: priority_score})

            # Set job status to queued
            await self.update_job_status(job.id, JobStatus.QUEUED)

            logger.info(f"Job {job.id} enqueued successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to enqueue job {job.id}: {e}")
            return False

    async def dequeue_job(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Get the next job from the queue for processing."""
        if not await self.is_connected():
            await self.connect()

        try:
            queue_name = self.settings.JOB_QUEUE_NAME

            # Get highest priority job (lowest score)
            result = await self.redis_client.zpopmin(queue_name, count=1)

            if not result:
                return None

            job_json, score = result[0]
            job_data = json.loads(job_json)

            # Mark job as running and assign worker
            job_data["status"] = JobStatus.RUNNING.value
            job_data["worker_id"] = worker_id
            job_data["started_at"] = datetime.now(timezone.utc).isoformat()

            # Store running job in separate key
            running_key = f"{queue_name}:running:{job_data['id']}"
            await self.redis_client.setex(
                running_key,
                job_data.get("timeout_seconds", self.settings.JOB_TIMEOUT),
                json.dumps(job_data)
            )

            logger.info(f"Job {job_data['id']} dequeued by worker {worker_id}")
            return job_data

        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None

    async def update_job_status(self, job_id: str, status: JobStatus,
                              progress: Optional[Dict[str, Any]] = None) -> bool:
        """Update job status and optionally progress."""
        if not await self.is_connected():
            await self.connect()

        try:
            queue_name = self.settings.JOB_QUEUE_NAME
            running_key = f"{queue_name}:running:{job_id}"

            # Get current job data if it's running
            job_data = None
            if status not in [JobStatus.PENDING, JobStatus.QUEUED]:
                existing_data = await self.redis_client.get(running_key)
                if existing_data:
                    job_data = json.loads(existing_data)

            if not job_data:
                # Create minimal job data for status update
                job_data = {
                    "id": job_id,
                    "status": status.value,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                job_data["status"] = status.value
                job_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Update progress if provided
            if progress:
                job_data.update(progress)

            # Handle different status transitions
            if status == JobStatus.COMPLETED:
                # Move to completed jobs
                completed_key = f"{queue_name}:completed:{job_id}"
                await self.redis_client.setex(
                    completed_key,
                    self.settings.JOB_RESULT_TTL,
                    json.dumps(job_data)
                )
                # Remove from running
                await self.redis_client.delete(running_key)

            elif status == JobStatus.FAILED:
                # Check if should retry
                retry_count = job_data.get("retry_count", 0)
                max_retries = job_data.get("max_retries", 3)

                if retry_count < max_retries:
                    # Re-queue for retry
                    job_data["retry_count"] = retry_count + 1
                    job_data["status"] = JobStatus.PENDING.value
                    priority_score = self._get_priority_score(
                        JobPriority(job_data.get("priority", "normal"))
                    )
                    await self.redis_client.zadd(
                        queue_name,
                        {json.dumps(job_data): priority_score}
                    )
                    await self.redis_client.delete(running_key)
                    logger.info(f"Job {job_id} re-queued for retry {retry_count + 1}/{max_retries}")
                else:
                    # Move to failed jobs
                    failed_key = f"{queue_name}:failed:{job_id}"
                    await self.redis_client.setex(
                        failed_key,
                        self.settings.JOB_RESULT_TTL,
                        json.dumps(job_data)
                    )
                    await self.redis_client.delete(running_key)
                    logger.error(f"Job {job_id} failed permanently after {max_retries} retries")

            elif status == JobStatus.CANCELLED:
                # Remove from running
                await self.redis_client.delete(running_key)

            elif status == JobStatus.RUNNING:
                # Update running job
                await self.redis_client.setex(
                    running_key,
                    job_data.get("timeout_seconds", self.settings.JOB_TIMEOUT),
                    json.dumps(job_data)
                )

            logger.info(f"Job {job_id} status updated to {status.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update job status for {job_id}: {e}")
            return False

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status and data."""
        if not await self.is_connected():
            await self.connect()

        try:
            queue_name = self.settings.JOB_QUEUE_NAME

            # Check in running jobs
            running_key = f"{queue_name}:running:{job_id}"
            running_data = await self.redis_client.get(running_key)
            if running_data:
                return json.loads(running_data)

            # Check in completed jobs
            completed_key = f"{queue_name}:completed:{job_id}"
            completed_data = await self.redis_client.get(completed_key)
            if completed_data:
                return json.loads(completed_data)

            # Check in failed jobs
            failed_key = f"{queue_name}:failed:{job_id}"
            failed_data = await self.redis_client.get(failed_key)
            if failed_data:
                return json.loads(failed_data)

            # Check in queue (pending/queued)
            queued_jobs = await self.redis_client.zrange(queue_name, 0, -1)
            for job_json in queued_jobs:
                job_data = json.loads(job_json)
                if job_data.get("id") == job_id:
                    return job_data

            return None

        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        return await self.update_job_status(job_id, JobStatus.CANCELLED)

    async def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        if not await self.is_connected():
            await self.connect()

        try:
            queue_name = self.settings.JOB_QUEUE_NAME

            # Get queued jobs count
            queued_count = await self.redis_client.zcard(queue_name)

            # Get running jobs count
            running_keys = await self.redis_client.keys(f"{queue_name}:running:*")
            running_count = len(running_keys)

            # Get completed jobs count (approximate)
            completed_keys = await self.redis_client.keys(f"{queue_name}:completed:*")
            completed_count = len(completed_keys)

            # Get failed jobs count (approximate)
            failed_keys = await self.redis_client.keys(f"{queue_name}:failed:*")
            failed_count = len(failed_keys)

            return {
                "queued": queued_count,
                "running": running_count,
                "completed": completed_count,
                "failed": failed_count,
                "total": queued_count + running_count + completed_count + failed_count
            }

        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {"queued": 0, "running": 0, "completed": 0, "failed": 0, "total": 0}

    async def cleanup_expired_jobs(self) -> int:
        """Clean up expired running jobs (timeout cleanup)."""
        if not await self.is_connected():
            await self.connect()

        try:
            queue_name = self.settings.JOB_QUEUE_NAME
            running_keys = await self.redis_client.keys(f"{queue_name}:running:*")
            cleaned_count = 0

            for key in running_keys:
                # Check if job data exists (key hasn't expired)
                job_data = await self.redis_client.get(key)
                if not job_data:
                    continue

                job = json.loads(job_data)
                job_id = job.get("id")

                if job_id:
                    # Mark as failed due to timeout
                    await self.update_job_status(job_id, JobStatus.FAILED)
                    cleaned_count += 1
                    logger.warning(f"Job {job_id} timed out and marked as failed")

            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired jobs: {e}")
            return 0

    def _get_priority_score(self, priority: JobPriority) -> float:
        """Convert priority to numeric score for Redis sorted set."""
        # Lower scores = higher priority
        priority_scores = {
            JobPriority.URGENT: 1.0,
            JobPriority.HIGH: 2.0,
            JobPriority.NORMAL: 3.0,
            JobPriority.LOW: 4.0
        }
        base_score = priority_scores.get(priority, 3.0)

        # Add timestamp to maintain FIFO order within same priority
        timestamp = datetime.now(timezone.utc).timestamp()
        return base_score + (timestamp / 1000000)  # Microsecond precision


# Global job queue client instance
job_client = JobQueueClient()