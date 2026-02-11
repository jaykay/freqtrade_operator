# Tiltfile for local development with kind

if k8s_context() != 'kind-freqtrade-dev':
  fail("failing early to avoid overwriting production cluster")


# Create namespaces
k8s_yaml('deploy/namespaces.yaml')

# if k8s_namespace() == 'default':
#   fail("failing early to avoid deployment in default ns")


# Load Kubernetes YAML
k8s_yaml('deploy/crds/freqtrade_v1alpha1.yaml')
k8s_yaml('deploy/crds/freqtrade_webserver_v1alpha1.yaml')

# Build operator image
docker_build(
    'freqtrade-operator',
    '.',
    dockerfile='Dockerfile',
    live_update=[
        sync('./src', '/app/src'),
        run('pip install -r requirements.txt', trigger='./requirements.txt'),
    ]
)

# Deploy operator
k8s_yaml(helm(
    'charts/freqtrade-operator',
    name='freqtrade-operator',
    namespace='freqtrade-system',
    set=[
        'image.repository=freqtrade-operator',
        'image.tag=latest',
        'image.pullPolicy=Never',
    ]
))


# Port forwards
k8s_resource(
    'freqtrade-operator',
    port_forwards=['8080:8080'],
    labels=['operator'],
)

# Optional: Load example bot for testing
# Uncomment to auto-deploy an example bot
k8s_yaml('docs/examples/simple-bot.yaml')
