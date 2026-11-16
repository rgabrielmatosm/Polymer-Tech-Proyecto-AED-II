# POLYMER · AWS con Terraform (EC2 + Docker Compose + HTTPS automático con Caddy y Let's Encrypt).
# Guía paso a paso: docs/final/DESPLIEGUE_AWS_TERRAFORM.md. Nada se crea hasta que TÚ ejecutes `terraform apply`.
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.7"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "polymer"
      ManagedBy = "terraform"
    }
  }
}
