# CHANGELOG


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
