#!/usr/bin/env python3
"""
Quick test script to verify the service consolidation works correctly.

This script tests the main functionality after consolidating the scanner
service into the API service.
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any

class ConsolidationTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def test_health_endpoints(self) -> bool:
        """Test health endpoints"""
        print("🏥 Testing health endpoints...")

        try:
            # Main API health
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code != 200:
                print(f"❌ API health check failed: {response.status_code}")
                return False
            print("✅ API health check passed")

            # Scanner health
            response = await self.client.get(f"{self.base_url}/scanner/health")
            if response.status_code != 200:
                print(f"❌ Scanner health check failed: {response.status_code}")
                return False
            print("✅ Scanner health check passed")

            # LLM health
            response = await self.client.get(f"{self.base_url}/scanner/llm-health")
            if response.status_code != 200:
                print(f"❌ LLM health check failed: {response.status_code}")
                return False
            llm_data = response.json()
            print(f"✅ LLM health check passed (provider: {llm_data.get('provider', 'unknown')})")

            return True

        except Exception as e:
            print(f"❌ Health endpoint test failed: {e}")
            return False

    async def test_scanner_endpoints(self) -> bool:
        """Test scanner functionality"""
        print("\n🔍 Testing scanner endpoints...")

        try:
            # Test code scanning
            response = await self.client.post(
                f"{self.base_url}/scanner/scan",
                json={
                    "query": "test_query",
                    "paths": ["/tmp"]
                }
            )
            if response.status_code != 200:
                print(f"❌ Scan endpoint failed: {response.status_code}")
                return False
            scan_data = response.json()
            print("✅ Code scanning works")

            # Test dependency analysis
            response = await self.client.post(
                f"{self.base_url}/scanner/analyze-dependencies",
                json={"paths": ["/tmp"]}
            )
            if response.status_code != 200:
                print(f"❌ Dependency analysis failed: {response.status_code}")
                return False
            print("✅ Dependency analysis works")

            # Test impact analysis
            response = await self.client.post(
                f"{self.base_url}/scanner/impact-analysis",
                json={
                    "query": "test_query",
                    "paths": ["/tmp"]
                }
            )
            if response.status_code != 200:
                print(f"❌ Impact analysis failed: {response.status_code}")
                return False
            print("✅ Impact analysis works")

            return True

        except Exception as e:
            print(f"❌ Scanner endpoint test failed: {e}")
            return False

    async def test_job_endpoints(self) -> bool:
        """Test job management endpoints"""
        print("\n📋 Testing job management...")

        try:
            # Test worker status
            response = await self.client.get(f"{self.base_url}/scanner/jobs/worker/status")
            if response.status_code != 200:
                print(f"❌ Worker status failed: {response.status_code}")
                return False
            worker_data = response.json()
            print(f"✅ Worker status works (running: {worker_data.get('is_running', False)})")

            # Test queue stats
            response = await self.client.get(f"{self.base_url}/scanner/jobs/queue/stats")
            if response.status_code not in [200, 503]:  # 503 is OK if Redis not available
                print(f"❌ Queue stats failed: {response.status_code}")
                return False
            print("✅ Queue stats works")

            # Test job status (should return 404 for non-existent job)
            response = await self.client.get(f"{self.base_url}/scanner/jobs/status/nonexistent_job")
            if response.status_code != 404:
                print(f"❌ Job status failed (expected 404): {response.status_code}")
                return False
            print("✅ Job status works correctly")

            return True

        except Exception as e:
            print(f"❌ Job endpoint test failed: {e}")
            return False

    async def test_llm_functionality(self) -> bool:
        """Test LLM investigation functionality"""
        print("\n🤖 Testing LLM functionality...")

        try:
            # Test LLM investigation with mock
            response = await self.client.post(
                f"{self.base_url}/scanner/investigate",
                json={
                    "query": "What happens if we change term_sheet_id from string to UUID?",
                    "use_mock": True
                }
            )
            if response.status_code != 200:
                print(f"❌ LLM investigation failed: {response.status_code}")
                return False
            investigation_data = response.json()

            required_fields = ["nodes", "edges", "knowledge_gaps", "explanation"]
            for field in required_fields:
                if field not in investigation_data:
                    print(f"❌ LLM investigation missing field: {field}")
                    return False

            print("✅ LLM investigation works")
            return True

        except Exception as e:
            print(f"❌ LLM functionality test failed: {e}")
            return False

    async def test_api_integration(self) -> bool:
        """Test main API integration"""
        print("\n🔗 Testing API integration...")

        try:
            # Test main investigate endpoint
            response = await self.client.post(
                f"{self.base_url}/api/v1/investigate",
                json={"query": "test query"}
            )
            if response.status_code != 200:
                print(f"❌ Main investigate endpoint failed: {response.status_code}")
                return False
            investigation_data = response.json()

            required_fields = ["query", "nodes", "edges", "knowledge_gaps", "summary"]
            for field in required_fields:
                if field not in investigation_data:
                    print(f"❌ Main investigation missing field: {field}")
                    return False

            print("✅ Main API integration works")

            # Test investigation status
            response = await self.client.get(f"{self.base_url}/api/v1/investigation-status")
            if response.status_code != 200:
                print(f"❌ Investigation status failed: {response.status_code}")
                return False
            status_data = response.json()

            if "components" not in status_data or "capabilities" not in status_data:
                print("❌ Investigation status missing required fields")
                return False

            print("✅ Investigation status works")
            return True

        except Exception as e:
            print(f"❌ API integration test failed: {e}")
            return False

    async def run_all_tests(self) -> bool:
        """Run all consolidation tests"""
        print("🚀 Starting Archaeologist Service Consolidation Tests\n")

        tests = [
            self.test_health_endpoints,
            self.test_scanner_endpoints,
            self.test_job_endpoints,
            self.test_llm_functionality,
            self.test_api_integration,
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            try:
                if await test():
                    passed += 1
                else:
                    print("⚠️  Test failed, continuing with remaining tests...")
            except Exception as e:
                print(f"💥 Test crashed: {e}")

        print(f"\n📊 Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! Service consolidation is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the service configuration.")
            return False

async def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"

    print(f"🔧 Testing service at: {base_url}")

    async with ConsolidationTester(base_url) as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())