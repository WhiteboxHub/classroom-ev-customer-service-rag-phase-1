# ==============================================================
# EV RAG Platform — Terraform Infrastructure
# AWS: EKS cluster, S3 buckets, RDS PostgreSQL, ElastiCache Redis
# ==============================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
  backend "s3" {
    bucket = "ev-rag-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# ---- S3 Buckets for EV Documentation ----
resource "aws_s3_bucket" "ev_docs" {
  bucket = "${var.project_name}-docs-${var.environment}"

  tags = {
    Name        = "${var.project_name}-docs"
    Environment = var.environment
    Project     = "EV-RAG-Platform"
    ManagedBy   = "Terraform"
  }
}

resource "aws_s3_bucket_versioning" "ev_docs_versioning" {
  bucket = aws_s3_bucket.ev_docs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ev_docs_sse" {
  bucket = aws_s3_bucket.ev_docs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ---- RDS PostgreSQL (Metadata DB) ----
resource "aws_db_instance" "ev_rag_postgres" {
  identifier           = "${var.project_name}-postgres-${var.environment}"
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = var.db_instance_class
  db_name              = "evragdb"
  username             = var.db_username
  password             = var.db_password
  allocated_storage    = 50
  max_allocated_storage = 200
  storage_type         = "gp3"
  storage_encrypted    = true
  multi_az             = var.environment == "prod" ? true : false
  skip_final_snapshot  = var.environment != "prod"

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  tags = {
    Name        = "${var.project_name}-postgres"
    Environment = var.environment
  }
}

# ---- ElastiCache Redis (Cache & Celery Broker) ----
resource "aws_elasticache_cluster" "ev_rag_redis" {
  cluster_id           = "${var.project_name}-redis-${var.environment}"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379

  tags = {
    Name        = "${var.project_name}-redis"
    Environment = var.environment
  }
}

# ---- EKS Cluster ----
resource "aws_eks_cluster" "ev_rag_eks" {
  name     = "${var.project_name}-eks-${var.environment}"
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = "1.28"

  vpc_config {
    subnet_ids = var.subnet_ids
  }

  tags = {
    Name        = "${var.project_name}-eks"
    Environment = var.environment
  }

  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy]
}

resource "aws_iam_role" "eks_cluster_role" {
  name = "${var.project_name}-eks-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}
