from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import subprocess
import json
import os
import sys
import re
import logging
from pathlib import Path
from .config import get_settings

# Import RAG components
from .rag.rag_service import get_rag_service
from .rag.models import (
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
    HealthCheckResponse
)

# Import LLM components
from .llm.llm_interface import get_llm_provider

# Import telemetry and middleware from shared package
# from telemetry import initialize_telemetry, get_tracer
# from middleware import TracingMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings and initialize telemetry
settings = get_settings()

app = FastAPI(title="Code Scanner Service", version="1.0.0")

# Add automatic tracing middleware
# app.add_middleware(TracingMiddleware)

# Instrument FastAPI for additional automatic tracing
# telemetry_config = initialize_telemetry(settings)
# telemetry_config.instrument_fastapi(app)
# telemetry_config.instrument_httpx()

class ScanRequest(BaseModel):
    query: str
    paths: List[str] = ["/app/mock_enterprise"]

class ScanResult(BaseModel):
    file_path: str
    line_number: int
    content: str
    confidence: float  # 1.0 for literal matches
    match_type: str  # "literal"

class ScanResponse(BaseModel):
    results: List[ScanResult]
    total_matches: int

# Dependency Analysis Models
class DependencyResult(BaseModel):
    source_file: str
    target_file: str
    relationship_type: str  # "reads_from", "writes_to", "imports", "defines_structure_for"
    evidence: str
    confidence: float

class DependencyAnalysisRequest(BaseModel):
    paths: List[str] = ["/app/mock_enterprise"]

class DependencyAnalysisResponse(BaseModel):
    dependencies: List[DependencyResult]
    total_found: int

class ComponentNode(BaseModel):
    id: str
    name: str
    file_path: str
    component_type: str  # "database", "service", "file", "api"
    source_type: str  # "live_repo", "snapshot"
    confidence: float
    last_updated: Optional[str] = None
    relevant_code: Optional[str] = None

class ComponentEdge(BaseModel):
    source: str
    target: str
    relationship_type: str
    confidence: float
    evidence: str

class ImpactAnalysisRequest(BaseModel):
    query: str
    paths: List[str] = ["/app/mock_enterprise"]

class ImpactAnalysisResponse(BaseModel):
    nodes: List[ComponentNode]
    edges: List[ComponentEdge]
    knowledge_gaps: List[Dict[str, Any]]
    explanation: Dict[str, Any]


@app.get("/")
async def root():
    return {"service": "code-scanner", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "code-scanner"}

@app.post("/scan", response_model=ScanResponse)
async def scan_code(request: ScanRequest):
    """
    Scan code files for literal matches using ripgrep.
    
    This service uses ripgrep to find exact string matches in the codebase.
    It returns high-confidence, literal matches that are guaranteed to be accurate.
    """
    results = []
    
    # Use ripgrep to search for the literal string
    cmd = [
        'rg',
        '--json',
        '--line-number',
        '--no-heading',
        '--with-filename',
        request.query
    ] + request.paths
    
    # Run ripgrep
    process = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if process.returncode == 0:
        # Parse ripgrep JSON output
        for line in process.stdout.strip().split('\n'):
            if line.strip():
                try:
                    rg_result = json.loads(line)
                    if rg_result.get('type') == 'match':
                        scan_result = ScanResult(
                            file_path=rg_result['data']['path']['text'],
                            line_number=rg_result['data']['line_number'],
                            content=rg_result['data']['lines']['text'].strip(),
                            confidence=1.0,  # Literal matches have 100% confidence
                            match_type="literal"
                        )
                        results.append(scan_result)
                except json.JSONDecodeError:
                    continue
    
    logger.info(f"Scan completed: {len(results)} matches found")

    return ScanResponse(
        results=results,
        total_matches=len(results)
    )        


# Dependency Analysis Functions
def find_files(paths: List[str], pattern: str) -> List[str]:
    """Find files matching pattern in given paths"""
    files = []
    for path in paths:
        path_obj = Path(path)
        if path_obj.is_dir():
            files.extend(path_obj.rglob(pattern))
        elif path_obj.match(pattern):
            files.append(path_obj)
    return [str(f) for f in files]

def extract_table_names(sql_file: str) -> List[str]:
    """Extract table names from SQL file"""
    try:
        with open(sql_file, 'r') as f:
            content = f.read()
        
        # Find CREATE TABLE statements
        table_pattern = r'CREATE\s+TABLE\s+(\w+)'
        matches = re.findall(table_pattern, content, re.IGNORECASE)
        return matches
    except Exception as e:
        logger.error(f"Error reading SQL file {sql_file}: {e}")
        return []

