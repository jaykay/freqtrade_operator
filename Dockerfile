# Use a Python image with uv
FROM ghcr.io/astral-sh/uv:python3.11-slim AS builder

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a multi-stage build
ENV UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first to leverage Docker cache
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy the rest of the source code
COPY . .

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/src

# Copy source code (optional if already in .venv as editable, but better for clarity)
COPY src/ /app/src/

# Create non-root user (using existing operator group)
# Note: we don't need to copy the operator group if it's already in the base image,
# but python:slim doesn't have it by default.
RUN groupadd -g 1000 operator || true && \
    useradd -m -u 1000 -g 1000 operator && \
    chown -R operator:operator /app

USER operator

# Run the operator
CMD ["kopf", "run", "--all-namespaces", "--liveness=http://0.0.0.0:8080/healthz", "/app/src/freqtrade_operator/main.py"]
