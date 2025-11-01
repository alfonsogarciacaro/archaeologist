"""
Shared telemetry configuration and initialization for Enterprise Code Archaeologist.
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
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

logger = logging.getLogger(__name__)


class TelemetryConfig:
    """Manages OpenTelemetry configuration for the application."""
    
    def __init__(self, settings):
        self.settings = settings
        self._initialized = False
    
    def is_enabled(self):
        """Check if telemetry is enabled using standard OTEL environment variables."""
        # Standard OTEL SDK way to disable telemetry
        if os.getenv("OTEL_SDK_DISABLED") == "true":
            return False
        
        # Also check if exporter endpoint is not set
        if not self.settings.OTEL_EXPORTER_OTLP_ENDPOINT:
            return False
            
        return True
    
    def initialize_telemetry(self):
        """Initialize OpenTelemetry tracing and metrics."""
        if self._initialized:
            return
        
        if not self.is_enabled():
            logger.info("OpenTelemetry disabled: OTEL_SDK_DISABLED=true or OTEL_EXPORTER_OTLP_ENDPOINT not set")
            self._initialized = True
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
            # Don't fail the application if telemetry fails
            self._initialized = True
    
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
        if not self.is_enabled():
            logger.info("FastAPI instrumentation disabled: telemetry disabled")
            return
            
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument FastAPI: {e}")
    
    def instrument_httpx(self):
        """Instrument HTTPX client for automatic tracing."""
        if not self.is_enabled():
            logger.info("HTTPX instrumentation disabled: telemetry disabled")
            return
            
        try:
            HTTPXClientInstrumentor().instrument()
            logger.info("HTTPX instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument HTTPX: {e}")
    
    def instrument_requests(self):
        """Instrument requests library for automatic tracing."""
        if not self.is_enabled():
            logger.info("Requests instrumentation disabled: telemetry disabled")
            return
            
        try:
            RequestsInstrumentor().instrument()
            logger.info("Requests instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument requests: {e}")


# Global telemetry instance
_telemetry_config = None


def get_telemetry_config(settings=None):
    """Get or create global telemetry configuration."""
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
    _config = get_telemetry_config()
    if _config and _config.is_enabled():
        if name:
            return trace.get_tracer(name)
        return trace.get_tracer(__name__)
    else:
        # Return a no-op tracer when telemetry is disabled
        return NoOpTracer()


def get_meter(name: str = None):
    """Get a meter instance."""
    _config = get_telemetry_config()
    if _config and _config.is_enabled():
        if name:
            return metrics.get_meter(name)
        return metrics.get_meter(__name__)
    else:
        # Return a no-op meter when telemetry is disabled
        return NoOpMeter()


class NoOpTracer:
    """No-op tracer that does nothing when telemetry is disabled."""
    
    def start_as_current_span(self, name, **kwargs):
        return NoOpSpan()
    
    def start_span(self, name, **kwargs):
        return NoOpSpan()


class NoOpSpan:
    """No-op span that does nothing when telemetry is disabled."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def set_attribute(self, key, value):
        pass
    
    def set_status(self, status):
        pass
    
    def set_error(self, exception):
        pass
    
    def record_exception(self, exception):
        pass


class NoOpMeter:
    """No-op meter that does nothing when telemetry is disabled."""
    
    def create_counter(self, name, **kwargs):
        return NoOpCounter()
    
    def create_histogram(self, name, **kwargs):
        return NoOpHistogram()
    
    def create_up_down_counter(self, name, **kwargs):
        return NoOpUpDownCounter()


class NoOpCounter:
    """No-op counter that does nothing when telemetry is disabled."""
    
    def add(self, amount, **kwargs):
        pass


class NoOpHistogram:
    """No-op histogram that does nothing when telemetry is disabled."""
    
    def record(self, amount, **kwargs):
        pass


class NoOpUpDownCounter:
    """No-op up-down counter that does nothing when telemetry is disabled."""
    
    def add(self, amount, **kwargs):
        pass