def extract_table_references(file_path: str) -> List[str]:
    """Extract table references from code file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Look for table references in different patterns
        patterns = [
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'DELETE\s+FROM\s+(\w+)',
            r'(\w+)\.\w+',  # table.column pattern
            r'table_name["\']?\s*=\s*["\']?(\w+)',  # table_name = "table"
        ]
        
        references = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            references.extend(matches)
        
        return list(set(references))  # Remove duplicates
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

def extract_function_imports(file_path: str) -> List[str]:
    """Extract function/module imports from code file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        imports = []
        
        # Python imports
        if file_path.endswith('.py'):
            patterns = [
                r'from\s+(\w+)',
                r'import\s+(\w+)',
            ]
        # JavaScript imports
        elif file_path.endswith('.js'):
            patterns = [
                r'require\(["\']([^"\']+)["\']\)',
                r'import.*from\s+["\']([^"\']+)["\']',
            ]
        else:
            return []
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
        
        return list(set(imports))
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

def analyze_dependencies(paths: List[str]) -> List[DependencyResult]:
    """Analyze dependencies between files in given paths"""
    dependencies = []
    
    # Find different file types
    sql_files = find_files(paths, "*.sql")
    python_files = find_files(paths, "*.py")
    js_files = find_files(paths, "*.js")
    vba_files = find_files(paths, "*.vba")
    
    # Analyze SQL -> Code dependencies (database structure)
    for sql_file in sql_files:
        tables = extract_table_names(sql_file)
        for code_file in python_files + js_files:
            referenced_tables = extract_table_references(code_file)
            common_tables = set(tables) & set(referenced_tables)
            
            if common_tables:
                dependencies.append(DependencyResult(
                    source_file=sql_file,
                    target_file=code_file,
                    relationship_type="defines_structure_for",
                    evidence=f"Tables {', '.join(common_tables)} defined in SQL are referenced in code",
                    confidence=0.9
                ))
    
    # Analyze code -> code dependencies (imports, function calls)
    all_code_files = python_files + js_files + vba_files
    for i, source_file in enumerate(all_code_files):
        for target_file in all_code_files[i+1:]:
            source_imports = extract_function_imports(source_file)
            target_functions = extract_function_imports(target_file)
            
            # Check for cross-references
            source_name = Path(source_file).stem
            target_name = Path(target_file).stem
            
            if target_name.lower() in [imp.lower() for imp in source_imports]:
                dependencies.append(DependencyResult(
                    source_file=source_file,
                    target_file=target_file,
                    relationship_type="imports",
                    evidence=f"{source_file} imports from {target_file}",
                    confidence=0.8
                ))
            
            # Check for shared data structures (term_sheet_id, etc.)
            try:
                with open(source_file, 'r') as f:
                    source_content = f.read().lower()
                with open(target_file, 'r') as f:
                    target_content = f.read().lower()
                
                # Look for common identifiers
                common_identifiers = []
                for identifier in ['term_sheet_id', 'client_identifier', 'user_id']:
                    if identifier in source_content and identifier in target_content:
                        common_identifiers.append(identifier)
                
                if common_identifiers:
                    dependencies.append(DependencyResult(
                        source_file=source_file,
                        target_file=target_file,
                        relationship_type="shares_data_with",
                        evidence=f"Both files reference: {', '.join(common_identifiers)}",
                        confidence=0.7
                    ))
            except Exception as e:
                logger.error(f"Error comparing files {source_file} and {target_file}: {e}")
    
    return dependencies

@app.post("/analyze-dependencies", response_model=DependencyAnalysisResponse)
async def analyze_dependencies_endpoint(request: DependencyAnalysisRequest):
    """
    Analyze dependencies between files in the given paths.
    
    This endpoint identifies relationships like:
    - SQL files defining structure for code files
    - Import dependencies between code files
    - Shared data structures between files
    """
    dependencies = analyze_dependencies(request.paths)
    
    logger.info(f"Dependency analysis completed: {len(dependencies)} dependencies found")
    
    return DependencyAnalysisResponse(
        dependencies=dependencies,
        total_found=len(dependencies)
    )

