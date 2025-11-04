from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sys
import logging
from .config import get_settings
from dependencies import get_database, close_database

# Import telemetry and middleware from shared package
from dependencies.telemetry import initialize_telemetry, get_tracer
from dependencies.middleware import TracingMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings and initialize telemetry
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Enterprise Code Archaeologist API")

    # Initialize job client and start worker
    try:
        from .job_client import job_client
        from .job_manager import job_manager

        # Connect to Redis
        await job_client.connect()

        # Start job worker in background
        worker_task = asyncio.create_task(
            job_client.start_worker(job_manager.process_job)
        )

        # Store worker task for shutdown
        app.state.worker_task = worker_task

        logger.info("Job client and worker initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize job client/worker: {e}")
        # Continue without job worker - job processing will be disabled

    yield
    # Shutdown
    logger.info("Shutting down application")

    # Stop job worker and disconnect job client
    try:
        from .job_client import job_client
        await job_client.stop_worker()
        await job_client.disconnect()
        logger.info("Job worker stopped and client disconnected")
    except Exception as e:
        logger.warning(f"Error stopping job worker/client: {e}")

    await close_database()


app = FastAPI(
    title="Enterprise Code Archaeologist API", 
    version="1.0.0",
    lifespan=lifespan
)

# Add automatic tracing middleware
app.add_middleware(TracingMiddleware)

# Instrument FastAPI for additional automatic tracing
telemetry_config = initialize_telemetry(settings)
if telemetry_config:
    telemetry_config.instrument_fastapi(app)
    telemetry_config.instrument_httpx()

# Create API v1 router
from fastapi import APIRouter
api_v1_router = APIRouter(prefix="/api/v1")

# Import authentication dependencies
from dependencies.auth import get_current_user
from models.database import User

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

# Node Management Models
class NodeDeleteRequest(BaseModel):
    node_id: str
    project_id: Optional[str] = None

class NodeDeleteResponse(BaseModel):
    success: bool
    message: str
    deleted_node_id: str

class NodeMetadataUpdateRequest(BaseModel):
    node_id: str
    metadata: Dict[str, Any]
    project_id: Optional[str] = None

class NodeMetadataUpdateResponse(BaseModel):
    success: bool
    message: str
    node_id: str
    updated_metadata: Dict[str, Any]

@app.get("/")
async def root():
    return {"message": "Enterprise Code Archaeologist API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "archaeologist-api"}

@api_v1_router.post("/investigate", response_model=ImpactReport)
async def investigate_change(
    request: InvestigationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Investigate the impact of a proposed change across the enterprise system.

    This endpoint now uses the integrated scanner functionality to handle LLM analysis
    and identify potentially affected components, dependencies, and knowledge gaps.
    """
    # Note: Automatic HTTP tracing is handled by middleware
    # Business logic tracing can be added here if needed

    try:
        # Use integrated scanner for LLM investigation
        from .scanner.llm.llm_interface import get_llm_provider
        from .routes.scanner import InvestigationRequest as ScannerInvestigationRequest

        # Create scanner investigation request
        scanner_request = ScannerInvestigationRequest(query=request.query, use_mock=False)

        # Get LLM provider and perform investigation
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
        # Check integrated scanner components
        from .scanner.llm.llm_interface import get_llm_provider
        from .scanner.rag.rag_service import get_rag_service

        # Check LLM status
        llm_provider = await get_llm_provider()
        llm_status = await llm_provider.health_check()

        # Check RAG status
        rag_service = await get_rag_service()
        rag_status = await rag_service.health_check()

        scanner_status = {"status": "healthy", "components": {"llm": llm_status, "rag": rag_status}}
    except Exception as e:
        scanner_status = {"status": f"unavailable: {str(e)}", "llm": {"status": "unavailable"}, "rag": {"status": "unavailable"}}
        llm_status = {"status": f"unavailable: {str(e)}"}
    
    # Determine capabilities based on scanner LLM
    capabilities = [
        "literal_search",
        "dependency_analysis", 
        "knowledge_gap_detection",
        "llm_investigation"
    ]
    
    if llm_status.get("provider") == "mock":
        capabilities.append("mock_llm_reasoning")
    else:
        capabilities.append("llm_reasoning")
        capabilities.append("tool_calling")
    
    return {
        "status": "healthy",
        "components": {
            "api": "healthy",
            "llm": llm_status,
            "scanner": scanner_status
        },
        "capabilities": capabilities
    }


# Node Management Endpoints
@api_v1_router.delete("/nodes/{node_id}", response_model=NodeDeleteResponse)
async def delete_node(
    node_id: str,
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Delete a node from the dependency graph.

    This endpoint removes a node and all its associated edges from the system.
    """
    try:
        logger.info(f"User {current_user.username} deleting node {node_id} for project {project_id or 'default'}")

        # Check if node exists
        node = await db.get_node_by_id(node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

        # Check user permissions for the project if node is project-scoped
        if node.project_id:
            user_role = await db.get_user_project_role(node.project_id, current_user.id)
            if not user_role or user_role not in ['owner', 'admin']:
                raise HTTPException(status_code=403, detail="Insufficient permissions to delete nodes in this project")

        # Delete the node
        success = await db.delete_node(node_id)
        
        if success:
            return NodeDeleteResponse(
                success=True,
                message=f"Node {node_id} successfully deleted",
                deleted_node_id=node_id
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete node")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting node {node_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete node: {str(e)}")


@api_v1_router.put("/nodes/{node_id}/metadata", response_model=NodeMetadataUpdateResponse)
async def update_node_metadata(
    node_id: str,
    request: NodeMetadataUpdateRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Update metadata for a node in the dependency graph.

    This endpoint allows updating custom metadata associated with a node.
    This could include things like custom labels, descriptions, or other user-defined properties.
    """
    try:
        logger.info(f"User {current_user.username} updating metadata for node {node_id} with data: {request.metadata}")

        # Check if node exists
        node = await db.get_node_by_id(node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

        # Check user permissions for project if node is project-scoped
        if node.project_id:
            user_role = await db.get_user_project_role(node.project_id, current_user.id)
            if not user_role or user_role not in ['owner', 'admin', 'member']:
                raise HTTPException(status_code=403, detail="Insufficient permissions to update nodes in this project")

        # Update metadata
        success = await db.update_node_metadata(node_id, request.metadata)
        
        if success:
            return NodeMetadataUpdateResponse(
                success=True,
                message=f"Metadata for node {node_id} successfully updated",
                node_id=node_id,
                updated_metadata=request.metadata
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to update node metadata")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating metadata for node {node_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update node metadata: {str(e)}")


@api_v1_router.post("/nodes/delete", response_model=NodeDeleteResponse)
async def delete_node_with_body(
    request: NodeDeleteRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Alternative endpoint to delete a node using POST with request body.

    This is useful when the node_id might contain special characters that cause issues with URL parameters,
    or when you want to include additional context in the request.
    """
    return await delete_node(request.node_id, request.project_id, current_user)


# Include all routers under the API v1 router
from .routes.auth import router as auth_router
from .routes.projects import router as projects_router
from .routes.jobs import router as jobs_router
from .routes.scanner import router as scanner_router
from dependencies.database import get_database

# Include all routers under the /api/v1 prefix
api_v1_router.include_router(auth_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(jobs_router)

# Include scanner router directly (not under /api/v1 for backward compatibility)
app.include_router(scanner_router)

# Include the API v1 router in the main app
app.include_router(api_v1_router)

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
