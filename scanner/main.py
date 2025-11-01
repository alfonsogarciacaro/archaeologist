from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import subprocess
import json
import os
import logging

# Import telemetry
from telemetry import initialize_telemetry, get_tracer
from config import get_settings
from opentelemetry import trace

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings and initialize telemetry
settings = get_settings()
telemetry_config = initialize_telemetry(settings)

# Get tracer for manual instrumentation
tracer = get_tracer(__name__)

app = FastAPI(title="Code Scanner Service", version="1.0.0")

# Instrument FastAPI for automatic tracing
telemetry_config.instrument_fastapi(app)
telemetry_config.instrument_requests()

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
    with tracer.start_as_current_span("scan_code") as span:
        span.set_attribute("scan.query", request.query)
        span.set_attribute("scan.paths_count", len(request.paths))
        span.set_attribute("scan.service", "code-scanner")
        
        try:
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
            
            span.set_attribute("scan.matches_found", len(results))
            span.set_status(trace.Status(trace.StatusCode.OK))
            logger.info(f"Scan completed: {len(results)} matches found")

            return ScanResponse(
                results=results,
                total_matches=len(results)
            )
        
        except subprocess.TimeoutExpired:
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Search timed out"))
            span.set_attribute("scan.error", "timeout")
            raise HTTPException(status_code=408, detail="Search timed out")
        except Exception as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            span.set_attribute("scan.error", str(e))
            logger.error(f"Scan failed: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/test-scan")
async def test_scan():
    """Test endpoint to verify scanner works with mock data"""
    test_request = ScanRequest(
        query="term_sheet_id",
        paths=["/app/mock_enterprise"]
    )
    return await scan_code(test_request)