@app.post("/impact-analysis", response_model=ImpactAnalysisResponse)
async def impact_analysis_endpoint(request: ImpactAnalysisRequest):
    """
    Perform comprehensive impact analysis for a given query.
    
    This combines literal search with dependency analysis to create
    a complete impact graph with nodes and edges.
    """
    # Step 1: Find literal matches
    scan_request = ScanRequest(query=request.query, paths=request.paths)
    scan_result = await scan_code(scan_request)
    
    # Step 2: Analyze dependencies
    dependencies = analyze_dependencies(request.paths)
    
    # Step 3: Build nodes from scan results
    nodes = []
    node_id = 0
    
    # Create nodes for files with literal matches
    for match in scan_result.results:
        node_id += 1
        component_type = "database" if match.file_path.endswith('.sql') else \
                       "service" if any(x in match.file_path for x in ['user-service', 'reporting-service']) else \
                       "file"
        
        source_type = "snapshot" if "data_lake" in match.file_path else "live_repo"
        
        # Extract relevant code snippet
        try:
            with open(match.file_path, 'r') as f:
                lines = f.readlines()
                start_line = max(0, match.line_number - 2)
                end_line = min(len(lines), match.line_number + 2)
                relevant_code = ''.join(lines[start_line:end_line]).strip()
        except:
            relevant_code = match.content
        
        nodes.append(ComponentNode(
            id=str(node_id),
            name=Path(match.file_path).name,
            file_path=match.file_path,
            component_type=component_type,
            source_type=source_type,
            confidence=match.confidence,
            last_updated="2023-10-27" if source_type == "snapshot" else None,
            relevant_code=relevant_code
        ))
    
    # Step 4: Build edges from dependencies
    edges = []
    for dep in dependencies:
        # Find corresponding nodes
        source_node = next((n for n in nodes if n.file_path == dep.source_file), None)
        target_node = next((n for n in nodes if n.file_path == dep.target_file), None)
        
        # Create nodes for dependency files if they don't exist
        if not source_node:
            node_id += 1
            source_node = ComponentNode(
                id=str(node_id),
                name=Path(dep.source_file).name,
                file_path=dep.source_file,
                component_type="database" if dep.source_file.endswith('.sql') else "file",
                source_type="snapshot" if "data_lake" in dep.source_file else "live_repo",
                confidence=dep.confidence
            )
            nodes.append(source_node)
        
        if not target_node:
            node_id += 1
            target_node = ComponentNode(
                id=str(node_id),
                name=Path(dep.target_file).name,
                file_path=dep.target_file,
                component_type="database" if dep.target_file.endswith('.sql') else "file",
                source_type="snapshot" if "data_lake" in dep.target_file else "live_repo",
                confidence=dep.confidence
            )
            nodes.append(target_node)
        
        edges.append(ComponentEdge(
            source=source_node.id,
            target=target_node.id,
            relationship_type=dep.relationship_type,
            confidence=dep.confidence,
            evidence=dep.evidence
        ))
    
    # Step 5: Generate knowledge gaps
    knowledge_gaps = []
    
    # Look for external dependencies
    all_files = [node.file_path for node in nodes]
    if any('external-payment-api' in node.relevant_code or '' for node in nodes):
        knowledge_gaps.append({
            "component": "external-payment-api",
            "missing_information": "API schema and authentication details",
            "required_action": "Request API documentation from Payments Team",
            "estimated_impact": "Medium - payment processing may be affected"
        })
    
    # Step 6: Generate explanation
    explanation = {
        "reasoning_steps": [
            f"Found {len(scan_result.results)} literal matches for '{request.query}'",
            f"Analyzed {len(dependencies)} dependencies between files",
            f"Created {len(nodes)} component nodes and {len(edges)} relationships",
            "Identified potential knowledge gaps and external dependencies"
        ],
        "evidence_sources": [
            {
                "file": match.file_path,
                "line": match.line_number,
                "content": match.content,
                "confidence": match.confidence
            } for match in scan_result.results[:5]  # Limit to top 5 for demo
        ],
        "confidence_score": min(0.9, len(scan_result.results) / 10.0)  # Simple confidence calculation
    }
    
    return ImpactAnalysisResponse(
        nodes=nodes,
        edges=edges,
        knowledge_gaps=knowledge_gaps,
        explanation=explanation
    )

@app.get("/test-scan")
async def test_scan():
    """Test endpoint to verify scanner works with mock data"""
    test_request = ScanRequest(
        query="term_sheet_id",
        paths=["/app/mock_enterprise"]
    )
    return await scan_code(test_request)

@app.get("/test-impact-analysis")
async def test_impact_analysis():
    """Test endpoint for impact analysis"""
    test_request = ImpactAnalysisRequest(
        query="term_sheet_id",
        paths=["/app/mock_enterprise"]
    )
    return await impact_analysis_endpoint(test_request)


# RAG Endpoints

