# Redis Cluster Scaling Architecture

## Overview

This document explains how to scale the Redis-based job queue system for high-availability and high-throughput deployments. The Redis queue system is designed to scale from single-node development setups to multi-node production clusters.

## Architecture Levels

### **Level 1: Single Node (Development)**
```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   API Service   │───▶│ Redis Single │◀───│ Worker Process  │
│                 │    │ Node         │    │ (In-process)    │
└─────────────────┘    └──────────────┘    └─────────────────┘
```

**Use Case**: Development, testing, small production deployments
**Configuration**: Single Redis instance with persistence
**Pros**: Simple, low cost, easy to manage
**Cons**: Single point of failure, limited scalability

### **Level 2: Primary-Replica (Production)**
```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   API Service   │───▶│ Redis        │◀───│ Worker Cluster  │
│                 │    │ Primary      │    │                 │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │Redis Replica│ │Redis Replica│ │Redis Replica│
            │ (Read-only) │ │ (Read-only) │ │ (Read-only) │
            └─────────────┘ └─────────────┘ └─────────────┘
```

**Use Case**: Medium production deployments, read-heavy workloads
**Configuration**: Primary with multiple replicas for reads
**Pros**: High availability, read scaling, automatic failover
**Cons**: Write bottleneck on primary, manual scaling

### **Level 3: Redis Cluster (High-Scale Production)**
```
┌─────────────────┐    ┌──────────────────────────┐    ┌─────────────────┐
│   API Service   │───▶│    Redis Cluster         │◀───│ Worker Cluster  │
│                 │    │  (Sharded + Replicated)   │    │                 │
└─────────────────┘    └──────────────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
        ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
        │  Slot Range     │ │  Slot Range     │ │  Slot Range     │
        │  0-5460         │ │  5461-10922     │ │  10923-16383    │
        │                 │ │                 │ │                 │
        │ Master + Replica│ │ Master + Replica│ │ Master + Replica│
        └─────────────────┘ └─────────────────┘ └─────────────────┘
```

**Use Case**: Large production deployments, high throughput, global scale
**Configuration**: 6+ node cluster with sharding and replication
**Pros**: Horizontal scaling, high availability, automatic failover, geographic distribution
**Cons**: Complex setup, higher cost, operational overhead

## Implementation Examples

### **Docker Compose: Primary-Replica Setup**
```yaml
version: '3.8'
services:
  redis-primary:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis_primary_data:/data
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}

  redis-replica:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD} --replicaof redis-primary 6379 --masterauth ${REDIS_PASSWORD}
    ports:
      - "6380:6379"
    volumes:
      - redis_replica_data:/data
    depends_on:
      - redis-primary
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}

  redis-sentinel:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
    ports:
      - "26379:26379"
    volumes:
      - ./redis/sentinel.conf:/etc/redis/sentinel.conf
    depends_on:
      - redis-primary

  api:
    build: ./api
    environment:
      - REDIS_HOST=redis-sentinel
      - REDIS_PORT=26379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - REDIS_MODE=sentinel
    depends_on:
      - redis-sentinel

  worker:
    build: ./worker
    environment:
      - REDIS_HOST=redis-sentinel
      - REDIS_PORT=26379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - REDIS_MODE=sentinel
    depends_on:
      - redis-sentinel
    deploy:
      replicas: 3

volumes:
  redis_primary_data:
  redis_replica_data:
```

**sentinel.conf**:
```conf
port 26379
sentinel monitor mymaster redis-primary 6379 2
sentinel auth-pass mymaster ${REDIS_PASSWORD}
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 10000
sentinel announce-ip redis-sentinel
sentinel announce-port 26379
```

### **Kubernetes: Redis Cluster Setup**
```yaml
# redis-cluster.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
spec:
  serviceName: redis-cluster
  replicas: 6
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command:
        - redis-server
        - /etc/redis/redis.conf
        ports:
        - containerPort: 6379
          name: client
        - containerPort: 16379
          name: gossip
        volumeMounts:
        - name: conf
          mountPath: /etc/redis
        - name: data
          mountPath: /data
      volumes:
      - name: conf
        configMap:
          name: redis-cluster-config
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-cluster-config
data:
  redis.conf: |
    cluster-enabled yes
    cluster-config-file nodes.conf
    cluster-node-timeout 5000
    appendonly yes
    appendfilename appendonly.aof
    protected-mode no
    bind 0.0.0.0
    port 6379
```

**Redis Cluster Initialization**:
```bash
# Create cluster
kubectl exec -it redis-cluster-0 -- redis-cli --cluster create \
  $(kubectl get pods -l app=redis-cluster -o jsonpath='{range.items[*]}{.status.podIP}:6379 '):16379 \
  --cluster-replicas 1 --cluster-yes

# Verify cluster
kubectl exec -it redis-cluster-0 -- redis-cli cluster nodes
```

