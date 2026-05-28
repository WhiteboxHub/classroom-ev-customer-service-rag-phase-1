# ==============================================================
# EV RAG Platform — Terraform Variables
# ==============================================================

variable "aws_region" {
  description = "AWS region for EV RAG platform deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "ev-rag-platform"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "db_instance_class" {
  description = "RDS instance class for PostgreSQL metadata DB"
  type        = string
  default     = "db.t3.medium"
}

variable "db_username" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "evrag_admin"
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "subnet_ids" {
  description = "VPC subnet IDs for EKS and RDS"
  type        = list(string)
  default     = []
}

variable "vpc_id" {
  description = "VPC ID for EV RAG platform"
  type        = string
  default     = ""
}