@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """
    Ingest a document into the RAG system.
    
    This endpoint processes a document by:
    1. Preprocessing the text content
    2. Creating overlapping chunks optimized for embeddings
    3. Generating embeddings using local GGUF models
    4. Storing chunks with embeddings in vector database
    
    The collection name follows the pattern: {VECTORDB_COLLECTION_PREFIX}_{project}_{normalized_file_name}
    """
    logger.info(f"Received ingestion request for file: {request.file_name}")
    
    try:
        rag_service = await get_rag_service()
        result = await rag_service.ingest_document(request)
        
        logger.info(f"Successfully ingested {result.chunks_created} chunks from {request.file_name}")
        return result
        
    except Exception as e:
        logger.error(f"Error during document ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Perform semantic search on ingested documents.
    
    This endpoint searches for semantically similar chunks across all documents
    or within a specific project if specified.
    """
    logger.info(f"Received search request: '{request.query}'")
    
    try:
        rag_service = await get_rag_service()
        result = await rag_service.search(request)
        
        logger.info(f"Search completed: {result.total_found} results found")
        return result
        
    except Exception as e:
        logger.error(f"Error during semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rag-health", response_model=HealthCheckResponse)
async def rag_health_check():
    """
    Perform health check on RAG service components.
    
    Returns the status of:
    - Embedding model (GGUF/sentence-transformers)
    - Vector database connection
    - Available collections
    """
    logger.info("Performing RAG health check")
    
    try:
        rag_service = await get_rag_service()
        result = await rag_service.health_check()
        
        logger.info(f"RAG health check completed: {result.status}")
        return result
        
    except Exception as e:
        logger.error(f"Error during RAG health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test-ingest")
async def test_ingest():
    """Test endpoint for document ingestion"""
    test_request = IngestRequest(
        file_name="test_user_service.py",
        project="test_project",
        content='''def authenticate_user(username, password):
    """
    Authenticate a user with username and password.
    
    Args:
        username (str): User's username
        password (str): User's password
        
    Returns:
        dict: User information if authentication successful
    """
    # Hash the password for security
    hashed_password = hash_password(password)
    
    # Query database for user
    user = db.query("SELECT * FROM users WHERE username = ?", (username,))
    
    if user and verify_password(hashed_password, user.password_hash):
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }
    
    return None


def create_user(username, password, email):
    """
    Create a new user account.
    
    Args:
        username (str): Desired username
        password (str): User's password
        email (str): User's email address
        
    Returns:
        dict: Created user information
    """
    # Validate input
    if not username or not password or not email:
        raise ValueError("All fields are required")
    
    # Check if user already exists
    existing_user = db.query("SELECT id FROM users WHERE username = ?", (username,))
    if existing_user:
        raise ValueError("Username already exists")
    
    # Create new user
    hashed_password = hash_password(password)
    user_id = db.insert(
        "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
        (username, hashed_password, email)
    )
    
    return {
        "user_id": user_id,
        "username": username,
        "email": email
    }
''',
        file_type="python",
        timestamp="2023-10-27T10:30:00Z",
        metadata={"author": "test", "version": "1.0.0"}
    )
    
    return await ingest_document(test_request)


@app.get("/test-search")
async def test_search():
    """Test endpoint for semantic search"""
    test_request = SearchRequest(
        query="user authentication password hashing",
        project="test_project",
        limit=5,
        score_threshold=0.5
    )

    return await search_documents(test_request)


# LLM Investigation Models

class InvestigationRequest(BaseModel):
    query: str
    use_mock: Optional[bool] = False

class InvestigationResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    knowledge_gaps: List[Dict[str, Any]]
    explanation: Dict[str, Any]
    recommendations: Optional[List[str]] = None

class LLMHealthResponse(BaseModel):
    status: str
    provider: Optional[str] = None
    api_url: Optional[str] = None
    model: Optional[str] = None
    note: Optional[str] = None


# LLM Endpoints

@app.post("/investigate", response_model=InvestigationResponse)
async def investigate_change(request: InvestigationRequest):
    """
    Investigate a proposed change using LLM analysis.
    
    This endpoint uses LLM to analyze the impact of changes by:
    - Finding exact matches using literal search
    - Analyzing dependencies between files
    - Discovering semantically related code
    - Synthesizing findings into comprehensive impact report
    """
    logger.info(f"Received investigation request: '{request.query}'")
    
    try:
        # Get LLM provider
        llm_provider = await get_llm_provider()
        
        # Perform investigation
        result = await llm_provider.investigate_change(request.query)
        
        logger.info(f"Investigation completed for query: '{request.query}'")
        return InvestigationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error during investigation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/llm-health", response_model=LLMHealthResponse)
async def llm_health_check():
    """
    Perform health check on LLM service.
    
    Returns the status of:
    - LLM provider (mock, OpenAI, etc.)
    - API connectivity (for external providers)
    - Model availability
    """
    logger.info("Performing LLM health check")
    
    try:
        llm_provider = await get_llm_provider()
        health_result = await llm_provider.health_check()
        
        logger.info(f"LLM health check completed: {health_result.get('status', 'unknown')}")
        return LLMHealthResponse(**health_result)
        
    except Exception as e:
        logger.error(f"Error during LLM health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-investigate")
async def test_investigate():
    """Test endpoint for LLM investigation"""
    test_request = InvestigationRequest(
        query="What happens if we change term_sheet_id from string to UUID?",
        use_mock=True
    )
    
    return await investigate_change(test_request)

