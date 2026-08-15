output "cluster_name" {
  description = "Name of the provisioned Kind cluster"
  value       = kind_cluster.this.name
}

output "kubeconfig_path" {
  description = "Absolute path to the generated kubeconfig file"
  value       = kind_cluster.this.kubeconfig_path
}

output "endpoint" {
  description = "Kubernetes API server endpoint"
  value       = kind_cluster.this.endpoint
}

output "app_url" {
  description = "Local URL to access the Hello World application"
  value       = "http://localhost:${var.app_host_port}"
}
