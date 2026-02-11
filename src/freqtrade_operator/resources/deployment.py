"""Deployment resource generation for Freqtrade bots."""

from typing import Any

from freqtrade_operator.utils.git_sync import create_git_sync_container, create_ssh_key_volume


def create_deployment(
    name: str,
    namespace: str,
    spec: dict[str, Any],
    api_port: int,
    owner_references: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create Deployment resource for a Freqtrade bot.

    Args:
        name: Bot instance name
        namespace: Namespace
        spec: FreqtradeBot spec
        api_port: Assigned API server port
        owner_references: Owner references for garbage collection

    Returns:
        Deployment resource dict
    """
    exchange_config = spec["exchange"]
    resources = spec.get("resources", {})
    strategies = spec.get("strategies", [])

    # Build containers
    containers = [
        {
            "name": "freqtrade",
            "image": "freqtradeorg/freqtrade:stable",
            "command": ["freqtrade"],
            "args": [
                "trade",
                "--config",
                "/config/config.json",
                "--strategy-path",
                "/strategies",
            ],
            "env": [
                {
                    "name": "EXCHANGE_API_KEY",
                    "valueFrom": {
                        "secretKeyRef": {
                            "name": exchange_config.get("apiKeySecret", f"{name}-exchange"),
                            "key": "api-key",
                            "optional": True,
                        }
                    },
                },
                {
                    "name": "EXCHANGE_API_SECRET",
                    "valueFrom": {
                        "secretKeyRef": {
                            "name": exchange_config.get("apiKeySecret", f"{name}-exchange"),
                            "key": "api-secret",
                            "optional": True,
                        }
                    },
                },
                {
                    "name": "API_USERNAME",
                    "value": "freqtrade",
                },
                {
                    "name": "API_PASSWORD",
                    "valueFrom": {
                        "secretKeyRef": {
                            "name": f"{name}-api",
                            "key": "password",
                        }
                    },
                },
                {
                    "name": "JWT_SECRET_KEY",
                    "valueFrom": {
                        "secretKeyRef": {
                            "name": f"{name}-api",
                            "key": "jwt-secret",
                        }
                    },
                },
            ],
            "ports": [
                {
                    "name": "api",
                    "containerPort": api_port,
                    "protocol": "TCP",
                }
            ],
            "volumeMounts": [
                {
                    "name": "config",
                    "mountPath": "/config",
                },
                {
                    "name": "strategies",
                    "mountPath": "/strategies",
                },
                {
                    "name": "data",
                    "mountPath": "/freqtrade/user_data",
                },
            ],
            "livenessProbe": {
                "httpGet": {
                    "path": "/api/v1/ping",
                    "port": api_port,
                },
                "initialDelaySeconds": 30,
                "periodSeconds": 10,
            },
            "readinessProbe": {
                "httpGet": {
                    "path": "/api/v1/ping",
                    "port": api_port,
                },
                "initialDelaySeconds": 10,
                "periodSeconds": 5,
            },
            "resources": resources,
        }
    ]

    # Add git-sync sidecar for each strategy
    for strategy in strategies:
        git_sync_container = create_git_sync_container(strategy, volume_name="strategies")
        containers.append(git_sync_container)

    # Build volumes
    volumes = [
        {
            "name": "config",
            "configMap": {
                "name": f"{name}-config",
            },
        },
        {
            "name": "strategies",
            "emptyDir": {},
        },
        {
            "name": "data",
            "emptyDir": {},
        },
    ]

    # Add SSH key volume if any strategy uses it
    for strategy in strategies:
        ssh_key_secret = strategy.get("gitRepository", {}).get("sshKeySecret")
        if ssh_key_secret:
            volumes.append(create_ssh_key_volume(ssh_key_secret))
            break  # Only need one SSH key volume

    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "app": "freqtrade",
                "bot": name,
            },
            "ownerReferences": owner_references,
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": "freqtrade",
                    "bot": name,
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "freqtrade",
                        "bot": name,
                    },
                    "annotations": {
                        "prometheus.io/scrape": "true",
                        "prometheus.io/port": str(api_port),
                        "prometheus.io/path": "/api/v1/metrics",
                    },
                },
                "spec": {
                    "containers": containers,
                    "volumes": volumes,
                    "securityContext": {
                        "fsGroup": 1000,
                        "runAsNonRoot": True,
                        "runAsUser": 1000,
                    },
                },
            },
        },
    }
