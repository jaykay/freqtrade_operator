"""Database resource utilities for CloudNativePG integration."""

from typing import Any


def create_database(
    name: str,
    namespace: str,
    cluster_name: str,
    owner_references: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create a Database resource for CloudNativePG.
    
    Args:
        name: Bot instance name
        namespace: Namespace
        cluster_name: CNPG cluster name
        owner_references: Owner references
    
    Returns:
        Database resource dict
    """
    return {
        "apiVersion": "postgresql.cnpg.io/v1",
        "kind": "Database",
        "metadata": {
            "name": f"{name}-db",
            "namespace": namespace,
            "labels": {
                "app": "freqtrade",
                "bot": name,
            },
            "ownerReferences": owner_references,
        },
        "spec": {
            "cluster": {
                "name": cluster_name,
            },
            "owner": "freqtrade",
            "name": name.replace("-", "_"),  # PostgreSQL naming convention
        },
    }


def get_database_connection_string(
    cluster_name: str,
    namespace: str,
    database_name: str,
    username: str = "freqtrade",
) -> str:
    """Generate PostgreSQL connection string.
    
    Args:
        cluster_name: CNPG cluster name
        namespace: Namespace
        database_name: Database name
        username: Database username
    
    Returns:
        Connection string with environment variable placeholders
    """
    # Use cluster service for connection
    host = f"{cluster_name}-rw.{namespace}.svc.cluster.local"
    port = 5432
    
    return f"postgresql://{username}:${{DB_PASSWORD}}@{host}:{port}/{database_name}"


def create_database_secret(
    name: str,
    namespace: str,
    cluster_name: str,
    owner_references: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create a secret for database credentials.
    
    Note: This creates a placeholder secret. The actual password
    should be injected from the CNPG cluster's app user secret.
    
    Args:
        name: Bot instance name
        namespace: Namespace
        cluster_name: CNPG cluster name
        owner_references: Owner references
    
    Returns:
        Secret resource dict
    """
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {
            "name": f"{name}-db",
            "namespace": namespace,
            "labels": {
                "app": "freqtrade",
                "bot": name,
            },
            "ownerReferences": owner_references,
        },
        "stringData": {
            "cluster": cluster_name,
            "database": name.replace("-", "_"),
            "username": "freqtrade",
            # Password will be synced from CNPG cluster secret
        },
    }
