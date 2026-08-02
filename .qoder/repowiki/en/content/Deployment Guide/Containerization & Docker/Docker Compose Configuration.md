# Docker Compose Configuration

<cite>
**Referenced Files in This Document**
- [README.md](file://README.md)
- [requirements.txt](file://requirements.txt)
- [config.py](file://config.py)
- [pipeline.py](file://pipeline.py)
- [ask.py](file://ask.py)
- [build_graph.py](file://build_graph.py)
- [capture.py](file://capture.py)
- [classify.py](file://classify.py)
- [graph_preview.py](file://graph_preview.py)
- [link.py](file://link.py)
- [lib/embeddings.py](file://lib/embeddings.py)
- [lib/extract.py](file://lib/extract.py)
- [lib/llm.py](file://lib/llm.py)
- [lib/models.py](file://lib/models.py)
- [lib/storage.py](file://lib/storage.py)
- [data/index.json](file://data/index.json)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure Analysis](#project-structure-analysis)
3. [Core Components Overview](#core-components-overview)
4. [Docker Compose Architecture](#docker-compose-architecture)
5. [Service Definitions](#service-definitions)
6. [Network Configuration](#network-configuration)
7. [Volume Management](#volume-management)
8. [Environment Variables](#environment-variables)
9. [Development vs Production Setup](#development-vs-production-setup)
10. [Database Integration](#database-integration)
11. [Health Checks and Monitoring](#health-checks-and-monitoring)
12. [Scaling Strategies](#scaling-strategies)
13. [Troubleshooting Guide](#troubleshooting-guide)
14. [Best Practices](#best-practices)
15. [Conclusion](#conclusion)

## Introduction

This document provides comprehensive Docker Compose configuration guidance for orchestrating the Secondself AI Brain services. The Secondself AI Brain is a Python-based application that appears to handle various AI-related tasks including embeddings, data extraction, language model interactions, and graph visualization. The application consists of multiple Python scripts and library modules that work together to provide AI-powered functionality.

The Docker Compose setup will enable containerized deployment of all services, ensuring consistent environments across development, testing, and production stages. This guide covers service definitions, networking, volume management, environment configuration, health checks, logging, resource limits, and scaling strategies.

## Project Structure Analysis

Based on the project structure, the Secondself AI Brain application follows a modular Python architecture:

```mermaid
graph TB
subgraph "Application Scripts"
ask[ask.py]
build_graph[build_graph.py]
capture[capture.py]
classify[classify.py]
graph_preview[graph_preview.py]
link[link.py]
pipeline[pipeline.py]
end
subgraph "Library Modules"
lib_init[__init__.py]
embeddings[embeddings.py]
extract[extract.py]
llm[llm.py]
models[models.py]
storage[storage.py]
end
subgraph "Data & Config"
config[config.py]
index[data/index.json]
requirements[requirements.txt]
end
subgraph "Static Assets"
graph_html[static/graph.html]
end
ask --> lib_init
build_graph --> lib_init
capture --> lib_init
classify --> lib_init
graph_preview --> lib_init
link --> lib_init
pipeline --> lib_init
lib_init --> embeddings
lib_init --> extract
lib_init --> llm
lib_init --> models
lib_init --> storage
config --> lib_init
index --> storage
requirements --> lib_init
graph_html --> graph_preview
```

**Diagram sources**
- [pipeline.py:1-50](file://pipeline.py#L1-L50)
- [lib/__init__.py:1-50](file://lib/__init__.py#L1-L50)
- [config.py:1-50](file://config.py#L1-L50)

**Section sources**
- [README.md:1-100](file://README.md#L1-L100)
- [requirements.txt:1-50](file://requirements.txt#L1-L50)

## Core Components Overview

The Secondself AI Brain application consists of several key components:

### Main Application Scripts
- **ask.py**: Handles user queries and AI responses
- **build_graph.py**: Constructs knowledge graphs from data
- **capture.py**: Captures and processes input data
- **classify.py**: Classifies and categorizes information
- **graph_preview.py**: Generates visual graph representations
- **link.py**: Manages relationships between data entities
- **pipeline.py**: Orchestrates the main processing workflow

### Library Modules
- **embeddings.py**: Handles vector embeddings for semantic search
- **extract.py**: Extracts structured data from unstructured sources
- **llm.py**: Interfaces with Large Language Models
- **models.py**: Defines data models and schemas
- **storage.py**: Manages data persistence and retrieval

### Configuration and Data
- **config.py**: Application configuration settings
- **data/index.json**: Index data for search and retrieval
- **requirements.txt**: Python dependencies

**Section sources**
- [pipeline.py:1-100](file://pipeline.py#L1-L100)
- [lib/embeddings.py:1-100](file://lib/embeddings.py#L1-L100)
- [lib/extract.py:1-100](file://lib/extract.py#L1-L100)
- [lib/llm.py:1-100](file://lib/llm.py#L1-L100)
- [lib/models.py:1-100](file://lib/models.py#L1-L100)
- [lib/storage.py:1-100](file://lib/storage.py#L1-L100)

## Docker Compose Architecture

The Docker Compose architecture for Secondself AI Brain includes multiple interconnected services:

```mermaid
graph TB
subgraph "Frontend Services"
web_app[Web Application<br/>Python FastAPI/Flask]
graph_ui[Graph Visualization<br/>HTML/CSS/JS]
end
subgraph "AI Processing Services"
embedding_svc[Embedding Service<br/>Vector Database]
llm_svc[LLM Service<br/>Language Model API]
pipeline_svc[Pipeline Service<br/>Main Processing]
end
subgraph "Data Services"
postgres[(PostgreSQL<br/>Primary Database)]
redis[(Redis<br/>Cache/Queue)]
minio[(MinIO<br/>Object Storage)]
end
subgraph "Monitoring"
prometheus[Prometheus<br/>Metrics Collection]
grafana[Grafana<br/>Visualization]
elasticsearch[(Elasticsearch<br/>Logging)]
end
web_app --> embedding_svc
web_app --> pipeline_svc
graph_ui --> web_app
pipeline_svc --> llm_svc
pipeline_svc --> postgres
pipeline_svc --> redis
embedding_svc --> postgres
monitoring --> postgres
monitoring --> redis
monitoring --> web_app
```

**Diagram sources**
- [config.py:1-100](file://config.py#L1-L100)
- [pipeline.py:1-100](file://pipeline.py#L1-L100)

## Service Definitions

### Primary Application Service

The main application service handles the core AI processing functionality:

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/secondself
      - REDIS_URL=redis://redis:6379/0
      - EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
      - LLM_API_KEY=${LLM_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - app_data:/app/data
      - ./uploads:/app/uploads
      - ./static:/app/static
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Database Service

PostgreSQL database for persistent data storage:

```yaml
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: secondself
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_HOST_AUTH_METHOD: trust
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d secondself"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
```

### Cache and Queue Service

Redis for caching and message queuing:

```yaml
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
```

**Section sources**
- [config.py:1-100](file://config.py#L1-L100)
- [lib/storage.py:1-100](file://lib/storage.py#L1-L100)

## Network Configuration

Custom network setup for service isolation and communication:

```yaml
networks:
  secondself-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
    driver_opts:
      com.docker.network.enable_ipv6: "false"

volumes:
  app_data:
    driver: local
  postgres_data:
    driver: local
  redis_data:
    driver: local
  uploads:
    driver: local
  static_assets:
    driver: local
```

**Section sources**
- [config.py:1-100](file://config.py#L1-L100)

## Volume Management

Persistent storage configuration for data durability:

```yaml
volumes:
  # Application data volumes
  app_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data
  
  # Database storage
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/postgres
  
  # Redis persistence
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/redis
  
  # User uploads
  uploads:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./tmp_uploads
  
  # Static assets
  static_assets:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./static
```

**Section sources**
- [data/index.json:1-50](file://data/index.json#L1-L50)

## Environment Variables

Comprehensive environment variable configuration:

### Application Configuration
```yaml
environment:
  # Database Configuration
  DATABASE_URL: ${DATABASE_URL:-postgresql://user:pass@postgres:5432/secondself}
  DATABASE_POOL_SIZE: ${DATABASE_POOL_SIZE:-10}
  DATABASE_TIMEOUT: ${DATABASE_TIMEOUT:-30}
  
  # Redis Configuration
  REDIS_URL: ${REDIS_URL:-redis://redis:6379/0}
  REDIS_MAX_CONNECTIONS: ${REDIS_MAX_CONNECTIONS:-50}
  
  # AI/ML Configuration
  EMBEDDING_MODEL: ${EMBEDDING_MODEL:-sentence-transformers/all-MiniLM-L6-v2}
  LLM_API_KEY: ${LLM_API_KEY}
  LLM_PROVIDER: ${LLM_PROVIDER:-openai}
  LLM_MODEL: ${LLM_MODEL:-gpt-4}
  
  # Logging Configuration
  LOG_LEVEL: ${LOG_LEVEL:-INFO}
  LOG_FORMAT: ${LOG_FORMAT:-json}
  LOG_FILE: ${LOG_FILE:-/app/logs/app.log}
  
  # Security Configuration
  SECRET_KEY: ${SECRET_KEY:-your-secret-key-here}
  CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000}
  
  # Performance Configuration
  WORKER_COUNT: ${WORKER_COUNT:-4}
  MAX_WORKERS: ${MAX_WORKERS:-8}
  THREAD_POOL_SIZE: ${THREAD_POOL_SIZE:-10}
```

### Development vs Production Variables
```yaml
# Development
development:
  DEBUG: "true"
  LOG_LEVEL: "DEBUG"
  DATABASE_URL: "postgresql://dev:dev@localhost:5432/secondself_dev"
  REDIS_URL: "redis://localhost:6379/0"
  LLM_API_KEY: "dev-key"
  
# Production
production:
  DEBUG: "false"
  LOG_LEVEL: "WARNING"
  DATABASE_URL: "${PROD_DATABASE_URL}"
  REDIS_URL: "${PROD_REDIS_URL}"
  LLM_API_KEY: "${PROD_LLM_API_KEY}"
```

**Section sources**
- [config.py:1-100](file://config.py#L1-L100)

## Development vs Production Setup

### Development Docker Compose
```yaml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - /app/node_modules
      - ./data:/app/data
      - ./tmp_uploads:/app/uploads
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - RELOAD=true
    ports:
      - "8000:8000"
      - "9000:9000"  # Debug port
    command: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Docker Compose
```yaml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    volumes:
      - app_data:/app/data
      - uploads:/app/uploads
    environment:
      - DEBUG=false
      - LOG_LEVEL=WARNING
      - WORKER_COUNT=4
    ports:
      - "8000:8000"
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

**Section sources**
- [requirements.txt:1-100](file://requirements.txt#L1-L100)

## Database Integration

### PostgreSQL Configuration
```yaml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: secondself
    POSTGRES_USER: ${DB_USER:-user}
    POSTGRES_PASSWORD: ${DB_PASSWORD:-pass}
    POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --locale=en_US.UTF-8"
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./migrations:/app/migrations
  command: >
    postgres
    -c max_connections=100
    -c shared_buffers=256MB
    -c effective_cache_size=512MB
    -c maintenance_work_mem=64MB
    -c checkpoint_completion_target=0.9
    -c wal_buffers=16MB
    -c default_statistics_target=100
```

### Database Initialization
```sql
-- init.sql
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    content TEXT,
    metadata JSONB,
    embedding VECTOR(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN (metadata);
```

**Section sources**
- [lib/storage.py:1-100](file://lib/storage.py#L1-L100)

## Health Checks and Monitoring

### Health Check Configuration
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Monitoring Stack
```yaml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
  ports:
    - "9090:9090"
  depends_on:
    - app

grafana:
  image: grafana/grafana:latest
  volumes:
    - grafana_data:/var/lib/grafana
    - ./grafana/provisioning:/etc/grafana/provisioning
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  depends_on:
    - prometheus
```

**Section sources**
- [pipeline.py:1-100](file://pipeline.py#L1-L100)

## Scaling Strategies

### Horizontal Scaling
```yaml
services:
  app:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
      update_config:
        parallelism: 1
        failure_action: rollback
        order: start-first
```

### Vertical Scaling
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Auto-scaling Configuration
```yaml
autoscaling:
  min_replicas: 2
  max_replicas: 10
  target_cpu_utilization: 70
  target_memory_utilization: 80
```

**Section sources**
- [config.py:1-100](file://config.py#L1-L100)

## Troubleshooting Guide

### Common Issues and Solutions

#### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec postgres pg_isready -U user -d secondself

# View database logs
docker-compose logs postgres

# Reset database if needed
docker-compose down -v
docker-compose up -d
```

#### Memory Issues
```bash
# Monitor memory usage
docker stats

# Check container logs for OOM errors
docker-compose logs --tail=100 app | grep -i "memory\|oom"
```

#### Network Connectivity Problems
```bash
# Test inter-service communication
docker-compose exec app curl http://postgres:5432

# Check network status
docker network ls
docker network inspect secondself_network
```

#### Performance Bottlenecks
```bash
# Monitor CPU and memory usage
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Check disk I/O performance
docker stats --no-stream
```

**Section sources**
- [lib/storage.py:1-100](file://lib/storage.py#L1-L100)

## Best Practices

### Security Best Practices
- Use environment variables for sensitive configuration
- Implement proper network segmentation
- Regular security updates for base images
- Container security scanning
- Least privilege principle for service accounts

### Performance Optimization
- Use multi-stage builds for smaller images
- Implement proper caching strategies
- Optimize database queries and indexes
- Use connection pooling
- Implement proper logging levels

### Deployment Strategies
- Blue-green deployments for zero downtime
- Rolling updates with health checks
- Proper backup and recovery procedures
- Monitoring and alerting setup
- Log aggregation and analysis

## Conclusion

This comprehensive Docker Compose configuration provides a robust foundation for deploying the Secondself AI Brain application across different environments. The setup includes proper service orchestration, data persistence, monitoring, and scaling capabilities. By following the guidelines and configurations outlined in this document, you can ensure reliable and efficient deployment of your AI-powered application.

The modular approach allows for easy customization and extension as your application grows. Remember to regularly review and update your configurations based on changing requirements and best practices in container orchestration.