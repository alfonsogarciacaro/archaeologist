# Background Workers Deployment Guide

## Overview

The Archaeologist project uses Redis-based background workers to handle long-running tasks like file processing, RAG ingestion, and complex LLM analysis. This guide explains how background workers work and their deployment options.

## Current Architecture

### **Integrated Worker Model**
```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   API Service   │───▶│ Redis Queue  │───▶│ Background      │
│ (FastAPI)       │    │              │    │ Worker Process  │
│                 │    │ • Jobs       │    │ (Same Process)  │
│ • HTTP Endpoints│    │ • Priority   │    │                 │
│ • Job Creation  │    │ • Status     │    │ • File Process  │
│ • Status Checks │    │ • TTL        │    │ • RAG Ingest    │
│                 │    │             │    │ • LLM Analysis  │
│ ┌─────────────┐ │    └──────────────┘    └─────────────────┘
│ │Job Worker   │ │
│ │(async task) │ │
│ └─────────────┘ │
└─────────────────┘
```

## How Background Workers Work

### **1. Job Creation**
- API endpoints create jobs for long-running operations
- Jobs are stored in both database (for persistence) and Redis (for queue)
- Each job has a type, priority, and parameters

### **2. Job Queue**
- Redis sorted sets provide priority-based job queuing
- Jobs are automatically ordered by priority (urgent > high > normal > low)
- Failed jobs can be retried with exponential backoff

### **3. Worker Process**
- Background worker runs as an async task within the API service
- Continuously polls Redis for new jobs
- Processes jobs based on type:
  - `file_processing`: Upload file → chunk → embed → store in vector DB
  - `batch_processing`: Process multiple files as a batch
  - `investigation`: Complex LLM analysis with tool usage

### **4. Progress Tracking**
- Workers update job status in Redis during processing
- API endpoints can check job progress in real-time
- Results are stored with configurable TTL

## Deployment Options

### **Option 1: In-Process Workers (Current Implementation)**

**Best for**: Development, small deployments, single-server setups

**Configuration**:
```python
# In api/app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await job_client.connect()
    worker_task = asyncio.create_task(
        job_client.start_worker(job_manager.process_job)
    )
    app.state.worker_task = worker_task

    yield

    # Shutdown
    await job_client.stop_worker()
    await job_client.disconnect()
```

**Pros**:
- ✅ Simple deployment - single process
- ✅ Easy debugging - same process, same logs
- ✅ Resource efficient - shared memory and connections
- ✅ Fast iteration for development

**Cons**:
- ❌ Worker can block API process if resource-intensive
- ❌ Harder to scale workers independently
- ❌ Single point of failure

**Docker Compose**:
```yaml
services:
  api:
    build: ./api
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis
    # Worker starts automatically in same process
```

### **Option 2: Separate Worker Process**

**Best for**: Production, medium deployments, resource isolation

**Architecture**:
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ API Service │───▶│ Redis Queue  │◀───│Worker Service│
│ (Web Only)  │    │              │    │ (CPU Heavy) │
└─────────────┘    └──────────────┘    └─────────────┘
```

**Implementation**:
```python
# api/app/main.py - No worker
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - only connect to Redis, no worker
    await job_client.connect()
    yield
    # Shutdown
    await job_client.disconnect()

# worker/main.py - Separate worker process
import asyncio
from app.job_client import job_client
from app.job_manager import job_manager

async def main():
    await job_client.connect()
    await job_client.start_worker(job_manager.process_job)

if __name__ == "__main__":
    asyncio.run(main())
```

**Docker Compose**:
```yaml
services:
  api:
    build: ./api
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis

  worker:
    build: ./worker
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis
    deploy:
      replicas: 2  # Multiple worker instances
```

**Pros**:
- ✅ Worker doesn't affect API performance
- ✅ Can scale workers independently
- ✅ Can optimize worker resources (CPU, memory)
- ✅ Better fault isolation

**Cons**:
- ❌ More complex deployment
- ❌ Need to manage two services
- ❌ Resource duplication (connections, memory)

### **Option 3: Auto-Scaling Worker Cluster**

**Best for**: Large production, variable workloads, cloud deployments

**Architecture**:
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ API Service │───▶│ Redis Queue  │◀───│Worker Cluster│
│ (Web Only)  │    │              │    │ (Auto Scale) │
└─────────────┘    └──────────────┘    └─────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │Worker Pod 1 │ │Worker Pod 2 │ │Worker Pod N │
            └─────────────┘ └─────────────┘ └─────────────┘
```

