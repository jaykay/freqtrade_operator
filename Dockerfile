# Multi-stage Dockerfile for Freqtrade Operator
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY src/ /app/src/

# Create non-root user (using existing operator group)
RUN useradd -m -u 1000 -g operator operator && \
    chown -R operator:operator /app

# Set PYTHONPATH so 'operator' package imports work
ENV PYTHONPATH=/app/src

USER operator

# Run the operator
CMD ["kopf", "run", "--all-namespaces", "--liveness=http://0.0.0.0:8080/healthz", "/app/src/freqtrade_operator/main.py"]
