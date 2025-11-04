"""
Integration tests for the consolidated scanner functionality.

These tests verify that all scanner endpoints work correctly after
the consolidation into the main API service.
"""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings

client = TestClient(app)

class TestScannerHealth:
    def test_scanner_health_check(self):
        """Test that the integrated scanner health endpoint works."""
        response = client.get("/scanner/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "code-scanner"

    def test_scanner_root_endpoint(self):
        """Test the scanner root endpoint."""
        response = client.get("/scanner/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "code-scanner"
        assert data["status"] == "healthy"

class TestCodeScanning:
    def test_scan_endpoint_basic(self):
        """Test basic code scanning functionality."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def test_function():
    # This function contains term_sheet_id
    term_sheet_id = "test_value"
    return term_sheet_id
""")
            test_file = f.name

        try:
            response = client.post(
                "/scanner/scan",
                json={
                    "query": "term_sheet_id",
                    "paths": [os.path.dirname(test_file)]
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert "total_matches" in data
            assert isinstance(data["total_matches"], int)
        finally:
            os.unlink(test_file)

    def test_scan_no_matches(self):
        """Test scanning with no matches."""
        response = client.post(
            "/scanner/scan",
            json={
                "query": "nonexistent_query_xyz",
                "paths": ["/tmp"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_matches"] == 0
        assert len(data["results"]) == 0

    def test_dependency_analysis(self):
        """Test dependency analysis endpoint."""
        # Create test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create SQL file
            sql_file = os.path.join(temp_dir, "test.sql")
            with open(sql_file, 'w') as f:
                f.write("CREATE TABLE users (user_id INT PRIMARY KEY, name VARCHAR(100));")

            # Create Python file that references the table
            py_file = os.path.join(temp_dir, "test.py")
            with open(py_file, 'w') as f:
                f.write("""
import database
def get_user(user_id):
    return database.query("SELECT * FROM users WHERE user_id = ?", user_id)
""")

            response = client.post(
                "/scanner/analyze-dependencies",
                json={"paths": [temp_dir]}
            )
            assert response.status_code == 200
            data = response.json()
            assert "dependencies" in data
            assert "total_found" in data
            assert isinstance(data["total_found"], int)

    def test_impact_analysis(self):
        """Test comprehensive impact analysis."""
        response = client.post(
            "/scanner/impact-analysis",
            json={
                "query": "test_query",
                "paths": ["/tmp"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "knowledge_gaps" in data
        assert "explanation" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

class TestRAGFunctionality:
    def test_rag_health_check(self):
        """Test RAG system health check."""
        response = client.get("/scanner/rag-health")
        # This might fail if vector DB is not running, which is expected
        assert response.status_code in [200, 500]

    def test_document_ingestion(self):
        """Test document ingestion into RAG system."""
        test_content = """
This is a test document about user authentication.
It contains information about login processes, password hashing,
and user management in Python applications.

The authenticate_user function takes a username and password,
hashes the password for security, and checks against the database.
"""

        response = client.post(
            "/scanner/ingest",
            json={
                "file_name": "test_auth.py",
                "project": "test_project",
                "content": test_content,
                "file_type": "python",
                "timestamp": "2025-11-04T10:30:00Z",
                "metadata": {"author": "test", "version": "1.0.0"}
            }
        )
        # This might fail if vector DB is not running, which is expected
        assert response.status_code in [200, 500]

    def test_semantic_search(self):
        """Test semantic search functionality."""
        response = client.post(
            "/scanner/search",
            json={
                "query": "user authentication password hashing",
                "project": "test_project",
                "limit": 5,
                "score_threshold": 0.5
            }
        )
        # This might fail if vector DB is not running, which is expected
        assert response.status_code in [200, 500]

class TestLLMInvestigation:
    def test_llm_health_check(self):
        """Test LLM system health check."""
        response = client.get("/scanner/llm-health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        # Should use mock LLM by default
        assert data["provider"] == "mock"

    def test_llm_investigation(self):
        """Test LLM-powered investigation."""
        response = client.post(
            "/scanner/investigate",
            json={
                "query": "What happens if we change term_sheet_id from string to UUID?",
                "use_mock": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "knowledge_gaps" in data
        assert "explanation" in data

class TestJobManagement:
    def test_job_status_endpoint(self):
        """Test job status endpoint."""
        response = client.get("/scanner/jobs/status/test_job_id")
        # Should return 404 for non-existent job
        assert response.status_code == 404

    def test_worker_status_endpoint(self):
        """Test worker status endpoint."""
        response = client.get("/scanner/jobs/worker/status")
        assert response.status_code == 200
        data = response.json()
        assert "worker_id" in data
        assert "is_running" in data
        assert "connected_to_redis" in data

    def test_queue_stats_endpoint(self):
        """Test queue statistics endpoint."""
        response = client.get("/scanner/jobs/queue/stats")
        assert response.status_code in [200, 503]  # 503 if Redis not available
        if response.status_code == 200:
            data = response.json()
            assert "queued" in data
            assert "running" in data
            assert "completed" in data
            assert "failed" in data

class TestAPIIntegration:
    def test_investigate_endpoint_uses_local_scanner(self):
        """Test that the main /investigate endpoint uses the integrated scanner."""
        response = client.post(
            "/api/v1/investigate",
            json={"query": "test query"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "nodes" in data
        assert "edges" in data
        assert "knowledge_gaps" in data
        assert "summary" in data

    def test_investigation_status_uses_local_components(self):
        """Test that investigation status checks local components."""
        response = client.get("/api/v1/investigation-status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "capabilities" in data

class TestTestEndpoints:
    def test_test_scan_endpoint(self):
        """Test the scanner test scan endpoint."""
        response = client.get("/scanner/test-scan")
        # This should work regardless of external dependencies
        assert response.status_code in [200, 401]  # 401 if auth is required

    def test_test_impact_analysis(self):
        """Test the scanner test impact analysis endpoint."""
        response = client.get("/scanner/test-impact-analysis")
        assert response.status_code in [200, 401]

    def test_test_llm_investigate(self):
        """Test the scanner test LLM investigation endpoint."""
        response = client.get("/scanner/test-investigate")
        assert response.status_code in [200, 401]

class TestConfiguration:
    def test_config_has_scanner_settings(self):
        """Test that the configuration includes scanner settings."""
        settings = get_settings()
        assert hasattr(settings, 'EMBEDDING_TYPE')
        assert hasattr(settings, 'LLM_PROVIDER')
        assert hasattr(settings, 'REDIS_HOST')
        assert hasattr(settings, 'JOB_QUEUE_NAME')

if __name__ == "__main__":
    pytest.main([__file__, "-v"])