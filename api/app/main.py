from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sys
import logging
from .config import get_settings
from .llm_interface import get_llm_provider
from api.dependencies import get_database, close_database

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Enterprise Code Archaeologist API")
    yield
    # Shutdown
    logger.info("Shutting down application")
    await close_database()


app = FastAPI(
    title="Enterprise Code Archaeologist API", 
    version="1.0.0",
    lifespan=lifespan
)

# Add automatic tracing middleware
app.add_middleware(TracingMiddleware)

# Instrument FastAPI for additional automatic tracing
telemetry_config.instrument_fastapi(app)
telemetry_config.instrument_httpx()

# Create API v1 router
from fastapi import APIRouter
api_v1_router = APIRouter(prefix="/api/v1")

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
    explanation: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None

@app.get("/")
async def root():
    return {"message": "Enterprise Code Archaeologist API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "archaeologist-api"}

@api_v1_router.post("/investigate", response_model=ImpactReport)
async def investigate_change(request: InvestigationRequest):
    """
    Investigate the impact of a proposed change across the enterprise system.
    
    This endpoint uses the LLM provider to analyze the change and identify
    potentially affected components, dependencies, and knowledge gaps.
    """
    # Note: Automatic HTTP tracing is handled by middleware
    # Business logic tracing can be added here if needed
    
    try:
        # Get the LLM provider and investigate the change
        llm_provider = await get_llm_provider()
        investigation_result = await llm_provider.investigate_change(request.query)
        
        # Convert the LLM response to our ImpactReport format
        nodes = []
        for node_data in investigation_result.get("nodes", []):
            # Ensure the node has all required fields
            node = {
                "id": node_data.get("id", ""),
                "name": node_data.get("name", ""),
                "type": node_data.get("type", node_data.get("component_type", "unknown")),
                "path": node_data.get("path", node_data.get("file_path", "")),
                "source_type": node_data.get("source_type", "unknown"),
                "confidence": node_data.get("confidence", 0.5),
                "last_updated": node_data.get("last_updated")
            }
            nodes.append(DependencyNode(**node))
        
        edges = []
        for edge_data in investigation_result.get("edges", []):
            # Ensure the edge has all required fields
            edge = {
                "source": edge_data.get("source", ""),
                "target": edge_data.get("target", ""),
                "confidence": edge_data.get("confidence", 0.5),
                "relationship_type": edge_data.get("relationship_type", "unknown"),
                "evidence": edge_data.get("evidence", "")
            }
            edges.append(DependencyEdge(**edge))
        
        knowledge_gaps = []
        for gap_data in investigation_result.get("knowledge_gaps", []):
            # Ensure the knowledge gap has all required fields
            gap = {
                "component": gap_data.get("component", ""),
                "missing_information": gap_data.get("missing_information", ""),
                "required_action": gap_data.get("required_action", ""),
                "estimated_impact": gap_data.get("estimated_impact", "")
            }
            knowledge_gaps.append(KnowledgeGap(**gap))
        
        # Create the impact report
        return ImpactReport(
            query=request.query,
            nodes=nodes,
            edges=edges,
            knowledge_gaps=knowledge_gaps,
            summary=investigation_result.get("summary", f"Analysis completed for: {request.query}"),
            explanation=investigation_result.get("explanation"),
            recommendations=investigation_result.get("recommendations", [])
        )
        
    except Exception as e:
        logger.error(f"Error during investigation: {str(e)}")
        # Return a minimal impact report with error information
        return ImpactReport(
            query=request.query,
            nodes=[],
            edges=[],
            knowledge_gaps=[KnowledgeGap(
                component="llm_service",
                missing_information=f"LLM service error: {str(e)}",
                required_action="Check LLM service configuration and availability",
                estimated_impact="High - investigation cannot proceed"
            )],
            summary=f"Investigation failed due to error: {str(e)}",
            explanation={
                "reasoning_steps": [f"Error occurred during investigation: {str(e)}"],
                "evidence_sources": [],
                "confidence_score": 0.0
            }
        )

@api_v1_router.get("/investigation-status")
async def investigation_status():
    """Get status of investigation components"""
    try:
        # Check if scanner service is available
        if settings.SCANNER_URL is None:
            raise ValueError("SCANNER_URL is not configured")
        import httpx
        async with httpx.AsyncClient() as client:
            scanner_response = await client.get(settings.SCANNER_URL + "/health", timeout=5.0)
            scanner_status = scanner_response.json().get("status", "unknown")
    except Exception as e:
        scanner_status = f"unavailable: {str(e)}"
    
    # Check LLM provider status
    try:
        llm_provider = await get_llm_provider()
        llm_status = await llm_provider.health_check()
        llm_provider_type = settings.LLM_PROVIDER or "unknown"
    except Exception as e:
        llm_status = {"status": f"unavailable: {str(e)}"}
        llm_provider_type = settings.LLM_PROVIDER or "unknown"
    
    # Determine capabilities based on provider
    capabilities = [
        "literal_search",
        "dependency_analysis",
        "knowledge_gap_detection"
    ]
    
    if llm_provider_type == "ollama":
        capabilities.append("ollama_reasoning")
        capabilities.append("tool_calling")
    elif llm_provider_type == "mock":
        capabilities.append("mock_llm_reasoning")
    else:
        capabilities.append("llm_reasoning")
    
    return {
        "status": "healthy",
        "components": {
            "api": "healthy",
            "llm": {
                "provider": llm_provider_type,
                "status": llm_status.get("status", "unknown"),
                "model": settings.LLM_MODEL or "unknown",
                "api_url": settings.LLM_API_URL or "unknown"
            },
            "scanner": scanner_status
        },
        "capabilities": capabilities
    }


# Include the API v1 router
app.include_router(api_v1_router)

# Include database router
from .routes.database import database_router
app.include_router(database_router)

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