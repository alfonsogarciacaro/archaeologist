"""
Automatic tracing middleware for FastAPI applications.
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from dependencies.telemetry import get_tracer


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware that automatically traces all HTTP requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        tracer = get_tracer("middleware")
        
        # Create span with HTTP method and path
        span_name = f"{request.method} {request.url.path}"
        with tracer.start_as_current_span(span_name) as span:
            # Add standard HTTP attributes
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.scheme", request.url.scheme)
            span.set_attribute("http.host", request.url.hostname or "")
            span.set_attribute("http.target", request.url.path)
            if request.url.port:
                span.set_attribute("http.port", request.url.port)
            
            # Add user agent if available
            user_agent = request.headers.get("user-agent")
            if user_agent:
                span.set_attribute("http.user_agent", user_agent)
            
            # Add content length if available
            content_length = request.headers.get("content-length")
            if content_length:
                span.set_attribute("http.request_content_length", int(content_length))
            
            # Process request and measure time
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Add response attributes
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response_content_length", len(response.body) if hasattr(response, 'body') else 0)
            span.set_attribute("http.server.duration", process_time)
            
            # Set status based on response code
            if response.status_code >= 400:
                span.set_attribute("error", True)
                span.set_attribute("error.type", "http_error")
            
            return response