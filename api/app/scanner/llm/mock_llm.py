"""
Mock LLM Service for Scanner Service

This module provides a rule-based mock LLM service for the prototype.
It simulates LLM responses without requiring actual LLM API calls,
making it perfect for fast development and demonstration.
"""

import logging
from typing import Dict, Any, List
import httpx
from ..config import get_settings

logger = logging.getLogger(__name__)

class MockLLMService:
    """
    Mock LLM service that provides rule-based responses for common queries.
    This simulates the behavior of a real LLM but with deterministic responses.
    """
    
    def __init__(self):
        settings = get_settings()
        self.api_port = settings.WEB_PORT
        self.client = httpx.AsyncClient(base_url=f"http://localhost:{self.api_port}", timeout=30.0)
    
    async def investigate_change(self, query: str) -> Dict[str, Any]:
        """
        Investigate a proposed change using rule-based logic.
        
        Args:
            query: The change investigation query
            
        Returns:
            Dictionary containing nodes, edges, knowledge gaps, and explanation
        """
        logger.info(f"Mock LLM investigating: {query}")
        
        # Extract key terms from query for rule-based responses
        query_lower = query.lower()
        
        if "term_sheet_id" in query_lower:
            return await self._investigate_term_sheet_id(query)
        elif "client_identifier" in query_lower or "client identifier" in query_lower:
            return await self._investigate_client_identifier(query)
        elif "payment" in query_lower:
            return await self._investigate_payment_system(query)
        else:
            return await self._generate_generic_response(query)
    
    async def _investigate_term_sheet_id(self, query: str) -> Dict[str, Any]:
        """Handle term_sheet_id related investigations"""
        
        # Call scanner for impact analysis
        try:
            response = await self.client.post("/impact-analysis", json={
                "query": "term_sheet_id",
                "paths": ["/app/mock_enterprise"]
            })
            scanner_result = response.json()
        except Exception as e:
            logger.error(f"Error calling scanner: {e}")
            scanner_result = self._fallback_scanner_response()
        
        # Enhance with mock LLM reasoning
        enhanced_result = {
            "nodes": scanner_result.get("nodes", []),
            "edges": scanner_result.get("edges", []),
            "knowledge_gaps": scanner_result.get("knowledge_gaps", []),
            "explanation": {
                "reasoning_steps": [
                    f"Analyzing query: '{query}'",
                    "Detected reference to 'term_sheet_id' field",
                    "Scanning codebase for literal matches of 'term_sheet_id'",
                    "Analyzing dependencies between files containing 'term_sheet_id'",
                    "Identifying potential impact on database schema and application code",
                    "Checking for external dependencies and knowledge gaps"
                ],
                "evidence_sources": scanner_result.get("explanation", {}).get("evidence_sources", []),
                "confidence_score": 0.85,
                "analysis_type": "term_sheet_id_change"
            },
            "recommendations": [
                "Update database schema to use UUID instead of VARCHAR",
                "Modify application code to handle UUID format",
                "Update VBA macros to work with new ID format",
                "Test data migration from string to UUID",
                "Update API documentation"
            ]
        }
        
        return enhanced_result
    
    async def _investigate_client_identifier(self, query: str) -> Dict[str, Any]:
        """Handle client identifier related investigations"""
        
        try:
            response = await self.client.post("/scan", json={
                "query": "client_identifier",
                "paths": ["/app/mock_enterprise"]
            })
            scan_result = response.json()
        except Exception as e:
            logger.error(f"Error calling scanner: {e}")
            scan_result = {"results": []}
        
        return {
            "nodes": self._create_nodes_from_scan(scan_result.get("results", []), "client_identifier"),
            "edges": [
                {
                    "source": "1",
                    "target": "2",
                    "relationship_type": "semantic",
                    "confidence": 0.8,
                    "evidence": "Both user-service and reporting-service handle client identification"
                }
            ],
            "knowledge_gaps": [],
            "explanation": {
                "reasoning_steps": [
                    f"Analyzing query: '{query}'",
                    "Searching for client identification mechanisms",
                    "Found references to client_identifier in multiple services",
                    "Analyzing data flow between services"
                ],
                "evidence_sources": scan_result.get("results", [])[:3],
                "confidence_score": 0.75,
                "analysis_type": "client_identifier_analysis"
            },
            "recommendations": [
                "Standardize client identification across services",
                "Implement client ID validation",
                "Add client lookup service for consistency"
            ]
        }
    
    async def _investigate_payment_system(self, query: str) -> Dict[str, Any]:
        """Handle payment system related investigations"""
        
        return {
            "nodes": [
                {
                    "id": "1",
                    "name": "payment_transactions",
                    "file_path": "/mock_enterprise/data_lake/db_schemas/schema.sql",
                    "component_type": "database",
                    "source_type": "snapshot",
                    "confidence": 0.9
                },
                {
                    "id": "2",
                    "name": "external-payment-api",
                    "file_path": "external",
                    "component_type": "api_endpoint",
                    "source_type": "external",
                    "confidence": 0.6
                }
            ],
            "edges": [
                {
                    "source": "1",
                    "target": "2",
                    "relationship_type": "potential",
                    "confidence": 0.5,
                    "evidence": "Payment transactions may use external payment processing"
                }
            ],
            "knowledge_gaps": [
                {
                    "component": "external-payment-api",
                    "missing_information": "API authentication and schema details",
                    "required_action": "Contact Payments Team for API documentation",
                    "estimated_impact": "High - payment processing core functionality"
                }
            ],
            "explanation": {
                "reasoning_steps": [
                    f"Analyzing query: '{query}'",
                    "Identified payment system components",
                    "Detected potential external payment API dependency",
                    "Knowledge gap identified for external system"
                ],
                "evidence_sources": [],
                "confidence_score": 0.6,
                "analysis_type": "payment_system_analysis"
            },
            "recommendations": [
                "Document external payment API integration",
                "Implement payment processing monitoring",
                "Create fallback payment processing mechanism"
            ]
        }
    
    async def _generate_generic_response(self, query: str) -> Dict[str, Any]:
        """Generate a generic response for unknown queries"""
        
        return {
            "nodes": [],
            "edges": [],
            "knowledge_gaps": [
                {
                    "component": "unknown_system",
                    "missing_information": f"No information found for '{query}'",
                    "required_action": "Provide more specific query terms",
                    "estimated_impact": "Unknown - cannot determine impact"
                }
            ],
            "explanation": {
                "reasoning_steps": [
                    f"Analyzing query: '{query}'",
                    "No specific patterns detected in query",
                    "Unable to determine system components affected",
                    "Recommend refining the query with more specific terms"
                ],
                "evidence_sources": [],
                "confidence_score": 0.1,
                "analysis_type": "generic_analysis"
            },
            "recommendations": [
                "Use more specific terminology in query",
                "Include exact field names or component names",
                "Specify the type of change (e.g., 'database schema', 'API endpoint')"
            ]
        }
    
    def _create_nodes_from_scan(self, scan_results: List[Dict], search_term: str) -> List[Dict]:
        """Create nodes from scan results"""
        nodes = []
        for i, result in enumerate(scan_results):
            component_type = "database" if result.get("file_path", "").endswith('.sql') else \
                           "service" if any(x in result.get("file_path", "") for x in ['user-service', 'reporting-service']) else \
                           "file"
            
            source_type = "snapshot" if "data_lake" in result.get("file_path", "") else "live_repo"
            
            nodes.append({
                "id": str(i + 1),
                "name": result.get("file_path", "").split('/')[-1],
                "file_path": result.get("file_path"),
                "component_type": component_type,
                "source_type": source_type,
                "confidence": result.get("confidence", 1.0)
            })
        
        return nodes
    
    def _fallback_scanner_response(self) -> Dict[str, Any]:
        """Fallback response when scanner is unavailable"""
        return {
            "nodes": [
                {
                    "id": "1",
                    "name": "schema.sql",
                    "file_path": "/mock_enterprise/data_lake/db_schemas/schema.sql",
                    "component_type": "database",
                    "source_type": "snapshot",
                    "confidence": 1.0,
                    "last_updated": "2023-10-27"
                }
            ],
            "edges": [],
            "knowledge_gaps": [
                {
                    "component": "scanner_service",
                    "missing_information": "Scanner service unavailable",
                    "required_action": "Check scanner service status",
                    "estimated_impact": "Medium - limited analysis capability"
                }
            ],
            "explanation": {
                "reasoning_steps": ["Scanner service unavailable, using fallback response"],
                "evidence_sources": [],
                "confidence_score": 0.3
            }
        }

# Singleton instance for easy access
_mock_llm_service: MockLLMService | None = None

async def get_mock_llm_service() -> MockLLMService:
    """Get the singleton mock LLM service instance"""
    global _mock_llm_service
    if _mock_llm_service is None:
        _mock_llm_service = MockLLMService()
    return _mock_llm_service