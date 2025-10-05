# ============================================================================
# Sake Sensei - Terraform Variables
# ============================================================================

# ----------------------------------------------------------------------------
# General Configuration
# ----------------------------------------------------------------------------
variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "sakesensei"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
  default     = "<your-aws-account-id>"
}

# ----------------------------------------------------------------------------
# VPC Configuration
# ----------------------------------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

# ----------------------------------------------------------------------------
# ECS Configuration
# ----------------------------------------------------------------------------
variable "ecs_task_cpu" {
  description = "CPU units for ECS task (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 1024
}

variable "ecs_task_memory" {
  description = "Memory for ECS task in MB (512, 1024, 2048, 4096, 8192)"
  type        = number
  default     = 2048
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

variable "container_port" {
  description = "Container port for Streamlit app"
  type        = number
  default     = 8501
}

variable "health_check_path" {
  description = "Health check path for target group"
  type        = string
  default     = "/_stcore/health"
}

# ----------------------------------------------------------------------------
# Application Configuration
# ----------------------------------------------------------------------------
variable "app_image_tag" {
  description = "Docker image tag for deployment"
  type        = string
  default     = "latest"
}

# ----------------------------------------------------------------------------
# Environment Variables (from .env)
# ----------------------------------------------------------------------------

variable "agentcore_agent_id" {
  description = "AgentCore Agent ID"
  type        = string
  default     = ""
}

variable "agentcore_agent_alias_id" {
  description = "AgentCore Agent Alias ID"
  type        = string
  default     = ""
}

variable "agentcore_runtime_arn" {
  description = "AgentCore Runtime ARN"
  type        = string
  default     = ""
}

variable "dynamodb_users_table" {
  description = "DynamoDB Users table name"
  type        = string
  default     = "SakeSensei-Users"
}

variable "dynamodb_sake_table" {
  description = "DynamoDB Sake table name"
  type        = string
  default     = "SakeSensei-SakeMaster"
}

variable "dynamodb_brewery_table" {
  description = "DynamoDB Brewery table name"
  type        = string
  default     = "SakeSensei-BreweryMaster"
}

variable "dynamodb_tasting_table" {
  description = "DynamoDB Tasting table name"
  type        = string
  default     = "SakeSensei-TastingRecords"
}

variable "lambda_recommendation_url" {
  description = "Lambda Recommendation function URL"
  type        = string
  default     = ""
}

variable "lambda_preference_url" {
  description = "Lambda Preference function URL"
  type        = string
  default     = ""
}

variable "lambda_tasting_url" {
  description = "Lambda Tasting function URL"
  type        = string
  default     = ""
}

variable "lambda_brewery_url" {
  description = "Lambda Brewery function URL"
  type        = string
  default     = ""
}

variable "lambda_imagerecognition_url" {
  description = "Lambda Image Recognition function URL"
  type        = string
  default     = ""
}

# ----------------------------------------------------------------------------
# Tags
# ----------------------------------------------------------------------------
variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "SakeSensei"
    ManagedBy   = "Terraform"
    Environment = "dev"
    Owner       = "AI-Hakcathon"
    Team        = "13_S3"
  }
}
