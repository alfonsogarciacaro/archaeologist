"""
JSON Schemas

This module contains JSON schema templates for LLM responses.
"""

class ResponseSchemas:
    """JSON schemas for structuring LLM responses"""
    
    INVESTIGATION_RESPONSE = {
        "type": "object",
        "properties": {
            "nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "file_path": {"type": "string"},
                        "component_type": {"type": "string"},
                        "source_type": {"type": "string"},
                        "confidence": {"type": "number"}
                    }
                }
            },
            "edges": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "target": {"type": "string"},
                        "relationship_type": {"type": "string"},
                        "confidence": {"type": "number"},
                        "evidence": {"type": "string"}
                    }
                }
            },
            "knowledge_gaps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "component": {"type": "string"},
                        "missing_information": {"type": "string"},
                        "required_action": {"type": "string"},
                        "estimated_impact": {"type": "string"}
                    }
                }
            },
            "explanation": {
                "type": "object",
                "properties": {
                    "reasoning_steps": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "evidence_sources": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "confidence_score": {"type": "number"}
                }
            }
        }
    }