### **Cloud Provider: AWS ElastiCache**
```yaml
# terraform/aws-redis.tf
resource "aws_elasticache_replication_group" "archaeologist_redis" {
  replication_group_id = "archaeologist-redis"
  description = "Redis cluster for Archaeologist job queue"

  node_type = "cache.r6g.large"
  port = 6379
  parameter_group_name = "default.redis7"

  cluster_mode {
    replicas_per_node_group = 1
    num_node_groups = 3
  }

  security_group_ids = [aws_security_group.redis.id]
  subnet_group_name = aws_elasticache_subnet_group.archaeologist.name

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token = var.redis_password

  automatic_failover_enabled = true
  multi_az_enabled = true

  tags = {
    Name = "archaeologist-redis"
    Environment = var.environment
  }
}
```

## Application Configuration

### **Redis Connection Modes**
```python
# app/config.py
class Settings:
    def __init__(self):
        # Redis configuration
        self.REDIS_MODE = os.getenv("REDIS_MODE", "single")  # single, sentinel, cluster
        self.REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

        # Sentinel configuration
        self.REDIS_SENTINEL_SERVICE = os.getenv("REDIS_SENTINEL_SERVICE", "mymaster")
        self.REDIS_SENTINEL_HOSTS = os.getenv("REDIS_SENTINEL_HOSTS", "").split(",")

        # Cluster configuration
        self.REDIS_CLUSTER_NODES = os.getenv("REDIS_CLUSTER_NODES", "").split(",")
```

### **Redis Client Implementation**
```python
# app/redis_client.py
import redis.asyncio as redis
from redis.sentinel import Sentinel
from .config import get_settings

class RedisClient:
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.mode = self.settings.REDIS_MODE

    async def connect(self):
        if self.mode == "single":
            self.client = redis.Redis(
                host=self.settings.REDIS_HOST,
                port=self.settings.REDIS_PORT,
                password=self.settings.REDIS_PASSWORD,
                decode_responses=True
            )
        elif self.mode == "sentinel":
            sentinel = Sentinel(
                [(host, 26379) for host in self.settings.REDIS_SENTINEL_HOSTS],
                socket_timeout=5,
                password=self.settings.REDIS_PASSWORD
            )
            self.client = sentinel.master_for(
                self.settings.REDIS_SENTINEL_SERVICE,
                decode_responses=True
            )
        elif self.mode == "cluster":
            from redis.cluster import RedisCluster
            nodes = []
            for node in self.settings.REDIS_CLUSTER_NODES:
                host, port = node.split(":")
                nodes.append({"host": host, "port": int(port)})

            self.client = RedisCluster(
                startup_nodes=nodes,
                decode_responses=True,
                password=self.settings.REDIS_PASSWORD
            )

        # Test connection
        await self.client.ping()

    async def disconnect(self):
        if self.client:
            await self.client.close()
```

### **Job Queue Implementation**
```python
# app/job_client.py (Updated for clustering)
class JobClient:
    def __init__(self):
        self.redis_client = None
        self.settings = get_settings()

    async def enqueue_job(self, job: Job) -> bool:
        """Enqueue job with cluster-aware routing"""
        job_data = job.model_dump_json()

        if self.settings.REDIS_MODE == "cluster":
            # For cluster mode, use consistent hashing
            queue_key = f"{self.settings.JOB_QUEUE_NAME}:{job.id}"
            score = self._get_priority_score(job.priority)

            await self.redis_client.set(queue_key, job_data, ex=self.settings.JOB_RESULT_TTL)
            await self.redis_client.zadd(
                self.settings.JOB_QUEUE_NAME,
                {queue_key: score}
            )
        else:
            # Single node or sentinel mode
            await self.redis_client.lpush(
                f"{self.settings.JOB_QUEUE_NAME}:{job.priority.value}",
                job_data
            )

        return True

    async def get_next_job(self) -> Optional[Dict[str, Any]]:
        """Get next job with cluster-aware handling"""
        if self.settings.REDIS_MODE == "cluster":
            # Cluster mode: get highest priority job
            result = await self.redis_client.zpopmin(self.settings.JOB_QUEUE_NAME)
            if result:
                queue_key, score = result[0]
                job_data = await self.redis_client.get(queue_key)
                await self.redis_client.delete(queue_key)
                return json.loads(job_data) if job_data else None
        else:
            # Single node mode: check queues by priority
            for priority in ["urgent", "high", "normal", "low"]:
                queue_name = f"{self.settings.JOB_QUEUE_NAME}:{priority}"
                job_data = await self.redis_client.rpop(queue_name)
                if job_data:
                    return json.loads(job_data)

        return None
```

