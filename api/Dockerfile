# Must be run with root dir as path context

ARG CONTAINER_REGISTRY
FROM ${CONTAINER_REGISTRY}/ubi9/python-311

WORKDIR /app

# Install system dependencies including Node.js for frontend builds
RUN dnf update -y && dnf install -y \
    gcc \
    ripgrep \
    curl \
    && dnf clean all

# Install Node.js 18.x from NodeSource
RUN curl -fsSL https://rpm.nodesource.com/setup_18.x | bash - \
    && dnf install -y nodejs \
    && dnf clean all

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
COPY api/pyproject.toml api/uv.lock ./
RUN /root/.cargo/bin/uv pip sync uv.lock

# Install frontend dependencies and build for production
COPY ui/package*.json ./ui/
RUN cd ui && npm install

# Copy shared modules first
COPY shared/ ./shared/

# Copy application code (excluding tests for production)
COPY api/app/ ./app/
COPY ui/ ./ui/

# Build frontend static files
RUN cd ui && npm run build

EXPOSE 8000

CMD gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
