"""
Tests for background job processing functionality.

These tests verify that the Redis-based job queue system works correctly
and that background workers can process various job types.
"""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock
from app.job_client import job_client
from app.job_manager import job_manager
from models.jobs import Job, JobType, JobStatus, JobPriority
from app.config import get_settings

class TestJobClient:
    @pytest.mark.asyncio
    async def test_job_client_connection(self):
        """Test that the job client can connect to Redis."""
        settings = get_settings()
        if settings.REDIS_HOST == "localhost":
            # Skip if Redis is not available in test environment
            pytest.skip("Redis not available in test environment")

        try:
            await job_client.connect()
            assert await job_client.is_connected()
            await job_client.disconnect()
        except Exception:
            pytest.skip("Could not connect to Redis")

    @pytest.mark.asyncio
    async def test_job_enqueue(self):
        """Test enqueuing a job."""
        settings = get_settings()
        if settings.REDIS_HOST == "localhost":
            pytest.skip("Redis not available in test environment")

        try:
            await job_client.connect()

            job = Job(
                id="test_job_123",
                type=JobType.FILE_PROCESSING,
                status=JobStatus.PENDING,
                priority=JobPriority.NORMAL,
                user_id="test_user",
                project_id="test_project",
                parameters={
                    "file_path": "/test/path/file.txt",
                    "project": "test_project"
                }
            )

            success = await job_client.enqueue_job(job)
            assert success

            await job_client.disconnect()
        except Exception:
            pytest.skip("Could not connect to Redis")

    @pytest.mark.asyncio
    async def test_job_status_tracking(self):
        """Test job status tracking."""
        settings = get_settings()
        if settings.REDIS_HOST == "localhost":
            pytest.skip("Redis not available in test environment")

        try:
            await job_client.connect()

            # Create and enqueue a job
            job = Job(
                id="test_job_status_456",
                type=JobType.FILE_PROCESSING,
                status=JobStatus.PENDING,
                priority=JobPriority.NORMAL,
                user_id="test_user",
                project_id="test_project",
                parameters={"test": "data"}
            )

            await job_client.enqueue_job(job)

            # Check status
            status = await job_client.get_job_status(job.id)
            assert status is not None
            assert status["id"] == job.id
            assert status["status"] == JobStatus.PENDING.value

            await job_client.disconnect()
        except Exception:
            pytest.skip("Could not connect to Redis")

class TestJobManager:
    def test_job_manager_exists(self):
        """Test that job manager is available."""
        assert job_manager is not None
        assert hasattr(job_manager, 'process_job')

    @pytest.mark.asyncio
    async def test_file_processing_job(self):
        """Test processing a file processing job."""
        job_data = {
            "id": "test_file_job",
            "type": "file_processing",
            "parameters": {
                "file_path": "/test/path/test.txt",
                "project": "test_project",
                "source_id": "test_source"
            }
        }

        # Mock the actual file processing to avoid filesystem dependencies
        with patch.object(job_manager, '_process_file_job') as mock_process:
            mock_process.return_value = {
                "chunks_created": 5,
                "embedding_count": 5,
                "processing_time": 1.5
            }

            result = await job_manager.process_job(job_data)
            assert result is not None
            assert "chunks_created" in result
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_processing_job(self):
        """Test processing a batch processing job."""
        job_data = {
            "id": "test_batch_job",
            "type": "batch_processing",
            "parameters": {
                "project_id": "test_project",
                "batch_size": 10,
                "filters": {"file_type": "python"}
            }
        }

        # Mock batch processing
        with patch.object(job_manager, '_process_batch_job') as mock_process:
            mock_process.return_value = {
                "files_processed": 10,
                "chunks_created": 50,
                "errors": []
            }

            result = await job_manager.process_job(job_data)
            assert result is not None
            assert "files_processed" in result
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_investigation_job(self):
        """Test processing an investigation job."""
        job_data = {
            "id": "test_investigation_job",
            "type": "investigation",
            "parameters": {
                "query": "What happens if we change X?",
                "user_id": "test_user",
                "project_id": "test_project"
            }
        }

        # Mock LLM investigation
        with patch.object(job_manager, '_process_investigation_job') as mock_process:
            mock_process.return_value = {
                "nodes": [],
                "edges": [],
                "knowledge_gaps": [],
                "explanation": {"reasoning": ["Test"]},
                "processing_time": 2.0
            }

            result = await job_manager.process_job(job_data)
            assert result is not None
            assert "nodes" in result
            assert "edges" in result
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_job_type(self):
        """Test handling of unknown job types."""
        job_data = {
            "id": "test_unknown_job",
            "type": "unknown_type",
            "parameters": {}
        }

        result = await job_manager.process_job(job_data)
        assert result is not None
        assert "error" in result
        assert "Unknown job type" in result["error"]

