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

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install frontend dependencies and build for production
COPY ui/package*.json ./ui/
RUN cd ui && npm install

# Copy application code
COPY . .

# Build frontend static files
RUN cd ui && npm run build

# Expose port
EXPOSE 8000

# For development: use reload and serve frontend dev server
# For production: serve static files and API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]