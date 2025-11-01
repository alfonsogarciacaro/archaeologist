FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Node.js for frontend builds
RUN apt-get update && apt-get install -y \
    gcc \
    ripgrep \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18.x
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

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