# KubeLabs Production Deployment Architecture

## 1. Deployment Topology
KubeLabs can be deployed as a single-node containerized stack via Podman Compose or as a multi-tenant cluster on Kubernetes.

```mermaid
graph TD
    ALB[Ingress / ALB Gateway]
    
    subgraph KubeLabs [KubeLabs Namespace]
        Web[Web Frontend Deployment (Nginx)]
        API[Backend API Deployment (FastAPI)]
        Redis[(Redis Queue / Cache)]
        DB[(PostgreSQL Primary)]
    end
    
    subgraph SandboxNodes [Dedicated Worker Nodes]
        SandboxPool[Podman / CRI-O Rootless Sandbox Pods]
    end
    
    ALB -->|/| Web
    ALB -->|/api & /ws| API
    API --> DB
    API --> Redis
    API --> SandboxPool
```

## 2. Kubernetes Production Manifests
Deploying KubeLabs into Kubernetes:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubelabs-api
  namespace: kubelabs
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kubelabs-api
  template:
    metadata:
      labels:
        app: kubelabs-api
    spec:
      containers:
      - name: api
        image: registry.corp.com/kubelabs/api:v1.0.0
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: kubelabs-secrets
              key: database-url
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8000
```

## 3. High Availability Strategy
- API servers are stateless and scale horizontally behind standard Ingress controllers.
- Sandboxes are isolated on dedicated Kubernetes worker nodes with taints (`kubelabs.io/role=sandbox:NoSchedule`) to protect control-plane infrastructure.
- PostgreSQL runs in Multi-AZ configuration with read replicas.
