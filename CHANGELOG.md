# CHANGELOG


## v0.4.0 (2026-02-12)

### Features

- Persist user data with PVCs and bootstrap userdir via init container
  ([`7d7765c`](https://github.com/jaykay/freqtrade_operator/commit/7d7765c04c6970f4a83495d496c7905458c58281))

Replace emptyDir with a PersistentVolumeClaim for the user_data volume so data survives pod
  restarts. An init container runs `freqtrade create-userdir` to bootstrap the directory structure
  on first start. Adds an optional `storage` field to the CRD for configuring PVC size and
  storageClass.

Closes #4

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>


## v0.3.1 (2026-02-12)

### Bug Fixes

- Add explicit namespace to ServiceAccount and Deployment templates
  ([`c1f4349`](https://github.com/jaykay/freqtrade_operator/commit/c1f4349e96cf118c55042837c3ff5042e34c9574))

Helm template rendering does not inject namespace into resource metadata, causing the ServiceAccount
  to be created in the wrong namespace when deployed via Tilt or other template-based tools.

Closes #2


## v0.3.0 (2026-02-12)

### Features

- Use built-in SampleStrategy for simple-bot, make gitRepository optional
  ([`f2ee1ad`](https://github.com/jaykay/freqtrade_operator/commit/f2ee1ad639f8d4d3d3671175ab137ba87dd9cd28))

Make gitRepository optional in the strategy CRD so bots can use freqtrade's built-in strategies
  without a git-sync sidecar. The update handler now fully reconciles the ConfigMap and Deployment
  on spec changes.

Closes #1

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>


## v0.2.0 (2026-02-12)

### Bug Fixes

- Correct cache key syntax in docs workflow and update chart-release dependencies
  ([`963fe9d`](https://github.com/jaykay/freqtrade_operator/commit/963fe9d35ca2d28964c7e9b2ba8a4d8ebd901aa5))

### Features

- Enhance documentation workflow and dependencies for MkDocs
  ([`928de76`](https://github.com/jaykay/freqtrade_operator/commit/928de76a70b9de790efb5e9c1c7ae8b6d1f619c7))


## v0.1.0 (2026-02-12)

### Bug Fixes

- Make operator group and user creation idempotent in the Dockerfile.
  ([`70010e7`](https://github.com/jaykay/freqtrade_operator/commit/70010e7fe9baa3408d2c38710aacc6c5c1915d20))

- Remove build_command from semantic_release configuration in pyproject.toml
  ([`f62da68`](https://github.com/jaykay/freqtrade_operator/commit/f62da68c695c65ca551cc14f0ec90e122c745bf1))

- Update GitHub Actions workflow to use GH_TOKEN for authentication and set build_command to false
  in pyproject.toml
  ([`1fd14b9`](https://github.com/jaykay/freqtrade_operator/commit/1fd14b91226affc3170ad14215fe473e6e9081c6))

### Build System

- Update Docker builder base image to `bookworm-slim`.
  ([`0961e49`](https://github.com/jaykay/freqtrade_operator/commit/0961e490aa5a1232ff844ed71d5c85091e0a67df))

### Features

- Add MIT license and declare it in Chart.yaml.
  ([`1495d80`](https://github.com/jaykay/freqtrade_operator/commit/1495d807e5512082743ec9acb7e30957fbb40142))

- Add placeholder test files and refactor import order in `freqtradebot` and `main` modules.
  ([`32adb1d`](https://github.com/jaykay/freqtrade_operator/commit/32adb1ded1380373b2171c3c0f55e4005386edbb))

- Add python-semantic-release and related dependencies to project
  ([`d24eba7`](https://github.com/jaykay/freqtrade_operator/commit/d24eba7fec283f2f5a3ab7d11fd2fff45512dccf))

- Introduce Freqtrade Kubernetes operator with CRDs, resource handlers, and database integration.
  ([`694dafb`](https://github.com/jaykay/freqtrade_operator/commit/694dafb5deb72f5017b547afe325864570955471))

- Migrate to uv for dependency management and introduce pre-commit hooks, updating CI/CD workflows
  and project configuration accordingly.
  ([`53880c3`](https://github.com/jaykay/freqtrade_operator/commit/53880c3875bb0efc30758ce197def538981eedec))
