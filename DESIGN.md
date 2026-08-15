# DESIGN.md — Technical Architecture & Design Decisions

---

## 1. Architectural Choices

### Why Kind + Terraform?

| Concern | Tool Chosen | Alternatives Considered | Reason |
|---|---|---|---|
| Cluster provisioning | **Terraform + `tehcyx/kind`** | Minikube, k3d | Kind runs purely in Docker (no VM/hypervisor), starts in ~30s, and — critically — works inside GitHub Actions runners without extra setup. Terraform ensures the cluster is declared as code and reproducible. |
| Container runtime | **Docker** | Podman, containerd | Universally available on developer workstations and CI runners. |
| Observability | **Metrics Server + K9s** | Prometheus/Grafana | Metrics Server is the Kubernetes-native resource metrics pipeline. K9s is a zero-setup TUI that surfaces real-time CPU/memory data. A full Prometheus stack adds ~500MB of containers that are unnecessary for a local demo. |
| Web framework | **Flask + Gunicorn** | FastAPI, Django | Flask is minimal, dependency-light, and straightforward to unit-test. Gunicorn is the industry-standard WSGI production server. |
| Database | **PostgreSQL 16 (Alpine)** | MySQL, SQLite | PostgreSQL is the reference enterprise RDBMS. The Alpine variant minimises image size and attack surface. |

### Two-Tier Architecture

```
┌──────────────────────────────────────┐
│          Kubernetes Namespace        │
│              hello-app               │
│                                      │
│  ┌─────────────────┐                 │
│  │  hello-app Pod  │◄── NodePort     │◄── localhost:8080 (host)
│  │  (Flask/Gunicorn│    30080        │
│  │   Port 5000)    │                 │
│  └────────┬────────┘                 │
│           │ ClusterIP:5432           │
│  ┌────────▼────────┐                 │
│  │  postgres Pod   │                 │
│  │  (Port 5432)    │                 │
│  └────────┬────────┘                 │
│           │ PVC (1Gi)                │
│  ┌────────▼────────┐                 │
│  │ PersistentVolume│                 │
│  │ (hostPath/Kind) │                 │
│  └─────────────────┘                 │
└──────────────────────────────────────┘
```

**Configuration separation:**
- `ConfigMap` holds non-sensitive values (`DB_HOST`, `DB_PORT`, `PORT`).
- `Secret` holds credentials (`DB_PASSWORD`). Values are base64-encoded for the local demo; in production these would be sourced from Azure Key Vault via the External Secrets Operator.

---

## 2. Scalability — Local → Azure AKS (Production HA)

| Dimension | Local (Kind, Single-Node) | Production (Azure AKS) |
|---|---|---|
| **Control Plane** | Single embedded node | AKS-managed HA control plane (3 replicas across AZs) |
| **Worker Nodes** | 1 Docker container | Node pools with autoscaler (`min: 2, max: 10`) |
| **Storage** | Kind hostPath PVC | Azure Managed Disks (Premium SSD) or Azure Files for RWX |
| **Database** | PostgreSQL in-cluster | Azure Database for PostgreSQL Flexible Server (HA mode) |
| **Ingress** | NodePort | NGINX Ingress Controller + Azure Application Gateway |
| **Secrets** | Base64 in YAML | Azure Key Vault + External Secrets Operator |
| **Container Registry** | `imagePullPolicy: Never` (local load) | Azure Container Registry (ACR) with geo-replication |
| **Observability** | Metrics Server + K9s | Azure Monitor + Managed Prometheus + Grafana |
| **TLS** | None | cert-manager + Let's Encrypt / internal CA |

### Migration Path

1. **Containerise** — The Dockerfile produces a portable image; no changes needed.
2. **Push image to ACR** — Replace `imagePullPolicy: Never` with ACR pull secret.
3. **Replace storage class** — Change PVC `storageClassName` from default (hostPath) to `managed-premium`.
4. **Deploy to AKS** — Apply the same K8s manifests; update namespace and resource limits for production sizing.
5. **Add HorizontalPodAutoscaler** — Scale `hello-app` replicas 2–10 based on CPU utilisation (requires Metrics Server, which AKS provides natively).
6. **Offload PostgreSQL** — Use Azure Database for PostgreSQL Flexible Server; remove in-cluster Deployment and PVC; update `DB_HOST` in ConfigMap.

---

## 3. Failure Analysis — Post-Mortem (SPOF)

### Identified SPOF: Single-Node Kind Cluster

**Description:**
The entire architecture runs on one Docker container acting as both control plane and worker. Any failure — Docker daemon crash, host OS reboot, disk I/O error — immediately takes down all workloads *and* the Kubernetes API server simultaneously.

**Impact in local scenario:**
- Zero redundancy for the web tier or database tier.
- PVC data survives only if the host disk is intact.
- No automatic recovery; manual `terraform apply` is required.

**Mitigation in production:**

| Layer | Mitigation |
|---|---|
| Control plane | AKS-managed HA control plane across 3 availability zones |
| Worker nodes | `PodDisruptionBudget` + multi-AZ node pools; `minAvailable: 1` for `hello-app` |
| Database | Azure PostgreSQL Flexible Server in Zone-Redundant HA mode (automatic failover < 60s) |
| Storage | Azure Managed Disk with zone-redundant storage (ZRS) replication |
| Application | Replicas ≥ 2 with pod anti-affinity rules to spread across nodes |

---

## 4. Trade-offs

### Security Trade-offs

| Trade-off | Local Decision | Production Mitigation |
|---|---|---|
| Secret management | Base64 values committed to repo (demo only) | Azure Key Vault + External Secrets Operator; never commit secrets |
| TLS | No TLS between components or externally | mTLS via Istio/Linkerd; TLS termination at Application Gateway |
| Network policies | No `NetworkPolicy` objects | Calico/Cilium policies restricting pod-to-pod traffic to minimum required |
| RBAC | Default `admin` kubeconfig | Workload Identity, minimal RBAC roles per service account |
| Image scanning | Not in pipeline | Trivy or Microsoft Defender for Containers in CI gate |

### Performance Trade-offs

| Trade-off | Local Decision | Production Mitigation |
|---|---|---|
| Gunicorn workers | 2 workers hardcoded | Tune `WEB_CONCURRENCY` per node CPU count; use async workers (gevent) if I/O-bound |
| Resource limits | Conservative (CPU: 200m, RAM: 256Mi) | Profile under load; right-size via VPA (Vertical Pod Autoscaler) |
| No caching layer | Direct DB queries on every request | Add Redis sidecar or Azure Cache for Redis for repeated read patterns |

### Complexity Trade-offs

| Trade-off | Local Decision | Production Mitigation |
|---|---|---|
| No service mesh | Direct pod-to-pod communication | Istio or Linkerd for traffic management, observability, and mTLS |
| Metrics only | Metrics Server without Prometheus | Managed Prometheus + Grafana in AKS; alerting via Azure Monitor |
| No GitOps | `kubectl apply` driven by Terraform/CI | Flux v2 or Argo CD for declarative, auditable cluster state |
| Docker Compose for CI smoke test | Simpler than spinning Kind in CI | Replace with dedicated staging cluster for full integration tests |
