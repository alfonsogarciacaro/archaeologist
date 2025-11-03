"""
Redis-based job client for scanner service.

This module provides a client interface for consuming jobs from Redis queues
and processing them in the scanner service.
"""

import json
import logging
import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timezone

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from .config import get_settings

logger = logging.getLogger(__name__)


class ScannerJobClient:
    """Redis-based job client for consuming and processing jobs."""

    def __init__(self):
        self.settings = get_settings()
        self.redis_pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False
        self._worker_id: Optional[str] = None
        self._running = False

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

            # Generate worker ID
            import uuid
            self._worker_id = f"scanner-worker-{uuid.uuid4().hex[:8]}"

            logger.info(f"Scanner job client {self._worker_id} connected to Redis")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise RuntimeError(f"Redis connection failed: {e}")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        self._running = False
        if self.redis_pool:
            await self.redis_pool.disconnect()
            self._connected = False
            logger.info(f"Scanner job client {self._worker_id} disconnected from Redis")

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

    async def get_next_job(self) -> Optional[Dict[str, Any]]:
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
            job_data["status"] = "running"
            job_data["worker_id"] = self._worker_id
            job_data["started_at"] = datetime.now(timezone.utc).isoformat()

            # Store running job in separate key
            running_key = f"{queue_name}:running:{job_data['id']}"
            await self.redis_client.setex(
                running_key,
                job_data.get("timeout_seconds", self.settings.JOB_TIMEOUT),
                json.dumps(job_data)
            )

            logger.info(f"Job {job_data['id']} dequeued by worker {self._worker_id}")
            return job_data

        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None

    async def update_job_progress(self, job_id: str, progress_current: int,
                                progress_total: int, progress_message: str = None) -> bool:
        """Update job progress."""
        if not await self.is_connected():
            await self.connect()

        try:
            queue_name = self.settings.JOB_QUEUE_NAME
            running_key = f"{queue_name}:running:{job_id}"

            # Get current job data
            job_data = await self.redis_client.get(running_key)
            if not job_data:
                logger.warning(f"Running job {job_id} not found")
                return False

            job = json.loads(job_data)
            job["progress_current"] = progress_current
            job["progress_total"] = progress_total
            if progress_message:
                job["progress_message"] = progress_message
            job["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Update running job
            await self.redis_client.setex(
                running_key,
                job.get("timeout_seconds", self.settings.JOB_TIMEOUT),
                json.dumps(job)
            )

            return True

        except Exception as e:
            logger.error(f"Failed to update job progress for {job_id}: {e}")
            return False

    async def complete_job(self, job_id: str, result_data: Dict[str, Any]) -> bool:
        """Mark a job as completed with results."""
        return await self._finish_job(job_id, "completed", result_data=result_data)

    async def fail_job(self, job_id: str, error_message: str) -> bool:
        """Mark a job as failed with error message."""
        return await self._finish_job(job_id, "failed", error_message=error_message)

    async def _finish_job(self, job_id: str, status: str,
                         result_data: Optional[Dict[str, Any]] = None,
                         error_message: Optional[str] = None) -> bool:
        """Mark a job as finished (completed or failed)."""
        if not await self.is_connected():
            await self.connect()

        try:
            queue_name = self.settings.JOB_QUEUE_NAME
            running_key = f"{queue_name}:running:{job_id}"

            # Get current job data
            job_data = await self.redis_client.get(running_key)
            if not job_data:
                logger.warning(f"Running job {job_id} not found")
                return False

            job = json.loads(job_data)
            job["status"] = status
            job["completed_at"] = datetime.now(timezone.utc).isoformat()

            if result_data:
                job["result_data"] = result_data
            if error_message:
                job["error_message"] = error_message

            # Move to appropriate final storage
            if status == "completed":
                completed_key = f"{queue_name}:completed:{job_id}"
                await self.redis_client.setex(
                    completed_key,
                    self.settings.JOB_RESULT_TTL,
                    json.dumps(job)
                )
                logger.info(f"Job {job_id} completed successfully")
            else:  # failed
                failed_key = f"{queue_name}:failed:{job_id}"
                await self.redis_client.setex(
                    failed_key,
                    self.settings.JOB_RESULT_TTL,
                    json.dumps(job)
                )
                logger.error(f"Job {job_id} failed: {error_message}")

            # Remove from running
            await self.redis_client.delete(running_key)

            return True

        except Exception as e:
            logger.error(f"Failed to finish job {job_id}: {e}")
            return False

    async def start_worker(self, job_handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """Start the worker to continuously process jobs."""
        if self._running:
            logger.warning("Worker is already running")
            return

        self._running = True
        logger.info(f"Starting scanner worker {self._worker_id}")

        while self._running:
            try:
                # Get next job
                job = await self.get_next_job()
                if not job:
                    # No jobs available, wait before checking again
                    await asyncio.sleep(self.settings.JOB_POLL_INTERVAL)
                    continue

                job_id = job.get("id", "unknown")
                logger.info(f"Processing job {job_id}: {job.get('job_type', 'unknown')}")

                try:
                    # Update progress to show processing started
                    await self.update_job_progress(job_id, 0, 100, "Starting processing...")

                    # Process the job
                    result = await job_handler(job)

                    # Mark job as completed
                    await self.complete_job(job_id, result)
                    logger.info(f"Job {job_id} completed successfully")

                except Exception as e:
                    # Mark job as failed
                    error_msg = f"Job processing failed: {str(e)}"
                    await self.fail_job(job_id, error_msg)
                    logger.error(f"Job {job_id} failed: {e}")

            except Exception as e:
                logger.error(f"Worker error: {e}")
                # Wait before retrying
                await asyncio.sleep(5)

        logger.info(f"Scanner worker {self._worker_id} stopped")

    async def stop_worker(self) -> None:
        """Stop the worker."""
        self._running = False
        logger.info(f"Stopping scanner worker {self._worker_id}")

    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running

    @property
    def worker_id(self) -> Optional[str]:
        """Get worker ID."""
        return self._worker_id


# Global job client instance
job_client = ScannerJobClient()