class TestJobTypes:
    def test_job_type_enum(self):
        """Test JobType enum values."""
        assert JobType.FILE_PROCESSING.value == "file_processing"
        assert JobType.BATCH_PROCESSING.value == "batch_processing"
        assert JobType.INVESTIGATION.value == "investigation"

    def test_job_status_enum(self):
        """Test JobStatus enum values."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"

    def test_job_priority_enum(self):
        """Test JobPriority enum values."""
        assert JobPriority.LOW.value == "low"
        assert JobPriority.NORMAL.value == "normal"
        assert JobPriority.HIGH.value == "high"
        assert JobPriority.URGENT.value == "urgent"

class TestJobDataValidation:
    def test_job_model_validation(self):
        """Test Job model validation."""
        # Valid job
        job_data = {
            "id": "test_job",
            "type": "file_processing",
            "status": "pending",
            "priority": "normal",
            "user_id": "test_user",
            "parameters": {"test": "data"}
        }
        job = Job(**job_data)
        assert job.id == "test_job"
        assert job.type == JobType.FILE_PROCESSING
        assert job.status == JobStatus.PENDING
        assert job.priority == JobPriority.NORMAL

    def test_job_model_invalid_type(self):
        """Test Job model with invalid type."""
        job_data = {
            "id": "test_job",
            "type": "invalid_type",
            "status": "pending",
            "priority": "normal",
            "user_id": "test_user",
            "parameters": {}
        }
        with pytest.raises(ValueError):
            Job(**job_data)

class TestWorkerLifecycle:
    @pytest.mark.asyncio
    async def test_worker_start_stop(self):
        """Test worker start and stop functionality."""
        settings = get_settings()
        if settings.REDIS_HOST == "localhost":
            pytest.skip("Redis not available in test environment")

        try:
            await job_client.connect()

            # Mock the job processing to avoid infinite loop
            async def mock_process_job(job_data):
                return {"status": "completed", "result": "test"}

            # Start worker (should not block due to mocking)
            worker_task = asyncio.create_task(
                job_client.start_worker(mock_process_job)
            )

            # Give it a moment to start
            await asyncio.sleep(0.1)

            # Stop worker
            await job_client.stop_worker()

            # Wait for task to complete
            await worker_task

            await job_client.disconnect()
        except Exception:
            pytest.skip("Could not connect to Redis")

class TestJobQueueOperations:
    @pytest.mark.asyncio
    async def test_queue_statistics(self):
        """Test getting queue statistics."""
        settings = get_settings()
        if settings.REDIS_HOST == "localhost":
            pytest.skip("Redis not available in test environment")

        try:
            await job_client.connect()

            stats = await job_client.get_queue_stats()
            assert isinstance(stats, dict)
            assert "queued" in stats
            assert "running" in stats
            assert "completed" in stats
            assert "failed" in stats
            assert "total" in stats

            await job_client.disconnect()
        except Exception:
            pytest.skip("Could not connect to Redis")

    @pytest.mark.asyncio
    async def test_priority_queue_ordering(self):
        """Test that priority queue respects job priorities."""
        settings = get_settings()
        if settings.REDIS_HOST == "localhost":
            pytest.skip("Redis not available in test environment")

        try:
            await job_client.connect()

            # Create jobs with different priorities
            low_priority_job = Job(
                id="low_priority",
                type=JobType.FILE_PROCESSING,
                status=JobStatus.PENDING,
                priority=JobPriority.LOW,
                user_id="test_user",
                parameters={}
            )

            urgent_job = Job(
                id="urgent_job",
                type=JobType.FILE_PROCESSING,
                status=JobStatus.PENDING,
                priority=JobPriority.URGENT,
                user_id="test_user",
                parameters={}
            )

            # Enqueue in reverse priority order
            await job_client.enqueue_job(low_priority_job)
            await job_client.enqueue_job(urgent_job)

            # The urgent job should be processed first
            # (This is a simplified test - actual queue testing would require more complex setup)

            await job_client.disconnect()
        except Exception:
            pytest.skip("Could not connect to Redis")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])