**Kubernetes Deployment**:
```yaml
# worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: archaeologist-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: archaeologist-worker
  template:
    metadata:
      labels:
        app: archaeologist-worker
    spec:
      containers:
      - name: worker
        image: archaeologist/worker:latest
        env:
        - name: REDIS_HOST
          value: "redis-service"
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: archaeologist-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: archaeologist-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Pros**:
- ✅ Automatic scaling based on load
- ✅ High availability and fault tolerance
- ✅ Optimal resource utilization
- ✅ Handles variable workloads efficiently

**Cons**:
- ❌ Most complex deployment
- ❌ Requires orchestration platform
- ❌ Higher operational overhead

## Communication Patterns

### **Redis Queue Communication**
All deployment options use the same Redis-based communication:

```python
# API Service - Enqueue Job
job = Job(
    type="file_processing",
    priority=Priority.NORMAL,
    parameters={"file_path": "/data/file.txt"}
)
await job_client.enqueue_job(job)

# Worker Process - Dequeue and Process
while True:
    job_data = await job_client.get_next_job()
    if job_data:
        result = await job_manager.process_job(job_data)
        await job_client.update_job_status(job_data["id"], "completed", result)
    await asyncio.sleep(settings.JOB_POLL_INTERVAL)
```

### **Status Updates**
Workers update job status in Redis for real-time tracking:

```python
# Worker updates progress
await job_client.update_job_status(
    job_id="123",
    status="running",
    progress={"current": 5, "total": 10, "message": "Processing chunks"}
)

# API checks status
status = await job_client.get_job_status("123")
# Returns: {"status": "running", "progress": {...}}
```

## Scaling Considerations

### **Redis Scaling**
For high-volume deployments, consider Redis scaling:

```yaml
# Redis Cluster for high availability
services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --appendonly yes

  redis-replica:
    image: redis:7-alpine
    command: redis-server --replicaof redis-master 6379
    depends_on:
      - redis-master

  redis-sentinel:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
```

### **Load Balancing**
API services can be load-balanced while sharing the same Redis queue:

```yaml
# Multiple API instances
services:
  api:
    build: ./api
    deploy:
      replicas: 3
    environment:
      - REDIS_HOST=redis-cluster

  worker:
    build: ./worker
    deploy:
      replicas: 5
    environment:
      - REDIS_HOST=redis-cluster
```

## Configuration Options

### **Worker Tuning**
```python
# Environment variables
JOB_POLL_INTERVAL=5          # Seconds between job checks
JOB_BATCH_SIZE=10            # Jobs to process in parallel
MAX_CONCURRENT_JOBS=5        # Max concurrent jobs per worker
JOB_TIMEOUT=3600            # Max job duration (seconds)
WORKER_HEARTBEAT_INTERVAL=30 # Worker health check interval
```

### **Queue Configuration**
```python
# Redis queue settings
JOB_QUEUE_NAME=archaeologist_jobs
JOB_RESULT_TTL=86400        # Keep job results for 24 hours
FAILED_JOB_TTL=3600         # Keep failed jobs for 1 hour
PRIORITY_QUEUE=true         # Enable priority-based processing
```

## Monitoring and Observability

### **Worker Metrics**
- Jobs processed per minute
- Average job processing time
- Queue depth (pending jobs)
- Worker CPU and memory usage
- Error rates by job type

### **Health Checks**
```python
# Worker health endpoint
@app.get("/worker/health")
async def worker_health():
    return {
        "status": "healthy",
        "worker_id": job_client.worker_id,
        "uptime_seconds": uptime,
        "jobs_processed": total_jobs,
        "queue_depth": await job_client.get_queue_depth()
    }
```

## Debugging and Development

### **Local Development**
```bash
# Start all services for development
docker-compose --env-file .env.dev up

# View worker logs
docker-compose logs -f worker

# Debug specific job
curl http://localhost:8000/api/v1/jobs/{job_id}
```

### **Testing Jobs**
```python
# Test job processing
from app.job_manager import job_manager

job_data = {
    "id": "test_job",
    "type": "file_processing",
    "parameters": {"file_path": "test.txt"}
}
result = await job_manager.process_job(job_data)
```

This architecture provides flexible deployment options from simple single-process setups to large-scale auto-scaling clusters, all using the same Redis-based communication pattern.