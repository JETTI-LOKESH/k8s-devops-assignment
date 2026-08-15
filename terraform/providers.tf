terraform {
  required_version = ">= 1.6.0"

  required_providers {
    # tehcyx/kind is the most actively maintained Terraform provider for Kind clusters.
    kind = {
      source  = "tehcyx/kind"
      version = "~> 0.4.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

# The Kind provider communicates with the Docker daemon on the local machine.
# No credentials are required; it uses the Docker socket automatically.
provider "kind" {}
