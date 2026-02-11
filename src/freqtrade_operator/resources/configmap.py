"""ConfigMap generation for Freqtrade configuration."""

import json
from typing import Any


def generate_freqtrade_config(
    name: str,
    namespace: str,
    spec: dict[str, Any],
    api_port: int,
    database_url: str,
) -> dict[str, Any]:
    """Generate Freqtrade configuration from FreqtradeBot spec.
    
    Args:
        name: Bot instance name
        namespace: Namespace
        spec: FreqtradeBot spec
        api_port: Assigned API server port
        database_url: PostgreSQL connection URL
    
    Returns:
        Complete Freqtrade configuration dict
    """
    exchange_config = spec["exchange"]
    stake_config = spec["stake"]
    strategies = spec.get("strategies", [])
    api_server_config = spec.get("apiServer", {})
    webhooks = spec.get("webhooks", [])
    
    # Build strategy list
    strategy_list = []
    for strategy in strategies:
        strategy_path = f"/strategies/{strategy['name']}/current/{strategy['gitRepository']['path']}"
        weight = strategy.get("weight", 1)
        for _ in range(weight):
            strategy_list.append(strategy_path)
    
    config = {
        "max_open_trades": 3,
        "stake_currency": stake_config["currency"],
        "stake_amount": stake_config["amount"],
        "tradable_balance_ratio": 0.99,
        "fiat_display_currency": "USD",
        "dry_run": exchange_config.get("dryRun", True),
        "cancel_open_orders_on_exit": False,
        
        # Pricing
        "entry_pricing": {
            "price_side": "same",
            "use_order_book": True,
            "order_book_top": 1,
            "price_last_balance": 0.0,
            "check_depth_of_market": {
                "enabled": False,
                "bids_to_ask_delta": 1,
            },
        },
        "exit_pricing": {
            "price_side": "same",
            "use_order_book": True,
            "order_book_top": 1,
        },

        # Exchange configuration
        "exchange": {
            "name": exchange_config["name"],
            "key": "${EXCHANGE_API_KEY}",
            "secret": "${EXCHANGE_API_SECRET}",
            "ccxt_config": {},
            "ccxt_async_config": {},
            "pair_whitelist": [],
            "pair_blacklist": [],
        },
        
        # Pairlists
        "pairlists": [
            {"method": "StaticPairList"},
        ],

        # Database
        "db_url": database_url,
        
        # Strategy
        "strategy_list": strategy_list,
        
        # API Server
        "api_server": {
            "enabled": api_server_config.get("enabled", True),
            "listen_ip_address": "0.0.0.0",
            "listen_port": api_port,
            "verbosity": api_server_config.get("verbosity", "info"),
            "username": "${API_USERNAME}",
            "password": "${API_PASSWORD}",
            "jwt_secret_key": "${JWT_SECRET_KEY}",
            "CORS_origins": [],
        },
        
        # Webhooks
        "webhook": {
            "enabled": len(webhooks) > 0,
            "webhooks": [
                {
                    "url": wh["url"],
                    "format": "json",
                    "events": wh.get("events", ["*"]),
                }
                for wh in webhooks
            ],
        },
    }
    
    return config


def create_configmap(
    name: str,
    namespace: str,
    spec: dict[str, Any],
    api_port: int,
    database_url: str,
    owner_references: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create ConfigMap resource for Freqtrade configuration.
    
    Args:
        name: Bot instance name
        namespace: Namespace
        spec: FreqtradeBot spec
        api_port: Assigned API server port
        database_url: Database connection URL
        owner_references: Owner references for garbage collection
    
    Returns:
        ConfigMap resource dict
    """
    config = generate_freqtrade_config(name, namespace, spec, api_port, database_url)
    
    return {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": f"{name}-config",
            "namespace": namespace,
            "labels": {
                "app": "freqtrade",
                "bot": name,
            },
            "ownerReferences": owner_references,
        },
        "data": {
            "config.json": json.dumps(config, indent=2),
        },
    }
