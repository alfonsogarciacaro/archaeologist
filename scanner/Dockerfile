# Must be run with root dir as path context

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

# Copy shared modules first
COPY shared/ ./shared/

# Copy scanner requirements for better caching
COPY scanner/pyproject.toml scanner/uv.lock ./
RUN /root/.cargo/bin/uv pip sync uv.lock

# Copy scanner application code (excluding tests for production)
COPY scanner/app .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]