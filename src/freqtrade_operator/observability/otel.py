"""OpenTelemetry configuration and instrumentation for the operator."""

import logging
from typing import Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def setup_opentelemetry(
    service_name: str = "freqtrade-operator",
    otlp_endpoint: Optional[str] = None,
) -> tuple[trace.Tracer, metrics.Meter]:
    """Set up OpenTelemetry instrumentation.
    
    Args:
        service_name: Name of the service for telemetry
        otlp_endpoint: OTLP collector endpoint (if None, telemetry is disabled)
    
    Returns:
        Tuple of (tracer, meter) for creating spans and metrics
    """
    if not otlp_endpoint:
        logger.info("OTLP endpoint not configured, telemetry disabled")
        # Return no-op tracer and meter
        return trace.get_tracer(__name__), metrics.get_meter(__name__)
    
    # Create resource with service information
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "0.1.0",
    })
    
    # Set up tracing
    trace_provider = TracerProvider(resource=resource)
    trace_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)
    
    # Set up metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True),
        export_interval_millis=10000,  # Export every 10 seconds
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )
    metrics.set_meter_provider(meter_provider)
    
    logger.info(f"OpenTelemetry configured with endpoint: {otlp_endpoint}")
    
    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)
    
    return tracer, meter


def create_operator_metrics(meter: metrics.Meter) -> dict[str, metrics.Instrument]:
    """Create custom metrics for the operator.
    
    Args:
        meter: OpenTelemetry meter instance
    
    Returns:
        Dictionary of metric instruments
    """
    return {
        "bot_created": meter.create_counter(
            name="freqtrade_bot_created_total",
            description="Total number of FreqtradeBot resources created",
            unit="1",
        ),
        "bot_deleted": meter.create_counter(
            name="freqtrade_bot_deleted_total",
            description="Total number of FreqtradeBot resources deleted",
            unit="1",
        ),
        "bot_errors": meter.create_counter(
            name="freqtrade_bot_errors_total",
            description="Total number of bot errors",
            unit="1",
        ),
        "reconciliation_duration": meter.create_histogram(
            name="freqtrade_reconciliation_duration_seconds",
            description="Duration of reconciliation loop",
            unit="s",
        ),
        "active_bots": meter.create_up_down_counter(
            name="freqtrade_active_bots",
            description="Number of active trading bots",
            unit="1",
        ),
    }
