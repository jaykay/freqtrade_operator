"""Git synchronization utilities for strategy repositories."""

from typing import Any


def create_git_sync_container(
    strategy_config: dict[str, Any],
    volume_name: str = "strategies",
    sync_interval: int = 60,
) -> dict[str, Any]:
    """Create a git-sync sidecar container specification.

    Args:
        strategy_config: Strategy configuration from FreqtradeBot spec
        volume_name: Name of the volume to mount
        sync_interval: Sync interval in seconds

    Returns:
        Container specification dict
    """
    git_repo = strategy_config["gitRepository"]
    url = git_repo["url"]
    branch = git_repo.get("branch", "main")

    container = {
        "name": f"git-sync-{strategy_config['name']}",
        "image": "registry.k8s.io/git-sync/git-sync:v4.0.0",
        "args": [
            f"--repo={url}",
            f"--branch={branch}",
            f"--period={sync_interval}s",
            "--depth=1",
            f"--root=/strategies/{strategy_config['name']}",
            "--link=current",
        ],
        "volumeMounts": [
            {
                "name": volume_name,
                "mountPath": "/strategies",
            }
        ],
        "resources": {
            "requests": {
                "cpu": "10m",
                "memory": "32Mi",
            },
            "limits": {
                "cpu": "50m",
                "memory": "64Mi",
            },
        },
    }

    # Add SSH key if specified
    ssh_key_secret = git_repo.get("sshKeySecret")
    if ssh_key_secret:
        container["env"] = [
            {
                "name": "GIT_SYNC_SSH",
                "value": "true",
            }
        ]
        container["volumeMounts"].append(
            {
                "name": "git-ssh-key",
                "mountPath": "/etc/git-secret",
                "readOnly": True,
            }
        )
        container["args"].append("--ssh-key-file=/etc/git-secret/ssh-privatekey")

    return container


def create_ssh_key_volume(secret_name: str) -> dict[str, Any]:
    """Create a volume for SSH private key.

    Args:
        secret_name: Name of the secret containing the SSH key

    Returns:
        Volume specification dict
    """
    return {
        "name": "git-ssh-key",
        "secret": {
            "secretName": secret_name,
            "defaultMode": 0o400,
        },
    }
