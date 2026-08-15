# k8s-devops-assignment

A two-tier Kubernetes application demonstrating Infrastructure as Code, container security best practices, and a full CI/CD pipeline.

**Stack:** Terraform (Kind provider) · Python Flask · PostgreSQL · GitHub Actions · Metrics Server

---

## Prerequisites

Ensure the following are installed on your local workstation before proceeding:

| Tool | Minimum Version | Install |
|---|---|---|
| Docker Desktop | 24+ | https://docs.docker.com/get-docker/ |
| Terraform | 1.6+ | https://developer.hashicorp.com/terraform/install |
| kubectl | 1.29+ | https://kubernetes.io/docs/tasks/tools/ |
| Kind | 0.24+ | https://kind.sigs.k8s.io/docs/user/quick-start/#installation |
| K9s *(optional)* | latest | https://k9scli.io/topics/install/ |
| Python | 3.12+ | https://www.python.org/downloads/ |

---

## Quick Start — Full Local Cluster

### Step 1 — Clone the repository

```bash
git clone <your-repo-url>
cd k8s-devops-assignment
```

### Step 2 — Provision the Kind cluster with Terraform

```bash
cd terraform
terraform init
terraform apply -auto-approve
cd ..
```

Terraform will:
- Pull the `tehcyx/kind` provider
- Create a single-node Kind cluster named `devops-cluster`
- Map NodePort `30080` → `localhost:8080` on your machine

Verify the cluster is running:

```bash
kubectl cluster-info --context kind-devops-cluster
kubectl get nodes
```

### Step 3 — Build the Docker image

```bash
docker build -t hello-app:latest ./app
```

### Step 4 — Load the image into Kind

Kind does not pull from Docker Hub by default. Load the locally-built image directly:

```bash
kind load docker-image hello-app:latest --name devops-cluster
```

### Step 5 — Deploy all Kubernetes manifests

```bash
# Create namespace first
kubectl apply -f k8s/namespace.yaml

# Apply all base manifests
kubectl apply -f k8s/

# Deploy Metrics Server (patched for Kind's self-signed certs)
kubectl apply -k k8s/observability/
```

### Step 6 — Wait for pods to be ready

```bash
kubectl get pods -n hello-app -w
```

Expected output once healthy:
```
NAME                         READY   STATUS    RESTARTS
hello-app-xxxxx              1/1     Running   0
postgres-xxxxx               1/1     Running   0
```

### Step 7 — Access the application

Open your browser or run:

```bash
curl http://localhost:8080/
curl http://localhost:8080/health
curl http://localhost:8080/db-check
```

---

## Run Unit Tests Locally

```bash
cd app
pip install -r requirements.txt pytest pytest-cov
pytest test_main.py -v --cov=main --cov-report=term-missing
```

---

## Run with Docker Compose (no Kubernetes required)

For a quick local run without Kind:

```bash
docker compose up --build
```

Application is available at `http://localhost:5000`.

Tear down:

```bash
docker compose down -v
```

---

## Observability with Metrics Server

After deploying Metrics Server, wait ~60 seconds then:

```bash
# Node resource usage
kubectl top nodes

# Pod resource usage
kubectl top pods -n hello-app
```

To launch K9s (if installed):

```bash
k9s --context kind-devops-cluster
```

---

## CI/CD Pipeline

The GitHub Actions pipeline at [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) runs automatically on every push to `main` or `develop`, and on all pull requests to `main`.

**Pipeline stages:**

```
push/PR
  │
  ├─ [test]        Run pytest unit tests with coverage
  │
  ├─ [build]       Build Docker image, save as artifact
  │
  └─ [smoke-test]  Docker Compose up → curl health/db endpoints → pass/fail
```

---

## Tear Down

Remove all Kubernetes resources:

```bash
kubectl delete namespace hello-app
```

Destroy the Kind cluster:

```bash
cd terraform
terraform destroy -auto-approve
```

Or directly with Kind:

```bash
kind delete cluster --name devops-cluster
```

---

## Project Structure

```
k8s-devops-assignment/
├── app/
│   ├── .dockerignore       # Excludes test files and caches from production image
│   ├── Dockerfile          # Multi-stage, non-root container build
│   ├── main.py             # Flask application
│   ├── requirements.txt    # Production Python dependencies
│   ├── requirements-dev.txt# Test-only dependencies (pytest, pytest-cov)
│   └── test_main.py        # Pytest unit tests
├── terraform/
│   ├── providers.tf        # Terraform + Kind provider configuration
│   ├── main.tf             # Kind cluster resource
│   ├── variables.tf        # Input variables
│   └── outputs.tf          # Cluster name, kubeconfig path, endpoint
├── k8s/
│   ├── namespace.yaml
│   ├── configmap.yaml      # Non-sensitive app configuration
│   ├── secret.yaml         # Credentials (demo only — see DESIGN.md)
│   ├── postgres-pvc.yaml   # Persistent volume claim for database
│   ├── postgres-deployment.yaml
│   ├── postgres-service.yaml
│   ├── app-deployment.yaml
│   ├── app-service.yaml    # NodePort 30080
│   ├── network-policy.yaml # Default-deny + allow-only-what's-needed policies
│   ├── pdb.yaml            # PodDisruptionBudget for hello-app
│   └── observability/
│       └── kustomization.yaml  # Metrics Server with Kind TLS patch
├── .github/
│   └── workflows/
│       └── ci-cd.yml       # GitHub Actions: test → build + Trivy scan → smoke test
├── docker-compose.yml      # Local dev / CI smoke test stack
├── pyproject.toml          # Pytest config and coverage settings
├── DESIGN.md               # Architecture, scalability, trade-offs
└── README.md               # This file
```

---

## Repository Access

Grant repository access to: **@jarred-utt_adbsg** (`jarred.utt@adbsafegate.com`)

Settings → Collaborators → Add people → search `jarred-utt_adbsg`
