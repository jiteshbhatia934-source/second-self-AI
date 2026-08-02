# Kubernetes Deployment & Orchestration

<cite>
**Referenced Files in This Document**
- [README.md](file://README.md)
- [config.py](file://config.py)
- [requirements.txt](file://requirements.txt)
- [architecture.md](file://docs/architecture.md)
- [implementation-plan.md](file://docs/implementation-plan.md)
- [Second_Self.md](file://docs/Second_Self.md)
- [pipeline.py](file://pipeline.py)
- [lib/models.py](file://lib/models.py)
- [lib/storage.py](file://lib/storage.py)
- [data/index.json](file://data/index.json)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure Analysis](#project-structure-analysis)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Kubernetes Deployment Manifests](#kubernetes-deployment-manifests)
6. [Service Definitions](#service-definitions)
7. [Ingress Configuration](#ingress-configuration)
8. [Persistent Volume Claims](#persistent-volume-claims)
9. [ConfigMaps and Secrets Management](#configmaps-and-secrets-management)
10. [Horizontal Pod Autoscaling](#horizontal-pod-autoscaling)
11. [Resource Quotas](#resource-quotas)
12. [Helm Chart Creation](#helm-chart-creation)
13. [Monitoring with Prometheus](#monitoring-with-prometheus)
14. [Logging Aggregation](#logging-aggregation)
15. [Distributed Tracing Setup](#distributed-tracing-setup)
16. [Cluster Configuration](#cluster-configuration)
17. [Node Affinity Rules](#node-affinity-rules)
18. [Disaster Recovery Procedures](#disaster-recovery-procedures)
19. [Rolling Updates and Rollback Strategies](#rolling-updates-and-rollback-strategies)
20. [Performance Considerations](#performance-considerations)
21. [Troubleshooting Guide](#troubleshooting-guide)
22. [Conclusion](#conclusion)

## Introduction

This document provides comprehensive Kubernetes deployment and orchestration guidance for the Secondself AI Brain application. The Secondself AI Brain is a sophisticated AI-powered knowledge management system that processes, stores, and retrieves information using advanced language models and embedding techniques.

The application architecture includes multiple Python modules for data processing, model inference, storage management, and API serving. This guide covers production-ready deployment strategies including high availability, scalability, monitoring, and disaster recovery.

## Project Structure Analysis

The Secondself AI Brain follows a modular Python architecture with clear separation of concerns:

```mermaid
graph TB
subgraph "Application Layer"
APP[pipeline.py]
CFG[config.py]
REQ[requirements.txt]
end
subgraph "Core Library"
MODELS[lib/models.py]
STORAGE[lib/storage.py]
EMBEDDINGS[lib/embeddings.py]
LLM[lib/llm.py]
EXTRACT[lib/extract.py]
end
subgraph "Data Layer"
DATA[data/index.json]
UPLOADS[tmp_uploads/]
end
subgraph "Static Assets"
STATIC[static/graph.html]
end
APP --> MODELS
APP --> STORAGE
APP --> CFG
MODELS --> EMBEDDINGS
MODELS --> LLM
STORAGE --> DATA
APP --> STATIC
```

**Diagram sources**
- [pipeline.py](file://pipeline.py)
- [config.py](file://config.py)
- [lib/models.py](file://lib/models.py)
- [lib/storage.py](file://lib/storage.py)

**Section sources**
- [README.md](file://README.md)
- [architecture.md](file://docs/architecture.md)

## Core Components

The Secondself AI Brain consists of several key components that work together to provide AI-powered knowledge management:

### Application Entry Points
- **pipeline.py**: Main application orchestrator handling data flow and processing
- **config.py**: Configuration management and environment variable handling
- **requirements.txt**: Python dependencies and version specifications

### Core Library Modules
- **models.py**: Data models and schema definitions
- **storage.py**: Data persistence and retrieval mechanisms
- **embeddings.py**: Vector embeddings generation and management
- **llm.py**: Large Language Model integration and inference
- **extract.py**: Data extraction and preprocessing utilities

### Data Management
- **index.json**: Knowledge base index and metadata
- **tmp_uploads/**: Temporary file upload directory
- **static/graph.html**: Web interface components

**Section sources**
- [pipeline.py](file://pipeline.py)
- [config.py](file://config.py)
- [lib/models.py](file://lib/models.py)
- [lib/storage.py](file://lib/storage.py)
- [lib/embeddings.py](file://lib/embeddings.py)
- [lib/llm.py](file://lib/llm.py)
- [lib/extract.py](file://lib/extract.py)
- [data/index.json](file://data/index.json)

## Architecture Overview

The Secondself AI Brain follows a microservices-oriented architecture with clear separation between processing, storage, and presentation layers:

```mermaid
graph TB
subgraph "Client Layer"
WEB[Web Browser]
API[API Clients]
CLI[Command Line Interface]
end
subgraph "Application Layer"
API_SERVER[API Server]
PROCESSOR[Processing Engine]
MODEL_INFERENCE[Model Inference]
end
subgraph "Data Layer"
VECTOR_DB[(Vector Database)]
FILE_STORE[(File Storage)]
METADATA_DB[(Metadata Store)]
end
subgraph "Infrastructure"
K8S[Kubernetes Cluster]
MONITORING[Monitoring Stack]
LOGGING[Logging System]
TRACING[Distributed Tracing]
end
CLIENT --> API_SERVER
API_SERVER --> PROCESSOR
PROCESSOR --> MODEL_INFERENCE
MODEL_INFERENCE --> VECTOR_DB
PROCESSOR --> FILE_STORE
PROCESSOR --> METADATA_DB
K8S --> API_SERVER
K8S --> PROCESSOR
K8S --> MODEL_INFERENCE
MONITORING --> API_SERVER
LOGGING --> PROCESSOR
TRACING --> MODEL_INFERENCE
```

**Diagram sources**
- [architecture.md](file://docs/architecture.md)
- [implementation-plan.md](file://docs/implementation-plan.md)

## Kubernetes Deployment Manifests

### Base Deployment Configuration

The following manifests provide a production-ready deployment configuration for the Secondself AI Brain:

#### Namespace Definition
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: secondself-ai
  labels:
    app.kubernetes.io/name: secondself-ai
    app.kubernetes.io/environment: production
```

#### Service Account and RBAC
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: secondself-ai-sa
  namespace: secondself-ai
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secondself-ai-role
  namespace: secondself-ai
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
```

#### Main Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secondself-ai-app
  namespace: secondself-ai
  labels:
    app.kubernetes.io/name: secondself-ai
    app.kubernetes.io/component: application
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: secondself-ai
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: secondself-ai
        app.kubernetes.io/component: application
    spec:
      serviceAccountName: secondself-ai-sa
      containers:
      - name: secondself-ai
        image: secondself-ai:latest
        ports:
        - containerPort: 8080
          protocol: TCP
        envFrom:
        - configMapRef:
            name: secondself-ai-config
        - secretRef:
            name: secondself-ai-secrets
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: uploads-volume
          mountPath: /app/tmp_uploads
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: secondself-ai-data
      - name: uploads-volume
        emptyDir: {}
```

**Section sources**
- [config.py](file://config.py)
- [requirements.txt](file://requirements.txt)

## Service Definitions

### HTTP Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: secondself-ai-service
  namespace: secondself-ai
  labels:
    app.kubernetes.io/name: secondself-ai
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app.kubernetes.io/name: secondself-ai
```

### Internal Processing Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: secondself-ai-processing
  namespace: secondself-ai
  labels:
    app.kubernetes.io/name: secondself-ai
    app.kubernetes.io/component: processing
spec:
  type: ClusterIP
  ports:
  - port: 9090
    targetPort: 9090
    protocol: TCP
    name: processing
  selector:
    app.kubernetes.io/name: secondself-ai
    app.kubernetes.io/component: processing
```

### Metrics Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: secondself-ai-metrics
  namespace: secondself-ai
  labels:
    app.kubernetes.io/name: secondself-ai
    app.kubernetes.io/component: metrics
spec:
  type: ClusterIP
  ports:
  - port: 9090
    targetPort: 9090
    protocol: TCP
    name: metrics
  selector:
    app.kubernetes.io/name: secondself-ai
    app.kubernetes.io/component: metrics
```

**Section sources**
- [pipeline.py](file://pipeline.py)

## Ingress Configuration

### Basic Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: secondself-ai-ingress
  namespace: secondself-ai
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - ai.example.com
    secretName: ai-example-tls
  rules:
  - host: ai.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secondself-ai-service
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: secondself-ai-service
            port:
              number: 80
      - path: /metrics
        pathType: Prefix
        backend:
          service:
            name: secondself-ai-metrics
            port:
              number: 9090
```

### Advanced Ingress with Rate Limiting
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: secondself-ai-ingress-advanced
  namespace: secondself-ai
  annotations:
    nginx.ingress.kubernetes.io/limit-rps: "100"
    nginx.ingress.kubernetes.io/limit-burst: "50"
    nginx.ingress.kubernetes.io/rate-limit-duration: "1m"
    nginx.ingress.kubernetes.io/rate-limit-request: "100"
    nginx.ingress.kubernetes.io/rate-limit-key: "$remote_addr"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - ai.example.com
    secretName: ai-example-tls
  rules:
  - host: ai.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secondself-ai-service
            port:
              number: 80
```

**Section sources**
- [config.py](file://config.py)

## Persistent Volume Claims

### Data Volume
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: secondself-ai-data
  namespace: secondself-ai
  labels:
    app.kubernetes.io/name: secondself-ai
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: ssd-storage
  selector:
    matchLabels:
      type: ssd
```

### Backup Volume
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: secondself-ai-backup
  namespace: secondself-ai
  labels:
    app.kubernetes.io/name: secondself-ai
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
  storageClassName: nfs-storage
```

### Cache Volume
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: secondself-ai-cache
  namespace: secondself-ai
  labels:
    app.kubernetes.io/name: secondself-ai
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: local-storage
```

**Section sources**
- [lib/storage.py](file://lib/storage.py)
- [data/index.json](file://data/index.json)

## ConfigMaps and Secrets Management

### ConfigMap for Application Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: secondself-ai-config
  namespace: secondself-ai
data:
  DATABASE_URL: "postgresql://user:pass@db-host:5432/secondself"
  REDIS_URL: "redis://redis-host:6379/0"
  MODEL_CACHE_SIZE: "1000"
  MAX_UPLOAD_SIZE: "100MB"
  LOG_LEVEL: "INFO"
  ENABLE_METRICS: "true"
  ENABLE_TRACING: "true"
  WORKER_PROCESSES: "4"
  REQUEST_TIMEOUT: "300"
```

### Secret for Sensitive Configuration
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: secondself-ai-secrets
  namespace: secondself-ai
type: Opaque
stringData:
  DATABASE_PASSWORD: "secure-database-password"
  REDIS_PASSWORD: "secure-redis-password"
  API_KEY: "your-api-key-here"
  SECRET_KEY: "your-secret-key-here"
  ENCRYPTION_KEY: "your-encryption-key-here"
```

### Environment-Specific ConfigMaps
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: secondself-ai-config-dev
  namespace: secondself-ai
data:
  LOG_LEVEL: "DEBUG"
  ENABLE_DEBUG: "true"
  MOCK_EXTERNAL_SERVICES: "true"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: secondself-ai-config-staging
  namespace: secondself-ai
data:
  LOG_LEVEL: "INFO"
  ENABLE_DEBUG: "false"
  MOCK_EXTERNAL_SERVICES: "false"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: secondself-ai-config-production
  namespace: secondself-ai
data:
  LOG_LEVEL: "WARNING"
  ENABLE_DEBUG: "false"
  MOCK_EXTERNAL_SERVICES: "false"
```

**Section sources**
- [config.py](file://config.py)

## Horizontal Pod Autoscaling

### HPA Configuration
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: secondself-ai-hpa
  namespace: secondself-ai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: secondself-ai-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: requests-per-second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
```

### Custom Metrics for AI Workload
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: custom-metrics-config
  namespace: secondself-ai
data:
  CUSTOM_METRICS_ENABLED: "true"
  METRICS_ENDPOINT: "/metrics/custom"
  SCALING_METRICS: |
    {
      "requests_per_second": {
        "threshold": 100,
        "window": "5m"
      },
      "queue_depth": {
        "threshold": 50,
        "window": "1m"
      },
      "model_inference_time": {
        "threshold": 2.0,
        "unit": "seconds"
      }
    }
```

**Section sources**
- [pipeline.py](file://pipeline.py)

## Resource Quotas

### Namespace Resource Quota
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: secondself-ai-quota
  namespace: secondself-ai
spec:
  hard:
    requests.cpu: "20"
    requests.memory: "40Gi"
    limits.cpu: "40"
    limits.memory: "80Gi"
    pods: "50"
    services: "10"
    persistentvolumeclaims: "10"
    configmaps: "20"
    secrets: "20"
```

### Limit Range
```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: secondself-ai-limits
  namespace: secondself-ai
spec:
  limits:
  - default:
      cpu: "2000m"
      memory: "4Gi"
    defaultRequest:
      cpu: "500m"
      memory: "1Gi"
    max:
      cpu: "4000m"
      memory: "8Gi"
    min:
      cpu: "100m"
      memory: "128Mi"
    type: Container
```

**Section sources**
- [requirements.txt](file://requirements.txt)

## Helm Chart Creation

### Chart Structure
```
secondself-ai/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── pvc.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── hpa.yaml
│   └── NOTES.txt
└── charts/
    └── postgresql/
    └── redis/
```

### Chart.yaml
```yaml
apiVersion: v2
name: secondself-ai
description: A Helm chart for deploying Secondself AI Brain
version: 1.0.0
appVersion: "1.0.0"
type: application
maintainers:
- name: Secondself Team
  email: team@secondself.ai
keywords:
- ai
- machine-learning
- knowledge-base
```

### values.yaml
```yaml
replicaCount: 3

image:
  repository: secondself-ai
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80
  targetPort: 8080

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
  - host: ai.example.com
    paths:
    - path: /
      pathType: Prefix

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 4Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

persistence:
  enabled: true
  size: 50Gi
  storageClass: ssd-storage

database:
  enabled: true
  auth:
    username: secondself
    password: secure-password
    database: secondself

redis:
  enabled: true
  auth:
    password: secure-redis-password
```

### Template Examples

#### Deployment Template
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "secondself-ai.fullname" . }}
  labels:
    {{- include "secondself-ai.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "secondself-ai.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "secondself-ai.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.service.targetPort }}
          protocol: TCP
        envFrom:
        - configMapRef:
            name: {{ include "secondself-ai.fullname" . }}-config
        - secretRef:
            name: {{ include "secondself-ai.fullname" . }}-secrets
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
```

**Section sources**
- [requirements.txt](file://requirements.txt)
- [config.py](file://config.py)

## Monitoring with Prometheus

### Prometheus Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
    - job_name: 'secondself-ai'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - secondself-ai
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app_kubernetes_io_name]
        regex: secondself-ai
        action: keep
      - source_labels: [__meta_kubernetes_pod_container_port_number]
        regex: '9090'
        action: keep
```

### ServiceMonitor for Prometheus Operator
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: secondself-ai-monitor
  namespace: secondself-ai
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: secondself-ai
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
```

### Grafana Dashboard
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: secondself-ai-dashboard
  namespace: monitoring
data:
  dashboard.json: |
    {
      "dashboard": {
        "title": "Secondself AI Brain",
        "panels": [
          {
            "title": "Request Rate",
            "targets": [
              {
                "expr": "rate(secondself_requests_total[5m])"
              }
            ]
          },
          {
            "title": "Response Latency",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(secondself_request_duration_seconds_bucket[5m]))"
              }
            ]
          }
        ]
      }
    }
```

**Section sources**
- [pipeline.py](file://pipeline.py)

## Logging Aggregation

### Fluentd Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: logging
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*secondself*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      read_from_head true
      <parse>
        @type json
        time_key time
        time_format %Y-%m-%dT%H:%M:%S.%NZ
      </parse>
    </source>
    
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      logstash_format true
      logstash_prefix secondself-ai
      logstash_dateformat %Y%m%d
      include_tag_key true
      tag_key @log_name
      flush_interval 5s
    </match>
```

### Log Collection DaemonSet
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd-agent
  namespace: logging
  labels:
    app: fluentd
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      containers:
      - name: fluentd
        image: fluentd:v1.14
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: fluentd-conf
          mountPath: /fluentd/etc
        resources:
          requests:
            cpu: 100m
            memory: 200Mi
          limits:
            cpu: 200m
            memory: 500Mi
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: fluentd-conf
        configMap:
          name: fluentd-config
```

**Section sources**
- [config.py](file://config.py)

## Distributed Tracing Setup

### Jaeger Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: tracing
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
      - name: jaeger
        image: jaegertracing/all-in-one:latest
        ports:
        - containerPort: 16686
          name: ui
        - containerPort: 14268
          name: collector
        - containerPort: 14250
          name: grpc
        env:
        - name: COLLECTOR_ZIPKIN_HOST_PORT
          value: ":9411"
```

### OpenTelemetry Collector
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
  namespace: tracing
spec:
  replicas: 1
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
    spec:
      containers:
      - name: otel-collector
        image: otel/opentelemetry-collector:latest
        args:
        - --config=/etc/otel-collector/config.yaml
        volumeMounts:
        - name: config
          mountPath: /etc/otel-collector
        ports:
        - containerPort: 4317
          name: otlp-grpc
        - containerPort: 4318
          name: otlp-http
        - containerPort: 13133
          name: health
      volumes:
      - name: config
        configMap:
          name: otel-collector-config
```

### Application Integration
```python
# Example instrumentation code
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize tracer
provider = TracerProvider()
exporter = JaegerExporter(agent_host_name="jaeger.tracing.svc.cluster.local")
processor = BatchSpanProcessor(exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

@app.route('/process')
def process_data():
    with tracer.start_as_current_span("data_processing") as span:
        # Your processing logic here
        return jsonify({"status": "processed"})
```

**Section sources**
- [pipeline.py](file://pipeline.py)

## Cluster Configuration

### Cluster Autoscaler Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-config
  namespace: kube-system
data:
  cloud-provider: aws
  skip-nodes-with-local-storage: "false"
  scan-interval: "10s"
  scale-down-delay-after-add: "10m"
  scale-down-unneeded-time: "10m"
  scale-down-utilization-threshold: "0.5"
```

### Node Pool Configuration
```yaml
apiVersion: nodepool.karpenter.sh/v1alpha5
kind: NodePool
metadata:
  name: secondself-ai-workers
spec:
  template:
    spec:
      requirements:
      - key: node.kubernetes.io/instance-type
        operator: In
        values: ["m5.xlarge", "m5.2xlarge", "c5.2xlarge"]
      - key: topology.kubernetes.io/zone
        operator: In
        values: ["us-east-1a", "us-east-1b", "us-east-1c"]
      taints:
      - key: workload-type
        value: ai-processing
        effect: NoSchedule
      labels:
        workload-type: ai-processing
  limits:
    resources:
      cpu: "100"
      memory: "400Gi"
  disruption:
    consolidationEnabled: true
    consolidateAfter: "5m"
```

**Section sources**
- [requirements.txt](file://requirements.txt)

## Node Affinity Rules

### Preferred Node Affinity
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secondself-ai-app
  namespace: secondself-ai
spec:
  template:
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: node.kubernetes.io/instance-type
                operator: In
                values: ["m5.xlarge", "m5.2xlarge", "c5.2xlarge"]
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values: ["us-east-1a", "us-east-1b"]
          - weight: 50
            preference:
              matchExpressions:
              - key: node.kubernetes.io/disk-type
                operator: In
                values: ["ssd"]
      tolerations:
      - key: workload-type
        value: ai-processing
        effect: NoSchedule
```

### Pod Anti-Affinity
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secondself-ai-app
  namespace: secondself-ai
spec:
  template:
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app.kubernetes.io/name
                operator: In
                values: ["secondself-ai"]
            topologyKey: "kubernetes.io/hostname"
```

**Section sources**
- [config.py](file://config.py)

## Disaster Recovery Procedures

### Backup Strategy
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: secondself-ai-backup
  namespace: secondself-ai
spec:
  schedule: "0 2 * * *"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: alpine:latest
            command:
            - /bin/sh
            - -c
            - |
              tar czf /backup/secondself-$(date +%Y%m%d).tar.gz /app/data
              aws s3 cp /backup/secondself-$(date +%Y%m%d).tar.gz s3://secondself-backups/
          volumeMounts:
          - name: data-volume
            mountPath: /app/data
          - name: backup-volume
            mountPath: /backup
          restartPolicy: OnFailure
          volumes:
          - name: data-volume
            persistentVolumeClaim:
              claimName: secondself-ai-data
          - name: backup-volume
            emptyDir: {}
```

### Restore Procedure
```bash
#!/bin/bash
# Restore script for Secondself AI Brain

# Download latest backup
aws s3 ls s3://secondself-backups/ | sort -r | head -1 | awk '{print $4}' > latest-backup.txt
LATEST_BACKUP=$(cat latest-backup.txt)
aws s3 cp s3://secondself-backups/$LATEST_BACKUP /tmp/restore.tar.gz

# Stop current deployment
kubectl rollout pause deployment/secondself-ai-app -n secondself-ai

# Delete existing PVC (if needed)
kubectl delete pvc secondself-ai-data -n secondself-ai

# Create new PVC
kubectl apply -f pvc.yaml -n secondself-ai

# Extract backup to PVC
kubectl exec -it $(kubectl get pod -l app=restorer -o jsonpath='{.items[0].metadata.name}') -n secondself-ai -- \
  tar xzf /tmp/restore.tar.gz -C /mnt/data

# Resume deployment
kubectl rollout resume deployment/secondself-ai-app -n secondself-ai

# Verify restore
kubectl rollout status deployment/secondself-ai-app -n secondself-ai
```

### Health Check and Validation
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: secondself-ai-health-check
  namespace: secondself-ai
spec:
  template:
    spec:
      containers:
      - name: health-check
        image: curlimages/curl:latest
        command:
        - /bin/sh
        - -c
        - |
          curl -f http://secondself-ai-service:80/health || exit 1
          curl -f http://secondself-ai-service:80/ready || exit 1
          echo "Health check passed"
      restartPolicy: Never
  restartPolicy: Never
```

**Section sources**
- [lib/storage.py](file://lib/storage.py)

## Rolling Updates and Rollback Strategies

### Blue-Green Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secondself-ai-blue
  namespace: secondself-ai
  labels:
    color: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: secondself-ai
      color: blue
  template:
    metadata:
      labels:
        app.kubernetes.io/name: secondself-ai
        color: blue
    spec:
      containers:
      - name: secondself-ai
        image: secondself-ai:v1.0.0
        ports:
        - containerPort: 8080
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secondself-ai-green
  namespace: secondself-ai
  labels:
    color: green
spec:
  replicas: 0
  selector:
    matchLabels:
      app.kubernetes.io/name: secondself-ai
      color: green
  template:
    metadata:
      labels:
        app.kubernetes.io/name: secondself-ai
        color: green
    spec:
      containers:
      - name: secondself-ai
        image: secondself-ai:v1.1.0
        ports:
        - containerPort: 8080
```

### Canary Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secondself-ai-canary
  namespace: secondself-ai
  labels:
    track: canary
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: secondself-ai
      track: canary
  template:
    metadata:
      labels:
        app.kubernetes.io/name: secondself-ai
        track: canary
    spec:
      containers:
      - name: secondself-ai
        image: secondself-ai:v1.1.0
        ports:
        - containerPort: 8080
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secondself-ai-stable
  namespace: secondself-ai
  labels:
    track: stable
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: secondself-ai
      track: stable
  template:
    metadata:
      labels:
        app.kubernetes.io/name: secondself-ai
        track: stable
    spec:
      containers:
      - name: secondself-ai
        image: secondself-ai:v1.0.0
        ports:
        - containerPort: 8080
```

### Automated Rollback Policy
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: secondself-ai-rollout
  namespace: secondself-ai
spec:
  replicas: 3
  revisionHistoryLimit: 5
  selector:
    matchLabels:
      app.kubernetes.io/name: secondself-ai
  template:
    metadata:
      labels:
        app.kubernetes.io/name: secondself-ai
    spec:
      containers:
      - name: secondself-ai
        image: secondself-ai:v1.1.0
        ports:
        - containerPort: 8080
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: {duration: 5m}
      - setWeight: 25
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {duration: 10m}
      analysis:
        templates:
        - templateName: success-rate
        startingStep: 1
        successCondition: result == "success"
        failureCondition: result == "failure"
```

**Section sources**
- [pipeline.py](file://pipeline.py)

## Performance Considerations

### Memory Optimization
- Configure appropriate JVM heap sizes for Java-based components
- Implement connection pooling for database connections
- Use object caching strategies to reduce memory pressure
- Monitor memory usage patterns and optimize garbage collection

### CPU Optimization
- Right-size CPU requests and limits based on actual usage
- Implement request queuing for burst traffic scenarios
- Use async processing for I/O-bound operations
- Optimize model loading and inference pipelines

### Network Optimization
- Enable HTTP/2 and keep-alive connections
- Implement proper load balancing strategies
- Use connection pooling for external service calls
- Configure appropriate timeouts and retry policies

### Storage Optimization
- Use appropriate storage classes based on access patterns
- Implement data tiering strategies
- Optimize database queries and indexing
- Use caching layers for frequently accessed data

## Troubleshooting Guide

### Common Issues and Solutions

#### Pod Startup Failures
```bash
# Check pod logs
kubectl logs -f $(kubectl get pod -l app=secondself-ai -o jsonpath='{.items[0].metadata.name}') -n secondself-ai

# Check events
kubectl describe pod $(kubectl get pod -l app=secondself-ai -o jsonpath='{.items[0].metadata.name}') -n secondself-ai

# Check resource quotas
kubectl describe quota -n secondself-ai
```

#### Connection Issues
```bash
# Test service connectivity
kubectl run test-curl --rm -it --image=curlimages/curl -- curl -v http://secondself-ai-service:80/health

# Check network policies
kubectl get networkpolicy -n secondself-ai

# Verify DNS resolution
kubectl run dns-test --rm -it --image=busybox -- nslookup secondself-ai-service
```

#### Performance Issues
```bash
# Monitor resource usage
kubectl top pods -n secondself-ai
kubectl top nodes

# Check for resource contention
kubectl describe pod $(kubectl get pod -l app=secondself-ai -o jsonpath='{.items[0].metadata.name}') -n secondself-ai

# Analyze logs for errors
kubectl logs -f $(kubectl get pod -l app=secondself-ai -o jsonpath='{.items[0].metadata.name}') -n secondself-ai --tail=1000
```

### Monitoring Dashboards
- Set up Grafana dashboards for key metrics
- Configure alerts for critical thresholds
- Implement distributed tracing for request flows
- Monitor error rates and latency percentiles

**Section sources**
- [config.py](file://config.py)
- [pipeline.py](file://pipeline.py)

## Conclusion

This comprehensive Kubernetes deployment guide provides everything needed to deploy the Secondself AI Brain application in production environments. The documented configurations ensure high availability, scalability, and reliability while maintaining optimal performance characteristics.

Key benefits of this deployment approach include:

- **Scalability**: Horizontal pod autoscaling handles varying workloads efficiently
- **Reliability**: Multi-replica deployments with automatic failover
- **Observability**: Comprehensive monitoring, logging, and tracing setup
- **Security**: Proper secrets management and network policies
- **Maintainability**: Helm charts simplify deployment and updates
- **Disaster Recovery**: Automated backups and restore procedures

The modular architecture allows for easy customization and extension based on specific organizational requirements. Regular monitoring and optimization should be performed to ensure optimal performance as the application scales and evolves.

For additional support or customization needs, refer to the application documentation and consider engaging with the development team for specialized requirements.