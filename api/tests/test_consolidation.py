"""
Consolidation tests to verify that the service consolidation works correctly.

These tests verify that all the basic functionality after consolidating the scanner
service into the main API service is working without requiring authentication.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestConsolidationHealth:
    """Test that the consolidated service health checks work."""

    def test_api_health_check(self):
        """Test main API health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "archaeologist-api"

    def test_scanner_health_check(self):
        """Test integrated scanner health check."""
        response = client.get("/scanner/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "code-scanner"

    def test_scanner_root_endpoint(self):
        """Test scanner root endpoint."""
        response = client.get("/scanner/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "code-scanner"

    def test_investigation_status_endpoint(self):
        """Test investigation status endpoint."""
        response = client.get("/api/v1/investigation-status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "capabilities" in data


class TestConsolidationEndpoints:
    """Test that consolidated endpoints exist and respond appropriately."""

    def test_scanner_endpoints_exist(self):
        """Test that key scanner endpoints exist."""
        endpoints = [
            "/scanner/scan",
            "/scanner/analyze-dependencies",
            "/scanner/impact-analysis",
            "/scanner/rag-health",
            "/scanner/llm-health",
            "/scanner/jobs/status/test_job",
            "/scanner/jobs/worker/status"
        ]

        for endpoint in endpoints:
            response = client.post(endpoint, json={"test": "data"}) if endpoint.startswith("/scanner/") else client.get(endpoint)
            # Should return either success, auth error, or method not allowed - but not 404
            assert response.status_code != 404, f"Endpoint {endpoint} should exist (not return 404)"

    def test_job_status_endpoint_for_nonexistent_job(self):
        """Test job status endpoint with non-existent job."""
        response = client.get("/scanner/jobs/status/nonexistent_job_12345")
        # Should return 404 for non-existent job
        assert response.status_code == 404

    def test_scanner_config_integration(self):
        """Test that scanner configuration is properly integrated."""
        from app.config import get_settings
        from app.scanner.config import get_settings as get_scanner_settings

        api_settings = get_settings()
        scanner_settings = get_scanner_settings()

        # Both should have the same basic settings
        assert hasattr(api_settings, 'REDIS_HOST')
        assert hasattr(scanner_settings, 'REDIS_HOST')
        assert hasattr(api_settings, 'LLM_PROVIDER')
        assert hasattr(scanner_settings, 'LLM_PROVIDER')


class TestConsolidationModels:
    """Test that the consolidated models work correctly."""

    def test_job_models_exist(self):
        """Test that job models are available."""
        from models.jobs import Job, JobType, JobStatus, JobPriority

        # Test enum values
        assert JobType.FILE_PROCESSING.value == "file_processing"
        assert JobType.BATCH_PROCESSING.value == "batch_processing"
        assert JobType.INVESTIGATION.value == "investigation"

        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"

        assert JobPriority.LOW.value == "low"
        assert JobPriority.NORMAL.value == "normal"
        assert JobPriority.HIGH.value == "high"
        assert JobPriority.URGENT.value == "urgent"

    def test_job_model_validation(self):
        """Test job model validation."""
        from models.jobs import Job, JobType, JobStatus, JobPriority

        # Valid job should work
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

    def test_job_model_invalid_type(self):
        """Test job model with invalid type."""
        from models.jobs import Job

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


class TestConsolidationComponents:
    """Test that consolidated components are available."""

    def test_job_manager_available(self):
        """Test that job manager is available."""
        from app.job_manager import job_manager
        assert job_manager is not None
        assert hasattr(job_manager, 'process_job')

    def test_scanner_modules_available(self):
        """Test that scanner modules are available."""
        # Test that key scanner modules can be imported
        from app.scanner.rag.rag_service import get_rag_service
        from app.scanner.llm.llm_interface import get_llm_provider
        from app.scanner.tools.vector_db_factory import get_vector_db

        # They should be callable functions/classes
        assert callable(get_rag_service)
        assert callable(get_llm_provider)
        assert callable(get_vector_db)

    def test_data_lake_modules_available(self):
        """Test that data lake modules are available."""
        from app.disk_data_lake import DiskDataLake
        from app.data_lake_interface import DataLakeEntry, DataType

        assert DiskDataLake is not None
        assert DataLakeEntry is not None
        assert DataType is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])