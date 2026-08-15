# Provision a single-node Kind cluster with host port mappings for local access.
#
# Architecture decision: Kind (Kubernetes in Docker) is chosen over Minikube
# because it:
#   - Requires no hypervisor (runs entirely in Docker)
#   - Works identically inside GitHub Actions runners (Docker-in-Docker)
#   - Starts in ~30 seconds on a modern laptop
#
# See DESIGN.md § Architectural Choices for full rationale.

resource "kind_cluster" "this" {
  name           = var.cluster_name
  wait_for_ready = true

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role  = "control-plane"
      image = var.kubernetes_version

      # Map NodePort 30080 (hello-app) to localhost:8080
      extra_port_mappings {
        container_port = 30080
        host_port      = var.app_host_port
        protocol       = "TCP"
      }
    }
  }
}
