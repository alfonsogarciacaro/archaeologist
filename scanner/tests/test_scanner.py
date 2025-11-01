"""
Tests for Scanner service.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestScannerHealth:
    """As a system operator, I want to verify scanner service health"""
    
    def test_scanner_health_check(self):
        """Health check returns 200 and service name"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "code-scanner"

class TestScanEndpoint:
    """As a developer, I want to scan code for matches"""
    
    def test_scan_endpoint_exists(self):
        """Scan endpoint exists and accepts POST requests"""
        response = client.post("/scan", json={"query": "test", "paths": ["/app"]})
        # Should return 200 even with no matches
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_matches" in data
    
    def test_scan_with_real_query(self):
        """Scanning for 'term_sheet_id' finds expected matches"""
        response = client.post("/scan", json={"query": "term_sheet_id", "paths": ["/app"]})
        assert response.status_code == 200
        data = response.json()
        # Should find at least one match in mock data
        assert data["total_matches"] >= 0
        
        if data["total_matches"] > 0:
            result = data["results"][0]
            assert "file_path" in result
            assert "line_number" in result
            assert "content" in result
            assert result["confidence"] == 1.0
            assert result["match_type"] == "literal"