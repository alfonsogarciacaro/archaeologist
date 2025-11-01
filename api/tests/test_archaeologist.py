import pytest
import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAPIHealth:
    def test_api_health_check(self):
        """Can the API server receive a heartbeat?"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "archaeologist-api"

class TestInvestigateEndpoint:
    def test_investigate_endpoint_exists(self):
        """Does the /investigate endpoint exist and accept a POST request?"""
        response = client.post(
            "/investigate",
            json={"query": "test query"}
        )
        # Should return 200 with dummy data for now
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "knowledge_gaps" in data
        assert "summary" in data

    def test_simple_literal_search(self):
        """When querying for a known string (term_sheet_id), the system returns the correct file (schema.sql) with high confidence."""
        # This test will FAIL until we implement the actual scanner integration
        response = client.post(
            "/investigate",
            json={"query": "term_sheet_id"}
        )
        
        data = response.json()
        
        # Find schema.sql in the results
        schema_node = None
        for node in data["nodes"]:
            if "schema.sql" in node["path"]:
                schema_node = node
                break
        
        assert schema_node is not None, "schema.sql should be in the results"
        assert schema_node["confidence"] >= 0.8, "schema.sql match should have high confidence"
        assert schema_node["type"] == "db_table", "schema.sql should be identified as db_table"
        
        # TODO: This should fail when we replace dummy data with real scanner results
        # The real implementation should find actual matches in schema.sql

    def test_semantic_search(self):
        """When querying for a concept (client identifier), the system returns semantically related files."""
        # This test will FAIL until we implement RAG integration
        response = client.post(
            "/investigate",
            json={"query": "client identifier"}
        )
        
        data = response.json()
        
        # Should find user-service and reporting-service files
        service_files = [node for node in data["nodes"] if "user-service" in node["path"] or "reporting-service" in node["path"]]
        assert len(service_files) >= 1, "Should find service files related to client identifier"

    def test_knowledge_gap_reporting(self):
        """When a dependency points to a non-existent component, the system's final report includes a knowledge_gaps entry."""
        # This test will FAIL until we implement proper knowledge gap detection
        response = client.post(
            "/investigate",
            json={"query": "external payment processing"}
        )
        
        data = response.json()
        
        assert len(data["knowledge_gaps"]) > 0, "Should identify knowledge gaps for external components"
        gap = data["knowledge_gaps"][0]
        assert "required_action" in gap
        assert "missing_information" in gap

    def test_source_type_differentiation(self):
        """The system correctly identifies and tags sources as live_repo or snapshot."""
        # This test will FAIL until we implement proper source type detection
        response = client.post(
            "/investigate",
            json={"query": "term_sheet_id"}
        )
        
        data = response.json()
        
        # Should have both live repos and snapshots
        live_repos = [node for node in data["nodes"] if node["source_type"] == "live_repo"]
        snapshots = [node for node in data["nodes"] if node["source_type"] == "snapshot"]
        
        assert len(live_repos) >= 1, "Should identify at least one live repo"
        assert len(snapshots) >= 1, "Should identify at least one snapshot"

    def test_guardrail_validation(self):
        """If the LLM hallucinates a file not found by the tools, the guardrail adds it to the report with a 'verification needed' flag."""
        # This test will FAIL until we implement the guardrail system
        response = client.post(
            "/investigate",
            json={"query": "nonexistent_component_xyz"}
        )
        
        data = response.json()
        
        # Should not hallucinate files that don't exist
        for node in data["nodes"]:
            # Either the node should be real or marked for verification
            if not node["path"].startswith("/mock_enterprise"):
                assert "verification_needed" in node, "Non-mock files should be flagged for verification"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])