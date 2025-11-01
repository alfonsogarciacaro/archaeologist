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

# Expose port
EXPOSE 8000

# For development: use reload and serve frontend dev server
# For production: serve static files and API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]