"""FreqtradeWebserver resource handlers."""

import logging
from typing import Any

import kopf
from kubernetes import client

logger = logging.getLogger(__name__)


@kopf.on.create("trading.freqtrade.io", "v1alpha1", "freqtradewebservers")
def create_webserver(
    spec: dict[str, Any],
    name: str,
    namespace: str,
    meta: dict[str, Any],
    **kwargs: object,
) -> dict[str, str]:
    """Handle FreqtradeWebserver creation."""
    logger.info(f"Creating FreqtradeWebserver: {namespace}/{name}")

    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()
    networking_v1 = client.NetworkingV1Api()

    ingress_spec = spec["ingress"]

    # Create deployment for FreqUI
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name=f"{name}-frequi",
            namespace=namespace,
            owner_references=[
                client.V1OwnerReference(
                    api_version="trading.freqtrade.io/v1alpha1",
                    kind="FreqtradeWebserver",
                    name=name,
                    uid=meta["uid"],
                    controller=True,
                    block_owner_deletion=True,
                )
            ],
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(
                match_labels={"app": "freqtrade-webserver", "instance": name}
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={"app": "freqtrade-webserver", "instance": name}
                ),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="frequi",
                            image="freqtradeorg/freqtrade:stable_freqaiui",
                            ports=[
                                client.V1ContainerPort(
                                    container_port=80,
                                    name="http",
                                )
                            ],
                            resources=spec.get("resources", {}),
                        )
                    ]
                ),
            ),
        ),
    )
    apps_v1.create_namespaced_deployment(namespace, deployment)
    logger.info(f"Created FreqUI deployment for {name}")

    # Create service
    service = client.V1Service(
        metadata=client.V1ObjectMeta(
            name=name,
            namespace=namespace,
            owner_references=[
                client.V1OwnerReference(
                    api_version="trading.freqtrade.io/v1alpha1",
                    kind="FreqtradeWebserver",
                    name=name,
                    uid=meta["uid"],
                    controller=True,
                    block_owner_deletion=True,
                )
            ],
        ),
        spec=client.V1ServiceSpec(
            selector={"app": "freqtrade-webserver", "instance": name},
            ports=[
                client.V1ServicePort(
                    name="http",
                    port=80,
                    target_port=80,
                )
            ],
        ),
    )
    core_v1.create_namespaced_service(namespace, service)
    logger.info(f"Created service for {name}")

    # Create ingress
    ingress = client.V1Ingress(
        metadata=client.V1ObjectMeta(
            name=name,
            namespace=namespace,
            annotations=ingress_spec.get("annotations", {}),
            owner_references=[
                client.V1OwnerReference(
                    api_version="trading.freqtrade.io/v1alpha1",
                    kind="FreqtradeWebserver",
                    name=name,
                    uid=meta["uid"],
                    controller=True,
                    block_owner_deletion=True,
                )
            ],
        ),
        spec=client.V1IngressSpec(
            rules=[
                client.V1IngressRule(
                    host=ingress_spec["host"],
                    http=client.V1HTTPIngressRuleValue(
                        paths=[
                            client.V1HTTPIngressPath(
                                path="/",
                                path_type="Prefix",
                                backend=client.V1IngressBackend(
                                    service=client.V1IngressServiceBackend(
                                        name=name,
                                        port=client.V1ServiceBackendPort(number=80),
                                    )
                                ),
                            )
                        ]
                    ),
                )
            ],
            tls=[
                client.V1IngressTLS(
                    hosts=[ingress_spec["host"]],
                    secret_name=ingress_spec.get("tlsSecretName", f"{name}-tls"),
                )
            ]
            if ingress_spec.get("tls", True)
            else None,
        ),
    )
    networking_v1.create_namespaced_ingress(namespace, ingress)
    logger.info(f"Created ingress for {name}")

    # Build URL
    protocol = "https" if ingress_spec.get("tls", True) else "http"
    url = f"{protocol}://{ingress_spec['host']}"

    return {"message": f"FreqtradeWebserver {name} created", "url": url}


@kopf.on.delete("trading.freqtrade.io", "v1alpha1", "freqtradewebservers")
def delete_webserver(
    name: str,
    namespace: str,
    **kwargs: object,
) -> dict[str, str]:
    """Handle FreqtradeWebserver deletion."""
    logger.info(f"Deleting FreqtradeWebserver: {namespace}/{name}")
    return {"message": f"FreqtradeWebserver {name} deleted"}
