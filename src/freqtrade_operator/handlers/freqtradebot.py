"""FreqtradeBot resource handlers."""

import logging
import random
import string
from typing import Any

import kopf
from kubernetes import client
from kubernetes.client.rest import ApiException

from freqtrade_operator.resources.configmap import create_configmap
from freqtrade_operator.resources.database import (
    create_database,
    get_database_connection_string,
)
from freqtrade_operator.resources.deployment import create_deployment

logger = logging.getLogger(__name__)

# Port range for API servers (one unique port per bot)
API_PORT_BASE = 8080
API_PORT_MAX = 8180


def generate_random_secret(length: int = 32) -> str:
    """Generate a random secret string."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def assign_api_port(name: str) -> int:
    """Assign a unique API port based on bot name hash."""
    # Simple port assignment based on name hash
    name_hash = abs(hash(name))
    port_offset = name_hash % (API_PORT_MAX - API_PORT_BASE)
    return API_PORT_BASE + port_offset


@kopf.on.create("trading.freqtrade.io", "v1alpha1", "freqtradebots")
def create_freqtradebot(
    spec: dict[str, Any],
    name: str,
    namespace: str,
    meta: dict[str, Any],
    **kwargs: object,
) -> dict[str, str]:
    """Handle FreqtradeBot creation."""
    logger.info(f"Creating FreqtradeBot: {namespace}/{name}")

    # Check for operator dry-run mode
    if spec.get("dryRun", False):
        logger.info(f"Operator dry-run mode enabled for {name}, skipping deployment")
        return {"message": "Operator dry-run mode - validation only"}

    # Create Kubernetes API clients
    core_v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()

    # Owner reference for garbage collection
    owner_references = [
        {
            "apiVersion": "trading.freqtrade.io/v1alpha1",
            "kind": "FreqtradeBot",
            "name": name,
            "uid": meta["uid"],
            "controller": True,
            "blockOwnerDeletion": True,
        }
    ]

    try:
        # 1. Create API server secret
        api_secret_dict = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": f"{name}-api",
                "namespace": namespace,
            },
            "stringData": {
                "password": generate_random_secret(16),
                "jwt-secret": generate_random_secret(32),
            },
        }
        kopf.adopt(api_secret_dict, owner=kwargs.get("body"))
        core_v1.create_namespaced_secret(namespace=namespace, body=api_secret_dict)
        logger.info(f"Created API secret for {name}")

        # 2. Configure database
        db_config = spec.get("database", {})
        db_type = db_config.get("type", "sqlite")
        api_port = assign_api_port(name)

        if db_type == "postgresql":
            pg_config = db_config.get("postgresql", {})
            cluster_name = pg_config.get("clusterName", "freqtrade-db")
            database_name = name.replace("-", "_")

            db_resource = create_database(name, namespace, cluster_name, owner_references)
            custom_api = client.CustomObjectsApi()
            custom_api.create_namespaced_custom_object(
                group="postgresql.cnpg.io",
                version="v1",
                namespace=namespace,
                plural="databases",
                body=db_resource,
            )
            logger.info(f"Created database {database_name} for {name}")
            db_url = get_database_connection_string(cluster_name, namespace, database_name)
        else:
            db_url = "sqlite:////freqtrade/user_data/tradesv3.sqlite"
            logger.info(f"Using SQLite database for {name}")

        # 3. Create ConfigMap

        configmap_dict = create_configmap(name, namespace, spec, api_port, db_url, owner_references)
        kopf.adopt(configmap_dict, owner=kwargs.get("body"))

        core_v1.create_namespaced_config_map(
            namespace=namespace,
            body=configmap_dict,
        )
        logger.info(f"Created ConfigMap for {name}")

        # 4. Create PVC for user data persistence
        storage_config = spec.get("storage", {})
        pvc_dict = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": f"{name}-data",
                "namespace": namespace,
                "labels": {"app": "freqtrade", "bot": name},
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {
                    "requests": {
                        "storage": storage_config.get("size", "1Gi"),
                    }
                },
            },
        }
        if "storageClassName" in storage_config:
            pvc_dict["spec"]["storageClassName"] = storage_config["storageClassName"]
        kopf.adopt(pvc_dict, owner=kwargs.get("body"))
        core_v1.create_namespaced_persistent_volume_claim(namespace=namespace, body=pvc_dict)
        logger.info(f"Created PVC for {name}")

        # 5. Create Deployment using kopf.adopt for owner references
        deployment_dict = create_deployment(name, namespace, spec, api_port, owner_references)

        # Use kopf.adopt to set owner references properly
        kopf.adopt(deployment_dict, owner=kwargs.get("body"))

        # Create deployment using CustomObjectsApi to avoid object conversion issues
        apps_v1.create_namespaced_deployment(
            namespace=namespace,
            body=deployment_dict,
        )
        logger.info(f"Created Deployment for {name}")

        # 6. Create Service
        service_dict = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": name,
                "namespace": namespace,
                "labels": {"app": "freqtrade", "bot": name},
            },
            "spec": {
                "selector": {"app": "freqtrade", "bot": name},
                "ports": [
                    {
                        "name": "api",
                        "port": api_port,
                        "targetPort": api_port,
                        "protocol": "TCP",
                    }
                ],
                "type": "ClusterIP",
            },
        }
        kopf.adopt(service_dict, owner=kwargs.get("body"))
        core_v1.create_namespaced_service(namespace=namespace, body=service_dict)
        logger.info(f"Created Service for {name}")

        return {
            "message": f"FreqtradeBot {name} created successfully",
            "apiPort": str(api_port),
        }

    except ApiException as e:
        logger.error(f"Failed to create resources for {name}: {e}")
        raise kopf.PermanentError(f"Failed to create bot: {e}")


@kopf.on.update("trading.freqtrade.io", "v1alpha1", "freqtradebots")
def update_freqtradebot(
    spec: dict[str, Any],
    name: str,
    namespace: str,
    meta: dict[str, Any],
    old: dict[str, Any],
    new: dict[str, Any],
    **kwargs: object,
) -> dict[str, str]:
    """Handle FreqtradeBot updates by reconciling ConfigMap and Deployment."""
    logger.info(f"Updating FreqtradeBot: {namespace}/{name}")

    core_v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()

    owner_references = [
        {
            "apiVersion": "trading.freqtrade.io/v1alpha1",
            "kind": "FreqtradeBot",
            "name": name,
            "uid": meta["uid"],
            "controller": True,
            "blockOwnerDeletion": True,
        }
    ]

    api_port = assign_api_port(name)
    db_config = spec.get("database", {})
    db_type = db_config.get("type", "sqlite")

    if db_type == "postgresql":
        pg_config = db_config.get("postgresql", {})
        cluster_name = pg_config.get("clusterName", "freqtrade-db")
        database_name = name.replace("-", "_")
        db_url = get_database_connection_string(cluster_name, namespace, database_name)
    else:
        db_url = "sqlite:////freqtrade/user_data/tradesv3.sqlite"

    try:
        # Reconcile ConfigMap
        configmap_dict = create_configmap(name, namespace, spec, api_port, db_url, owner_references)
        kopf.adopt(configmap_dict, owner=kwargs.get("body"))
        core_v1.replace_namespaced_config_map(
            name=f"{name}-config",
            namespace=namespace,
            body=configmap_dict,
        )
        logger.info(f"Updated ConfigMap for {name}")

        # Reconcile Deployment
        deployment_dict = create_deployment(name, namespace, spec, api_port, owner_references)
        kopf.adopt(deployment_dict, owner=kwargs.get("body"))
        apps_v1.replace_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=deployment_dict,
        )
        logger.info(f"Updated Deployment for {name}")

    except ApiException as e:
        logger.error(f"Failed to update resources for {name}: {e}")
        raise kopf.TemporaryError(f"Failed to update bot: {e}", delay=15)

    return {"message": f"FreqtradeBot {name} updated"}


@kopf.on.delete("trading.freqtrade.io", "v1alpha1", "freqtradebots")
def delete_freqtradebot(
    name: str,
    namespace: str,
    **kwargs: object,
) -> dict[str, str]:
    """Handle FreqtradeBot deletion."""
    logger.info(f"Deleting FreqtradeBot: {namespace}/{name}")

    # Resources will be automatically deleted via owner references
    # We can add cleanup logic here if needed

    return {"message": f"FreqtradeBot {name} deleted"}


@kopf.on.field(
    "trading.freqtrade.io",
    "v1alpha1",
    "freqtradebots",
    field="status.phase",
)
def status_changed(
    old: str,
    new: str,
    name: str,
    namespace: str,
    **kwargs: object,
) -> None:
    """React to status phase changes."""
    logger.info(f"FreqtradeBot {namespace}/{name} status: {old} -> {new}")
