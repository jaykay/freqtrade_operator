> [!CAUTION]
> **DISCLAIMER: FOR DEMONSTRATION PURPOSES ONLY**
> 
> This software is provided for educational and demonstration purposes only. It is **NOT** intended for production trading with real money.
> 
> Trading cryptocurrencies involves significant risk and can result in the loss of your capital. You should not invest more than you can afford to lose and you should ensure that you fully understand the risks involved.
> 
> The authors and contributors of this project accept **NO RESPONSIBILITY** for any financial losses, damages, or legal consequences resulting from the use of this software. By using this software, you agree that you are solely responsible for your own trading decisions and actions.
> 
> **USE AT YOUR OWN RISK.**

# Freqtrade Operator

A Kubernetes operator for managing [Freqtrade](https://www.freqtrade.io/) trading bot instances with centralized management, automated strategy synchronization, and comprehensive observability.

## Features

- 🤖 **Multi-Bot Management**: Deploy and manage multiple Freqtrade instances declaratively
- 🌐 **Centralized UI**: Single FreqUI webserver for monitoring all bots
- 🔄 **Strategy Sync**: Automatic synchronization from private Git repositories
- 📊 **Backtesting**: Run backtests via Kubernetes Jobs
- 📈 **Observability**: Full OpenTelemetry integration (metrics, traces, logs)
- 🔒 **Security**: Proper RBAC, secrets management, non-root containers
- 💾 **PostgreSQL**: CloudNativePG integration with S3 backups
- 🚀 **GitOps Ready**: ArgoCD deployment with custom health checks

## Quick Start

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3

### Installation

1. **Install CRDs**:
```bash
kubectl apply -f deploy/crds/
```

2. **Deploy operator** (via Helm):
```bash
helm install freqtrade-operator charts/freqtrade-operator \
  --create-namespace \
  --namespace freqtrade-system
```

3. **Deploy a trading bot**:
```bash
kubectl apply -f docs/examples/simple-bot.yaml
```

4. **Check status**:
```bash
kubectl get freqtradebots -n freqtrade-bots
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                                                              │
│  ┌────────────────┐        ┌──────────────────────────┐    │
│  │ Freqtrade      │        │  FreqtradeWebserver      │    │
│  │ Operator       │───────▶│  (FreqUI)                │    │
│  │ (Kopf)         │        │  - Ingress               │    │
│  └────────────────┘        │  - Service               │    │
│         │                   └──────────────────────────┘    │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────┐          │
│  │ FreqtradeBot Instances                        │          │
│  │  ┌─────────────────────────────────────┐     │          │
│  │  │ Bot Pod                              │     │          │
│  │  │  ┌──────────────────┐               │     │          │
│  │  │  │ Freqtrade        │               │     │          │
│  │  │  │ Container        │               │     │          │
│  │  │  └──────────────────┘               │     │          │
│  │  │  ┌──────────────────┐               │     │          │
│  │  │  │ Git-Sync         │               │     │          │
│  │  │  │ Sidecar          │◀─── Strategy │     │          │
│  │  │  │                  │      Repo     │     │          │
│  │  │  └──────────────────┘               │     │          │
│  │  └─────────────────────────────────────┘     │          │
│  │                    │                          │          │
│  │                    ▼                          │          │
│  │  ┌─────────────────────────────────────┐     │          │
│  │  │ PostgreSQL (CloudNativePG)          │     │          │
│  │  │  - Per-instance databases           │     │          │
│  │  │  - S3 backup                        │     │          │
│  │  └─────────────────────────────────────┘     │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Custom Resources

### FreqtradeBot

Manages a single Freqtrade trading bot instance.

```yaml
apiVersion: trading.freqtrade.io/v1alpha1
kind: FreqtradeBot
metadata:
  name: my-bot
spec:
  exchange:
    name: binance
    dryRun: true  # Paper trading mode
  stake:
    currency: USDT
    amount: "100"
  strategies:
    - name: my-strategy
      gitRepository:
        url: https://github.com/user/strategies.git
        path: strategies/MyStrategy.py
```

### FreqtradeWebserver

Manages the centralized FreqUI instance.

```yaml
apiVersion: trading.freqtrade.io/v1alpha1
kind: FreqtradeWebserver
metadata:
  name: trading-ui
spec:
  ingress:
    host: freqtrade.example.com
    tls: true
```

See [docs/examples/](docs/examples/) for complete examples.

## Development

### Local Development with Tilt

1. **Start kind cluster**:
```bash
kind create cluster --config kind-config.yaml
```

2. **Start Tilt**:
```bash
tilt up
```

3. **Deploy example bot**:
```bash
kubectl apply -f docs/examples/simple-bot.yaml
```

### Manual Development

1. **Install dependencies**:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

2. **Apply CRDs**:
```bash
kubectl apply -f deploy/crds/
```

3. **Run operator locally**:
```bash
kopf run src/operator/main.py --verbose
```

## Configuration

### Environment Variables

- `WATCH_NAMESPACE`: Limit operator to specific namespace (default: all namespaces)
- `OTLP_ENDPOINT`: OpenTelemetry collector endpoint for observability

### Database Setup

The operator requires a CloudNativePG cluster named `freqtrade-db` in the target namespace:

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: freqtrade-db
spec:
  instances: 3
  storage:
    size: 10Gi
  backup:
    barmanObjectStore:
      destinationPath: s3://my-bucket/freqtrade-backups
      s3Credentials:
        accessKeyId:
          name: s3-credentials
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: s3-credentials
          key: ACCESS_SECRET_KEY
```

## Examples

### Multi-Strategy Bot

Deploy a bot with multiple strategies from a private Git repository:

```bash
kubectl apply -f docs/examples/multi-strategy-bot.yaml
```

### Production Setup

Deploy with webserver and ingress:

```bash
kubectl apply -f docs/examples/production-setup.yaml
```

## Observability

The operator integrates with OpenTelemetry for comprehensive observability:

- **Metrics**: Bot lifecycle events, reconciliation duration, active bots
- **Traces**: Distributed tracing for operator actions
- **Logs**: Structured logging with trace correlation

Configure OTLP endpoint:
```bash
helm upgrade freqtrade-operator charts/freqtrade-operator \
  --set otel.endpoint=http://otel-collector:4317
```

## Security

- Non-root containers with security contexts
- Secrets for API keys and JWT tokens
- RBAC with minimal required permissions
- SSH key support for private Git repositories
- TLS for ingress with cert-manager integration

## Backup & Restore

Backups are managed by CloudNativePG with S3 storage:

```yaml
backup:
  barmanObjectStore:
    destinationPath: s3://bucket/path
    wal:
      compression: gzip
    schedule: "0 0 * * *"  # Daily at midnight
    retentionPolicy: "30d"
```

Point-in-time recovery (PITR) is supported.

## Troubleshooting

### Bot not starting

Check operator logs:
```bash
kubectl logs -n freqtrade-system deployment/freqtrade-operator
```

Check bot pod:
```bash
kubectl describe pod -n freqtrade-bots <bot-pod-name>
kubectl logs -n freqtrade-bots <bot-pod-name> -c freq trade
```

### Strategy not syncing

Check git-sync sidecar:
```bash
kubectl logs -n freqtrade-bots <bot-pod-name> -c git-sync-<strategy-name>
```

### Database connection issues

Verify CloudNativePG cluster:
```bash
kubectl get cluster -n freqtrade-bots freqtrade-db
kubectl get database -n freqtrade-bots
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Resources

- [Freqtrade Documentation](https://www.freqtrade.io/)
- [Kopf Framework](https://kopf.readthedocs.io/)
- [CloudNativePG](https://cloudnative-pg.io/)
- [Operator Best Practices](https://operatorframework.io/operator-capabilities/)
