FROM ${CONTAINER_REGISTRY}/ubi9/python-311

WORKDIR /app

# Install system dependencies
RUN dnf update -y && dnf install -y \
    gcc \
    ripgrep \
    && dnf clean all

# Copy shared modules first
COPY shared/ ./shared/

# Copy scanner requirements for better caching
COPY scanner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy scanner application code (excluding tests for production)
COPY scanner/app .

# Copy mock enterprise data
COPY scanner/mock_enterprise/ ./mock_enterprise/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]