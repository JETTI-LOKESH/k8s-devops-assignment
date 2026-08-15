variable "cluster_name" {
  description = "Name of the Kind Kubernetes cluster"
  type        = string
  default     = "devops-cluster"
}

variable "kubernetes_version" {
  description = "Kind node image — must match an available kindest/node tag"
  type        = string
  default     = "kindest/node:v1.31.0"
}

variable "app_host_port" {
  description = "Host port mapped to the NodePort service of the web application"
  type        = number
  default     = 8080
}
