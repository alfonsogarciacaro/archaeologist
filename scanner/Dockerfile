# Must be run with root dir as path context

ARG CONTAINER_REGISTRY
FROM ${CONTAINER_REGISTRY}/ubi9/python-311

WORKDIR /app

# Install system dependencies
RUN dnf update -y && dnf install -y \
    gcc \
    ripgrep \
    curl \
    && dnf clean all

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy scanner requirements for better caching
COPY scanner/pyproject.toml scanner/uv.lock ./
RUN /root/.cargo/bin/uv pip sync uv.lock

# Copy scanner application code (excluding tests for production)
COPY scanner/app .

EXPOSE 8000

CMD gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
