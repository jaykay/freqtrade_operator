"""Main entry point for the Freqtrade Kubernetes Operator."""

import logging
import os

import kopf
from kubernetes import config

from freqtrade_operator.observability.otel import create_operator_metrics, setup_opentelemetry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Kubernetes client
try:
    config.load_incluster_config()
    logger.info("Loaded in-cluster Kubernetes configuration")
except config.ConfigException:
    config.load_kube_config()
    logger.info("Loaded kubeconfig configuration")

# Initialize OpenTelemetry
otlp_endpoint = os.getenv("OTLP_ENDPOINT")
tracer, meter = setup_opentelemetry(
    service_name="freqtrade-operator",
    otlp_endpoint=otlp_endpoint,
)
metrics = create_operator_metrics(meter)


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_: object) -> None:
    """Configure operator settings on startup."""
    settings.persistence.finalizer = "freqtrade-operator/finalizer"
    settings.posting.level = logging.INFO

    # Watch all namespaces by default
    namespace = os.getenv("WATCH_NAMESPACE")
    if namespace:
        settings.watching.client_timeout = 600
        logger.info(f"Watching namespace: {namespace}")
    else:
        logger.info("Watching all namespaces")

    logger.info("Freqtrade Operator started successfully")


@kopf.on.probe(id="health")
def health_check(**_: object) -> dict[str, str]:
    """Health check endpoint for liveness probe."""
    return {"status": "healthy"}


# Import handlers to register them with Kopf
# These imports must come after the kopf setup above
from freqtrade_operator.handlers import freqtradebot, webserver  # noqa: E402, F401

logger.info("All handlers registered")