## Monitoring and Observability

### **Redis Metrics**
```python
# app/redis_monitoring.py
import redis
from prometheus_client import Gauge, Counter

# Metrics
redis_connections = Gauge('redis_connections_active', 'Active Redis connections')
redis_queue_depth = Gauge('redis_queue_depth', 'Number of jobs in queue', ['priority'])
redis_processing_time = Counter('redis_job_processing_seconds', 'Job processing time')

class RedisMonitor:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    async def get_metrics(self):
        """Get Redis cluster metrics"""
        info = await self.redis_client.info()

        metrics = {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory": info.get("used_memory", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
        }

        if self.settings.REDIS_MODE == "cluster":
            metrics["cluster_nodes"] = await self.redis_client.cluster_nodes()

        return metrics

    async def check_queue_health(self):
        """Check job queue health across cluster"""
        if self.settings.REDIS_MODE == "cluster":
            # Check queue depth across cluster
            nodes = await self.redis_client.cluster_nodes()
            total_jobs = 0

            for node in nodes:
                if node.get("flags") and "master" in node["flags"]:
                    node_client = self.redis_client.get_redis_connection(node["id"])
                    queue_depth = await node_client.zcard(self.settings.JOB_QUEUE_NAME)
                    total_jobs += queue_depth

            return {"total_jobs": total_jobs, "cluster_nodes": len(nodes)}
        else:
            # Single node check
            queue_depth = await self.redis_client.zcard(self.settings.JOB_QUEUE_NAME)
            return {"total_jobs": queue_depth, "cluster_nodes": 1}
```

### **Health Checks**
```python
# app/health_checks.py
from fastapi import HTTPException
from .redis_client import redis_client

async def check_redis_health():
    """Check Redis cluster health"""
    try:
        if not await redis_client.client.ping():
            raise HTTPException(status_code=503, detail="Redis not responding")

        if redis_client.mode == "cluster":
            # Check cluster health
            cluster_info = await redis_client.client.cluster_info()
            if cluster_info.get("cluster_state") != "ok":
                raise HTTPException(status_code=503, detail="Redis cluster not healthy")

            # Check all nodes are available
            nodes = await redis_client.client.cluster_nodes()
            failed_nodes = [n for n in nodes if "fail" in n.get("flags", "")]
            if failed_nodes:
                raise HTTPException(
                    status_code=503,
                    detail=f"Redis cluster has {len(failed_nodes)} failed nodes"
                )

        return {"status": "healthy", "mode": redis_client.mode}

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis health check failed: {str(e)}")
```

## Performance Tuning

### **Redis Configuration**
```conf
# redis.conf optimizations for job queues
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence settings
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Network settings
tcp-keepalive 300
timeout 0

# Memory optimization
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
```

### **Job Queue Optimization**
```python
# app/job_optimizer.py
class JobOptimizer:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    async def optimize_queue(self):
        """Optimize job queue performance"""
        # Clean up expired jobs
        await self._cleanup_expired_jobs()

        # Compress large job data
        await self._compress_job_data()

        # Batch similar jobs
        await self._batch_similar_jobs()

    async def _cleanup_expired_jobs(self):
        """Remove expired jobs from queue"""
        pattern = f"{self.settings.JOB_QUEUE_NAME}:*"
        keys = await self.redis_client.keys(pattern)

        for key in keys:
            ttl = await self.redis_client.ttl(key)
            if ttl == -1:  # No expiration set
                await self.redis_client.expire(key, self.settings.JOB_RESULT_TTL)
```

## Scaling Strategies

### **Horizontal Scaling**
1. **Add Redis Nodes**: Add more nodes to the cluster
2. **Rebalance Slots**: Redistribute hash slots across new nodes
3. **Update Application**: Update application configuration with new nodes

### **Vertical Scaling**
1. **Upgrade Node Size**: Use larger EC2 instances or VMs
2. **Increase Memory**: Add more RAM to handle larger queues
3. **Optimize Network**: Use faster network connections

### **Geographic Distribution**
```yaml
# Multi-region Redis cluster
# Region 1 (Primary)
redis-us-east-1:
  image: redis:7-alpine
  command: redis-server --cluster-enabled yes

# Region 2 (Replica)
redis-us-west-2:
  image: redis:7-alpine
  command: redis-server --cluster-enabled yes --replicaof redis-us-east-1 6379
```

This Redis cluster scaling architecture provides a roadmap from development to enterprise-scale production deployments, ensuring high availability, performance, and scalability for the Archaeologist job queue system.