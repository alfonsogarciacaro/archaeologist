from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import subprocess
import json
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

app = FastAPI(title="Code Scanner Service", version="1.0.0")

# Add automatic tracing middleware
app.add_middleware(TracingMiddleware)

# Instrument FastAPI for additional automatic tracing
telemetry_config.instrument_fastapi(app)
telemetry_config.instrument_httpx()

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


@app.get("/test-scan")
async def test_scan():
    """Test endpoint to verify scanner works with mock data"""
    test_request = ScanRequest(
        query="term_sheet_id",
        paths=["/app/mock_enterprise"]
    )
    return await scan_code(test_request)