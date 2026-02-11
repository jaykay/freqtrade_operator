"""Backtest job creation utilities."""

from typing import Any


def create_backtest_job(
    name: str,
    namespace: str,
    bot_name: str,
    strategy_name: str,
    timerange: str,
    owner_references: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create a Kubernetes Job for backtesting.
    
    Args:
        name: Job name
        namespace: Namespace
        bot_name: FreqtradeBot instance name
        strategy_name: Strategy to backtest
        timerange: Timerange for backtest (e.g., "20230101-20230201")
        owner_references: Owner references
    
    Returns:
        Job resource dict
    """
    return {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "app": "freqtrade-backtest",
                "bot": bot_name,
            },
            "ownerReferences": owner_references,
        },
        "spec": {
            "ttlSecondsAfterFinished": 3600,  # Clean up after 1 hour
            "template": {
                "metadata": {
                    "labels": {
                        "app": "freqtrade-backtest",
                        "bot": bot_name,
                    }
                },
                "spec": {
                    "restartPolicy": "Never",
                    "containers": [
                        {
                            "name": "backtest",
                            "image": "freqtradeorg/freqtrade:stable",
                            "command": ["freqtrade"],
                            "args": [
                                "backtesting",
                                "--config", "/config/config.json",
                                "--strategy", strategy_name,
                                "--timerange", timerange,
                                "--strategy-path", "/strategies",
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
                                    "name": "results",
                                    "mountPath": "/freqtrade/user_data/backtest_results",
                                },
                            ],
                            "resources": {
                                "requests": {
                                    "cpu": "500m",
                                    "memory": "1Gi",
                                },
                                "limits": {
                                    "cpu": "2000m",
                                    "memory": "2Gi",
                                },
                            },
                        }
                    ],
                    "volumes": [
                        {
                            "name": "config",
                            "configMap": {
                                "name": f"{bot_name}-config",
                            },
                        },
                        {
                            "name": "strategies",
                            "emptyDir": {},
                        },
                        {
                            "name": "results",
                            "emptyDir": {},
                        },
                    ],
                },
            },
        },
    }
