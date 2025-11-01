from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sys
import logging
from .config import get_settings

# Add shared directory to Python path (navigate up until found)
def find_dir_upwards(dirname: str = "shared") -> str:
    """Find shared directory by navigating up from current location"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        found = os.path.join(current_dir, dirname)
        if os.path.exists(found):
            return found        
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached root
            raise FileNotFoundError("shared directory not found")
        current_dir = parent_dir

sys.path.insert(0, find_dir_upwards("shared"))

# Import telemetry and middleware
from telemetry import initialize_telemetry, get_tracer
from middleware import TracingMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings and initialize telemetry
settings = get_settings()
telemetry_config = initialize_telemetry(settings)

# Get tracer for manual instrumentation
tracer = get_tracer(__name__)

app = FastAPI(title="Enterprise Code Archaeologist API", version="1.0.0")

# Add automatic tracing middleware
app.add_middleware(TracingMiddleware)

# Instrument FastAPI for additional automatic tracing
telemetry_config.instrument_fastapi(app)
telemetry_config.instrument_httpx()

class InvestigationRequest(BaseModel):
    query: str  # e.g., "Change term_sheet_id from string to UUID"

class DependencyNode(BaseModel):
    id: str
    name: str
    type: str  # "repo", "db_table", "file", "api_endpoint"
    path: str
    source_type: str  # "live_repo" or "snapshot"
    confidence: float  # 0.0 to 1.0
    last_updated: Optional[str] = None

class DependencyEdge(BaseModel):
    source: str
    target: str
    confidence: float
    relationship_type: str  # "literal", "semantic", "potential"
    evidence: str

class KnowledgeGap(BaseModel):
    component: str
    missing_information: str
    required_action: str
    estimated_impact: str

class ImpactReport(BaseModel):
    query: str
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]
    knowledge_gaps: List[KnowledgeGap]
    summary: str

@app.get("/")
async def root():
    return {"message": "Enterprise Code Archaeologist API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "archaeologist-api"}

@app.post("/investigate", response_model=ImpactReport)
async def investigate_change(request: InvestigationRequest):
    """
    Investigate the impact of a proposed change across the enterprise system.
    
    This is currently a placeholder that returns dummy data for testing the UI.
    The real implementation will:
    1. Use the Code Scanner to find literal matches
    2. Use the RAG Engine to find semantic matches  
    3. Apply guardrails to validate results
    4. Return a comprehensive impact report
    """
    # Note: Automatic HTTP tracing is handled by middleware
    # Business logic tracing can be added here if needed
    
    # Placeholder response for testing the UI
    dummy_nodes = [
        {
            "id": "1",
            "name": "schema.sql",
            "type": "db_table",
            "path": "/mock_enterprise/data_lake/db_schemas/schema.sql",
            "source_type": "snapshot",
            "confidence": 1.0,
            "last_updated": "2023-10-27"
        },
        {
            "id": "2", 
            "name": "user-service",
            "type": "repo",
            "path": "/mock_enterprise/live_repos/user-service.git",
            "source_type": "live_repo",
            "confidence": 0.9
        },
        {
            "id": "3",
            "name": "reporting-service",
            "type": "repo", 
            "path": "/mock_enterprise/live_repos/reporting-service.git",
            "source_type": "live_repo",
            "confidence": 0.8
        },
        {
            "id": "4",
            "name": "term_sheet_generator.vba",
            "type": "file",
            "path": "/mock_enterprise/data_lake/finance_macros/2023-10-27/term_sheet_generator.vba",
            "source_type": "snapshot", 
            "confidence": 0.7,
            "last_updated": "2023-10-27"
        }
    ]
    
    dummy_edges = [
        {
            "source": "1",
            "target": "2",
            "confidence": 1.0,
            "relationship_type": "literal",
            "evidence": "Found 'term_sheet_id VARCHAR(50)' in schema.sql"
        },
        {
            "source": "2",
            "target": "3",
            "confidence": 0.8,
            "relationship_type": "semantic",
            "evidence": "Both services reference term_sheet_id field"
        },
        {
            "source": "3",
            "target": "4",
            "confidence": 0.6,
            "relationship_type": "potential",
            "evidence": "Reporting service exports data used by Excel macros"
        }
    ]        
    
    dummy_knowledge_gaps = [
        {
            "component": "external-payment-api",
            "missing_information": "API schema for payment processing",
            "required_action": "Request API documentation from Payments Team",
            "estimated_impact": "Medium - payment processing may be affected"
        }
    ]
    
    return ImpactReport(
        query=request.query,
        nodes=[DependencyNode(**node) for node in dummy_nodes],
        edges=[DependencyEdge(**edge) for edge in dummy_edges],
        knowledge_gaps=[KnowledgeGap(**gap) for gap in dummy_knowledge_gaps],
        summary=f"Found 4 components potentially impacted by: {request.query}"
    )


if os.getenv("NODE_ENV") != "development":
    app.mount("/static", StaticFiles(directory="ui/build/static"), name="static")

    @app.get("/ui/{path:path}")
    async def serve_ui(path: str):
        """Serve React app for all UI routes"""
        return FileResponse("ui/build/index.html")

    @app.get("/")
    async def serve_root():
        """Serve React app at root"""
        return FileResponse("ui/build/index.html")
else:
    @app.get("/")
    async def root():
        return {"message": "Enterprise Code Archaeologist API", "version": "1.0.0"}