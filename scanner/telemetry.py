"""
Telemetry configuration and initialization for the Scanner service.
"""
import os
import logging
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.semantic_conventions import ResourceAttributes
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

logger = logging.getLogger(__name__)


class TelemetryConfig:
    """Manages OpenTelemetry configuration for the scanner service."""
    
    def __init__(self, settings):
        self.settings = settings
        self._initialized = False
    
    def initialize_telemetry(self):
        """Initialize OpenTelemetry tracing and metrics."""
        if self._initialized:
            return
        
        try:
            # Create resource with service information
            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: self.settings.OTEL_SERVICE_NAME,
                ResourceAttributes.SERVICE_VERSION: self.settings.OTEL_SERVICE_VERSION,
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.settings.NODE_ENV,
            })
            
            # Initialize Tracing
            self._initialize_tracing(resource)
            
            # Initialize Metrics
            self._initialize_metrics(resource)
            
            self._initialized = True
            logger.info(f"Telemetry initialized for service: {self.settings.OTEL_SERVICE_NAME}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize telemetry: {e}")
    
    def _initialize_tracing(self, resource: Resource):
        """Initialize distributed tracing."""
        # Create OTLP Span Exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=self.settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            insecure=True  # Set to False in production with proper TLS
        )
        
        # Create TracerProvider with resource
        trace.set_tracer_provider(TracerProvider(resource=resource))
        
        # Add OTLP exporter to tracer provider
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
    
    def _initialize_metrics(self, resource: Resource):
        """Initialize metrics collection."""
        # Create OTLP Metric Exporter
        otlp_metric_exporter = OTLPMetricExporter(
            endpoint=self.settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            insecure=True  # Set to False in production with proper TLS
        )
        
        # Create periodic metric reader
        metric_reader = PeriodicExportingMetricReader(
            exporter=otlp_metric_exporter,
            export_interval_millis=30000  # Export every 30 seconds
        )
        
        # Create and set MeterProvider
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)
    
    def instrument_fastapi(self, app):
        """Instrument FastAPI application for automatic tracing."""
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument FastAPI: {e}")
    
    def instrument_requests(self):
        """Instrument requests library for automatic tracing."""
        try:
            RequestsInstrumentor().instrument()
            logger.info("Requests instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument requests: {e}")


# Global telemetry instance
_telemetry_config = None


def get_telemetry_config(settings=None):
    """Get or create the global telemetry configuration."""
    global _telemetry_config
    if _telemetry_config is None and settings is not None:
        _telemetry_config = TelemetryConfig(settings)
    return _telemetry_config


def initialize_telemetry(settings):
    """Initialize telemetry with provided settings."""
    telemetry_config = get_telemetry_config(settings)
    telemetry_config.initialize_telemetry()
    return telemetry_config


def get_tracer(name: str = None):
    """Get a tracer instance."""
    if name:
        return trace.get_tracer(name)
    return trace.get_tracer(__name__)


def get_meter(name: str = None):
    """Get a meter instance."""
    if name:
        return metrics.get_meter(name)
    return metrics.get_meter(__name__)